author: Kamesh Sampath, Gilberto Hernandez
id: lakehouse-iceberg-production-pipelines
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/data-engineering,snowflake-site:taxonomy/product/analytics
language: en
summary: Build production Iceberg pipelines in Snowflake — from catalog-linked bronze to Dynamic Iceberg Tables, Semantic Views, Streamlit dashboards, and cross-engine queries with DuckDB — all without moving data.
environments: web
status: Published
duration: 45
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
fork repo link: <https://github.com/Snowflake-Labs/sfguide-lakehouse-iceberg-production-pipelines>

# Lakehouse Transformations: Build Production Pipelines for your Iceberg Tables
<!-- ------------------------ -->
## Overview

This quickstart shows how to build a production Iceberg pipeline entirely in Snowflake — no data copying, no external tooling. You start from a **Catalog-Linked Database** that mirrors an existing Iceberg catalog, build **Dynamic Iceberg Tables** that transform bronze JSON into silver aggregates, make the data AI-ready with a **Semantic View** and **Snowflake Intelligence**, visualize results with **Streamlit in Snowflake**, and query the same silver tables from **DuckDB** via Snowflake's Horizon Iceberg REST Catalog.

### What You'll Learn

- How Snowflake uses a catalog integration and Catalog Linked Databases to query externally managed Iceberg metadata without ETL duplication
- How Dynamic Iceberg Tables transform bronze JSON into production-ready silver aggregates while preserving Iceberg format and multi-engine access
- How to make your silver data AI-ready with a Semantic View for natural-language querying via Snowflake Intelligence
- How to build a live Streamlit in Snowflake dashboard over silver Dynamic Tables
- How to query Snowflake-managed Iceberg tables from DuckDB via the Horizon Iceberg REST Catalog
- How intent-driven development with Cortex Code can replace manual coding workflows

### What You'll Build

A production lakehouse workflow: bronze Iceberg tables accessed via a Catalog-Linked Database, transformed in Snowflake via Dynamic Iceberg Tables, surfaced as a Streamlit dashboard and natural-language AI agent, and queried from DuckDB — all in open Iceberg format.

### Prerequisites

- A [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with **ACCOUNTADMIN** access
- A warehouse available for compute (you will create one in the next step if needed)

> **Note:** The bronze Iceberg data and catalog integration (`glue_rest_catalog_int`) are pre-provisioned for this lab. You do not need an AWS account or any local CLI tools.

<!-- ------------------------ -->
## Use Case and Architecture

### The Balloon Game

The lab uses a balloon-popping game as the sample workload. A Python generator simulates players popping balloons of different colors, producing a stream of game events. Each event is a JSON object with these fields:

| Field | Type | Description |
|-------|------|-------------|
| **player** | string | Player identifier |
| **balloon_color** | string | Color of the popped balloon |
| **score** | integer | Points scored for this pop |
| **page_id** | string | Game page where the pop occurred |
| **favorite_color_bonus** | boolean | Whether a scoring bonus was applied |
| **event_ts** | timestamp | Event time |

Events land as raw JSON strings in a single **event** column in the bronze Iceberg table **balloon_game_events**. The silver layer uses **PARSE_JSON** to project and aggregate these fields into five production-ready tables.

### Architecture

![Architecture](assets/architecture.png)

### Lab Layers

| Layer | Technology | What it does |
|-------|------------|--------------|
| Bronze | Catalog-Linked Database | Mirrors externally managed Iceberg tables — no data copy |
| Silver | Dynamic Iceberg Tables | Transforms JSON bronze into 5 aggregation tables; writes to Snowflake-managed Iceberg storage |
| AI-Ready | Snowflake Intelligence | Semantic View over silver DTs enables natural-language querying via Cortex Analyst |
| Dashboard | Streamlit in Snowflake | Live dashboard over silver DTs; zero local server |
| Cross-engine | DuckDB via HIRC | Queries silver Iceberg tables through Snowflake's Horizon REST Catalog |

<!-- ------------------------ -->
## Catalog-Linked Database

A **Catalog-Linked Database** (CLD) connects Snowflake to an external Iceberg catalog and mirrors its namespaces and tables as Snowflake schemas — without copying any data. In this lab, the catalog integration has been pre-provisioned for you.

### Easy Path — Interactive Notebook

Open [cld_lab_guide.ipynb](https://github.com/Snowflake-Labs/sfguide-lakehouse-iceberg-production-pipelines/blob/main/notebooks/cld_lab_guide.ipynb) in Snowflake Notebooks for an interactive walkthrough.

### Detailed Path

#### Set Up Your Environment

Run the following in a Snowsight SQL worksheet:

```sql
USE ROLE ACCOUNTADMIN;

-- Create a warehouse for the lab (skip if you already have one)
CREATE WAREHOUSE IF NOT EXISTS BALLOON_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

USE WAREHOUSE BALLOON_WH;
```

#### Create the Catalog-Linked Database

Create a database linked to the pre-provisioned catalog integration:

```sql
CREATE OR REPLACE DATABASE balloon_game_events
  COMMENT = 'CLD: Glue bronze Iceberg (read-only lakehouse data)'
  LINKED_CATALOG = (
    CATALOG = 'glue_rest_catalog_int'
  );
```

> **What just happened?** Snowflake connected to the external Iceberg REST catalog and began syncing metadata. Remote namespaces appear as schemas; remote Iceberg tables appear as queryable tables — all without moving any data.

#### Verify the Catalog Link

Check that the sync is healthy:

```sql
SELECT SYSTEM$CATALOG_LINK_STATUS('balloon_game_events');
```

Expect a JSON response with `"executionState":"RUNNING"` and an empty `"failureDetails"` array.

#### Discover Schemas and Tables

List remote namespaces discovered from the catalog:

```sql
SHOW SCHEMAS IN DATABASE balloon_game_events;
```

List Iceberg tables in the discovered namespace:

```sql
-- The remote namespace appears as a lowercase schema name in double quotes
SHOW ICEBERG TABLES IN SCHEMA balloon_game_events."balloon_pops";
```

#### Query Bronze Data

Read raw events and project fields using **PARSE_JSON**:

```sql
SELECT
  PARSE_JSON(event):player::STRING         AS player,
  PARSE_JSON(event):balloon_color::STRING  AS balloon_color,
  PARSE_JSON(event):score::INTEGER         AS score,
  PARSE_JSON(event):event_ts::TIMESTAMP_TZ AS event_ts
FROM balloon_game_events."balloon_pops"."balloon_game_events"
LIMIT 10;
```

You now have live access to bronze Iceberg data without any ETL, data movement, or AWS configuration.

<!-- ------------------------ -->
## Dynamic Iceberg Tables

With bronze readable through the CLD, add [Dynamic Iceberg Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-create-iceberg) that write silver Iceberg data. Dynamic Iceberg Tables use [Snowflake Managed Storage](https://docs.snowflake.com/en/user-guide/tables-iceberg-internal-storage) — no external volume setup is required. The silver pipeline frequency is controlled by a declared **TARGET_LAG**. Five aggregation tables refresh automatically and remain readable by any Iceberg-compatible engine.

### Five Silver Tables

| Table | What it aggregates |
|-------|--------------------|
| **dt_player_leaderboard** | Per-player total score, bonus pops, last event |
| **dt_balloon_color_stats** | Per-player, per-color breakdown (pops, points, bonuses) |
| **dt_realtime_scores** | 15-second windowed scores per player |
| **dt_balloon_colored_pops** | 15-second windows by player and balloon color |
| **dt_color_performance_trends** | Average score per pop by color over 15-second windows |

### Easy Path — Interactive Notebook

Open [dt_lab_guide.ipynb](https://github.com/Snowflake-Labs/sfguide-lakehouse-iceberg-production-pipelines/blob/main/notebooks/dt_lab_guide.ipynb) in Snowflake Notebooks for an interactive walkthrough. The notebook includes Cortex Code prompts and a teachable moment around Iceberg type limitations.

### Detailed Path

#### Create Silver Database and Schema

```sql
CREATE DATABASE IF NOT EXISTS balloon_silver
  COMMENT = 'Snowflake-managed silver (Dynamic Iceberg Tables over CLD bronze)';

USE DATABASE balloon_silver;

CREATE SCHEMA IF NOT EXISTS silver
  COMMENT = 'Aggregates from bronze balloon_game_events (JSON column event)';

USE SCHEMA silver;
```

> **Iceberg type limitation:** Iceberg tables do not support `TIMESTAMP_TZ`. Use `TIMESTAMP_LTZ` (maps to Iceberg `timestamptz`) or `TIMESTAMP_NTZ` (maps to Iceberg `timestamp`). The DDLs below use `TIMESTAMP_LTZ`.

#### Create Dynamic Iceberg Tables

Run each of the five DDL statements below. They read from the CLD bronze table, parse JSON, and write typed aggregates to Snowflake-managed Iceberg storage.

**1. Player Leaderboard** — per-player totals:

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE dt_player_leaderboard (
  player STRING,
  total_score NUMBER(38,0),
  bonus_pops NUMBER(38,0),
  last_event_ts TIMESTAMP_LTZ
)
  TARGET_LAG = '5 minutes'
  WAREHOUSE = BALLOON_WH
  EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
  CATALOG = 'SNOWFLAKE'
AS
SELECT
  e.player AS player,
  SUM(e.score_i) AS total_score,
  COUNT_IF(e.fav_bonus) AS bonus_pops,
  MAX(e.ts) AS last_event_ts
FROM (
  SELECT
    v:player::STRING AS player,
    v:balloon_color::STRING AS balloon_color,
    v:score::INTEGER AS score_i,
    v:favorite_color_bonus::BOOLEAN AS fav_bonus,
    v:event_ts::TIMESTAMP_LTZ AS ts
  FROM (
    SELECT PARSE_JSON(event) AS v
    FROM balloon_game_events."balloon_pops"."balloon_game_events"
  ) q
) e
GROUP BY e.player;
```

**2. Balloon Color Stats** — per-player, per-color breakdown:

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE dt_balloon_color_stats (
  player STRING,
  balloon_color STRING,
  balloon_pops NUMBER(38,0),
  points_by_color NUMBER(38,0),
  bonus_hits NUMBER(38,0),
  last_event_ts TIMESTAMP_LTZ
)
  TARGET_LAG = '5 minutes'
  WAREHOUSE = BALLOON_WH
  EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
  CATALOG = 'SNOWFLAKE'
AS
SELECT
  e.player,
  e.balloon_color,
  COUNT(*) AS balloon_pops,
  SUM(e.score_i) AS points_by_color,
  COUNT_IF(e.fav_bonus) AS bonus_hits,
  MAX(e.ts) AS last_event_ts
FROM (
  SELECT
    v:player::STRING AS player,
    v:balloon_color::STRING AS balloon_color,
    v:score::INTEGER AS score_i,
    v:favorite_color_bonus::BOOLEAN AS fav_bonus,
    v:event_ts::TIMESTAMP_LTZ AS ts
  FROM (
    SELECT PARSE_JSON(event) AS v
    FROM balloon_game_events."balloon_pops"."balloon_game_events"
  ) q
) e
GROUP BY e.player, e.balloon_color;
```

**3. Realtime Scores** — 15-second windowed scores:

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE dt_realtime_scores (
  player STRING,
  total_score NUMBER(38,0),
  window_start TIMESTAMP_LTZ,
  window_end TIMESTAMP_LTZ
)
  TARGET_LAG = '5 minutes'
  WAREHOUSE = BALLOON_WH
  EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
  CATALOG = 'SNOWFLAKE'
AS
SELECT
  w.player,
  w.total_score,
  w.window_start,
  DATEADD(second, 15, w.window_start) AS window_end
FROM (
  SELECT
    e.player,
    SUM(e.score_i) AS total_score,
    TIME_SLICE(e.ts, 15, 'SECOND') AS window_start
  FROM (
    SELECT
      v:player::STRING AS player,
      v:score::INTEGER AS score_i,
      v:event_ts::TIMESTAMP_LTZ AS ts
    FROM (
      SELECT PARSE_JSON(event) AS v
      FROM balloon_game_events."balloon_pops"."balloon_game_events"
    ) q
  ) e
  GROUP BY e.player, TIME_SLICE(e.ts, 15, 'SECOND')
) w;
```

**4. Balloon Colored Pops** — windows by player and color:

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE dt_balloon_colored_pops (
  player STRING,
  balloon_color STRING,
  balloon_pops NUMBER(38,0),
  points_by_color NUMBER(38,0),
  bonus_hits NUMBER(38,0),
  window_start TIMESTAMP_LTZ,
  window_end TIMESTAMP_LTZ
)
  TARGET_LAG = '5 minutes'
  WAREHOUSE = BALLOON_WH
  EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
  CATALOG = 'SNOWFLAKE'
AS
SELECT
  w.player,
  w.balloon_color,
  w.balloon_pops,
  w.points_by_color,
  w.bonus_hits,
  w.window_start,
  DATEADD(second, 15, w.window_start) AS window_end
FROM (
  SELECT
    e.player,
    e.balloon_color,
    COUNT(*) AS balloon_pops,
    SUM(e.score_i) AS points_by_color,
    COUNT_IF(e.fav_bonus) AS bonus_hits,
    TIME_SLICE(e.ts, 15, 'SECOND') AS window_start
  FROM (
    SELECT
      v:player::STRING AS player,
      v:balloon_color::STRING AS balloon_color,
      v:score::INTEGER AS score_i,
      v:favorite_color_bonus::BOOLEAN AS fav_bonus,
      v:event_ts::TIMESTAMP_LTZ AS ts
    FROM (
      SELECT PARSE_JSON(event) AS v
      FROM balloon_game_events."balloon_pops"."balloon_game_events"
    ) q
  ) e
  GROUP BY e.player, e.balloon_color, TIME_SLICE(e.ts, 15, 'SECOND')
) w;
```

**5. Color Performance Trends** — average score per pop by color:

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE dt_color_performance_trends (
  balloon_color STRING,
  avg_score_per_pop NUMBER(38,6),
  total_pops NUMBER(38,0),
  window_start TIMESTAMP_LTZ,
  window_end TIMESTAMP_LTZ
)
  TARGET_LAG = '5 minutes'
  WAREHOUSE = BALLOON_WH
  EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
  CATALOG = 'SNOWFLAKE'
AS
SELECT
  w.balloon_color,
  w.avg_score_per_pop,
  w.total_pops,
  w.window_start,
  DATEADD(second, 15, w.window_start) AS window_end
FROM (
  SELECT
    e.balloon_color,
    AVG(e.score_i) AS avg_score_per_pop,
    COUNT(*) AS total_pops,
    TIME_SLICE(e.ts, 15, 'SECOND') AS window_start
  FROM (
    SELECT
      v:balloon_color::STRING AS balloon_color,
      v:score::INTEGER AS score_i,
      v:event_ts::TIMESTAMP_LTZ AS ts
    FROM (
      SELECT PARSE_JSON(event) AS v
      FROM balloon_game_events."balloon_pops"."balloon_game_events"
    ) q
  ) e
  GROUP BY e.balloon_color, TIME_SLICE(e.ts, 15, 'SECOND')
) w;
```

> **Alternatively**, you can execute these DDLs using the Snowflake CLI: `snow sql --filename snowflake/lab/generated/03_dt_pipelines.generated.sql` (from the [companion repository](https://github.com/Snowflake-Labs/sfguide-lakehouse-iceberg-production-pipelines)).

#### Verify

Check DT status after creation:

```sql
SHOW DYNAMIC TABLES LIKE 'dt_%' IN SCHEMA balloon_silver.silver;
```

Wait for an initial refresh (check Snowsight → **Data** → **Dynamic Tables**, or inspect **SCHEDULING_STATE** in the **SHOW** output), then query:

```sql
-- Top players by score
SELECT player, total_score, bonus_pops, last_event_ts
FROM balloon_silver.silver.dt_player_leaderboard
ORDER BY total_score DESC NULLS LAST
LIMIT 15;
```

```sql
-- 15-second windowed scores
SELECT player, total_score, window_start, window_end
FROM balloon_silver.silver.dt_realtime_scores
ORDER BY window_start DESC, player
LIMIT 20;
```

<!-- ------------------------ -->
## Snowflake Intelligence

Your silver Dynamic Iceberg Tables are now **AI-ready**. By creating a [Semantic View](https://docs.snowflake.com/en/user-guide/views-semantic) over the five silver tables, you enable natural-language querying via [Snowflake Intelligence](https://docs.snowflake.com/en/user-guide/snowflake-intelligence) and the [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) API — no additional ETL, no model training, no external tools.

A Semantic View defines the business meaning of your tables, columns, and metrics in YAML. Once created, users (and AI agents) can ask questions like:

- *"Who is the top-scoring player?"*
- *"Which balloon color gives the highest average points?"*
- *"Show me score trends over the last hour"*

…and get accurate SQL-backed answers grounded in your silver data.

### Easy Path — Interactive Notebook

Open [si_lab_guide.ipynb](https://github.com/Snowflake-Labs/sfguide-lakehouse-iceberg-production-pipelines/blob/main/notebooks/si_lab_guide.ipynb) in Snowflake Notebooks for a guided walkthrough. The notebook uses Cortex Code prompts to auto-generate the Semantic View.

### Detailed Path

#### Create the Semantic View

Create a Semantic View that describes all five silver tables with their business context:

```sql
CREATE OR REPLACE SEMANTIC VIEW balloon_silver.silver.balloon_game_semantic_view

  TABLES (
    player_leaderboard AS balloon_silver.silver.dt_player_leaderboard
      PRIMARY KEY (player)
      WITH SYNONYMS ('leaderboard', 'rankings', 'top players')
      COMMENT = 'Aggregated player scores: total score, bonus pops, last event timestamp per player',

    color_stats AS balloon_silver.silver.dt_balloon_color_stats
      UNIQUE (player, balloon_color)
      WITH SYNONYMS ('color breakdown', 'player colors', 'color scores')
      COMMENT = 'Per-player breakdown by balloon color: pops, points, and bonus hits',

    realtime_scores AS balloon_silver.silver.dt_realtime_scores
      WITH SYNONYMS ('live scores', 'recent scores', 'hot streaks')
      COMMENT = '15-second windowed score totals per player for time-series analysis',

    colored_pops AS balloon_silver.silver.dt_balloon_colored_pops
      WITH SYNONYMS ('detailed pops', 'player color windows')
      COMMENT = 'Most granular view: per-player, per-color pops in 15-second time windows',

    color_trends AS balloon_silver.silver.dt_color_performance_trends
      WITH SYNONYMS ('color trends', 'color performance', 'best colors')
      COMMENT = 'Average score per pop and total pops by balloon color over 15-second windows'
  )

  RELATIONSHIPS (
    color_stats_to_leaderboard AS
      color_stats (player) REFERENCES player_leaderboard,
    realtime_to_leaderboard AS
      realtime_scores (player) REFERENCES player_leaderboard,
    colored_pops_to_leaderboard AS
      colored_pops (player) REFERENCES player_leaderboard,
    colored_pops_to_color_stats AS
      colored_pops (player, balloon_color) REFERENCES color_stats
  )

  FACTS (
    player_leaderboard.total_score AS player_leaderboard.total_score
      WITH SYNONYMS = ('total score', 'overall score', 'total points')
      COMMENT = 'Cumulative score across all balloon pops',
    player_leaderboard.bonus_pops AS player_leaderboard.bonus_pops
      WITH SYNONYMS = ('bonus pops', 'bonuses', 'bonus count')
      COMMENT = 'Number of pops where player hit their favorite color',
    color_stats.balloon_pops AS color_stats.balloon_pops
      WITH SYNONYMS = ('pops', 'pop count', 'times popped')
      COMMENT = 'Number of times this player popped this color',
    color_stats.points_by_color AS color_stats.points_by_color
      WITH SYNONYMS = ('points by color', 'color points', 'color score')
      COMMENT = 'Total points earned from popping this color',
    color_stats.bonus_hits AS color_stats.bonus_hits
      WITH SYNONYMS = ('bonus hits', 'color bonuses')
      COMMENT = 'Number of favorite-color bonus pops for this color',
    realtime_scores.window_score AS realtime_scores.total_score
      WITH SYNONYMS = ('window score', 'live score', 'current score')
      COMMENT = 'Sum of scores within the 15-second window',
    colored_pops.window_pops AS colored_pops.balloon_pops
      COMMENT = 'Pop count for this player+color in this window',
    colored_pops.window_points AS colored_pops.points_by_color
      COMMENT = 'Points for this player+color in this window',
    colored_pops.window_bonus AS colored_pops.bonus_hits
      COMMENT = 'Bonus pops for this player+color in this window',
    color_trends.avg_score_per_pop AS color_trends.avg_score_per_pop
      WITH SYNONYMS = ('efficiency', 'points per pop', 'scoring rate', 'best value')
      COMMENT = 'Average points earned per pop of this color in this window',
    color_trends.total_pops AS color_trends.total_pops
      WITH SYNONYMS = ('volume', 'popularity', 'total pops')
      COMMENT = 'Total pops of this color in this window'
  )

  DIMENSIONS (
    player_leaderboard.player_name AS player_leaderboard.player
      WITH SYNONYMS = ('player', 'gamer', 'username', 'who')
      COMMENT = 'Unique player identifier',
    player_leaderboard.last_active AS player_leaderboard.last_event_ts
      WITH SYNONYMS = ('last active', 'last seen', 'last played')
      COMMENT = 'Timestamp of the most recent game event for this player',
    color_stats.cs_player AS color_stats.player
      COMMENT = 'Player identifier in color stats',
    color_stats.color AS color_stats.balloon_color
      WITH SYNONYMS = ('balloon color', 'color', 'balloon type')
      COMMENT = 'Color of the balloon (red, blue, green, yellow, etc.)',
    color_stats.cs_last_event AS color_stats.last_event_ts
      COMMENT = 'Most recent pop of this color by this player',
    realtime_scores.rs_player AS realtime_scores.player
      COMMENT = 'Player identifier in realtime scores',
    realtime_scores.window_start AS realtime_scores.window_start
      WITH SYNONYMS = ('start time', 'window start')
      COMMENT = 'Start of the 15-second time window',
    realtime_scores.window_end AS realtime_scores.window_end
      WITH SYNONYMS = ('end time', 'window end')
      COMMENT = 'End of the 15-second time window',
    colored_pops.cp_player AS colored_pops.player
      COMMENT = 'Player identifier in colored pops',
    colored_pops.cp_color AS colored_pops.balloon_color
      COMMENT = 'Balloon color in the detailed window view',
    colored_pops.cp_window_start AS colored_pops.window_start
      COMMENT = 'Start of the time window',
    colored_pops.cp_window_end AS colored_pops.window_end
      COMMENT = 'End of the time window',
    color_trends.ct_color AS color_trends.balloon_color
      WITH SYNONYMS = ('trending color', 'color trend')
      COMMENT = 'Balloon color for performance trend analysis',
    color_trends.ct_window_start AS color_trends.window_start
      COMMENT = 'Start of the trend analysis window',
    color_trends.ct_window_end AS color_trends.window_end
      COMMENT = 'End of the trend analysis window'
  )

  METRICS (
    player_leaderboard.m_total_score AS SUM(player_leaderboard.total_score)
      WITH SYNONYMS = ('total points', 'combined score')
      COMMENT = 'Total cumulative score across all players',
    player_leaderboard.m_total_bonus_pops AS SUM(player_leaderboard.bonus_pops)
      WITH SYNONYMS = ('bonus total', 'all bonuses')
      COMMENT = 'Total bonus pops across all players',
    player_leaderboard.m_player_count AS COUNT(player_leaderboard.player)
      WITH SYNONYMS = ('number of players', 'how many players')
      COMMENT = 'Count of players on the leaderboard',
    color_stats.m_total_pops_by_color AS SUM(color_stats.balloon_pops)
      WITH SYNONYMS = ('total balloon pops', 'all pops')
      COMMENT = 'Total balloon pops aggregated across players for a given color',
    color_stats.m_total_points_by_color AS SUM(color_stats.points_by_color)
      WITH SYNONYMS = ('color points total', 'total color points')
      COMMENT = 'Total points aggregated across players for a given color',
    color_stats.m_avg_points_per_pop AS AVG(color_stats.points_by_color / NULLIF(color_stats.balloon_pops, 0))
      WITH SYNONYMS = ('efficiency', 'scoring rate', 'points per pop')
      COMMENT = 'Average points per pop across colors',
    realtime_scores.m_max_window_score AS MAX(realtime_scores.window_score)
      WITH SYNONYMS = ('best window', 'peak score', 'hottest moment')
      COMMENT = 'Highest score in any single 15-second window',
    realtime_scores.m_avg_window_score AS AVG(realtime_scores.window_score)
      WITH SYNONYMS = ('average window score', 'typical window')
      COMMENT = 'Average score per 15-second window',
    color_trends.m_avg_efficiency AS AVG(color_trends.avg_score_per_pop)
      WITH SYNONYMS = ('trend efficiency', 'color efficiency')
      COMMENT = 'Weighted average score per pop across time windows',
    color_trends.m_total_pops AS SUM(color_trends.total_pops)
      WITH SYNONYMS = ('color popularity', 'total color pops')
      COMMENT = 'Total balloon pops across all colors and time windows'
  )

  COMMENT = 'AI-ready semantic layer over balloon game silver Dynamic Iceberg Tables'

  AI_SQL_GENERATION 'This is a balloon popping game. Players pop colored balloons to earn points. Some pops are bonus pops worth extra. The leaderboard has overall rankings by total_score. Color stats show which colors each player pops most and points per color. Realtime scores show 15-second windows of activity. Color trends show which balloon colors give the best points-per-pop over time. When asked about the top player, use the leaderboard total_score. When asked which color scores best, use color_trends avg_score_per_pop. When asked who is hot right now, use realtime_scores with the most recent window_start.';
```

#### Verify the Semantic View

```sql
SHOW SEMANTIC VIEWS IN SCHEMA balloon_silver.silver;
```

```sql
DESC SEMANTIC VIEW balloon_silver.silver.balloon_game_semantic_view;
```

#### Configure Snowflake Intelligence with the Semantic View

With the Semantic View created, set up a Snowflake Intelligence **agent** that uses it as a tool for natural-language querying.

##### Required Privileges

Lab users running as **ACCOUNTADMIN** already have the necessary permissions — no additional grants are needed.

> **Production note:** In a production environment, you would grant `SNOWFLAKE.CORTEX_USER` and `REFERENCES` + `SELECT` on the Semantic View to consumer roles:
> ```sql
> GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE <consumer_role>;
> GRANT REFERENCES, SELECT ON SEMANTIC VIEW balloon_silver.silver.balloon_game_semantic_view
>   TO ROLE <consumer_role>;
> ```

##### Create the Agent

**1. Navigate to the Agent admin page** — In Snowsight, go to **AI & ML → Agents**. Confirm your role is set to **ACCOUNTADMIN** (top-right role selector).

**2. Create a new agent:**

- Click **+ Create agent**
- **Agent object name:** `balloon_game_agent` (internal identifier)
- **Display name:** `Balloon Game Analytics` (shown to users in the chat UI)
- **Description:** *"Ask questions about balloon game player scores, color stats, and performance trends from the silver lakehouse tables."*
- Click **Create agent**

**3. Add the Cortex Analyst tool (Semantic View):**

- Select the **Tools** tab in the agent editor
- Find **Cortex Analyst** and click **+ Add**
- Choose **Semantic View** (not "Semantic model file" — we already have a view, not a YAML on a stage)
- Select database: `balloon_silver`, schema: `silver`, view: `balloon_game_semantic_view`
- For **Description**, click **Generate with Cortex** to auto-generate a tool description from your semantic metadata — or write your own, e.g.: *"Queries structured balloon game data including player leaderboards, color stats, real-time scores, and performance trends. Use for any question about players, scores, colors, or time-based patterns."*
- Set the **Warehouse** to `BALLOON_WH` (or your assigned warehouse)

**4. (Optional) Add the Email tool:**

If you want the agent to send query results or insights via email, first create the notification integration and stored procedure:

```sql
-- Notification integration for email delivery
CREATE OR REPLACE NOTIFICATION INTEGRATION email_integration
  TYPE = EMAIL
  ENABLED = TRUE
  DEFAULT_SUBJECT = 'Balloon Game Analytics';

-- Stored procedure that the agent calls to send emails
CREATE OR REPLACE PROCEDURE balloon_silver.silver.send_email(
    recipient_email VARCHAR,
    subject VARCHAR,
    body VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
AS
BEGIN
    CALL SYSTEM$SEND_EMAIL(
        'email_integration',
        :recipient_email,
        :subject,
        :body,
        'text/html'
    );
    RETURN 'Email sent successfully to ' || :recipient_email;
END;
```

Then, in the agent editor:

- In the **Tools** tab, find **Custom Tools** and click **+ Add**
- Select database: `balloon_silver`, schema: `silver`, procedure: `send_email`
- Configure parameter descriptions:
  - **recipient_email:** *"If the email is not provided, send it to the current user's email address."*
  - **subject:** *"If subject is not provided, use 'Balloon Game Analytics'."*
  - **body:** *"If body is not provided, summarize the last question and use that as content for the email."*

**5. Add sample questions (recommended):**

- Select the **Voice** tab (or **Instructions** tab depending on your Snowsight version)
- Under **Sample questions**, add examples:
  - *"Who are the top 5 players by total score?"*
  - *"Which balloon color gives the best average points per pop?"*
  - *"Show me score trends over the last few time windows"*
  - *"How many total bonus pops have all players earned?"*
  - *"Email me a summary of the top 3 players"*

**6. Set orchestration instructions:**

- In the **Instructions** section, add: *"Whenever you can answer visually with a chart, always choose to generate a chart even if the user didn't specify to."*

**7. Save the agent** — Click **Save** in the top-right corner. The agent is now live.

##### Access the Agent

Once saved, users can access the agent:

- **Snowflake Intelligence chat:** Navigate to **AI & ML → Snowflake Intelligence**, select `Balloon Game Analytics` from the agent picker, and start asking questions
- **Direct URL:** Go to [ai.snowflake.com](https://ai.snowflake.com) and select the agent

> **How it works:** When a user asks a question, the agent routes it to Cortex Analyst, which reads the Semantic View's table/column descriptions, relationships, and primary keys to generate accurate SQL. The query executes against your silver Dynamic Iceberg Tables and returns results in the chat — no SQL knowledge required.

#### Try It with Snowflake Intelligence

Example questions to try:

- *"Who are the top 5 players by total score?"*
- *"What's the most popular balloon color across all players?"*
- *"Which color gives the best average points per pop?"*
- *"Show me how player scores trend over time windows"*
- *"Which players have the most bonus pops as a percentage of total pops?"*

> **Why this matters:** Your silver data was already queryable by SQL users and BI tools. The Semantic View now makes it queryable by **anyone** — business analysts, executives, or automated agents — using plain English.

<!-- ------------------------ -->
## SiS Dashboard

After the silver Dynamic Tables are live, deploy a Streamlit in Snowflake app that visualizes the balloon game event data. The app runs entirely in your Snowflake account next to your data.

This chapter offers **two paths** to the same outcome — choose one (or try both):

| Path | How | What you'll learn |
|------|-----|-------------------|
| **Easy Path: Cortex Code** | Describe what you want in natural language; AI builds, debugs, and deploys | Intent-driven development — how iterative prompts replace manual coding |
| **Detailed Path: CLI** | Write every file and run every CLI command yourself | Full control, traditional workflow |

> **Recommended:** Try the Easy Path first. Watch Cortex Code encounter errors (missing packages, unsupported features, permission gaps) and self-heal. Then ask it to generate the "ideal prompt" that would have worked in one shot — that's the core lesson of [Intent-Driven Development (IDD)](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c).

**Prerequisites:**

- All five **dt_*** tables exist in **balloon_silver.silver**

### Easy Path: Intent-Driven (Cortex Code)

Open **Cortex Code** from the Snowsight sidebar. This path has three rounds that demonstrate the progression from vague intent to precise specification.

#### Round 1 — State Your Intent

*Tell the agent **what** you want, not **how** to build it.*

Copy and paste this into Cortex Code:

```text
First, ask me the following before you start building:

1. What database.schema has my game's Dynamic Tables?
2. Where should the Streamlit app and stage be created?
3. What warehouse should it use?

After I answer, build a multi-page Streamlit in Snowflake app that visualizes balloon game data from those Dynamic Tables.
```

**What to expect:**

- Cortex Code asks clarifying questions — answer with `balloon_silver.silver`, a schema of your choice for the app (e.g. `balloon_silver.apps`), and `BALLOON_WH`
- It generates a Streamlit app, deploys it, and likely hits errors (missing packages, unsupported chart types, permission issues)
- Watch it self-heal — this is the key learning

#### Round 2 — Refine

After Round 1 deploys (with or without errors), ask Cortex Code:

```text
Generate the ideal one-shot prompt that, if I had given it to you initially, would have produced a working app with no errors. Include all constraints you discovered.
```

This teaches the **IDD lesson**: the first attempt surfaces constraints; the second attempt codifies them into a reusable specification.

#### Round 3 — One-Shot Deploy

Paste the generated ideal prompt back into a fresh Cortex Code session. Observe that it deploys cleanly on the first try.

### Detailed Path: CLI

This path uses the [companion repository](https://github.com/Snowflake-Labs/sfguide-lakehouse-iceberg-production-pipelines) which contains the app source code under `snowflake/sis/`.

#### Prerequisites

- [Snowflake CLI](https://docs.snowflake.com/developer-guide/snowflake-cli/installation/installation) installed (version 3.14+)
- A configured connection (`snow connection test` succeeds)

#### Create Schema and Deploy

```sql
CREATE SCHEMA IF NOT EXISTS balloon_silver.apps;
```

From the companion repo root:

```bash
snow streamlit deploy balloon_game_dashboard --project snowflake/sis --replace
```

Add `--open` to launch the app in your browser after deploy.

#### Open and Share

Open the app in **Snowsight** → **Streamlit**, then `GRANT USAGE` on the Streamlit object to analyst roles as needed.

<!-- ------------------------ -->
## DuckDB via HIRC

This chapter queries the five silver Dynamic Iceberg Tables from **DuckDB** using Snowflake's **Horizon Iceberg REST Catalog (HIRC)** — no data copy, no ETL. DuckDB talks directly to Snowflake's Polaris-based REST catalog endpoint and reads Iceberg files from Snowflake-managed storage.

### Easy Path — Interactive Notebook

Open [duckdb_lab_guide.ipynb](https://github.com/Snowflake-Labs/sfguide-lakehouse-iceberg-production-pipelines/blob/main/notebooks/duckdb_lab_guide.ipynb) in Snowflake Notebooks (or locally in Jupyter/VS Code).

### Detailed Path

#### Create Service Account and PAT

Run the following SQL as ACCOUNTADMIN to create a dedicated service account for DuckDB access:

```sql
USE ROLE ACCOUNTADMIN;

-- Create a reader role
CREATE ROLE IF NOT EXISTS duckdb_silver_reader;

-- Create a service user
CREATE USER IF NOT EXISTS duckdb_sa
  TYPE = SERVICE
  DEFAULT_ROLE = duckdb_silver_reader;

-- Grant the role to the user
GRANT ROLE duckdb_silver_reader TO USER duckdb_sa;

-- Grant access to silver data
GRANT USAGE ON DATABASE balloon_silver TO ROLE duckdb_silver_reader;
GRANT USAGE ON SCHEMA balloon_silver.silver TO ROLE duckdb_silver_reader;
GRANT SELECT ON ALL DYNAMIC TABLES IN SCHEMA balloon_silver.silver TO ROLE duckdb_silver_reader;
GRANT SELECT ON FUTURE DYNAMIC TABLES IN SCHEMA balloon_silver.silver TO ROLE duckdb_silver_reader;

-- Create a network rule and policy (open for lab; restrict in production)
CREATE OR REPLACE NETWORK RULE balloon_silver.public.duckdb_nr
  MODE = INGRESS
  TYPE = IPV4
  VALUE_LIST = ('0.0.0.0/0');

CREATE OR REPLACE NETWORK POLICY duckdb_np
  ALLOWED_NETWORK_RULE_LIST = (balloon_silver.public.duckdb_nr);

ALTER USER duckdb_sa SET NETWORK_POLICY = duckdb_np;

-- Generate the PAT (save the token value — it is shown only once)
ALTER USER duckdb_sa ADD PROGRAMMATIC ACCESS TOKEN duckdb_sa_pat
  ROLE_RESTRICTION = duckdb_silver_reader
  DAYS_TO_EXPIRY = 7
  COMMENT = 'PAT for DuckDB HIRC access';
```

> **Important:** Copy the PAT value from the output — it is displayed only once and cannot be retrieved later.

#### DuckDB SQL

Install and load extensions:

```sql
INSTALL iceberg;
INSTALL httpfs;
LOAD iceberg;
LOAD httpfs;
```

Create the PAT-based Iceberg secret (replace `<your_pat>` and `<account>` with your values):

```sql
CREATE SECRET iceberg_pat_secret (
    TYPE iceberg,
    CLIENT_ID '',
    CLIENT_SECRET '<your_pat>',
    OAUTH2_SERVER_URI 'https://<account>.snowflakecomputing.com/polaris/api/catalog/v1/oauth/tokens',
    OAUTH2_GRANT_TYPE 'client_credentials',
    OAUTH2_SCOPE 'session:role:duckdb_silver_reader'
);
```

Attach the silver database — **catalog name must be UPPERCASE**:

```sql
ATTACH 'BALLOON_SILVER' AS balloon_silver (
    TYPE iceberg,
    SECRET iceberg_pat_secret,
    ENDPOINT 'https://<account>.snowflakecomputing.com/polaris/api/catalog',
    SUPPORT_NESTED_NAMESPACES false
);
```

Discover and query tables:

```sql
USE balloon_silver.SILVER;
SHOW TABLES;

-- Leaderboard
SELECT PLAYER, TOTAL_SCORE, BONUS_POPS, LAST_EVENT_TS
FROM balloon_silver.SILVER.DT_PLAYER_LEADERBOARD
ORDER BY TOTAL_SCORE DESC NULLS LAST
LIMIT 10;

-- Color stats
SELECT BALLOON_COLOR, BALLOON_POPS, POINTS_BY_COLOR
FROM balloon_silver.SILVER.DT_BALLOON_COLOR_STATS
ORDER BY POINTS_BY_COLOR DESC
LIMIT 10;

-- Realtime scores
SELECT PLAYER, TOTAL_SCORE, WINDOW_START, WINDOW_END
FROM balloon_silver.SILVER.DT_REALTIME_SCORES
ORDER BY WINDOW_START DESC, TOTAL_SCORE DESC
LIMIT 10;
```

> **Two HIRC rules to know:**
> - Warehouse name in `ATTACH` must be **UPPERCASE** — `'BALLOON_SILVER'`, not `'balloon_silver'`. Lowercase returns HTTP 404.
> - `GRANT SELECT ON ALL TABLES` silently skips Dynamic Iceberg Tables — always use `ON ALL DYNAMIC TABLES`.

<!-- ------------------------ -->
## Cleanup and Conclusion

### Cleanup

To remove all objects created in this lab:

```sql
-- Drop the silver database (removes all DTs, Semantic View, Streamlit app)
DROP DATABASE IF EXISTS balloon_silver;

-- Remove DuckDB service account objects
DROP NETWORK POLICY IF EXISTS duckdb_np;
DROP USER IF EXISTS duckdb_sa;
DROP ROLE IF EXISTS duckdb_silver_reader;

-- Drop the warehouse (optional — keep if you use it elsewhere)
DROP WAREHOUSE IF EXISTS BALLOON_WH;
```

> **Note:** The Catalog-Linked Database (`balloon_game_events`) connects to shared read-only data. You may drop it with `DROP DATABASE IF EXISTS balloon_game_events;` — this removes only the Snowflake metadata link, not the underlying Iceberg data.

### What You Learned

- How Snowflake uses Catalog Linked Databases to query externally managed Iceberg tables without moving data
- How Dynamic Iceberg Tables transform raw JSON into typed silver aggregates while preserving open Iceberg format
- How a Semantic View makes your data queryable in plain English via Snowflake Intelligence
- How to deploy a Streamlit in Snowflake dashboard that reads from silver Dynamic Tables
- How to query Snowflake-managed Iceberg tables from DuckDB via the Horizon REST Catalog using a Programmatic Access Token
- How intent-driven development with Cortex Code can replace manual coding workflows

### Related Resources

Documentation:

- [Snowflake Iceberg tables](https://docs.snowflake.com/en/user-guide/tables-iceberg)
- [Use a catalog-linked database](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-linked-database)
- [Create dynamic Apache Iceberg tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-create-iceberg)
- [Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic)
- [Snowflake Intelligence](https://docs.snowflake.com/en/user-guide/snowflake-intelligence)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Getting started with Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/getting-started/overview)
- [Programmatic Access Tokens](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)

Additional Reading:

- [Companion repository: sfguide-lakehouse-iceberg-production-pipelines](https://github.com/Snowflake-Labs/sfguide-lakehouse-iceberg-production-pipelines)
- [DuckDB HIRC demo: hirc-duckdb-demo](https://github.com/kameshsampath/hirc-duckdb-demo)
- [Apache Iceberg REST Catalog API spec](https://iceberg.apache.org/spec/#rest-catalog-api)
