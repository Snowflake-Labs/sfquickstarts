author: Elliott Botwick, Josh Reini
id: getting-started-with-cortex-agent-evaluations
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
language: en
summary: Get started with Cortex Agent Evaluations
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Cortex Agents, Evaluations, AI, LLM, Snowflake Cortex

# Getting Started with Cortex Agent Evaluations

## Overview

Duration: 5

Building AI agents is just the beginning—understanding how well they perform is critical for delivering reliable, production-ready applications. Snowflake Cortex Agent Evaluations provides a comprehensive framework for measuring agent performance across multiple dimensions, helping you identify issues and iterate toward better outcomes.

This quickstart guides you through setting up and running evaluations on Cortex Agents, building evaluation datasets, and comparing agent configurations to optimize performance.

:::info[Preview Feature — Private]

Support for this feature is currently not in production and is available only to selected accounts.

:::

### What is Cortex Agent Evaluations?

Cortex Agent Evaluations is a feature within Snowflake Cortex that enables you to systematically measure and improve your AI agents. It provides:

- **Tool Selection Accuracy**: Measures whether the agent selects the correct tools for a given query
- **Tool Execution Accuracy**: Evaluates whether tool calls are executed correctly with proper parameters
- **Answer Correctness**: Assesses the quality and accuracy of the agent's final response

### What You'll Learn

- How to set up sample marketing data and agents for evaluation
- How to create evaluation datasets with ground truth data
- How to run evaluations and interpret metrics
- How to compare agent configurations to identify improvements
- How to use the Evalset Generator app to build custom evaluation datasets

### What You'll Build

A complete evaluation workflow that enables you to:

- Create evaluation datasets from agent logs or manual input
- Run evaluations across multiple metrics
- Compare different agent configurations
- Iterate on agent design based on evaluation insights

### Prerequisites

- A [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with access to Cortex Agent Evaluations (Private Preview)
- A role with privileges to create databases, schemas, tables, and stages
- Python 3.8+ (for optional local Streamlit app)
- Basic familiarity with Snowflake SQL and Cortex Agents

<!-- ------------------------ -->

## Setup Environment

Duration: 10

### Clone the Repository

First, clone the quickstart repository to get all the necessary files:

```bash
git clone https://github.com/sfc-gh-ebotwick/CORTEX_AGENT_EVALS_QUICKSTART.git
cd CORTEX_AGENT_EVALS_QUICKSTART
```

### What's in the Repository

| File | Description |
|------|-------------|
| `SETUP.sql` | SQL script to create sample database, tables, agents, and services |
| `agent_evalset_generator.py` | Streamlit app for building evaluation datasets |
| `requirements.txt` | Python dependencies for the Streamlit app |
| `README.md` | Repository documentation |

### Run the Setup Script

**Step 1.** Open Snowsight and create a new SQL Worksheet.

**Step 2.** Copy and paste the contents of `SETUP.sql` into the worksheet.

**Step 3.** Execute all statements in order from top to bottom.

This script will create:

- **MARKETING_CAMPAIGNS_DB**: A database containing sample marketing data
- **Marketing data tables**: Campaign performance, feedback, and content data
- **Semantic View**: For Cortex Analyst Service on campaign performance and feedback data
- **Cortex Search Service**: On campaign content for semantic search capabilities
- **Stored Procedure**: Custom agent tool for specialized operations
- **Cortex Agents**: Pre-configured agents with the above services attached

![Setup Complete](assets/setup-complete.png)

<!-- ------------------------ -->

## Understanding the Evaluation Schema

Duration: 5

Before creating evaluations, it's important to understand the expected dataset schema that Cortex Agent Evaluations uses.

### Evaluation Dataset Schema

Your evaluation dataset should follow this structure:

| Column | Type | Description |
|--------|------|-------------|
| `INPUT_QUERY` | VARCHAR | The natural language query to send to the agent |
| `EXPECTED_TOOLS` | VARIANT | JSON object containing ground truth data |

### Expected Tools Format

The `EXPECTED_TOOLS` column contains a JSON object with the following structure:

```json
{
  "ground_truth_invocations": [
    {
      "tool_name": "cortex_analyst",
      "parameters": {...}
    }
  ],
  "ground_truth_output": "Expected response text..."
}
```

### Example Dataset Row

```sql
INSERT INTO EVALS_TABLE (INPUT_QUERY, EXPECTED_TOOLS)
VALUES (
  'What was the total spend on our summer campaign?',
  PARSE_JSON('{
    "ground_truth_invocations": [
      {"tool_name": "cortex_analyst", "service": "campaign_analytics"}
    ],
    "ground_truth_output": "The total spend on the summer campaign was $45,000."
  }')
);
```

<!-- ------------------------ -->

## Create Your First Evaluation

Duration: 15

Now let's create and run your first agent evaluation.

### Step 1: Navigate to the Agent Evaluations Tab

**1.** In Snowsight, navigate to **AI & ML » Agents**

**2.** Click on the agent you created during setup (from `SETUP.sql`)

**3.** Click the **Evaluations** tab

![Agent Evaluations Tab](assets/evaluations-tab.png)

### Step 2: Configure the Evaluation Run

**1.** Click **Create New Evaluation**

**2.** Enter a name for your evaluation run (e.g., "Baseline Marketing Agent Eval")

**3.** Optionally add a description to document your evaluation purpose

**4.** Click **Next**

### Step 3: Select or Create a Dataset

**Option A: Use the Pre-built Dataset**

If you ran the setup script, you'll have a sample evaluation dataset ready:

- Select **Use Existing Dataset**
- Choose `MARKETING_CAMPAIGNS_DB.PUBLIC.EVALS_TABLE` as your input table
- Select `MARKETING_CAMPAIGNS_DB.PUBLIC.QUICKSTART_EVALSET` as your dataset destination

**Option B: Create a New Dataset**

- Select **Create New Dataset**
- Choose your input table containing queries and expected outputs
- Specify a destination table for the processed dataset

**5.** Click **Next**

### Step 4: Configure Metrics

**1.** Select `INPUT_QUERY` as your Query Text column

**2.** Enable the evaluation metrics you want to measure:

   - ☑️ **Tool Selection Accuracy** - Reference the `EXPECTED_TOOLS` column
   - ☑️ **Tool Execution Accuracy** - Reference the `EXPECTED_TOOLS` column
   - ☑️ **Answer Correctness** - Reference the `EXPECTED_TOOLS` column

**3.** Click **Create Evaluation**

![Configure Metrics](assets/configure-metrics.png)

### Step 5: Wait for Results

The evaluation will now execute your queries and compute metrics. This typically takes **3-5 minutes** depending on dataset size.

![Evaluation Running](assets/evaluation-running.png)

<!-- ------------------------ -->

## Compare Agent Configurations

Duration: 10

One of the most powerful features of Cortex Agent Evaluations is the ability to compare different agent configurations to identify improvements.

### Create an Improved Agent

Before comparing, ensure you have two agent configurations:

1. **Baseline Agent**: Your original agent from the setup
2. **Improved Agent**: A modified agent with enhanced orchestration or response instructions

Common improvements to test:

- More detailed orchestration instructions
- Additional context in response instructions
- Different tool configurations
- Modified semantic models

### Run Evaluation on Improved Agent

**1.** Navigate to your improved agent in **AI & ML » Agents**

**2.** Click the **Evaluations** tab

**3.** Follow the same steps as the first evaluation:

   - Name your evaluation (e.g., "Improved Marketing Agent Eval")
   - **Reuse the same dataset** you created in the previous evaluation
   - Select the same metrics for an apples-to-apples comparison

**4.** Click **Create Evaluation**

### Analyze Comparison Results

Once both evaluations complete, you can compare results:

**1.** View side-by-side metrics for both agent configurations

**2.** Identify specific queries where the improved agent performed better

**3.** Investigate cases where added orchestration and response instructions led to:

   - Higher tool selection accuracy
   - Better tool execution accuracy
   - More correct answers

![Comparison Results](assets/comparison-results.png)

### Key Questions to Answer

- Which queries improved the most with the new configuration?
- Are there patterns in the queries that still fail?
- Did any queries regress with the changes?
- What's the overall improvement in each metric?

<!-- ------------------------ -->

## Using the Evalset Generator App

Duration: 15

The Evalset Generator is a Streamlit application that helps you build evaluation datasets interactively.

### Install Dependencies

First, ensure all required packages are installed:

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file in the repository root with your Snowflake credentials:

```bash
SNOWFLAKE_ACCOUNT=<ACCOUNT_LOCATOR.ACCOUNT_REGION>
SNOWFLAKE_USER=<YOUR_USERNAME>
SNOWFLAKE_USER_PASSWORD=<YOUR_PASSWORD>
```

> **Note**: Replace `<ACCOUNT_LOCATOR.ACCOUNT_REGION>` with your account identifier (e.g., `ABC1234.us-west-2`)

### Launch the Application

Start the Streamlit app:

```bash
streamlit run agent_evalset_generator.py
```

The app will open in your browser at `http://localhost:8501`

![Evalset Generator App](assets/evalset-generator.png)

### App Features

The Evalset Generator helps you build evaluation datasets through four main workflows:

#### 1. Load Data

- Import from agent observability logs
- Load from existing Snowflake tables
- Start with a blank dataset

#### 2. Add Records

- Manually add evaluation records for edge cases
- Define custom queries and expected outputs
- Specify expected tool invocations

#### 3. Edit Records

- Refine queries for clarity
- Update expected outputs based on new requirements
- Correct tool invocation expectations

#### 4. Export Dataset

- Save directly to Snowflake tables
- Export in the required evaluation schema format
- Create versioned datasets for tracking improvements

### Building a Dataset from Agent Logs

**1.** Select your existing agent from the dropdown

**2.** Choose **Load from Agent Logs**

**3.** Review the automatically populated queries from historical agent interactions

**4.** Add ground truth data:

   - Expected tool invocations
   - Expected output responses

**5.** Edit any queries or expectations as needed

**6.** Export to a Snowflake table

<!-- ------------------------ -->

## Best Practices

Duration: 5

### Evaluation Dataset Design

**Diverse Query Coverage**

- Include queries across all expected use cases
- Test edge cases and boundary conditions
- Include queries that should trigger different tools

**Ground Truth Quality**

- Ensure expected outputs are accurate and complete
- Review tool invocation expectations carefully
- Update ground truth as requirements evolve

**Dataset Size**

- Start with 20-50 representative queries
- Expand coverage based on failure analysis
- Balance breadth and depth

### Iterative Improvement

**1. Establish Baseline**

- Run initial evaluation on your current agent
- Document baseline metrics across all dimensions

**2. Identify Weaknesses**

- Analyze queries with low scores
- Look for patterns in failures
- Prioritize high-impact improvements

**3. Make Targeted Changes**

- Modify one aspect at a time
- Update orchestration or response instructions
- Adjust tool configurations as needed

**4. Measure Impact**

- Re-run evaluation with same dataset
- Compare metrics to baseline
- Document what worked and what didn't

**5. Iterate**

- Repeat the process with new improvements
- Track progress over time
- Build a history of evaluation runs

### Common Pitfalls to Avoid

- **Overfitting to evaluation data**: Ensure your agent generalizes beyond test queries
- **Ignoring regressions**: Watch for queries that get worse with changes
- **Inconsistent ground truth**: Maintain quality standards across your dataset
- **Skipping baseline**: Always establish a comparison point before making changes

<!-- ------------------------ -->

## Conclusion and Resources

Duration: 2

Congratulations! You've successfully set up and run Cortex Agent Evaluations. You now have the tools to systematically measure and improve your AI agents.

### What You Learned

- **Environment Setup**: How to configure sample agents and data for evaluation
- **Evaluation Creation**: How to build and run evaluation datasets
- **Metrics Interpretation**: Understanding tool selection, execution, and answer correctness
- **Agent Comparison**: How to compare configurations and identify improvements
- **Dataset Building**: Using the Evalset Generator app for custom datasets

### Next Steps

- Evaluate your own production agents
- Build comprehensive evaluation datasets covering your specific use cases
- Establish an evaluation workflow as part of your agent development process
- Set up automated evaluation runs for continuous monitoring

### Related Resources

- [Cortex Agent Evaluations Documentation](https://docs.snowflake.com/LIMITEDACCESS/cortex-agent-evaluations)
- [Cortex Agents Guide](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-agents)
- [Getting Started with Cortex Agents](https://quickstarts.snowflake.com/guide/getting-started-with-cortex-agents)
- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)

### Repository

- [CORTEX_AGENT_EVALS_QUICKSTART on GitHub](https://github.com/sfc-gh-ebotwick/CORTEX_AGENT_EVALS_QUICKSTART)

