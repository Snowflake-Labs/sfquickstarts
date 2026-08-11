# SEC Analytical Search — Self-Contained Quickstart

A Snowflake CoWork demo showing **Analytical Search** answering questions
that standard RAG can't, over real SEC EDGAR filings.

## What this demo proves

Most enterprise data is unstructured — filings, contracts, support notes.
Most enterprise *questions* over that data are analytical: counts, trends,
comparisons, exhaustive lists. Standard RAG can't answer those because
top-k retrieval is sampling, not analysis.

Snowflake CoWork + **Analytical Search** changes that. This demo answers
*"How many filings filed on Feb 3, 2025 mention cybersecurity risks?"* with a precise
count — backed by a persisted search + AI_FILTER + COUNT, not a top-k guess.

**Full quickstart guide:** [Analytical Search over SEC Filings with Snowflake CoWork](https://www.snowflake.com/en/developers/guides/analytical-search-over-sec-filings-with-snowflake-cowork/)
