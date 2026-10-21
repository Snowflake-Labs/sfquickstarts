"""Offline contracts and opt-in turbopuffer retrieval; no implicit network calls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
import hashlib
from importlib.metadata import version
import json
import math
import re
import time
from typing import Callable
import uuid


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def normalized(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


@dataclass(frozen=True)
class Example:
    id: str
    dataset: str
    revision: str
    split: str
    family: str
    duplicate_group: str
    question: str
    answer: str
    available_on: str
    grade: str = ""
    grade_source: str = ""

    def __post_init__(self):
        if self.split not in {"train", "dev", "test"}:
            raise ValueError("Unknown split")
        for key in ("id", "dataset", "revision", "family", "duplicate_group", "question"):
            if not getattr(self, key).strip():
                raise ValueError(f"Missing {key}")
        date.fromisoformat(self.available_on)


def freeze_examples(examples):
    """Validate explicit splits; return a stable manifest, never inferred labels.

    duplicate_group must be assigned by a reviewed near-duplicate process. Text
    normalization detects exact duplicates only, not arbitrary paraphrases.
    """
    if not examples:
        raise ValueError("Empty dataset")
    ids, groups = set(), {}
    for item in examples:
        if item.id in ids:
            raise ValueError("Duplicate example ID")
        ids.add(item.id)
        for kind, key in (("family", item.family), ("duplicate", item.duplicate_group),
                          ("text", normalized(item.question))):
            group = (item.dataset, kind, key)
            if group in groups and groups[group] != item.split:
                raise ValueError(f"Cross-split {kind} leakage: {item.id}")
            groups[group] = item.split
    records = sorted((asdict(item) for item in examples), key=lambda row: row["id"])
    return {"sha256": digest(records), "count": len(records),
            "splits": {split: sum(item.split == split for item in examples)
                       for split in ("train", "dev", "test")},
            "status": "local_split_manifest_not_source_authentication"}


def financebench_rows(rows, *, revision, split_assignments, duplicate_groups,
                      availability):
    """Adapt caller-supplied FinanceBench rows. Gold remains local/evaluator-only.

    No loader downloads data. Dates and document grouping must be reviewed by the
    caller; source-document evidence is not silently supplied to the responder.
    """
    examples = [Example(
        id=row["financebench_id"], dataset="financebench", revision=revision,
        split=split_assignments[row["financebench_id"]], family=row["doc_name"],
        duplicate_group=duplicate_groups[row["financebench_id"]],
        question=row["question"], answer=row["answer"],
        available_on=availability[row["financebench_id"]],
    ) for row in rows]
    freeze_examples(examples)
    return examples


def gsm8k_rows(rows, *, revision, split, duplicate_groups, available_on):
    examples = [Example(
        id=row["id"], dataset="gsm8k", revision=revision, split=split,
        family=duplicate_groups[row["id"]], duplicate_group=duplicate_groups[row["id"]],
        question=row["question"], answer=row["answer"], available_on=available_on,
    ) for row in rows]
    freeze_examples(examples)
    return examples


@dataclass(frozen=True)
class Scope:
    stage: str
    dataset: str
    revision: str
    target_id: str
    target_family: str
    target_duplicate_group: str
    as_of: str
    run_id: str = ""

    def filters(self):
        date.fromisoformat(self.as_of)
        if self.stage not in {"fewshot", "candidate", "judge"}:
            raise ValueError("Unknown retrieval stage")
        if not all((self.dataset, self.revision, self.target_id,
                    self.target_family, self.target_duplicate_group)):
            raise ValueError("Incomplete retrieval scope")
        clauses = [("dataset", "Eq", self.dataset), ("revision", "Eq", self.revision),
                   ("stage", "Eq", self.stage), ("available_on", "Lte", self.as_of)]
        if self.stage == "candidate":
            if not self.run_id:
                raise ValueError("Candidate retrieval requires a run ID")
            clauses += [("run_id", "Eq", self.run_id),
                        ("problem_id", "Eq", self.target_id)]
        else:
            clauses += [("split", "In", ["train", "dev"] if self.stage == "fewshot" else ["dev"]),
                        ("problem_id", "NotEq", self.target_id),
                        ("family", "NotEq", self.target_family),
                        ("duplicate_group", "NotEq", self.target_duplicate_group)]
            if self.stage == "judge":
                clauses += [("independently_graded", "Eq", True)]
        return ("And", clauses)


def reference_rows(examples, stage):
    freeze_examples(examples)
    if stage not in {"fewshot", "judge"}:
        raise ValueError("Reference stage required")
    rows = []
    for item in examples:
        allowed = item.split in {"train", "dev"} if stage == "fewshot" else item.split == "dev"
        if not allowed:
            continue
        if stage == "judge" and (item.grade not in {"pass", "fail"} or not item.grade_source):
            raise ValueError("Judge references require independently reviewed grades and provenance")
        rows.append(dict(id=item.id, content=item.question, answer=item.answer,
                         dataset=item.dataset, revision=item.revision, split=item.split,
                         stage=stage, problem_id=item.id, family=item.family,
                         duplicate_group=item.duplicate_group, available_on=item.available_on,
                         grade=item.grade, grade_source=item.grade_source,
                         independently_graded=bool(item.grade and item.grade_source)))
    return rows


def eligible(row, scope):
    """Local defense in depth mirrors the server-side scope filter."""
    for field, operator, expected in scope.filters()[1]:
        value = row.get(field)
        if value is None:
            return False
        if operator == "Eq" and value != expected:
            return False
        if operator == "NotEq" and value == expected:
            return False
        if operator == "In" and value not in expected:
            return False
        if operator == "Lte" and value > expected:
            return False
    return True


def reciprocal_rank_fusion(rankings, *, constant=60):
    if type(constant) is not int or constant <= 0:
        raise ValueError("RRF constant must be a positive integer")
    scores, ranks = {}, {}
    for arm, identifiers in enumerate(rankings):
        unique = list(dict.fromkeys(identifiers))
        for rank, identifier in enumerate(unique, 1):
            scores[identifier] = scores.get(identifier, 0.0) + 1.0 / (constant + rank)
            ranks.setdefault(identifier, {})[str(arm)] = rank
    return [{"id": identifier, "rrf_score": scores[identifier],
             "ranks": ranks[identifier], "fused_rank": index}
            for index, identifier in enumerate(sorted(scores, key=lambda key: (-scores[key], key)), 1)]


class HybridRetriever:
    """Injected SDK and embedding callbacks; both gates are required for queries.

    RRF is computed locally from turbopuffer's two ranked lists to retain raw
    ranks and deterministic ID tie-breaking. No claim of native-RRF tie parity.
    An embed callback must return a vector and must not silently change provider.
    """

    def __init__(self, client, embed: Callable, *, namespaces, embedding_model,
                 dimensions, sdk_version, approved_external=False,
                 approved_embeddings=False):
        if set(namespaces) != {"fewshot", "candidate", "judge"} or len(set(namespaces.values())) != 3:
            raise ValueError("Three distinct namespaces are required")
        if not embedding_model or type(dimensions) is not int or dimensions <= 0 or not sdk_version:
            raise ValueError("Pin SDK version, embedding model and dimensions")
        self.client, self.embed = client, embed
        self.namespaces, self.model, self.dimensions = namespaces, embedding_model, dimensions
        self.sdk_version = sdk_version
        self.approved_external, self.approved_embeddings = approved_external, approved_embeddings
        self.events = []

    def _check(self):
        if not self.approved_external or not self.approved_embeddings:
            raise PermissionError("External transfer and embedding approvals are required")
        if version("turbopuffer") != self.sdk_version:
            raise RuntimeError("Installed turbopuffer does not match the reviewed SDK pin")

    def _vector(self, text):
        vector = list(self.embed(text))
        if len(vector) != self.dimensions or any(type(value) not in (int, float) or not math.isfinite(value) for value in vector):
            raise ValueError("Embedding dimension or finite-number contract failed")
        return vector

    def index(self, rows, *, stage, approved_rows_sha256):
        self._check()
        if not rows or digest(rows) != approved_rows_sha256:
            raise PermissionError("Review and approve the exact export rows hash")
        if stage not in self.namespaces or len({row["id"] for row in rows}) != len(rows):
            raise ValueError("Invalid stage or duplicate index IDs")
        allowed = {"id", "content", "answer", "dataset", "revision", "split", "stage",
                   "problem_id", "family", "duplicate_group", "available_on", "grade",
                   "grade_source", "independently_graded", "run_id"}
        for row in rows:
            if set(row) - allowed or row["stage"] != stage:
                raise ValueError("Unexpected export fields or stage")
            if stage != "candidate" and row["split"] not in {"train", "dev"}:
                raise ValueError("Held-out rows cannot enter reference indexes")
            if stage == "judge" and (row["split"] != "dev" or not row.get("independently_graded")
                                     or not row.get("grade_source")):
                raise ValueError("Ungraded judge reference")
            date.fromisoformat(row["available_on"])
        enriched = [dict(row, vector=self._vector(row["content"])) for row in rows]
        return self.client.namespace(self.namespaces[stage]).write(
            upsert_rows=enriched, distance_metric="cosine_distance",
            schema={"content": {"type": "string", "full_text_search": True}})

    def retrieve(self, query, scope, *, limit=5, pool_size=20):
        self._check()
        if not 1 <= limit <= pool_size <= 100:
            raise ValueError("Use 1 <= limit <= pool_size <= 100")
        event = {"request_id": str(uuid.uuid4()), "scope": asdict(scope),
                 "query_sha256": digest(query), "namespace": self.namespaces[scope.stage],
                 "embedding_model": self.model, "dimensions": self.dimensions,
                 "sdk_version": self.sdk_version, "pool_size": pool_size, "limit": limit,
                 "utc": datetime.now(timezone.utc).isoformat(), "rrf_constant": 60}
        start = time.perf_counter()
        try:
            filters = scope.filters()
            common = dict(filters=filters, limit=pool_size, include_attributes=True)
            response = self.client.namespace(self.namespaces[scope.stage]).multi_query(queries=[
                dict(common, rank_by=("vector", "ANN", self._vector(query))),
                dict(common, rank_by=("content", "BM25", query)),
            ])
            if len(response.results) != 2:
                raise ValueError("Expected vector and BM25 results")
            rows, rankings = {}, []
            for result in response.results:
                identifiers = []
                for hit in result.rows:
                    row = hit.model_dump() if hasattr(hit, "model_dump") else dict(hit)
                    row.pop("vector", None)
                    if not eligible(row, scope):
                        raise ValueError("Server returned a row outside the approved scope")
                    identifier = str(row["id"])
                    row["id"] = identifier
                    # Search-specific $dist may differ across the two lists.
                    row.pop("$dist", None)
                    if identifier in rows and rows[identifier] != row:
                        raise ValueError("Conflicting content for a retrieved ID")
                    rows[identifier] = row
                    identifiers.append(identifier)
                rankings.append(identifiers)
            fused = reciprocal_rank_fusion(rankings)
            event.update(status="ok", rankings=rankings, fused=fused,
                         retrieved_rows_sha256=digest(rows), filters=filters)
            return [dict(rows[hit["id"]], retrieval=hit) for hit in fused[:limit]]
        except Exception as exc:
            event.update(status="error", error_type=type(exc).__name__, error=str(exc))
            raise
        finally:
            event["latency_ms"] = (time.perf_counter() - start) * 1000
            self.events.append(event)