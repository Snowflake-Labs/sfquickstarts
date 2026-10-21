# Snowflake-managed MCP showcase

## Architecture and implementation status

Use Snowflake's managed MCP SERVER object, not a custom HTTP service or an
EXTERNAL MCP SERVER. Snowflake hosts the endpoint and exposes supported Snowflake
objects as tools. No FastMCP server, container, public tunnel or third-party MCP
hosting is required.

The first showcase tool is the existing synthetic distribution reconciliation
function from `setup.sql`. `managed_mcp.yaml` is a local specification template;
its placeholders must be replaced with verified deployed object names. The source
SQL still requires retargeting to an approved standard database in your account.
Neither the function nor this MCP server has been deployed by this work.

An MCP client discovers tools and invokes the reconciliation function through the
managed endpoint. This demonstrates MCP directly, without confusing a notebook
function call with protocol execution. A Cortex Agent can also be exposed as a
managed MCP tool when governed orchestration is required. Do not create circular
agent-to-MCP-to-agent invocation paths.

## Cumulative finance extension

Keep all eleven PE, capital-markets, hedge-fund, quant and shared-control skills.
Add the following narrowly scoped Snowflake functions/procedures after their
backends are implemented, tested and deployed. Do not advertise them in the MCP
specification before they exist:

- Retrieve development-only few-shot examples with hybrid BM25/vector RRF.
- Rank a frozen candidate pool for one approved run/problem; never accept a gold
  answer or held-out reward as a selection input.
- Retrieve independently graded development examples on a separate evaluator
  MCP server, inaccessible to the answering client.
- Retrieve approved FRED/Treasury context with series, tenor, observation,
  availability and vintage dates, units, source and a bounded staleness policy.

`financebench_retrieval.py` and `financebench_experiment.py` currently provide
local supporting contracts/adapters only. They are not deployed Snowflake tools,
an MCP server, an authenticated client or evidence of live execution.

Turbopuffer remains an external service even when called behind a Snowflake
managed MCP tool. Its adapter will require approved network access, secrets,
data-export rights and budget. Do not silently replace it with Cortex Search
and label the result turbopuffer RRF. No dataset is downloaded automatically.
Keep original FinanceBench scoring separate from rates-enriched follow-up tasks.

## Deployment and authentication checkpoints

1. Verify the intended account, existing standard database/schema, warehouse and
   backing function. Do not use a personal database for deployment.
2. Review the exact retargeted MCP specification and create an MCP SERVER using
   Snowflake's documented FROM SPECIFICATION syntax after setup approval.
3. Use approved OAuth configuration and a least-privileged role. Access to the
   server does not itself grant access to the function or other underlying tools.
   Do not change user defaults, grants, network policies or OAuth integrations
   automatically. Never put tokens/client secrets in notebooks or screenshots.
4. Connect an approved MCP client to the endpoint:

   `https://<account-host>/api/v2/databases/<database>/schemas/<schema>/mcp-servers/<server>`

5. Use a client compatible with the documented MCP/SSE behavior. Tool-call
   responses require accepting both `application/json` and `text/event-stream`.

## Evidence required for the showcase

- Retain a real `tools/list` response from the Snowflake-managed endpoint.
- Retain a real `tools/call` for `review_distribution_reconciliation` with
  `P_CASE_ID: SHORTFALL`, its returned blocking status and the 63M discrepancy.
- Also retain BALANCED and unknown-case responses, with no payment authorization.
- Record timestamp, account/server identity, sanitized request/response, errors
  and available request/query identifiers. Never include authentication headers.
- Render these captured responses in the notebook, clearly labeled as MCP
  protocol results. A YAML display, fixture or direct Python/SQL call does not
  satisfy this checkpoint.
- For orchestration, retain the actual client/agent tool-call trace. Do not claim
  native managed evaluation results prove MCP invocation without that trace.

## Reference

https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp