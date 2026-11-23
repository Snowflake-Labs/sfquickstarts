import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import weight_space as ws


@pytest.fixture(scope="module")
def setup():
    return ws.build(seed=7)


def accuracy(weights, split):
    x, y = split
    return float((ws.forward(weights, x).argmax(1) == y).mean())


def test_planted_failure_hurts(setup):
    h, clean, _ = setup
    assert accuracy(clean, h._valset) - accuracy(h.base, h._valset) > 0.1


def test_scripted_control_repairs_and_patch_round_trips():
    h, _, _ = ws.build(seed=7)
    ws.run_writer(h, ws.scripted_writer(h))
    report = h.validate()["validation"]
    assert report["gain"] > 0.1
    patch = h.patch()
    assert list(patch["tensors"]) == ["block1.weight"]
    assert ws.fingerprint(ws.apply_patch(h.base, patch)) == ws.fingerprint(h.edited)


@pytest.mark.parametrize("action", [
    {"tool": "edit", "op": "set_entries", "tensor": "head.bias", "indices": [0], "values": [1.0]},
    {"tool": "edit", "op": "set_entries", "tensor": "embed.weight", "indices": [[0, 0]], "values": [0.0]},
    {"tool": "edit", "op": "set_entries", "tensor": "block1.bias", "indices": [0], "values": [float("nan")]},
    {"tool": "edit", "op": "set_entries", "tensor": "block1.bias", "indices": [0], "values": [1000]},
    {"tool": "edit", "op": "set_entries", "tensor": "block1.bias", "indices": [99], "values": [0.1]},
    {"tool": "generate", "split": "validation"},
    {"tool": "shell", "cmd": "ls"},
])
def test_refusals_cost_nothing(action):
    h, _, _ = ws.build(seed=7)
    result = h.step({"explanation": "probe", "action": action})
    assert "refused" in result
    assert h.passes == 0 and fingerprint_unchanged(h)


def fingerprint_unchanged(h):
    return ws.fingerprint(h.edited) == h.base_hash


def test_rescale_refused(setup):
    h, _, _ = setup
    with pytest.raises(ws.Refused):
        ws.check_edit(h.base, {**h.base, "block1.weight": h.base["block1.weight"] * 0.5})


def test_missing_explanation_is_not_run_and_ends_after_three():
    h, _, _ = ws.build(seed=7)
    for _ in range(3):
        result = h.step({"action": {"tool": "generate"}})
        assert "refused" in result
    assert h.passes == 0 and h.done


def test_budget_exhausts():
    h, _, _ = ws.build(seed=7, max_passes=1)
    assert "paired" in h.step({"explanation": "a", "action": {"tool": "generate", "weights": "both"}})
    assert "refused" in h.step({"explanation": "b", "action": {"tool": "generate"}})
    assert h.passes == 1


def test_holdout_hides_records():
    h, _, _ = ws.build(seed=7)
    result = h.step({"explanation": "a", "action": {"tool": "generate", "split": "holdout", "weights": "both"}})
    assert "records" not in result


def test_patch_rejects_tampering():
    h, _, _ = ws.build(seed=7)
    ws.run_writer(h, ws.scripted_writer(h))
    patch = h.patch()
    patch["tensors"]["block1.weight"]["edited_values"][0][0] += 0.01
    with pytest.raises(ValueError):
        ws.apply_patch(h.base, patch)


def test_parse_reply():
    assert ws.parse_reply('```json\n{"explanation": "x", "final": "y"}\n```') == {"explanation": "x", "final": "y"}
    assert ws.parse_reply('"{\\"explanation\\": \\"x\\"}"') == {"explanation": "x"}
    assert ws.parse_reply("no json here") is None


def test_random_projection_is_not_a_repair(setup):
    h, _, _ = setup
    d = np.random.default_rng(0).normal(size=32)
    d /= np.linalg.norm(d)
    w = {**h.base, "block1.weight": h.base["block1.weight"] - np.outer(h.base["block1.weight"] @ d, d)}
    assert accuracy(w, h._valset) < accuracy(h.base, h._valset) + 0.03


def test_miles_splits_are_disjoint_and_specs_deterministic():
    assert set(ws.MILES_TRAIN_SEEDS).isdisjoint(ws.MILES_HELDOUT_SEEDS)
    assert ws.task_spec(1234) == ws.task_spec(1234)
    assert {ws.task_spec(s)["nuisance"] for s in range(1000, 1030)} == set(ws.NUISANCE_FEATURES)


def test_miles_reward_controls():
    seeds = list(ws.MILES_HELDOUT_SEEDS)[:6]
    oracle = np.mean([ws.score_proposal(s, ws.oracle_response(s))["reward"] for s in seeds])
    wrong = np.mean([ws.score_proposal(s, json.dumps({"edits": [{"op": "project_out", "tensor": "block1.weight", "side": "input",
                     "direction": "feature:" + next(f for f in ws.NUISANCE_FEATURES if f != ws.task_spec(s)["nuisance"])}]}))["reward"]
                     for s in seeds])
    assert oracle > 0.5 and oracle > wrong


@pytest.mark.parametrize("response", [
    "not json", '{"edits": []}', '{"edits": [{"op": "drop_edit", "tensor": "block1.weight"}]}',
    '{"edits": [{"op": "set_entries", "tensor": "head.bias", "indices": [[0]], "values": [1]}]}',
    '{"edits": [{"op": "project_out", "tensor": "block1.weight", "direction": "feature:nope"}]}',
    "x" * 5000, None,
])
def test_miles_reward_rejects_invalid(response):
    out = ws.score_proposal(90000, response)
    assert out["reward"] == 0.0 and not out["valid"]


def test_miles_records_hide_answer(tmp_path):
    path = tmp_path / "train.jsonl"
    assert ws.write_miles_jsonl(str(path), [1000, 1001], "train") == 2
    row = json.loads(path.read_text().splitlines()[0])
    assert row["metadata"] == {"task": "wsp_repair", "seed": 1000, "split": "train"}
    assert ws.task_spec(1000)["nuisance"] not in json.dumps(row["metadata"])
