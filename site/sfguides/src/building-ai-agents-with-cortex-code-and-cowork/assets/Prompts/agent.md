# Instructions
Create a Snowflake Cortex Agent that leverages the HOL_COCO_COWORK.TOOLS.HOT_FOOD_SALES_ANALYTICS semantic view to provide real-time sales analytics.

## Specifications
- **Role**: Use role ACCOUNTADMIN
- **Agent Name**: HOT_FOOD_SALES_AGENT
- **Target Location**: HOL_COCO_COWORK.AGENTS
- **Tool**: Semantic view `HOL_COCO_COWORK.TOOLS.HOT_FOOD_SALES_ANALYTICS` (cortex_analyst_text_to_sql)
- **Skills** (from stage `@HOL_COCO_COWORK.TOOLS.SKILLS_STAGE`):
  - `anomaly_detection` at path `skills/anomaly_detection`
  - `sales_report` at path `skills/sales_report`
- **Targeted Users**: Data Analysts and C-Level executives who need evidence-based answers
- **Tone**: Assertive and precise — no hedging language
- **Behavior**: Ask follow-up questions to clarify ambiguous queries
- **Language**: Multi-lingual — always respond in the language the question was asked in
- **Charts**: Generate charts for trends, rankings, and comparisons

## Deploy

After validation passes, deploy the agent to HOL_COCO_COWORK.AGENTS.
