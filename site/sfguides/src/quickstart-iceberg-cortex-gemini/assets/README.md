# AI-Ready Open Lakehouse: Snowflake Cortex + Gemini Enterprise

A hands-on lab that builds an AI-ready data product on Apache Iceberg — from raw Marketplace data to a Cortex Agent consumed by Snowflake CoWork, Gemini Enterprise (via MCP), and Looker dashboards. One copy of data, one agent, many surfaces.

This lab loosely follows the architecture described in [blog-post.md](./blog-post.md).

If you are looking for how to setup MCP connection between Snowflake Cortex and Gemini Enterprise, please got [mcp guide](./mcp-server-setup-guide.md)

![Architecture](./input/arch-diagram.svg)

## What You Build

1. **Iceberg table** on your GCS bucket from Snowflake Marketplace economic data (BLS, Freddie Mac, IRS)
2. **Semantic View** defining dimensions, facts, and metrics — business logic in the data layer
3. **Cortex Agent** powered by Gemini that turns natural-language questions into governed SQL
4. **MCP Server + OAuth** exposing the agent to any MCP-compatible client
5. **Gemini Enterprise** data connector consuming the agent natively
6. **Looker dashboard** on the same Iceberg data — BI alongside AI chat

## Run the Lab

Open **`hol-cortex-gemini.ipynb`** in a Snowflake Workspace and run cells top-to-bottom. The notebook is self-contained — narration, code, and UI pointers all in one place.

## Contribute 

- main-prompt is human input only, it helps ai to create narration
- narration should be reviewed and confirmed by human. main prompt sets the tone and story.
- based on narration and main prompt, ai created how-to wich included UI pointers and code blocks.
- you can provide proofreads input for the final outcome.


| File | Purpose |
|------|---------|
| `hol-cortex-gemini.ipynb` | **The lab notebook** — run this |
| `blog-post.md` | Conceptual blog post explaining the architecture and "why" |
| `main-prompt.md` | Human-written input prompt used to guide AI content generation |
| `narration.md` | Pure narrative text for each section (no code, no UI) |
| `how-to.md` | Code cells + telegraphic UI pointers, organized by section |
| `diagrams.md` | Graphviz DOT source and spotlight display snippets |
| `proofreads.md` | Feedback and iteration notes — edit this to give AI direction |
| `mcp-server-setup-guide.md` | Gemini Enterprise MCP call to Snowflake Cortex |
| `input/` | Supporting assets (SVG diagram, reference docs) |

## Prerequisites

- Snowflake account (provided via DataOps registration for workshops)
- Google Cloud lab environment (Qwiklabs)
- ~75 minutes
