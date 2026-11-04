# Contributing

Issues and pull requests are welcome, for example:

- a fix when a script stops working after a Cortex release;
- a clearer explanation in the README or `docs/`;
- a new template for adapting the method to another domain.

Please keep changes in line with the quickstart:

- **Don't change the data generator** (`sql/01_synthetic_data.sql`) or the expected answers in `data/eval_questions.ndjson` unless you change both together; the answers are only valid for that exact data.
- **Synthetic data only.** Never add customer data, credentials or account identifiers.
- Test a change end to end in a sandbox account and say in the pull request which steps you ran.
- New files carry the Apache 2.0 header used across the repo.

This is sample code maintained on a best-effort basis; there's no support SLA. By contributing, you agree that your contributions are licensed under the Apache License 2.0.

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
