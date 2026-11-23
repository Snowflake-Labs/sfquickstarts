"""Snowflake-native weight-space programming harness, after dspy-wsp.

A frontier "writer" LM repairs a small trained network by editing its weights
directly: no gradients, no training. The protocol follows dspy-wsp and
*Sparks of Weight-Space Programming* (Takehi, Teoh, Zhang, Khattab, 2026):

- The writer works in turns. Each turn carries an explanation and exactly one
  action. A turn without an explanation is returned unrun, at most twice in a row.
- Forward passes (`generate`, `activations`) cost one unit of budget each,
  whatever their size. Refused requests cost nothing. `inspect` is free but capped.
- Practice records are visible. The holdout returns aggregate scores only. The
  validation set is never shown to the writer and is used once, at the end, as a
  paired original-vs-edited comparison with the same examples.
- Guardrails refuse edits to the embedding and the output head, non-finite or
  out-of-range values, and edits that only rescale a whole tensor. Every edit is
  re-checked before each pass.
- The result is a patch: changed tensors with SHA-256 hashes of the base and the
  edited values, plus the ordered edit log.

Differences from dspy-wsp: the writer returns JSON edit operations, never code,
so nothing it emits is executed (no sandbox is needed). The student is a small
NumPy MLP trained in-process, with a known planted failure, so a run is cheap and
the result can be checked against an analytic repair. This is a teaching harness,
not evidence about editing production LMs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re

import numpy as np

FEATURES = ["amount_due", "login_errors", "api_errors", "days_overdue",
            "seats", "outage_minutes", "password_resets", "caps_ratio", "emoji_count", "ticket_length"]
CLASSES = ["billing", "technical", "account"]
NUISANCE_FEATURES = ["caps_ratio", "emoji_count", "ticket_length"]   # carry no label information
TENSORS = ["embed.weight", "embed.bias", "block1.weight", "block1.bias", "head.weight", "head.bias"]
PROTECTED = {"embed.weight", "embed.bias", "head.weight", "head.bias"}
VALUE_LIMIT = 10.0
MAX_VECTOR_OPS_ENTRIES = 128
MAX_RESULT_CHARS = 3500


# ---------------------------------------------------------------- data + student

def make_dataset(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic ticket features in [0, 1] with a labeling rule that ignores caps_ratio."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.0, 1.0, size=(n, len(FEATURES)))
    billing = 1.6 * x[:, 0] + 1.2 * x[:, 3] + 0.6 * x[:, 4]
    technical = 1.5 * x[:, 2] + 1.4 * x[:, 5] + 0.5 * x[:, 1]
    account = 1.7 * x[:, 6] + 1.1 * x[:, 1] + 0.4 * x[:, 4]
    y = np.argmax(np.stack([billing, technical, account], axis=1), axis=1)
    return x, y


def _relu(z):
    return np.maximum(z, 0.0)


def forward(weights: dict, x: np.ndarray, return_hidden: bool = False):
    h0 = _relu(x @ weights["embed.weight"].T + weights["embed.bias"])
    h1 = _relu(h0 @ weights["block1.weight"].T + weights["block1.bias"])
    logits = h1 @ weights["head.weight"].T + weights["head.bias"]
    return (logits, h0, h1) if return_hidden else logits


def train_student(seed: int = 7, hidden: int = 32, epochs: int = 400, lr: float = 0.05) -> dict:
    """Full-batch gradient descent on the clean task. Training builds the student; the writer never uses gradients."""
    rng = np.random.default_rng(seed)
    x, y = make_dataset(3000, seed + 1000)
    d = len(FEATURES)
    w = {
        "embed.weight": rng.normal(0, math.sqrt(2 / d), (hidden, d)),
        "embed.bias": np.zeros(hidden),
        "block1.weight": rng.normal(0, math.sqrt(2 / hidden), (hidden, hidden)),
        "block1.bias": np.zeros(hidden),
        "head.weight": rng.normal(0, math.sqrt(1 / hidden), (len(CLASSES), hidden)),
        "head.bias": np.zeros(len(CLASSES)),
    }
    onehot = np.eye(len(CLASSES))[y]
    for _ in range(epochs):
        z0 = x @ w["embed.weight"].T + w["embed.bias"]; h0 = _relu(z0)
        z1 = h0 @ w["block1.weight"].T + w["block1.bias"]; h1 = _relu(z1)
        logits = h1 @ w["head.weight"].T + w["head.bias"]
        p = np.exp(logits - logits.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)
        g = (p - onehot) / len(x)
        grads = {"head.weight": g.T @ h1, "head.bias": g.sum(0)}
        g1 = (g @ w["head.weight"]) * (z1 > 0)
        grads["block1.weight"], grads["block1.bias"] = g1.T @ h0, g1.sum(0)
        g0 = (g1 @ w["block1.weight"]) * (z0 > 0)
        grads["embed.weight"], grads["embed.bias"] = g0.T @ x, g0.sum(0)
        for name in w:
            w[name] -= lr * 10 * grads[name]
    return w


def feature_direction(weights: dict, x: np.ndarray, feature: str) -> np.ndarray:
    """Unit direction in embed activations that tracks one input feature (high minus low)."""
    j = FEATURES.index(feature)
    _, h0, _ = forward(weights, x, return_hidden=True)
    high, low = x[:, j] > 0.6, x[:, j] < 0.4
    v = h0[high].mean(0) - h0[low].mean(0)
    return v / np.linalg.norm(v)


def plant_failure(clean: dict, x_ref: np.ndarray, strength: float = 10.0, nuisance: str = "caps_ratio",
                  target: str = "billing") -> tuple[dict, dict]:
    """Add a rank-1 shortcut to block1: a nuisance feature in the embedding pushes block1 toward a target class.

    Returns the corrupted weights and the hidden ground truth (for the analytic control only;
    it is never shown to the writer)."""
    w = copy.deepcopy(clean)
    if nuisance not in NUISANCE_FEATURES or target not in CLASSES:
        raise ValueError("unknown nuisance feature or target class")
    v = feature_direction(clean, x_ref, nuisance)
    t = CLASSES.index(target)
    others = [c for c in range(len(CLASSES)) if c != t]
    u = np.maximum(w["head.weight"][t] - w["head.weight"][others].mean(0), 0.0)
    u /= np.linalg.norm(u)
    w["block1.weight"] = w["block1.weight"] + strength * np.outer(u, v)
    return w, {"u": u, "v": v, "strength": strength, "nuisance": nuisance, "target": target}


# ---------------------------------------------------------------- hashing + stats

def tensor_sha(t: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(t, dtype=np.float64).tobytes()).hexdigest()


def fingerprint(weights: dict) -> str:
    return hashlib.sha256("".join(tensor_sha(weights[n]) for n in TENSORS).encode()).hexdigest()


def paired(original_correct: np.ndarray, edited_correct: np.ndarray) -> dict:
    diff = edited_correct.astype(float) - original_correct.astype(float)
    n = len(diff)
    se = float(diff.std(ddof=1) / math.sqrt(n)) if n > 1 else float("nan")
    return {"n": n, "original": round(float(original_correct.mean()), 4), "edited": round(float(edited_correct.mean()), 4),
            "gain": round(float(diff.mean()), 4), "se": round(se, 4)}


# ---------------------------------------------------------------- guardrails

class Refused(ValueError):
    """A request the harness will not run. Refusals cost no budget."""


def _vector(values, length: int, what: str) -> np.ndarray:
    if not isinstance(values, list) or len(values) != length:
        raise Refused(f"{what} must be a list of {length} numbers")
    arr = np.array([float(v) for v in values])
    if not np.all(np.isfinite(arr)):
        raise Refused(f"{what} must be finite")
    return arr


def check_edit(base: dict, edited: dict) -> None:
    for name in TENSORS:
        b, e = base[name], edited[name]
        if e.shape != b.shape:
            raise Refused(f"{name}: shape changed")
        if not np.all(np.isfinite(e)) or np.abs(e).max() > VALUE_LIMIT:
            raise Refused(f"{name}: values must be finite and within ±{VALUE_LIMIT}")
        if np.array_equal(b, e):
            continue
        if name in PROTECTED:
            raise Refused(f"{name} is protected (embedding and output head cannot be edited)")
        nz = np.abs(b) > 1e-12
        if nz.any():
            ratio = e[nz] / b[nz]
            if np.allclose(ratio, ratio[0], rtol=1e-6) and np.allclose(e[~nz], 0):
                raise Refused(f"{name}: an edit that only rescales the whole tensor is refused")


# ---------------------------------------------------------------- harness

class Harness:
    """Holds the base weights, the writer's current edit, the splits and the budget."""

    def __init__(self, base: dict, practice, holdout, valset, max_passes: int = 12, max_inspects: int = 40,
                 max_turns: int = 40, seed: int = 0):
        self.base = {k: v.copy() for k, v in base.items()}
        self.base_hash = fingerprint(self.base)
        self.edited = {k: v.copy() for k, v in base.items()}
        self.practice, self.holdout, self._valset = practice, holdout, valset
        self.max_passes, self.max_inspects, self.max_turns = max_passes, max_inspects, max_turns
        self.passes = self.inspects = self.turns = 0
        self.refusals_in_row = 0
        self.refs: dict[str, np.ndarray] = {}
        self.edit_log: list[dict] = []
        self.transcript: list[dict] = []
        self.notes = ""
        self.final: dict | None = None
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------ tools

    def _split(self, name):
        if name == "practice":
            return self.practice
        if name == "holdout":
            return self.holdout
        raise Refused("split must be 'practice' or 'holdout' (the validation set is hidden)")

    def _correct(self, weights, split):
        x, y = split
        pred = forward(weights, x).argmax(1)
        return pred, pred == y

    def _spend(self):
        if self.passes >= self.max_passes:
            raise Refused("forward-pass budget is exhausted; send a final answer")
        self.passes += 1

    def generate(self, split="practice", weights="both", max_records=12, only_failures=True):
        x, y = self._split(split)
        if weights not in ("original", "edited", "both"):
            raise Refused("weights must be 'original', 'edited' or 'both'")
        check_edit(self.base, self.edited)
        self._spend()
        out = {"split": split}
        p0, c0 = self._correct(self.base, (x, y))
        p1, c1 = self._correct(self.edited, (x, y))
        if weights == "both":
            out["paired"] = paired(c0, c1)
        else:
            c = c0 if weights == "original" else c1
            out["accuracy"] = round(float(c.mean()), 4)
        pred = p1 if weights != "original" else p0
        conf = np.zeros((len(CLASSES), len(CLASSES)), int)
        for t, p in zip(y, pred):
            conf[t, p] += 1
        out["confusion_rows_true_cols_pred"] = {"classes": CLASSES, "matrix": conf.tolist()}
        if split == "practice":
            correct = pred == y
            idx = np.where(~correct)[0] if only_failures else np.arange(len(y))
            idx = idx[: max(0, min(int(max_records), 32))]
            out["records"] = [{"i": int(i), "features": {f: round(float(v), 2) for f, v in zip(FEATURES, x[i])},
                               "label": CLASSES[y[i]], "pred": CLASSES[pred[i]]} for i in idx]
        return out

    def activations(self, split="practice", weights="edited", group_by="correct", feature=None):
        """Mean embed (h0) and block1 (h1) activations for two groups, and their difference.

        Differences are stored as refs (e.g. 'h0_diff') that edit ops can name instead of typing vectors."""
        x, y = self._split(split)
        if split != "practice":
            raise Refused("activations are only available on practice")
        w = self.base if weights == "original" else self.edited
        check_edit(self.base, self.edited)
        if group_by == "correct":
            pred = forward(w, x).argmax(1)
            a, b = pred != y, pred == y
            labels = ("wrong", "right")
        elif group_by == "feature":
            if feature not in FEATURES:
                raise Refused(f"feature must be one of {FEATURES}")
            j = FEATURES.index(feature)
            a, b = x[:, j] > 0.6, x[:, j] < 0.4
            labels = (f"{feature}>0.6", f"{feature}<0.4")
        else:
            raise Refused("group_by must be 'correct' or 'feature'")
        if a.sum() < 2 or b.sum() < 2:
            raise Refused("a group has fewer than 2 items")
        self._spend()
        _, h0, h1 = forward(w, x, return_hidden=True)
        out = {"groups": {labels[0]: int(a.sum()), labels[1]: int(b.sum())}}
        for name, h in (("h0", h0), ("h1", h1)):
            diff = h[a].mean(0) - h[b].mean(0)
            self.refs[f"{name}_diff"] = diff
            unit = diff / (np.linalg.norm(diff) or 1.0)
            self.refs[f"{name}_diff_unit"] = unit
            top = np.argsort(-np.abs(diff))[:8]
            out[name] = {"diff_norm": round(float(np.linalg.norm(diff)), 4),
                         "top_units": [{"unit": int(k), "diff": round(float(diff[k]), 3)} for k in top],
                         "ref": f"{name}_diff_unit"}
        if group_by == "correct":
            # How strongly each input feature differs between wrong and right items.
            fd = x[a].mean(0) - x[b].mean(0)
            out["feature_mean_diff"] = {f: round(float(v), 3) for f, v in zip(FEATURES, fd)}
        return out

    def inspect(self, tensor, what="stats", rows=None, cols=None, k=3, ref=None):
        if self.inspects >= self.max_inspects:
            raise Refused("inspect limit reached")
        if what == "ref":
            if ref not in self.refs:
                raise Refused(f"unknown ref; known: {sorted(self.refs)}")
            self.inspects += 1
            return {"ref": ref, "values": [round(float(v), 4) for v in self.refs[ref]]}
        if tensor not in TENSORS:
            raise Refused(f"tensor must be one of {TENSORS}")
        self.inspects += 1
        t = self.edited[tensor]
        out = {"tensor": tensor, "shape": list(t.shape), "protected": tensor in PROTECTED}
        if what == "stats":
            out.update(mean=round(float(t.mean()), 4), std=round(float(t.std()), 4),
                       min=round(float(t.min()), 4), max=round(float(t.max()), 4))
        elif what == "slice":
            r = slice(*rows) if rows else slice(0, min(8, t.shape[0]))
            if t.ndim == 1:
                out["values"] = [round(float(v), 3) for v in t[r]][:64]
            else:
                c = slice(*cols) if cols else slice(0, min(8, t.shape[1]))
                block = t[r, c]
                if block.size > 64:
                    raise Refused("slice is larger than 64 values")
                out["values"] = np.round(block, 3).tolist()
        elif what in ("svd", "svd_of_edit"):
            if t.ndim != 2:
                raise Refused("svd needs a matrix")
            m = t - self.base[tensor] if what == "svd_of_edit" else t
            uu, s, vt = np.linalg.svd(m)
            k = max(1, min(int(k), 5))
            out["singular_values"] = [round(float(v), 4) for v in s[:k]]
            for i in range(k):
                self.refs[f"{tensor}.u{i}"], self.refs[f"{tensor}.v{i}"] = uu[:, i], vt[i]
            out["refs"] = [f"{tensor}.u{i}" for i in range(k)] + [f"{tensor}.v{i}" for i in range(k)]
        elif what == "alignment":
            # Cosine between each input-side right singular vector and a ref.
            if ref not in self.refs:
                raise Refused(f"unknown ref; known: {sorted(self.refs)}")
            uu, s, vt = np.linalg.svd(t)
            r_ = self.refs[ref] / (np.linalg.norm(self.refs[ref]) or 1.0)
            if len(r_) != vt.shape[1]:
                raise Refused("ref length does not match the tensor's input side")
            out["cosine_with_right_singular_vectors"] = [round(float(vt[i] @ r_), 4) for i in range(min(5, len(s)))]
            out["singular_values"] = [round(float(v), 4) for v in s[:5]]
        else:
            raise Refused("what must be stats, slice, svd, svd_of_edit, alignment or ref")
        return out

    # ------------------------------------------------------------ edits

    def _resolve(self, spec, length, what):
        if isinstance(spec, str):
            if spec not in self.refs:
                raise Refused(f"unknown ref '{spec}'; known: {sorted(self.refs)}")
            vec = self.refs[spec]
            if len(vec) != length:
                raise Refused(f"ref '{spec}' has length {len(vec)}, expected {length}")
            return vec
        return _vector(spec, length, what)

    def edit(self, op: dict):
        name = op.get("tensor")
        if name not in TENSORS:
            raise Refused(f"tensor must be one of {TENSORS}")
        if name in PROTECTED:
            raise Refused(f"{name} is protected (embedding and output head cannot be edited)")
        kind = op.get("op")
        current = self.edited[name]
        new = current.copy()
        if kind == "drop_edit":
            new = self.base[name].copy()
        elif kind == "project_out":
            if current.ndim != 2:
                raise Refused("project_out needs a matrix")
            side = op.get("side", "input")
            n = current.shape[1] if side == "input" else current.shape[0]
            d = self._resolve(op.get("direction"), n, "direction")
            d = d / (np.linalg.norm(d) or 1.0)
            new = current - np.outer(current @ d, d) if side == "input" else current - np.outer(d, d @ current)
        elif kind == "add_rank1":
            if current.ndim != 2:
                raise Refused("add_rank1 needs a matrix")
            u = self._resolve(op.get("u"), current.shape[0], "u")
            v = self._resolve(op.get("v"), current.shape[1], "v")
            new = current + float(op.get("scale", 1.0)) * np.outer(u, v)
        elif kind == "set_entries":
            idx, vals = op.get("indices", []), op.get("values", [])
            if len(idx) != len(vals) or not 0 < len(idx) <= MAX_VECTOR_OPS_ENTRIES:
                raise Refused(f"set_entries needs 1–{MAX_VECTOR_OPS_ENTRIES} matching indices and values")
            for ix, v in zip(idx, vals):
                ix = tuple(int(i) for i in (ix if isinstance(ix, list) else [ix]))
                if len(ix) != current.ndim or any(not 0 <= i < s for i, s in zip(ix, current.shape)):
                    raise Refused(f"index {list(ix)} out of range for shape {list(current.shape)}")
                new[ix] = float(v)
        else:
            raise Refused("op must be project_out, add_rank1, set_entries or drop_edit")
        candidate = {**self.edited, name: new}
        check_edit(self.base, candidate)
        self.edited = candidate
        self.edit_log.append({k: v for k, v in op.items() if k in ("op", "tensor", "side", "scale")} |
                             {"refs": [op[k] for k in ("direction", "u", "v") if isinstance(op.get(k), str)]})
        changed = int((np.abs(new - self.base[name]) > 1e-12).sum())
        return {"applied": kind, "tensor": name, "entries_changed_vs_base": changed, "of": int(new.size),
                "edit_frobenius_norm": round(float(np.linalg.norm(new - self.base[name])), 4)}

    # ------------------------------------------------------------ turns

    def step(self, reply: dict) -> dict:
        """Run one writer turn. Returns the tool result shown to the writer."""
        self.turns += 1
        if not isinstance(reply, dict) or not str(reply.get("explanation", "")).strip():
            self.refusals_in_row += 1
            result = {"refused": "every turn needs a non-empty 'explanation'; the action was not run",
                      "strikes": self.refusals_in_row}
            if self.refusals_in_row > 2:
                self.final = {"summary": "ended: three turns in a row without an explanation"}
            self.transcript.append({"turn": self.turns, "reply": reply, "result": result})
            return result
        self.refusals_in_row = 0
        if reply.get("notes"):
            self.notes = str(reply["notes"])[:2000]
        if "final" in reply:
            self.final = {"summary": str(reply["final"])[:2000]}
            result = {"ok": "final answer recorded; the harness will now validate the current edit"}
        else:
            action = reply.get("action") or {}
            tool = action.get("tool")
            args = {k: v for k, v in action.items() if k != "tool"}
            before = self.passes
            try:
                if tool == "generate":
                    result = self.generate(**args)
                elif tool == "activations":
                    result = self.activations(**args)
                elif tool == "inspect":
                    result = self.inspect(**args)
                elif tool == "edit":
                    result = self.edit(args)
                else:
                    raise Refused("tool must be generate, activations, inspect or edit")
            except Refused as error:
                self.passes = before
                result = {"refused": str(error)}
            except TypeError as error:
                self.passes = before
                result = {"refused": f"bad arguments: {error}"}
        result["budget"] = {"passes_used": self.passes, "passes_left": self.max_passes - self.passes,
                            "inspects_left": self.max_inspects - self.inspects, "turns_left": self.max_turns - self.turns}
        if self.turns >= self.max_turns and self.final is None:
            self.final = {"summary": "ended: turn limit"}
        self.transcript.append({"turn": self.turns, "reply": reply, "result": result})
        return result

    @property
    def done(self):
        return self.final is not None

    # ------------------------------------------------------------ end of run

    def validate(self, fallback_if_worse: bool = False) -> dict:
        """Score the hidden validation set once, paired, with the same examples for both weights."""
        check_edit(self.base, self.edited)
        _, c0 = self._correct(self.base, self._valset)
        _, c1 = self._correct(self.edited, self._valset)
        report = {"validation": paired(c0, c1)}
        if fallback_if_worse and report["validation"]["gain"] < 0:
            self.edited = {k: v.copy() for k, v in self.base.items()}
            report["fell_back_to_original"] = True
        return report

    def patch(self) -> dict:
        """The changed tensors with base and edited hashes, plus the ordered edit log."""
        tensors = {}
        for name in TENSORS:
            delta = self.edited[name] - self.base[name]
            if np.any(np.abs(delta) > 1e-12):
                tensors[name] = {"shape": list(delta.shape), "base_sha256": tensor_sha(self.base[name]),
                                 "edited_sha256": tensor_sha(self.edited[name]),
                                 "entries_changed": int((np.abs(delta) > 1e-12).sum()),
                                 "frobenius": round(float(np.linalg.norm(delta)), 6),
                                 "edited_values": self.edited[name].tolist()}
        total = sum(self.base[n].size for n in TENSORS)
        changed = sum(t["entries_changed"] for t in tensors.values())
        return {"base_fingerprint": self.base_hash, "edited_fingerprint": fingerprint(self.edited),
                "fraction_of_weights_changed": round(changed / total, 6), "tensors": tensors, "edit_log": self.edit_log}


def apply_patch(base: dict, patch: dict) -> dict:
    """Rebuild edited weights from a patch, checking every hash."""
    if fingerprint(base) != patch["base_fingerprint"]:
        raise ValueError("patch was made for different base weights")
    out = {k: v.copy() for k, v in base.items()}
    for name, t in patch["tensors"].items():
        if tensor_sha(base[name]) != t["base_sha256"]:
            raise ValueError(f"{name}: base hash mismatch")
        out[name] = np.array(t["edited_values"], dtype=np.float64)
        if tensor_sha(out[name]) != t["edited_sha256"]:
            raise ValueError(f"{name}: edited hash mismatch")
    check_edit(base, out)
    if fingerprint(out) != patch["edited_fingerprint"]:
        raise ValueError("edited fingerprint mismatch")
    return out


# ---------------------------------------------------------------- writer prompt + parsing

TASK_PROMPT = """You are a weight-space programmer. A small classifier routes support tickets to
{classes}. Its inputs are {n_features} features in [0,1]: {features}.
Network: embed (Linear {n_features}->32, ReLU) -> block1 (Linear 32->32, ReLU) -> head (Linear 32->3).
Tensors: {shapes}. Protected (cannot edit): {protected}. You may edit block1.weight and block1.bias.

The model underperforms on practice data. Find the mechanism inside the network that causes the
errors and repair it with a targeted weight edit. You have no gradients and no training. You can
only read weights and run the budgeted tools below. Prefer small, explainable edits.

Each turn, reply with ONE JSON object and nothing else:
  {{"explanation": "<why this step>", "action": {{...}}, "notes": "<optional running notes>"}}
or, when you are done:
  {{"explanation": "<why you are stopping>", "final": "<summary of the mechanism and your edit>"}}
A turn without an explanation is returned unrun. Do not write code; you can only send JSON actions.

Actions (forward passes cost 1 unit of budget each; refused requests cost nothing):
  {{"tool":"generate","split":"practice"|"holdout","weights":"original"|"edited"|"both","max_records":12,"only_failures":true}}
      Scores the split. "both" gives a paired gain with its standard error. The holdout returns aggregates only.
  {{"tool":"activations","group_by":"correct"|"feature","feature":"<name if group_by=feature>","weights":"original"|"edited"}}
      Mean embed (h0) and block1 (h1) activations of two groups and their difference, stored as refs
      "h0_diff_unit" and "h1_diff_unit". With group_by=correct it also reports which input features differ.
Free actions (limited count):
  {{"tool":"inspect","tensor":"<name>","what":"stats"|"slice"|"svd"|"svd_of_edit"|"alignment"|"ref",
    "rows":[start,stop],"cols":[start,stop],"k":3,"ref":"<ref name>"}}
      svd stores refs "<tensor>.u0", "<tensor>.v0", ... ; alignment reports cosines between the tensor's
      right singular vectors and a ref.
  {{"tool":"edit","op":"project_out","tensor":"block1.weight","side":"input"|"output","direction":"<ref>" or [numbers]}}
  {{"tool":"edit","op":"add_rank1","tensor":"block1.weight","u":"<ref>"|[...],"v":"<ref>"|[...],"scale":1.0}}
  {{"tool":"edit","op":"set_entries","tensor":"<name>","indices":[[i,j],...],"values":[...]}}
  {{"tool":"edit","op":"drop_edit","tensor":"<name>"}}   (restores the original tensor)
Guardrails: values must be finite and within ±{limit}; whole-tensor rescales are refused.
At the end the harness scores your current edit once on a hidden validation set.
Budget: {passes} forward passes, {inspects} inspects, {turns} turns."""


def task_prompt(h: Harness) -> str:
    return TASK_PROMPT.format(classes=", ".join(CLASSES), features=", ".join(FEATURES), n_features=len(FEATURES),
                              shapes=", ".join(f"{n} {list(h.base[n].shape)}" for n in TENSORS),
                              protected=", ".join(sorted(PROTECTED)), limit=VALUE_LIMIT,
                              passes=h.max_passes, inspects=h.max_inspects, turns=h.max_turns)


def conversation(h: Harness, keep_last: int = 10) -> str:
    """Task, notes and the most recent turns. Older turns are dropped (the notes act as the handoff)."""
    parts = [task_prompt(h)]
    if h.notes:
        parts.append(f"Your notes so far:\n{h.notes}")
    if len(h.transcript) > keep_last:
        parts.append(f"({len(h.transcript) - keep_last} earlier turns omitted; rely on your notes.)")
    for t in h.transcript[-keep_last:]:
        parts.append(f"TURN {t['turn']} YOU SENT:\n{json.dumps(t['reply'])[:1500]}")
        parts.append(f"RESULT:\n{json.dumps(t['result'])[:MAX_RESULT_CHARS]}")
    parts.append("Reply with your next JSON object only.")
    return "\n\n".join(parts)


def parse_reply(raw) -> dict | None:
    """Extract one JSON object from the writer's text. Returns None if there is none."""
    text = raw
    for _ in range(3):
        if isinstance(text, str):
            stripped = text.strip()
            try:
                text = json.loads(stripped)
                continue
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", stripped, re.S)
                if not match:
                    return None
                try:
                    text = json.loads(match.group(0))
                except json.JSONDecodeError:
                    return None
        break
    return text if isinstance(text, dict) else None


# ---------------------------------------------------------------- setup + controls

def build(seed: int = 7, max_passes: int = 12, max_inspects: int = 40, max_turns: int = 40,
          nuisance: str = "caps_ratio", target: str = "billing", strength: float = 10.0):
    """Train the clean student, plant the failure, and return (harness, clean, truth)."""
    clean = train_student(seed)
    x_ref, _ = make_dataset(2000, seed + 2000)
    broken, truth = plant_failure(clean, x_ref, strength, nuisance, target)
    practice = make_dataset(300, seed + 1)
    holdout = make_dataset(100, seed + 2)
    valset = make_dataset(400, seed + 3)
    h = Harness(broken, practice, holdout, valset, max_passes=max_passes, max_inspects=max_inspects, max_turns=max_turns)
    return h, clean, truth


def scripted_writer(h: Harness):
    """A fixed, non-LLM policy used as an offline control. It is not model output."""
    yield {"explanation": "Baseline paired score on practice.", "action": {"tool": "generate", "weights": "both"}}
    yield {"explanation": "Which features and units separate wrong from right items?",
           "action": {"tool": "activations", "group_by": "correct", "weights": "original"}}
    yield {"explanation": "Errors track caps_ratio, a nuisance feature; get its embed direction.",
           "action": {"tool": "activations", "group_by": "feature", "feature": "caps_ratio", "weights": "original"}}
    yield {"explanation": "Look for an outlier direction in block1.", "action": {"tool": "inspect", "tensor": "block1.weight", "what": "svd", "k": 3}}
    yield {"explanation": "Does the top input-side singular vector line up with caps_ratio?",
           "action": {"tool": "inspect", "tensor": "block1.weight", "what": "alignment", "ref": "h0_diff_unit"}}
    yield {"explanation": "Project the outlier input direction out of block1.",
           "action": {"tool": "edit", "op": "project_out", "tensor": "block1.weight", "side": "input", "direction": "block1.weight.v0"}}
    yield {"explanation": "Check the edit on the holdout.", "action": {"tool": "generate", "split": "holdout", "weights": "both"}}
    yield {"explanation": "Done.", "final": "Projected block1's outlier, caps_ratio-aligned input direction out of block1."}


def run_writer(h: Harness, writer) -> Harness:
    """Drive a writer: a generator of reply dicts, or a callable(prompt_text) -> raw text."""
    if callable(writer) and not hasattr(writer, "send"):
        while not h.done:
            raw = writer(conversation(h))
            h.step(parse_reply(raw) or {"explanation": "", "unparsed": str(raw)[:500]})
    else:
        for reply in writer:
            h.step(reply)
            if h.done:
                break
    return h


# ---------------------------------------------------------------- Miles: train a proposer policy
#
# Miles (https://github.com/radixark/miles) trains an open-weight policy with RL. Here the policy
# reads a one-shot summary of a broken student and returns a JSON edit; the reward applies it under
# the same guardrails and scores it on that instance's hidden validation split. Instances vary the
# student seed, the nuisance feature, the target class and the shortcut strength, so no single
# memorized edit solves the family. Train and held-out instances use disjoint seed ranges.

MILES_TRAIN_SEEDS = range(1000, 6000)
MILES_HELDOUT_SEEDS = range(90000, 90500)
MAX_POLICY_EDITS = 3
MAX_RESPONSE_CHARS = 4096


def task_spec(seed: int) -> dict:
    """Instance parameters derived only from the seed (so a reward worker can rebuild it)."""
    rng = np.random.default_rng(seed)
    return {"seed": int(seed), "nuisance": str(rng.choice(NUISANCE_FEATURES)), "target": str(rng.choice(CLASSES)),
            "strength": round(float(rng.uniform(8.0, 12.0)), 3)}


_INSTANCES: dict[int, tuple] = {}


def instance(seed: int):
    """(harness, clean, truth) for one task seed, cached per process."""
    if seed not in _INSTANCES:
        spec = task_spec(seed)
        if len(_INSTANCES) > 256:
            _INSTANCES.clear()
        _INSTANCES[seed] = build(seed=spec["seed"], nuisance=spec["nuisance"], target=spec["target"], strength=spec["strength"])
    return _INSTANCES[seed]


def observation(h: Harness) -> dict:
    """What the policy sees: practice-set evidence and block1's spectrum. No validation data, no ground truth."""
    x, y = h.practice
    logits, h0, _ = forward(h.base, x, return_hidden=True)
    pred = logits.argmax(1)
    wrong, right = pred != y, pred == y
    conf = np.zeros((len(CLASSES), len(CLASSES)), int)
    for t, p in zip(y, pred):
        conf[t, p] += 1
    _, s, vt = np.linalg.svd(h.base["block1.weight"])
    align = {}
    for f in FEATURES:
        d = feature_direction(h.base, x, f)
        align[f] = [round(float(vt[i] @ d), 3) for i in range(4)]
    return {"practice_accuracy": round(float(right.mean()), 4),
            "confusion_rows_true_cols_pred": {"classes": CLASSES, "matrix": conf.tolist()},
            "feature_mean_wrong_minus_right": {f: round(float(v), 3) for f, v in zip(FEATURES, x[wrong].mean(0) - x[right].mean(0))},
            "block1_singular_values": [round(float(v), 3) for v in s[:6]],
            "cosine_of_feature_direction_with_block1_v": align}


POLICY_PROMPT = """A small classifier routes support tickets to {classes} from {n} features in [0,1]:
{features}. Network: embed (Linear {n}->32, ReLU) -> block1 (Linear 32->32, ReLU) -> head (Linear 32->3).
Some features carry no label information. The model has a defect in block1 that hurts accuracy.
Find it from the evidence below and repair it with at most {max_edits} edits to block1.weight or block1.bias.
Embed and head are protected. Do not write code.

Evidence from the practice set (original weights):
{evidence}

Direction refs you may use:
  "block1.weight.v0" .. "block1.weight.v3"   block1's top right singular vectors (input side)
  "block1.weight.u0" .. "block1.weight.u3"   block1's top left singular vectors (output side)
  "feature:<name>"                           embed-activation direction of a feature (high minus low)
Edit ops:
  {{"op":"project_out","tensor":"block1.weight","side":"input"|"output","direction":"<ref>"}}
  {{"op":"add_rank1","tensor":"block1.weight","u":"<ref>","v":"<ref>","scale":<number>}}
  {{"op":"set_entries","tensor":"block1.bias","indices":[[i]],"values":[<number>]}}
Return ONLY a JSON object: {{"explanation": "<the mechanism>", "edits": [ ... ]}}"""


def policy_prompt(h: Harness) -> str:
    return POLICY_PROMPT.format(classes=", ".join(CLASSES), n=len(FEATURES), features=", ".join(FEATURES),
                                max_edits=MAX_POLICY_EDITS, evidence=json.dumps(observation(h)))


def _load_policy_refs(h: Harness) -> None:
    u, _, vt = np.linalg.svd(h.base["block1.weight"])
    for i in range(4):
        h.refs[f"block1.weight.u{i}"], h.refs[f"block1.weight.v{i}"] = u[:, i], vt[i]
    for f in FEATURES:
        h.refs[f"feature:{f}"] = feature_direction(h.base, h.practice[0], f)


def score_proposal(seed: int, response) -> dict:
    """Apply a policy response to a fresh copy of one instance and score it on the hidden validation split.

    reward = (edited - broken) / (clean - broken) on validation, clipped to [-1, 1]; 0 for anything invalid."""
    base_h, clean, _ = instance(seed)
    out = {"seed": seed, "valid": False, "reward": 0.0}
    if not isinstance(response, str) or len(response) > MAX_RESPONSE_CHARS:
        out["error"] = "response must be text of at most 4096 characters"
        return out
    reply = parse_reply(response)
    edits = reply.get("edits") if isinstance(reply, dict) else None
    if not isinstance(edits, list) or not 0 < len(edits) <= MAX_POLICY_EDITS or not all(isinstance(e, dict) for e in edits):
        out["error"] = f"expected 1-{MAX_POLICY_EDITS} edit objects under 'edits'"
        return out
    h = Harness(base_h.base, base_h.practice, base_h.holdout, base_h._valset)
    _load_policy_refs(h)
    try:
        for e in edits:
            if e.get("op") == "drop_edit":
                raise Refused("drop_edit is not a repair")
            h.edit(e)
    except (Refused, TypeError, ValueError) as error:
        out["error"] = str(error)
        return out
    val = h.validate()["validation"]
    gap = accuracy_on(clean, h._valset) - val["original"]
    reward = (val["edited"] - val["original"]) / gap if gap > 1e-9 else 0.0
    out.update(valid=True, reward=round(float(np.clip(reward, -1.0, 1.0)), 4), validation=val,
               fraction_changed=h.patch()["fraction_of_weights_changed"])
    return out


def accuracy_on(weights: dict, split) -> float:
    x, y = split
    return float((forward(weights, x).argmax(1) == y).mean())


def miles_records(seeds, split: str) -> list[dict]:
    """One Miles prompt record per seed. Metadata carries only the seed and split, never the answer."""
    rows = []
    for seed in seeds:
        h, _, _ = instance(int(seed))
        rows.append({"prompt": [{"role": "user", "content": policy_prompt(h)}], "label": "",
                     "metadata": {"task": "wsp_repair", "seed": int(seed), "split": split}})
    return rows


def write_miles_jsonl(path: str, seeds, split: str) -> int:
    rows = miles_records(seeds, split)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return len(rows)


def oracle_response(seed: int) -> str:
    """The analytic control for one instance (uses the hidden nuisance; never a policy output)."""
    spec = task_spec(seed)
    return json.dumps({"explanation": f"{spec['nuisance']} is a shortcut in block1", "edits": [
        {"op": "project_out", "tensor": "block1.weight", "side": "input", "direction": f"feature:{spec['nuisance']}"}]})
