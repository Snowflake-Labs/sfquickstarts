# Security

This repository is sample code. It creates objects only in a database and warehouse it owns (`NORTHBANK_AGENT_EVALS`, `NORTHBANK_EVAL_WH`), uses synthetic data only, and contains no credentials.

Recommendations when running it:

- Use a sandbox account or a dedicated role. The setup script uses `ACCOUNTADMIN` for simplicity; see README "Privileges" for what a least-privilege role needs.
- Leave the two scheduled Tasks suspended unless you want nightly runs.
- Run `sql/99_teardown.sql` when you're done.

## Reporting a vulnerability

Please don't open a public issue for a security problem. Refer to the Snowflake [HackerOne program](https://hackerone.com/snowflake?type=team) for our security policies and for reporting vulnerabilities. For other security questions, contact the Snowflake security team at security@snowflake.com.
