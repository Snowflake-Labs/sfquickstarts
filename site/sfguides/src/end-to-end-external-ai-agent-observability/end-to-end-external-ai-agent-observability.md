author: Josh Reini
id: end-to-end-external-ai-agent-observability
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
language: en
summary: Build a multi-tool AI agent with full observability from batch evaluation to production monitoring using TruLens, OpenAI Agent SDK, and Snowflake AI Observability.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability
tags: AI Observability, TruLens, Agents, Cortex Analyst, Cortex Search, Evaluation, Monitoring




# End-to-End External AI Agent Observability

## Overview

Duration: 5

Modern AI agents orchestrate multiple tools — from text-to-SQL engines to knowledge base retrieval — making them powerful but difficult to debug and evaluate. When an agent chains Cortex Analyst for structured data queries and Cortex Search for unstructured knowledge retrieval, you need deep visibility into each step: what tool was called, what it returned, and whether the final answer was any good.

This guide walks you through building a **Support Intelligence Agent** with full observability coverage — from batch evaluation with ground truth to production monitoring with a live dashboard. You'll use the [OpenAI Agent SDK](https://github.com/openai/openai-agents-python) for agent orchestration, [TruLens](https://www.trulens.org/) for instrumentation and evaluation, and [Snowflake AI Observability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability) as the unified telemetry backend.

### What You Will Learn
- How to build an AI agent with Cortex Analyst and Cortex Search tools
- How to instrument agent code with TruLens `@instrument` decorators for OTEL-based tracing
- How to define custom client-side metrics (SQL Agreement, Precision@k, Recall@k) using `Metric` and `Selector`
- How to run batch evaluations with `RunConfig` and `compute_metrics()`
- How to add production tracing with `@trace_with_run` for live chat
- How to build a Streamlit monitoring dashboard over `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS`
- How to view traces and evaluation results in the Snowsight AI Observability UI

### What You Will Build
- A multi-tool AI agent using OpenAI Agent SDK with Snowflake Cortex
- TruLens instrumentation with semantic span types (RECORD_ROOT, TOOL, RETRIEVAL, GENERATION)
- Ground truth tables and custom evaluation metrics
- A batch evaluation pipeline with client-side and server-side metrics
- A FastAPI backend with production tracing
- A React chat frontend with streaming
- A Streamlit-in-Snowflake monitoring dashboard

### Prerequisites
- A Snowflake account with [Cortex LLM Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions), [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview), and [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) enabled.
- A Snowflake account login with a role that can create databases, warehouses, stages, Cortex Search services, and Streamlit apps.
- A [Programmatic Access Token (PAT)](https://docs.snowflake.com/en/user-guide/admin-programmatic-access-token) for REST API authentication.
- Python 3.10–3.12 with [uv](https://docs.astral.sh/uv/) (recommended) or pip.
- Node.js 18+ (for the React frontend).
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed.

### Architecture

The system architecture flows as follows:

1. **React Chat UI** sends questions via SSE to the **FastAPI Backend**
2. **FastAPI** uses `@trace_with_run` to create traced invocations
3. **OpenAI Agent SDK** routes to **Cortex Analyst** (structured queries) or **Cortex Search** (knowledge base)
4. **TruLens** instruments each layer with semantic span types and writes traces to **Snowflake AI Observability Events**
5. **Batch Evaluation** runs ground-truth metrics (SQL Agreement, Precision@k, Recall@k) plus server-side LLM-judge metrics (answer_relevance, groundedness, context_relevance, coherence)
6. **Streamlit Dashboard** queries the event table for real-time production monitoring
7. **Snowsight AI Observability UI** provides built-in trace exploration and evaluation comparison

<!-- ------------------------ -->

## Setup Snowflake Environment

Duration: 10

### Clone the Repository

Clone the companion GitHub repository that contains all source code for this guide:

```bash
git clone https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability.git
cd sfguide-end-to-end-external-ai-agent-observability
```

The repository is organized as follows:

```
sfguide-end-to-end-external-ai-agent-observability/
├── setup_snowflake.sql          # DDL: database, tables, Cortex Search service, ground truth
├── semantic_model.yaml          # Cortex Analyst semantic model
├── pyproject.toml               # Python dependencies
├── run_eval.py                  # Batch evaluation entry point
├── server.py                    # FastAPI production chat server
├── src/
│   ├── agent/
│   │   ├── app.py               # Agent definition + AgentApp wrapper
│   │   └── tools.py             # Cortex Analyst & Cortex Search tools
│   ├── services/
│   │   └── config.py            # Snowflake connection config
│   ├── eval/
│   │   ├── ground_truth.py      # Ground truth loaders + test query suites
│   │   ├── metrics.py           # Custom metrics (SQL Agreement, Precision@k, Recall@k)
│   │   └── sql_result_comparator.py  # Multi-strategy SQL result comparison
│   └── observability/
│       └── trulens_setup.py     # TruLens + Snowflake connector setup
├── frontend/                    # React chat UI with SSE streaming
│   ├── package.json
│   ├── index.html
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       └── index.css
└── monitoring_dashboard/        # Streamlit-in-Snowflake monitoring app
    ├── streamlit_app.py
    ├── snowflake.yml
    └── pyproject.toml
```

### Create Database and Sample Data

Open a SQL worksheet in Snowsight and run the [`setup_snowflake.sql`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/setup_snowflake.sql) script. This creates:

- **Database**: `SUPPORT_INTELLIGENCE` with schema `DATA`
- **Warehouse**: `SUPPORT_INTELLIGENCE_WH` (XSMALL)
- **TICKET_METRICS**: 20 support tickets with priority, category, status, agent assignment, response times, and CSAT scores
- **KB_ARTICLES**: 10 knowledge base articles covering account, technical, and billing topics
- **KB_SEARCH**: A Cortex Search service on the knowledge base content
- **MODELS stage**: For uploading the semantic model
- **GROUND_TRUTH_SEARCH**: 8 entries mapping queries to expected retrieval chunks
- **GROUND_TRUTH_ANALYST**: 13 entries mapping queries to golden SQL statements

```sql
-- Key objects created:
CREATE DATABASE IF NOT EXISTS SUPPORT_INTELLIGENCE;
CREATE SCHEMA IF NOT EXISTS SUPPORT_INTELLIGENCE.DATA;

CREATE OR REPLACE WAREHOUSE SUPPORT_INTELLIGENCE_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

-- Tables: TICKET_METRICS, KB_ARTICLES, GROUND_TRUTH_SEARCH, GROUND_TRUTH_ANALYST
-- Service: KB_SEARCH (Cortex Search)
-- Stage: MODELS
```

### Upload the Semantic Model

Upload [`semantic_model.yaml`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/semantic_model.yaml) to the MODELS stage. From the cloned repository directory:

```sql
PUT file://semantic_model.yaml @SUPPORT_INTELLIGENCE.DATA.MODELS
    AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

The semantic model defines dimensions (TICKET_ID, CUSTOMER_NAME, PRIORITY, CATEGORY, STATUS, ASSIGNED_AGENT), time dimensions (CREATED_DATE, RESOLVED_DATE), facts (FIRST_RESPONSE_HOURS, RESOLUTION_HOURS, CSAT_SCORE), aggregate metrics, and verified queries for Cortex Analyst.

### Set Up the Python Environment

From the cloned repository directory, create a virtual environment and install dependencies:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .
```

### Configure Snowflake Connection

The application reads connection details from `~/.snowflake/connections.toml`. Ensure you have a connection configured:

```toml
[default]
account = "your-account-identifier"
user = "your-username"
password = "your-programmatic-access-token"
database = "SUPPORT_INTELLIGENCE"
schema = "DATA"
warehouse = "SUPPORT_INTELLIGENCE_WH"
role = "SYSADMIN"
```

Set the connection name as an environment variable:

```bash
export SNOWFLAKE_CONNECTION_NAME=default
```

<!-- ------------------------ -->

## Build the AI Agent

Duration: 15

The Support Intelligence Agent uses the [OpenAI Agent SDK](https://github.com/openai/openai-agents-python) to orchestrate two Snowflake Cortex tools. The agent runs against Snowflake-hosted LLMs via the Cortex REST API.

### Connection Config ([`src/services/config.py`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/src/services/config.py))

The config module reads connection parameters from environment variables or `~/.snowflake/connections.toml`, derives the PAT token and account URL for REST API calls, and provides a `get_snowpark_session()` factory:

```python
SNOWFLAKE_PARAMS = _get_connection_params()
SNOWFLAKE_PAT = _get_pat()
SNOWFLAKE_ACCOUNT_URL = f"https://{_get_account_identifier()}.snowflakecomputing.com"

SEMANTIC_MODEL_FILE = "@SUPPORT_INTELLIGENCE.DATA.MODELS/semantic_model.yaml"
CORTEX_SEARCH_SERVICE = "SUPPORT_INTELLIGENCE.DATA.KB_SEARCH"
```

### Agent Tools ([`src/agent/tools.py`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/src/agent/tools.py))

Two tools are defined using `@function_tool` from the OpenAI Agent SDK:

**`query_ticket_metrics`** — Calls the Cortex Analyst REST API with the semantic model to convert natural language questions into SQL, execute it, and return results:

```python
@function_tool
@instrument(
    name="query_ticket_metrics",
    span_type=SpanAttributes.SpanType.TOOL,
    attributes=_analyst_attributes,
)
def query_ticket_metrics(question: str) -> str:
    """Query structured support ticket metrics using natural language."""
    resp = requests.post(
        f"{SNOWFLAKE_ACCOUNT_URL}/api/v2/cortex/analyst/message",
        headers={
            "Authorization": f"Bearer {SNOWFLAKE_PAT}",
            "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
        },
        json={
            "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
            "semantic_model_file": SEMANTIC_MODEL_FILE,
        },
    )
    # ... parse interpretation, SQL, and results
```

**`search_knowledge_base`** — Calls Cortex Search via the Snowpark Root API to retrieve relevant knowledge base articles:

```python
@function_tool
@instrument(
    name="search_knowledge_base",
    span_type=SpanAttributes.SpanType.RETRIEVAL,
    attributes=lambda ret, exception, *args, **kwargs: {
        SpanAttributes.RETRIEVAL.QUERY_TEXT: kwargs.get("query", ""),
        SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS: ret.split("\n\n---\n\n") if isinstance(ret, str) else [],
    },
)
def search_knowledge_base(query: str) -> str:
    """Search the support knowledge base for articles and documentation."""
```

> **Key Pattern**: `@instrument` must be the **outermost** decorator (above `@function_tool`). This ensures TruLens wraps the tool execution properly.

### Agent Definition ([`src/agent/app.py`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/src/agent/app.py))

The agent is built using OpenAI Agent SDK's `Agent` class, pointed at a Snowflake-hosted LLM via a custom `SnowflakeAsyncOpenAI` client:

```python
_snowflake_openai_client = SnowflakeAsyncOpenAI(
    api_key=SNOWFLAKE_PAT,
    base_url=f"{SNOWFLAKE_ACCOUNT_URL}/api/v2/cortex/v1",
)

_model = OpenAIChatCompletionsModel(
    model="openai-gpt-5.1",
    openai_client=_snowflake_openai_client,
)

support_agent = Agent(
    name="Support Cloud Agent",
    instructions="...",
    tools=[query_ticket_metrics, search_knowledge_base],
    model=_model,
)
```

The `AgentApp` class wraps the agent with a synchronous `ask()` method that serves as the entry point for both batch evaluation and live chat:

```python
class AgentApp:
    @instrument(
        span_type=SpanAttributes.SpanType.RECORD_ROOT,
        attributes={
            SpanAttributes.RECORD_ROOT.INPUT: "question",
            SpanAttributes.RECORD_ROOT.OUTPUT: "return",
        },
    )
    def ask(self, question: str) -> str:
        result = Runner.run_sync(support_agent, question)
        return result.final_output
```

### LLM Call Instrumentation

The `_SnowflakeChatCompletions` wrapper intercepts every LLM call to add `GENERATION` span instrumentation, capturing input messages, model name, output content, tool calls, token usage, and finish reason as semantic attributes:

```python
class _SnowflakeChatCompletions:
    @instrument(
        span_type=SpanAttributes.SpanType.GENERATION,
        attributes=_generation_attributes.__func__,
    )
    async def create(self, **kwargs):
        kwargs.pop("max_tokens", None)
        resp = await self._inner.create(**kwargs)
        return resp
```

<!-- ------------------------ -->

## Instrument with TruLens

Duration: 10

### Understanding Span Types

TruLens uses OpenTelemetry-based semantic span types to categorize different parts of your agent's execution:

| Span Type | Purpose | Where Used |
|-----------|---------|------------|
| `RECORD_ROOT` | Top-level invocation | `AgentApp.ask()` |
| `TOOL` | Tool/function calls | `query_ticket_metrics()` |
| `RETRIEVAL` | Search/retrieval operations | `search_knowledge_base()` |
| `GENERATION` | LLM completions | `_SnowflakeChatCompletions.create()` |

Each span type has semantic attributes that TruLens writes to the Snowflake AI Observability event table. For example:
- `RECORD_ROOT` captures `input` and `output`
- `RETRIEVAL` captures `query_text` and `retrieved_contexts`
- `TOOL` captures `call.kwargs` and `call.return`
- `GENERATION` captures `input_messages`, `content`, `tool_calls`, and token counts

### Setting Up Observability ([`src/observability/trulens_setup.py`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/src/observability/trulens_setup.py))

The setup function initializes TruLens with a Snowflake connector:

```python
from trulens.connectors.snowflake import SnowflakeConnector
from trulens.core import TruSession
from trulens.apps.app import TruApp

def setup_observability():
    snowpark_session = get_snowpark_session()
    sf_connector = SnowflakeConnector(snowpark_session=snowpark_session)
    session = TruSession(connector=sf_connector)

    agent_app = AgentApp()
    all_metrics = build_metrics(snowpark_session)

    tru_app = TruApp(
        agent_app,
        app_name="Support Cloud Agent",
        app_version="v2",
        connector=sf_connector,
        main_method=agent_app.ask,
    )

    return agent_app, tru_app, session, sf_connector, all_metrics
```

Key components:
- **`SnowflakeConnector`**: Routes all telemetry to `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS`
- **`TruSession`**: Manages the observability session
- **`TruApp`**: Wraps your application for tracing and evaluation, linking `main_method` to the agent's entry point

<!-- ------------------------ -->

## Define Ground Truth and Custom Metrics

Duration: 15

### Ground Truth Tables

Ground truth is stored in Snowflake tables (created by [`setup_snowflake.sql`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/setup_snowflake.sql)):

**`GROUND_TRUTH_ANALYST`** — 13 golden SQL entries mapping natural language questions to expected SQL:
```sql
SELECT QUERY, GOLDEN_SQL FROM SUPPORT_INTELLIGENCE.DATA.GROUND_TRUTH_ANALYST;
-- Example: "How many tickets are there by priority?" ->
--   SELECT PRIORITY, COUNT(TICKET_ID) AS TICKET_COUNT FROM TICKET_METRICS ...
```

**`GROUND_TRUTH_SEARCH`** — 8 entries mapping queries to expected retrieval chunks:
```sql
SELECT QUERY, EXPECTED_CHUNK_TEXT FROM SUPPORT_INTELLIGENCE.DATA.GROUND_TRUTH_SEARCH;
-- Example: "How do I reset my password?" -> "[account] How to Reset Your Password..."
```

Ground truth is loaded at runtime via `load_analyst_golden_sql()` and `load_search_ground_truth()` in [`src/eval/ground_truth.py`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/src/eval/ground_truth.py).

### Server-Side Metrics

These are LLM-as-judge metrics computed by Snowflake's evaluation infrastructure. You reference them by name as strings:

```python
SERVERSIDE_METRICS = [
    "answer_relevance",
    "groundedness",
    "context_relevance",
    "coherence",
]
```

### Custom Client-Side Metrics

Custom metrics use the `Metric` class with `Selector` to extract span attributes from traces.

**SQL Agreement (Golden)** — Compares the agent's generated SQL against golden SQL by executing both and comparing result sets:

```python
m_sql_agreement = (
    Metric(implementation=sql_agreement_golden, name="SQL Agreement (Golden)")
    .on_input()
    .on({
        "sql_output": Selector(
            span_type=SpanAttributes.SpanType.TOOL,
            span_attribute=SpanAttributes.CALL.RETURN,
            collect_list=False,
        ),
    })
)
```

The `sql_agreement_golden` function extracts SQL from the tool output, executes both the predicted and golden SQL, then uses a multi-strategy comparator ([`sql_result_comparator.py`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/src/eval/sql_result_comparator.py)) that handles column name alignment (via LLM), approximate numeric matching, categorical bijection, and null/sort normalization.

**Precision@k and Recall@k** — Measure retrieval quality against ground truth chunks:

```python
m_precision = (
    Metric(implementation=precision_with_reason, name="Precision@k")
    .on_input()
    .on({
        "retrieved_context_chunks": Selector(
            span_type=SpanAttributes.SpanType.RETRIEVAL,
            span_attribute=SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS,
            collect_list=True,
        ),
    })
)
```

The `Selector` extracts `RETRIEVED_CONTEXTS` from `RETRIEVAL` spans in the trace, automatically linking evaluation inputs to the right spans.

> **Critical Pattern**: All metrics — both client-side and server-side — are passed in a **single** `compute_metrics()` call. Do not call it separately for different metric types.

<!-- ------------------------ -->

## Run Batch Evaluation

Duration: 10

The batch evaluation script ([`run_eval.py`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/run_eval.py)) executes all test queries against the agent and computes both client-side and server-side metrics.

### Test Query Suites

Three query suites exercise different agent capabilities:

```python
TEST_QUERIES_ANALYST = [...]   # 13 structured data queries
TEST_QUERIES_SEARCH = [...]    # 5 knowledge base queries
TEST_QUERIES_MIXED = [...]     # 5 queries requiring both tools
```

### Running the Evaluation

```bash
python run_eval.py
```

The script:

1. **Initializes observability** via `setup_observability()`, which creates the TruApp, session, and metrics
2. **Creates a RunConfig** with a timestamped run name and dataset specification:

```python
run_config = RunConfig(
    run_name=run_name,
    dataset_name=f"{run_name}_dataset",
    source_type="DATAFRAME",
    dataset_spec={"input": "question"},
    description="Batch evaluation of Support Intelligence Agent",
    llm_judge_name="openai-gpt-5.1",
)
```

3. **Starts the run** by invoking the agent on all queries:

```python
run = tru_app.add_run(run_config=run_config)
run.start(input_df=input_df)
```

4. **Polls for completion** until spans are ingested
5. **Computes all metrics** in a single call:

```python
all_metrics = custom_metrics + SERVERSIDE_METRICS
run.compute_metrics(metrics=all_metrics)
```

This triggers:
- **Client-side**: SQL Agreement, Precision@k, Recall@k run locally using span data
- **Server-side**: answer_relevance, groundedness, context_relevance, coherence are computed by Snowflake's LLM judge

All results are written to the AI Observability event table and visible in Snowsight.

<!-- ------------------------ -->

## Production Chat with Live Tracing

Duration: 10

The FastAPI server ([`server.py`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/server.py)) provides a production-ready chat backend with real-time tracing via `@trace_with_run`.

### Server Architecture

```python
agent_app, tru_app, session, sf_connector, all_metrics = setup_observability()

app = FastAPI(title="Support Intelligence Agent")
```

### Traced Chat Endpoints

**Synchronous endpoint** (`/api/chat`):

```python
@app.post("/api/chat")
def chat(req: ChatRequest):
    run_name = req.run_name or f"PROD_MONITOR_{timestamp}"

    @trace_with_run(app=tru_app, run_name=run_name)
    def process_message(message: str):
        return agent_app.ask(message)

    result = process_message(req.message)
    # Background thread computes metrics after each chat
    threading.Thread(target=_compute_metrics_bg, args=(run_name,), daemon=True).start()
    return ChatResponse(response=result, run_name=run_name)
```

**Streaming endpoint** (`/api/chat/stream`) provides SSE events for thinking indicators, tool call status, text deltas, and final responses.

### Background Metrics

After each chat message, a background thread computes metrics on the production trace:

```python
def _compute_metrics_bg(run_name: str):
    metrics = all_metrics + SERVERSIDE_METRICS
    run.compute_metrics(metrics=metrics)
```

### Running the Server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

### React Chat Frontend

The [`frontend/`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/tree/main/frontend) directory contains a React chat UI with:
- SSE streaming with thinking indicators
- Tool call status display (showing "Calling Cortex Analyst..." / "Cortex Search returned results")
- Dark theme with suggestion chips

To run:

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api` requests to `localhost:8000` via Vite config.

<!-- ------------------------ -->

## Build the Monitoring Dashboard

Duration: 15

The Streamlit dashboard ([`monitoring_dashboard/streamlit_app.py`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/monitoring_dashboard/streamlit_app.py)) provides production monitoring by querying `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` directly.

### Dashboard Features

The dashboard includes four tabs:

**Latency Over Time** — Interactive scatter plot with LOESS trend line and IQR-based outlier detection. Click any dot to drill into the full trace:
- Question and answer display
- Analyst tool details (interpretation, generated SQL, query results)
- Search retrieval details (query, retrieved chunks)

**Tool Calls** — Tool call latency over time by function, call distribution donut chart, and average latency table.

**Eval Scores** — Combined client-side and server-side evaluation scores over time with metric filtering, source differentiation (client vs server), and box plot distributions.

**Trace Explorer** — Expandable details for every Analyst call (question, interpretation, SQL, results) and Retrieval call (query, retrieved chunks).

### Key Queries

The dashboard uses parameterized queries against the event table. For example, loading spans:

```python
@st.cache_data(ttl=timedelta(minutes=2))
def load_spans(run_names: tuple):
    run_list = ",".join(f"'{r}'" for r in run_names)
    return conn.query(f"""
        SELECT
            TIMESTAMP,
            RECORD_ATTRIBUTES:"ai.observability.span_type"::STRING AS span_type,
            RECORD_ATTRIBUTES:"ai.observability.run.name"::STRING AS run_name,
            TIMESTAMPDIFF('MILLISECOND', START_TIMESTAMP, TIMESTAMP) AS latency_ms,
            TRACE:"trace_id"::STRING AS trace_id
        FROM SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS
        WHERE RECORD_TYPE = 'SPAN'
          AND TIMESTAMP > DATEADD('day', -1, CURRENT_TIMESTAMP())
          AND RECORD_ATTRIBUTES:"ai.observability.run.name"::STRING IN ({run_list})
        ORDER BY TIMESTAMP ASC
    """)
```

### Deploying to Snowflake

Deploy the dashboard as a Streamlit-in-Snowflake app:

```bash
cd monitoring_dashboard
snow streamlit deploy --open
```

This uses the [`snowflake.yml`](https://github.com/Snowflake-Labs/sfguide-end-to-end-external-ai-agent-observability/blob/main/monitoring_dashboard/snowflake.yml) configuration to deploy with:
- Runtime: `SYSTEM$ST_CONTAINER_RUNTIME_PY3_11`
- Compute pool: `SYSTEM_COMPUTE_POOL_CPU`
- External access: `PYPI_ACCESS_INTEGRATION` (for altair and other packages)

<!-- ------------------------ -->

## Explore in Snowsight

Duration: 5

After running batch evaluation or production chat, navigate to the **AI Observability** section in Snowsight to explore your results.

### Traces View

Navigate to **Monitoring > AI Observability > Traces** to see:
- All traced invocations grouped by run
- Span waterfall showing the execution timeline of RECORD_ROOT → GENERATION → TOOL/RETRIEVAL → GENERATION
- Span details with all semantic attributes (input/output, SQL, retrieved contexts, token counts)
- Latency breakdown per span

### Evaluations View

Navigate to **Monitoring > AI Observability > Evaluations** to see:
- Run-level metric summaries with pass/fail rates
- Per-query evaluation scores for all metrics
- Score distributions and comparisons across runs
- Detailed evaluation reasons (the `reason` field from custom metrics)

### Comparing Runs

Run the batch evaluation multiple times (e.g., with different prompts or models) to create multiple runs. The Evaluations UI lets you compare metric scores across runs side by side, making it easy to identify improvements or regressions.

<!-- ------------------------ -->

## Conclusion and Resources

Duration: 2

Congratulations! You've built a complete AI agent observability pipeline covering:

- **Agent Construction**: Multi-tool agent with Cortex Analyst and Cortex Search via OpenAI Agent SDK
- **Instrumentation**: Semantic span types (RECORD_ROOT, TOOL, RETRIEVAL, GENERATION) with TruLens `@instrument`
- **Ground Truth**: Golden SQL and expected retrieval chunks stored in Snowflake tables
- **Custom Metrics**: SQL Agreement, Precision@k, Recall@k using `Metric` + `Selector` API
- **Server-Side Metrics**: answer_relevance, groundedness, context_relevance, coherence via LLM judge
- **Batch Evaluation**: `RunConfig` + `compute_metrics()` for systematic testing
- **Production Tracing**: `@trace_with_run` for live chat with background metric computation
- **Monitoring Dashboard**: Streamlit app querying `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS`
- **Snowsight UI**: Built-in trace exploration and evaluation comparison

### Related Resources

- [Snowflake AI Observability Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability)
- [TruLens Documentation](https://www.trulens.org/getting_started/)
- [OpenAI Agent SDK](https://github.com/openai/openai-agents-python)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Getting Started with AI Observability Quickstart](https://quickstarts.snowflake.com/guide/getting-started-with-ai-observability/)
