"""Offline tests; no dataset download, model call or network access."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
import unittest

from examples.live_verification_demo.financebench_retrieval import (
    Example, HybridRetriever, Scope, digest, eligible, freeze_examples,
    reciprocal_rank_fusion, reference_rows,
)
from examples.live_verification_demo.financebench_experiment import (
    Candidate, Judgment, Rate, call_budget, candidate_rows, judge_summary,
    offline_demo, rate_context, repeated_judging, run_frozen_pool, select_candidates,
)
from examples.live_verification_demo.managed_mcp_probe import probe, validate_endpoint


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.dev = Example("dev", "synthetic", "v1", "dev", "a", "a",
                           "Question one", "answer", "2020-01-01", "pass", "human")
        self.target = replace(self.dev, id="test", split="test", family="b",
                              duplicate_group="b", question="Question two")
        self.scope = Scope("fewshot", "synthetic", "v1", "test", "b", "b", "2020-01-02", "run")

    def test_manifest_order_independent(self):
        self.assertEqual(freeze_examples([self.dev, self.target]), freeze_examples([self.target, self.dev]))

    def test_cross_split_leakage(self):
        for change in ({"family": "a"}, {"duplicate_group": "a"}, {"question": "QUESTION ONE!"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                freeze_examples([self.dev, replace(self.target, **change)])

    def test_no_test_answers_exported(self):
        rows = reference_rows([self.dev, self.target], "fewshot")
        self.assertEqual([row["id"] for row in rows], ["dev"])
        self.assertTrue(eligible(rows[0], self.scope))
        self.assertFalse(eligible(dict(rows[0], available_on="2021-01-01"), self.scope))

    def test_judge_independent_grade_required(self):
        with self.assertRaises(ValueError):
            reference_rows([replace(self.dev, grade_source="")], "judge")

    def test_candidate_scope_isolation(self):
        candidate = Candidate("c", "run", "test", "answer")
        row = candidate_rows([candidate], self.scope)[0]
        scope = replace(self.scope, stage="candidate")
        self.assertTrue(eligible(row, scope))
        self.assertFalse(eligible(dict(row, run_id="other"), scope))
        self.assertFalse(eligible(dict(row, problem_id="other"), scope))
        with self.assertRaises(ValueError):
            candidate_rows([replace(candidate, problem_id="other")], self.scope)

    def test_rrf_ties_duplicates_and_empty(self):
        result = reciprocal_rank_fusion([["b", "b", "a"], ["a", "b"]])
        self.assertEqual([hit["id"] for hit in result], ["a", "b"])
        self.assertEqual(result[0]["rrf_score"], result[1]["rrf_score"])
        self.assertEqual(reciprocal_rank_fusion([[], []]), [])

    def retriever(self, **kwargs):
        return HybridRetriever(Mock(), Mock(return_value=[1., 0., 0.]),
                               namespaces={"fewshot": "f", "candidate": "c", "judge": "j"},
                               embedding_model="fixture", dimensions=3, sdk_version="test-pin", **kwargs)

    def test_external_disabled_before_callbacks(self):
        retriever = self.retriever()
        with self.assertRaises(PermissionError):
            retriever.retrieve("question", self.scope)
        retriever.client.namespace.assert_not_called()
        retriever.embed.assert_not_called()

    @patch("examples.live_verification_demo.financebench_retrieval.version", return_value="test-pin")
    def test_query_scope_and_provenance(self, installed_version):
        retriever = self.retriever(approved_external=True, approved_embeddings=True)
        row = reference_rows([self.dev], "fewshot")[0]
        response = SimpleNamespace(results=[SimpleNamespace(rows=[row]), SimpleNamespace(rows=[row])])
        retriever.client.namespace.return_value.multi_query.return_value = response
        self.assertEqual(retriever.retrieve("question", self.scope)[0]["id"], "dev")
        queries = retriever.client.namespace.return_value.multi_query.call_args.kwargs["queries"]
        self.assertEqual(queries[0]["filters"], self.scope.filters())
        self.assertEqual(queries[1]["filters"], self.scope.filters())
        self.assertEqual(retriever.events[-1]["status"], "ok")
        response.results[0].rows = [dict(row, split="test")]
        with self.assertRaises(ValueError):
            retriever.retrieve("question", self.scope)
        self.assertEqual(retriever.events[-1]["status"], "error")

    @patch("examples.live_verification_demo.financebench_retrieval.version", return_value="test-pin")
    def test_index_hash_and_test_split_blocks(self, installed_version):
        retriever = self.retriever(approved_external=True, approved_embeddings=True)
        rows = reference_rows([self.dev], "fewshot")
        with self.assertRaises(PermissionError):
            retriever.index(rows, stage="fewshot", approved_rows_sha256="wrong")
        rows[0]["split"] = "test"
        with self.assertRaises(ValueError):
            retriever.index(rows, stage="fewshot", approved_rows_sha256=digest(rows))
        retriever.embed.assert_not_called()

    def test_synthetic_selection(self):
        result = offline_demo()
        self.assertEqual(result["selection"]["rrf_only"], "a")
        self.assertEqual(result["selection"]["gated_rrf_judge"], "b")
        self.assertIn("not_coco_or_model", result["execution_kind"])

    def test_judge_contract_abstention(self):
        valid = dict(support="pass", numeric="pass", units="pass", temporal="pass",
                     score=5, abstain=False, reason="evidence")
        for change in ({"score": True}, {"score": 6}, {"abstain": "false"}, {"extra": 1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                Judgment.parse(dict(valid, **change))
        self.assertFalse(Judgment.parse(dict(valid, temporal="unknown")).passes)
        selected = select_candidates([Candidate("a", "run", "test", "answer")], ["a"],
                                     {"a": Judgment.parse(valid)}, {"a": None})
        self.assertIsNone(selected["gated_rrf_judge"])

    def test_judge_errors_retained(self):
        events = repeated_judging([Candidate("a", "run", "test", "answer")], "question", "evidence", [],
                                  self.scope, judge=Mock(side_effect=ValueError("fixture error")),
                                  repetitions=2, approved=True)
        self.assertEqual(len(events), 4)
        self.assertTrue(all(event["status"] == "error" for event in events))
        self.assertTrue(all(row["errors"] == 2 for row in judge_summary(events, {})))

    def test_budget(self):
        self.assertEqual(call_budget(2, group_size=4, repetitions=3)["judge_calls"], 48)
        with self.assertRaises(ValueError):
            call_budget(0)

    def test_frozen_pool_comparison(self):
        candidate = Candidate('c', 'run', 'test', 'answer')
        row = candidate_rows([candidate], self.scope)[0]
        retriever = Mock()
        retriever.retrieve.side_effect = [[row], reference_rows([self.dev], 'judge')]
        judge = Mock(return_value=dict(support='pass', numeric='pass', units='pass',
                                       temporal='pass', score=5, abstain=False, reason='fixture'))
        result = run_frozen_pool(retriever, [candidate], 'question', 'evidence', self.scope,
                                 judge=judge, deterministic_gates={'c': True},
                                 repetitions=2, approved_judging=True)
        self.assertEqual(len(result['comparisons']), 4)
        self.assertTrue(all(row['selection']['gated_rrf_judge'] == 'c' for row in result['comparisons']))
        self.assertEqual(judge.call_count, 4)

    def test_frozen_pool_errors_and_budget(self):
        candidate = Candidate('c', 'run', 'test', 'answer')
        retriever = Mock()
        with self.assertRaises(ValueError):
            run_frozen_pool(retriever, [candidate], 'q', 'e', self.scope, judge=Mock(),
                            deterministic_gates={'c': True}, repetitions=3,
                            max_judge_calls=1, approved_judging=True)
        retriever.retrieve.assert_not_called()
        retriever.retrieve.side_effect = [[candidate_rows([candidate], self.scope)[0]], []]
        result = run_frozen_pool(retriever, [candidate], 'q', 'e', self.scope,
                                 judge=Mock(side_effect=ValueError('fixture error')),
                                 deterministic_gates={'c': True}, repetitions=1, approved_judging=True)
        self.assertTrue(all(row['status'] == 'blocked_judge_error' for row in result['comparisons']))


class RateTests(unittest.TestCase):
    def setUp(self):
        self.rate = Rate("synthetic-10y", "10Y", "4.5", "percent", "2020-01-01",
                         "2020-01-01", "2020-01-01", "synthetic", "2020-01-02T00:00:00Z")

    def context(self, rates, **kwargs):
        options = dict(applicable=True, series="synthetic-10y", tenor="10Y", as_of="2020-01-01")
        options.update(kwargs)
        return rate_context(rates, **options)

    def test_units(self):
        self.assertEqual(self.context([self.rate])["decimal_rate"], "0.045")

    def test_missing_stale_future_and_vintage(self):
        for rates in ([], [replace(self.rate, available_on="2020-01-02", vintage_on="2020-01-02")],
                      [replace(self.rate, vintage_on=None)]):
            self.assertEqual(self.context(rates)["status"], "blocked_missing_or_stale_rate")
        self.assertEqual(self.context([self.rate], as_of="2020-01-03")["status"], "blocked_missing_or_stale_rate")
        self.assertEqual(self.context([self.rate], as_of="2020-01-03", max_age_days=2)["age_days"], 2)

    def test_retrospective_and_not_applicable(self):
        self.assertEqual(self.context([replace(self.rate, vintage_on=None)], point_in_time=False)["mode"], "retrospective")
        self.assertEqual(self.context([], applicable=False)["status"], "rates_not_applicable")

    def test_ambiguous_observation_blocks(self):
        with self.assertRaises(ValueError):
            self.context([self.rate, self.rate])


class MCPTests(unittest.IsolatedAsyncioTestCase):
    endpoint = "https://example-account.snowflakecomputing.com/api/v2/databases/DEMO/schemas/TEST/mcp-servers/REVIEW"
    host = "example-account.snowflakecomputing.com"

    async def test_disabled_probe(self):
        session = Mock()
        with self.assertRaises(PermissionError):
            await probe(session, endpoint=self.endpoint, approved_host=self.host)
        session.list_tools.assert_not_called()

    async def test_probe_records_three_calls(self):
        session = Mock()
        session.list_tools = AsyncMock(return_value={"tools": [{"name": "review_distribution_reconciliation",
            "inputSchema": {"type": "object", "properties": {"P_CASE_ID": {"type": "string"}}, "required": ["P_CASE_ID"]}}]})
        session.call_tool = AsyncMock(return_value={"content": [{"type": "text", "text": "synthetic mock"}]})
        evidence = await probe(session, endpoint=self.endpoint, approved_host=self.host, approved=True)
        self.assertEqual(len(evidence), 4)
        self.assertEqual(session.call_tool.await_count, 3)
        self.assertEqual(evidence[2]["arguments"], {"P_CASE_ID": "SHORTFALL"})

    async def test_inventory_blocks_calls(self):
        session = Mock(list_tools=AsyncMock(return_value={"tools": []}), call_tool=AsyncMock())
        with self.assertRaises(ValueError):
            await probe(session, endpoint=self.endpoint, approved_host=self.host, approved=True)
        session.call_tool.assert_not_called()

    def test_endpoint_restrictions(self):
        for endpoint in (self.endpoint.replace("https:", "http:"), self.endpoint + "?token=x",
                         self.endpoint.replace(self.host, "other.snowflakecomputing.com")):
            with self.assertRaises(ValueError):
                validate_endpoint(endpoint, self.host)


if __name__ == "__main__":
    unittest.main()