# AGENTS.md

## Project
Tundra SaaS Analytics is a Streamlit app over a Snowflake Postgres instance, using Snowflake Cortex AI for natural-language features. It visualizes a synthetic Global SaaS dataset (subscriptions, usage, and revenue across ~30 countries) with an interactive dark world map.

## How to use this file
This is the single source of truth for schema, allowed values, conventions, and gotchas. Read it before building; every step assumes it. Keep it in the repo root so the agent loads it automatically each session. Then run the numbered prompts in order.

## Stack
- Python >= 3.11
- Streamlit >= 1.50 (multipage via `st.navigation`)
- `psycopg2-binary` (Postgres), `pydeck` (dark world map), `plotly` (charts), `pandas`
- `snowflake-snowpark-python` (Cortex `COMPLETE` / `EMBED_TEXT_1024`)
- Data lives in the Snowflake Postgres instance `tundra_lab`; country geometry is bundled at `src/assets/countries.geojson`

## Repo layout
- `streamlit_app.py` — role-based navigation entry point
- `src/db.py` — psycopg2 connection, `run_query`, `run_query_df`, `get_schema_context`
- `src/cortex.py` — dual-mode Snowpark session; `cortex_complete`, `cortex_embed`
- `src/dashboard.py` — world map, adaptive metric row, accounts table, trend + donut
- `src/ai_agent.py` — NL chat to SQL over Postgres
- `src/chart_agent.py` — NL to chart
- `src/kpi_summary.py` — executive KPI page
- `src/semantic_search.py` — pgvector semantic search
- `src/assets/countries.geojson` — Natural Earth 110m country polygons
- `.streamlit/secrets.toml` — `[postgres]` + `[snowflake]` (gitignored)

## Run locally
```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
# put real creds in .streamlit/secrets.toml ([postgres] and [snowflake])
.venv/bin/streamlit run streamlit_app.py
```

## Schema (use these EXACT names)
- `countries(country_code CHAR(3) PK [ISO-3 alpha-3], country_name, region, latitude, longitude)`
- `plans(plan_id PK, plan_name, monthly_price, seat_limit, features TEXT[])`
- `customers(customer_id PK, company_name, country_code FK, industry, employee_count, signup_date, account_tier, description)`
- `subscriptions(subscription_id PK, customer_id FK, plan_id FK, seats, mrr, status, subscription_period TSTZRANGE, started_at, canceled_at)`
- `usage_events(event_id PK, customer_id FK, event_date, event_type, api_calls, metadata JSONB)`
- `invoices(invoice_id PK, customer_id FK, amount, invoice_date, status)`
- `customer_embeddings(customer_id FK, embedding pgvector)`

## Allowed values (never invent others)
- `subscriptions.status`: `active`, `trial`, `churned`. There is no `cancelled`; churn uses `churned`.
- `invoices.status`: `paid`, `pending`, `overdue`
- `customers.industry`: SaaS, Finance, Healthcare, Retail, Manufacturing, Media
- `plans.plan_name`: Starter, Pro, Enterprise
- `usage_events.event_type`: login, api_call, report_run, export

## Join keys
- `subscriptions.plan_id = plans.plan_id` (plans PK is `plan_id`, not `id`; name column is `plan_name`, not `name`)
- `subscriptions.customer_id = customers.customer_id`
- `customers.country_code = countries.country_code` (`country_name` lives only on `countries`)
- `plans.features` is `TEXT[]`: use `feature = ANY(p.features)` or `CROSS JOIN LATERAL unnest(p.features)`

## Postgres / SQL gotchas
- `round(x, 2)` needs numeric: `round((expr)::numeric, 2)`. `round(double, int)` raises "function does not exist".
- For synthetic data, call `random()` inline per row. A single `LATERAL (SELECT random())` joined to `generate_series` evaluates once and yields uniform (non-varying) data.
- Parameterize all filter and user values (`%(name)s`); never string-interpolate.

## Snowflake-Postgres DDL
- Ingress network rule: `TYPE=IPV4, MODE=POSTGRES_INGRESS` (not `INGRESS`).
- `CREATE POSTGRES INSTANCE`: `COMPUTE_FAMILY` (not `COMPUTE_SIZE`), `AUTHENTICATION_AUTHORITY=POSTGRES`, no `AUTO_RESUME`.
- `CREATE STREAMLIT`: assign a `COMPUTE_POOL` for container runtime; there is no `RUNTIME='...'` property; `ROOT_LOCATION` must be a stage path.
- External Access Integration is unavailable on trial accounts.

## Streamlit patterns
- Multipage: give every `st.Page` a unique `url_path` (page callables are all named `show()` and otherwise collide on pathname `show`).
- Button that fills a `text_input`: in the button branch set `st.session_state[<key>]=value` then `st.rerun()`; create the input with only `key=<key>` and no `value=`.
- Button that submits to `st.chat_input`: render buttons unconditionally and use `question = st.chat_input(...) or clicked_example`. A button gated on an empty conversation stops responding after the first message.
- Render zero-row query results with `st.info(...)`, not a blank dataframe.
- Use `width="stretch"` instead of the deprecated `use_container_width=True`.
- World map: `pydeck` `GeoJsonLayer` (filled country polygons) on `map_style="dark"`, matched on `ADM0_A3`, with a `ScatterplotLayer` fallback for countries lacking a low-res polygon. Read clicks from `selection.selection["objects"][<layer_id>]` (polygon fields under `properties`, point fields flat). Show full `country_name` in labels; keep the ISO-3 code for the SQL filter.

## Cortex / credentials
- `secrets.toml [snowflake]` needs REAL `account`/`user`/`password`/`warehouse` (and optional `role`); a placeholder fails with `250001 (08001)`.
- `cortex_embed`: `EMBED_TEXT_1024` may return a Python list or a JSON string depending on the connector; only `json.loads` when it is a string.
- The AI Agent and Charts pages must inject this schema and the allowed values into their LLM system prompt, plus one worked few-shot example, so generated SQL uses real names and values.

## Definition of Done (Acceptance Check)
Run before declaring any build step done:
1. Run it headlessly with Streamlit's testing API (`AppTest.from_file("streamlit_app.py")` for navigation; `AppTest.from_string(...)` calling the page's `show()` per page) and confirm `at.exception` is None and `at.error` is empty.
2. For data pages, run the generated SQL against the live Postgres and confirm it returns the expected non-empty result (and zero-row cases are handled).
3. For interactive elements (map click, example buttons), simulate the interaction (`at.button[i].click().run()`) and confirm state updates and the downstream output renders.
4. If anything fails, fix it and re-run the check.

## Safety
- Keep `.streamlit/secrets.toml` gitignored; never commit credentials.
- Parameterize all SQL; never interpolate user or filter values into query strings.
