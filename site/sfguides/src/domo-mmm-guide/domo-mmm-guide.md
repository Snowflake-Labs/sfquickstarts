author: Domo
id: getting-started-with-domo-mmm
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/partner-solution, snowflake-site:taxonomy/solution-center/includes/architecture, snowflake-site:taxonomy/industry/advertising-media-and-entertainment, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Build Marketing Mix Models with Domo MMM and Snowflake Cortex AI to measure channel incrementality, optimize budgets, and maximize marketing ROI.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Getting Started with Domo MMM

<!-- ------------------------ -->

## Overview
Duration: 5

In this quickstart, we'll walk through how to use Domo's MMM (Marketing Mix Modeling) app to build powerful Bayesian models that measure the true incremental impact of your marketing channels on revenue. By the end of this guide, you'll be equipped to deploy and utilize the app's capabilities to drive data-driven marketing decisions and optimize your budget allocation.


### What is Domo MMM?

Domo MMM is a sophisticated Marketing Mix Modeling application that Domo MMM analyses past performance, seasonality, and spend data to show which channels drive true incremental revenue. Trained on thousands of real incrementality studies, Domo MMM interprets complex statistical outputs and
translates them into actionable recommendations.Built natively within the Domo platform and natively integrated with  **Snowflake Cortex AI** , it helps marketing teams understand true channel performance, optimize budget allocation, and maximize ROI through data-driven insights.

Domo MMM isolates the incremental impact of each channel through a specialised AI agent trained exclusively on marketing measurement data from leading academics and measurement experts. This AI understands statistical significance, confidence intervals, and channel attribution in ways that general-purpose language models cannot. It processes complex statistical computations via Snowflake's enterprise infrastructure and embeds sophisticated measurement capabilities directly into daily workflows through Domo's AI Agent framework. 

### Prerequisites

- Basic understanding of Snowflake
- A Snowflake account. If you do not have a Snowflake account, you can register for a [free trial account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides).
- A Domo account and a basic understanding of Domo
- Access to data
- Familiarity with marketing metrics and KPIs

### What You'll Learn

- How to request and deploy Domo MMM from Domo
- How to intialize a dataset using Domo Connectors
- How to prepare and structure your marketing data for MMM analysis
- How to configure field mappings in Domo MMM
- How to run and interpret Bayesian Marketing Mix Model results
- How to use budget optimization recommendations
- How to leverage Snowflake Cortex AI for natural language insights

### What You'll Need

- A [Snowflake](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) account
- A [Domo](https://www.domo.com/) account with admin privileges
- Marketing performance data with revenue and channel spend (minimum 8 weeks, recommended 2 years)

### What You'll Build

- A Marketing Mix Modeling solution to analyze channel performance, view iROAS metrics with confidence intervals, decompose revenue by channel, and optimize budget allocation using AI-powered recommendations.

<!-- ------------------------ -->
# Install
## Request Access
Duration: 3

Request the Domo MMM app:

- Open the Domo provider page in the **Snowflake Marketplace**.
- Locate and click the Domo MMM app listing.
- Click **Request**.
- Fill out then submit the request form.

The Domo team will review the request and contact you with more information.

**Important**: Domo MMM cannot be self-installed from the Snowflake Marketplace. You must contact Domo to provision the application for your instance.

### What Domo Configures For You

| Component | Description |
|-----------|-------------|
| **Custom App** | Domo MMM application deployed to your instance |
| **Snowflake Connection** | Cortex AI integration (if requested) |

<!-- ------------------------ -->

## Prepare Your Data
Duration: 10

Domo MMM requires your data to be structured with specific components. This section covers how to prepare your marketing performance data for optimal modeling results.

Over the next few sections, you'll supercharge your marketing data by leveraging SQL in Snowflake alongside Domo’s Magic ETL. Connect key sources such as Adobe Analytics, Google Analytics, Marketo, NetSuite, Salesforce, Facebook, and Instagram. Use customizable join logic and preparatory steps tailored to your data environment to build a cohesive, centralized data foundation. These preparatory steps allow for advanced attribution models and media mix analysis, ensuring you have the insights needed to optimize your marketing strategy.

Leverage the Domo Data Warehouse to access your data wherever it sits to transform & visualize.
![assets/warehouse.png](assets/warehouse.png)

## Add a DataSet using a Connector

When you add a DataSet, you are automatically assigned as the DataSet owner. For information about changing the owner of a DataSet, see Changing the Owner of a DataSet.

You can access the interface for adding Connector DataSets via the Appstore, the Data Center, or the menu.

**To add a DataSet using a Connector**

1. Choose one of the following:

   - (Conditional) If you want to connect to data via the **APPSTORE**, do the following:

     - Select _Appstore_ in the toolbar at the top of the screen.
     - Click the _Search_ tab.
     - Click the _Connector_ checkbox under Capability.
     - Use the search bar or page navigation to locate the Connector you want to connect to, then click it to open its details view.
     - Click _Get the Data_.

     - Alternatively, for some of the most popular Connectors, a _Get the Cards_ button is available. This allows you to power up several prebuilt, live Cards based on your own data, without having to configure advanced options. This is a great way to "preview" the Connector to make sure it provides the data you want. If you choose this option, you are asked to select the desired account or input your account information if you haven't created an account for this Connector yet.

   - (Conditional) If you want to connect to data via the **DATA CENTER**, do the following:

     - Select _Data_ in the toolbar at the top of the screen.
     - In the Connect Data area at the top of the screen, select _Connectors_, _File_, or _Database_, depending on the connection type.

     - You can use the following table to learn more about these Connector types:

       | Connector Type | Description                                                                                                                                                                                   |
       | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
       | Connectors     | A Connector for a third-party app in which data is stored in the cloud. Most of Domo's Connectors fall into this category. Examples include Facebook, Salesforce, Adobe Analytics, and so on. |
       | File           | A Connector used to pull files into Domo. Examples include Excel, Google Sheets, and Box.                                                                                                     |
       | Database       | A Connector in which you write a query to pull data from a database into Domo. Examples include MySQL, Amazon Redshift, and MongoDB.                                                          |

     - The other two icons in this area denote other non-Connector methods for bringing data into Domo. Federated refers to federated DataSets, and API refers to Domo's development environment, where you can build your own custom Connectors. For more information on Federated DataSets, see Connecting to Data Using Workbench 5.
     - Select the Connector type you want.
     - Click the desired Connector tile.

     _Note: Popular Connectors are marked with a Preferred tag. This is also used when there are several different Connectors to the same data, such as Facebook. The most commonly used option will display the Preferred tag._

   - (Conditional) If you want to connect to data via the menu, do the following:
     - Select > _Data_.
     - Select _Connectors_, _File_, or _Database_. _For more information about these Connector types, see the above table._
     - Click the desired Connector tile.

1. Specify the settings in each section. - Refer to the general information included in this topic and to the help in the specific data Connector.
   _For more information about configuring specific data Connectors, see Configuring Each Connector.
   As applicable, click Connect, Next, or Save and open the next section._
1. When finished, click _Save_.
   - You are taken to the details view for the DataSet in the Data Center. For more information about this view, see Data Center Layout.

## Connector Settings

All Connector types in Domo have different options for setting up a DataSet.

Most Connectors require you to enter login credentials, an API key, a server URL, or a combination of these to access the Connector. If you cannot connect after entering your credentials, you have most likely entered incorrect credentials.

For information about finding credentials, see the documentation for your specific Connector. You can find this under [API Connectors](https://domo-support.domo.com/s/topic/0TO5w000000ZaoQGAS).

After you connect, you are usually asked for information about the data you want to pull and the desired format. Most Connectors have two or more associated report types. In addition, many Connectors request a timeframe for the data to be retrieved. You may also be asked to submit a query for retrieving data. For example, when connecting to JIRA you can enter a JQL query to retrieve data for a specified search filter.

For most Connectors, you are also asked to schedule data updates. You can use basic scheduling, in which you select a single, specific unit of time (such as "Every hour") and enter the time of day when the update is to occur, if required. Or you can use advanced scheduling, in which you can select multiple update times.

The information in this section is general and may or may not be required for a certain Connector. For specific requirements for Connectors, see [API Connectors](https://domo-support.domo.com/s/topic/0TO5w000000ZaoQGAS).

### Connector Credentials

If required, specify the credentials for connecting to the data provider. If available, you can select an account or create an account to use in connecting. For more information about accounts, see [Manage Connector Accounts](https://domo-support.domo.com/s/article/360042926054).

Some Connectors, such as Google Drive, use OAuth to connect. This means that you only need to enter your credentials once for a given account. In the future, when you go to create a DataSet using this Connector account, your credentials are passed in automatically. Other Connectors do not use OAuth, so you must enter your credentials each time you create a DataSet using this Connector account.

### Connector Details

Most Connectors include a Details settings category. Here you usually specify options like the report to run, the timeframe for the data, a data query for pulling specific information from a database, and so on. If a query is required, the type of query you need to use depends on the Connector type and the source data in your system.

Click _Load Preview_ to verify that your data is accessible. If connection errors occur, verify the specified connection information.

## Connector Scheduling

In the **Scheduling** settings category, you can specify the update schedule, retry settings, and update method you want for this DataSet.
You can use either basic or advanced scheduling for connectors.

### Basic scheduling

In the **Basic Scheduling** tab, you can create a basic update schedule in which you specify a predefined update interval for this DataSet (such as "every Monday at 10:00 AM").

By default, schedules are set from the current time. Update intervals include every hour, day, weekday, week, month, and manually. Schedule times are based on UTC and will also show what time that is for you based on your Company Time Zone setting.
For hour, day, and week options, you can specify the interval (every # hours/days/weekdays) and the start period.

_Note: If you set a Connector schedule using the hourly method, the end time is not inclusive. For example, if the schedule is set to hourly with the active hours set to run 8 AM UTC to 7 AM UTC it will skip the 7 AM UTC run because the end hour is not treated as inclusive.
If you select Manually for your update interval, you can instruct Domo to send you a notification when the data has not been updated for a given period of time. Time periods range from one hour to three months._

  ![assets/connector.png](assets/connector.png)

_Note: If you need your DataSet to update faster than every 15 minutes, please reach out to your account team for evaluation._

#### Update Method

When creating or editing a DataSet, you can specify whether to append or replace data when updates occur. The update options are found at the bottom of the Basic Scheduling and Advanced Scheduling tabs.
| Option | Description |
|----|----|
| Replace | Replace the current version of the data with a new version of the data. Previous versions are preserved. |
| Append | Add data to the current version of the data, increasing the size of the DataSet. |
Upsert | Update DataSets with restated data to ensure you have the most up-to-date information. Available for selected connectors only. For a list of available connectors, see [DataSet Update Methods](https://domo-support.domo.com/s/article/360043430733). |
Partition | Select a rolling window of data to keep, making it easier to focus on relevant data. Available for selected connectors only. For a list of available connectors, see [DataSet Update Methods](https://domo-support.domo.com/s/article/360043430733).

### Advanced Scheduling

In the **Advanced Scheduling** tab, you have more control over when data is updated than you do when using basic scheduling. You can create schedules by month, day of the month, or day of the week. You can even specify which days of the week out of the month you want to update (for example, every second and fourth Sunday).

You can indicate whether updates are done on a set interval (such as "every 15 minutes," "every 8 hours," etc.) or at a specified time. You can also set the start time (based on the current minute). If you want, you can set the update schedule to start immediately.

_Note: If you need your DataSet to update faster than every 15 minutes, please reach out to your account team for evaluation.
Schedule times are based on UTC but can be seen in your timezone._

  ![assets/advanced_connector.png](assets/advanced_connector.png)
  ![assets/advanced_connector2.png](assets/advanced_connector2.png)

## Connector Error handling

Retry settings determine whether Domo should attempt to retry if updates fail for this DataSet and, if so, the frequency and maximum number of retries. These settings apply only to scheduled runs, not manual runs. You access the retry options dialog by selecting *Always retry when an update fails*.

  ![assets/error_handling_connector.png](assets/error_handling_connector.png)

The options in this dialog are as follows:
| Option | Description |
|----|----|
| Always retry when an update fails | Domo retries to update the DataSet. After retrying the specified number of times, Domo sends a notification if the update attempt is unsuccessful. |
| Do not retry when update fails | Domo sends a notification if the update attempt is unsuccessful, and no retries are made.|

## Create a Magic ETL DataFlow

Follow these steps to create a *Magic ETL* DataFlow:

1. Navigate to the Domo *Data Center*.

1. In the ribbon at the top of the Data Center, select *Transform Data* > *Magic ETL* to open the Magic ETL canvas.

    ![assets/magic_etl.jpg](assets/magic_etl.jpg)

1. In the left panel, expand DataSets and drag an Input DataSet tile to the canvas.

    ![assets/canvas_magic_etl.png](assets/canvas_magic_etl.png)

1. The tile editor expands below the canvas.

    ![assets/dataset_magic_etl.jpg](assets/dataset_magic_etl.jpg)

1. In the tile editor, select Choose DataSet to choose the DataSet you want to transform.

1. Drag other tiles to the canvas, depending on what transformations you want to make, and make sure they are all connected by dragging the nodes on the sides of each tile to the node on the next tile.

1. Configure the Output DataSet tile:

   1. Connect a tile to the Output DataSet tile.
   1. Select the Output DataSet tile, then enter a name for the new output DataSet.
   1. (Optional) Schedule the DataFlow. By default, you must run the DataFlow manually. You can schedule it to run when a trigger activates. See [Advanced DataFlow Triggering](https://domo-support.domo.com/s/article/000005216) to learn more.
   1. Enter a name and description for the DataFlow.
   1. Select Save to keep your changes, adding an optional version description before saving again.
   1. When you save a DataFlow, an entry for this version is added to the Versions tab in the Details view for the DataFlow. If you add a version description, it appears in the version entry. Learn about Viewing the Version History for a DataFlow.

### Tips and Notes

- You must configure each tile in the editor before you can configure the following tile. If a tile is not configured, the connector to the next tile appears as a dashed line.  
  ![assets/tiles_magic_etl.png](assets/tiles_magic_etl.png)

- Use the search tool in the left panel to find the tile you need.  
  ![assets/search_magic_etl.png](assets/search_magic_etl.png)

- The Mini Map displays in the corner of the screen and helps you see the layout and navigate around complex and detailed DataFlows. Click and drag the white square in the mini map to move to a certain view of the DataFlow on the canvas.  
  ![assets/minimap_magic_etl.jpg](assets/minimap_magic_etl.jpg)

- If you close the mini map, reopen it by selecting the map pointer icon.  
  ![assets/show_minimap_magic_etl.png](assets/show_minimap_magic_etl.png)

- You can get help on a specific tile in the canvas by clicking the tile, then clicking ![assets/help_icon.png](assets/help_icon.png).

- You can select a number of tiles at once by clicking on the canvas then dragging the mouse pointer over them. When multiple tiles are selected, you can drag all of the selected tiles as a group to where you want them. You can also delete the selected tiles by selecting Delete in the left panel.

Why are output DataSets not marked as Updated when the DataFlow completes successfully?

This is usually because the data has not actually changed—no update has occurred. The DataSets show as updated if the data has changed during a successful DataFlow execution.

### Best Practices for Magic ETL DataFlows

We recommend the following for your DataFlow:

- Only include the DataSets that are necessary to create the output DataSet.
- Filter out rows that you don't need at the beginning of the DataFlow. Learn about Filter tiles.
- Reduce the number of columns to only those you need.
- Use descriptive names for each tile in your DataFlow.
- List the following in your DataFlow description:
  - The input DataSets being transformed and their owner's names.
  - The output DataSet created.
- Give your DataFlow the same name as the output DataSet.
  - This is because the outputs of a DataFlow become their own DataSet in the Data Center, and this allows you to more easily identify which DataFlows contribute to which output DataSets.
- Be aware that some tiles take longer to execute than others, including:
  - Group By
  - Rank & Window
  - Join Data
  - Remove Duplicates
  - Pivot
  - Scripting tiles
  - Data Science tiles

## Connect to Your Data

1. Select the _DataFlows_ icon on the left  
  ![assets/dataflows_menu.png](assets/dataflows_menu.png)

1. Locate the Mixed Media Model Dataflow  
  ![assets/dataflows_row.png](assets/dataflows_row.png)

1. Select the input dataset and click _Change Dataset_ to replace the sample data with the data you have created through this quickstart.  
  ![assets/change_dataset_magic_etl.png](assets/change_dataset_magic_etl.png)

### Data Structure Requirements

#### Required Fields

| Field Type | Description | Example |
|------------|-------------|---------|
| **Revenue** | Numeric sales/revenue metric | `total_revenue`, `sales_amount` |
| **Date** | Time dimension (weekly recommended) | `week_start_date`, `report_date` |
| **Channel Spend** | Marketing spend per channel (2-10 channels) | `facebook_spend`, `google_ads_spend` |

#### Optional Fields

| Field Type | Description | Example |
|------------|-------------|---------|
| **Control Variables** | External factors affecting revenue | `seasonality_index`, `competitor_activity` |
| **Custom Variables** | Binary or numeric indicators | `promotion_flag`, `holiday_indicator` |

### Example Data Schema

```sql
-- Example: Marketing Performance Dataset
SELECT
    week_start_date,           -- Date field
    total_revenue,             -- Revenue field
    facebook_ads_spend,        -- Channel 1
    google_search_spend,       -- Channel 2
    google_display_spend,      -- Channel 3
    tiktok_spend,              -- Channel 4
    email_marketing_spend,     -- Channel 5
    tv_advertising_spend,      -- Channel 6
    seasonality_index,         -- Control variable
    is_holiday_week            -- Custom variable
FROM marketing_performance
WHERE week_start_date BETWEEN '2022-01-01' AND '2024-12-31'
ORDER BY week_start_date;
```

### Data Requirements

| Requirement | Specification |
|-------------|---------------|
| Minimum Channels | 2 marketing channels |
| Maximum Channels | 10 marketing channels |
| Minimum Date Range | 8 weeks |
| Maximum Date Range | 208 weeks (~4 years) |
| Recommended Range | 1-3 years for robust modeling |
| Currency | All channels should use same currency |
| Granularity | Consistent time granularity (weekly recommended) |

> aside positive
> **Tip**: Weekly data aggregation typically provides the best balance between granularity and statistical power for MMM analysis. Include multiple seasonal cycles if possible.

<!-- ------------------------ -->

## Configure the Model
Duration: 15

Once Domo MMM is provisioned, follow these steps to configure your first model.

### Step 1: Launch the Application

1. Navigate to **Asset Library** in your Domo instance
2. Search for "Domo MMM" or "Stella MMM"
3. Click to launch the application
4. You'll see the **Welcome** screen

![Welcome Screen](assets/welcome_screen.png)

### Step 2: Field Mapping

Click **"Get Started"** to begin the configuration wizard.

#### Select Revenue Dataset

1. Click **"Select Dataset"** dropdown
2. Search for your marketing performance dataset
3. Select the dataset containing revenue and channel data

#### Map Revenue and Date Fields

1. In **"Revenue Amount"** dropdown, select your revenue metric
2. In **"Date Field"** dropdown, select your time dimension
3. Select the date range using the date pickers
4. Ensure you have at least 8 weeks of data

#### Add Marketing Channels

For each marketing channel:

1. Click **"+ Add Channel"**
2. Enter channel name (e.g., "Facebook Ads")
3. Select the dataset (same or different dataset)
4. Map the spend field (e.g., `facebook_ads_spend`)
5. Repeat for all channels (minimum 2, maximum 10)

![Channel Mapping](assets/channel_mapping.png)

#### Add Control Variables (Optional)

Control variables help account for external factors:

1. Click **"+ Add Control Variable"**
2. Select the control variable field
3. Examples: `seasonality_index`, `competitor_price_index`

### Step 3: Set iROAS Priors (Optional)

iROAS priors incorporate your domain knowledge into the model:

> aside positive
> **What are Priors?** In Bayesian statistics, priors represent your existing knowledge before seeing the data. Setting iROAS priors helps the model converge faster and can improve accuracy when you have reliable historical benchmarks.

1. Click **"Set iROAS Priors"** (optional section)
2. For each channel, enter expected iROAS value
3. Leave blank to let the model determine values from data

| Channel | Example Prior | Rationale |
|---------|--------------|-----------|
| Facebook Ads | 2.5 | Historical platform benchmarks |
| Google Search | 3.5 | High-intent traffic typically performs well |
| Display Ads | 1.2 | Awareness channels often have lower direct iROAS |
| Email Marketing | 5.0 | Low cost channel with high returns |

### Step 4: Save Configuration

1. Review all mappings in the summary panel
2. Click **"Save Mapping"**
3. System validates configuration:
   - Minimum 2 channels
   - 8-208 weeks of data
   - No duplicate column mappings
   - Required fields present

<!-- ------------------------ -->

## Run the Analysis
Duration: 10

### Launching Model Execution

After saving your configuration:

1. Click **"Run Stella MMM Analysis"**
2. The workflow execution modal appears
3. Monitor progress through 6 phases:

### Execution Phases

| Phase | Progress | Description |
|-------|----------|-------------|
| Data Validation | 10% | Verifying data quality and completeness |
| Feature Engineering | 30% | Creating adstock transformations and normalizations |
| Bayesian Model Setup | 50% | Initializing PyMC model with priors |
| MCMC Sampling | 70% | Running Markov Chain Monte Carlo sampling |
| Posterior Analysis | 85% | Computing statistics on posterior distributions |
| Generating Insights | 95% | Calculating metrics and preparing visualizations |

![Execution Progress](assets/execution_progress.png)

### What Happens Behind the Scenes

The Domo Code Engine executes a PyMC-based Bayesian model that:

1. **Applies Adstock Transformation** - Models carryover effects of marketing spend
2. **Applies Saturation Curves** - Uses Hill function to model diminishing returns
3. **Runs MCMC Sampling** - Generates thousands of samples from posterior distribution
4. **Calculates Key Metrics** - iROAS with confidence intervals, channel contribution, revenue decomposition

> aside negative
> **Note**: Model execution typically takes 5-15 minutes depending on data volume and number of channels. Do not close the browser during execution.

<!-- ------------------------ -->

## Interpret Results
Duration: 15

Once the model completes, you'll be taken to the **Insights Dashboard** with four main tabs.

### Tab 1: Channel Performance

#### iROAS Chart

![iROAS Results](assets/iroas_results.png)

**How to Read:**
- Each bar represents a channel's Incremental Return on Ad Spend
- Error bars show 95% confidence intervals
- Higher iROAS = more efficient channel

**Example Interpretation:**
> "Facebook Ads has an iROAS of 2.8x, meaning every $1 spent generates $2.80 in incremental revenue. The confidence interval of [2.3x - 3.2x] indicates statistical significance."

#### Revenue Waterfall

![Waterfall Results](assets/waterfall_results.png)

**How to Read:**
- **Baseline**: Revenue that would occur without marketing
- **Channel Bars**: Incremental revenue attributed to each channel
- **Total**: Sum of baseline + all channel contributions

#### Channel Contribution Over Time

![Contribution Trend](assets/contribution_trend.png)

**How to Read:**
- Stacked area chart showing weekly contribution by channel
- Helps identify seasonal patterns and trends
- Compare channel performance across time periods

### Tab 2: Budget Optimizer

![Budget Optimizer Results](assets/budget_optimizer_results.png)

**Features:**
- **Current Allocation**: Your existing budget distribution
- **Recommended Allocation**: AI-optimized budget distribution
- **Projected Lift**: Expected revenue increase from optimization
- **Constraints**: Set min/max budgets per channel

**How to Use:**
1. Review current vs. recommended allocations
2. Adjust constraints if needed (e.g., minimum brand spend)
3. Click "Apply Scenario" to see projected impact
4. Export recommendations for planning

### Tab 3: Model Diagnostics

#### Key Metrics

| Metric | Description | Good Range |
|--------|-------------|------------|
| **R²** | Variance explained by model | > 0.80 |
| **MAPE** | Mean Absolute Percentage Error | < 15% |
| **VIF** | Variance Inflation Factor | < 5.0 |

#### R² Interpretation

| R² Value | Quality | Interpretation |
|----------|---------|----------------|
| > 0.95 | Excellent | Model explains almost all variance |
| 0.85 - 0.95 | Good | Strong predictive power |
| 0.70 - 0.85 | Moderate | Acceptable for most use cases |
| < 0.70 | Needs Review | Consider adding variables |

#### VIF Analysis (Multicollinearity)

![VIF Chart](assets/vif_chart.png)

**How to Read:**
- VIF < 5: No multicollinearity concern
- VIF 5-10: Moderate correlation, monitor closely
- VIF > 10: High multicollinearity, consider combining channels

#### Correlation Matrix

![Correlation Matrix](assets/correlation_matrix.png)

**How to Read:**
- Blue = positive correlation
- Red = negative correlation
- High correlation between channels may indicate multicollinearity

### Tab 4: Settings

- **Export Results**: Download charts as PNG images
- **Model Metadata**: View execution details and parameters
- **Configuration**: Review mapped fields and settings

<!-- ------------------------ -->

## Using Cortex AI Analysis
Duration: 10

> aside positive
> **Snowflake Cortex Integration**: This optional feature provides AI-powered natural language insights on your MMM results.

### Enabling Cortex Analysis

If Snowflake Cortex integration was configured during provisioning:

1. Navigate to any chart in the Insights Dashboard
2. Look for the **"Cortex Analysis"** button
3. Click to initiate AI analysis

![Cortex Button](assets/cortex_button.png)

### How Cortex Analysis Works

1. **Thread Creation**: A conversation thread is created in Snowflake
2. **Data Context**: MMM metrics and chart data are sent to the Cortex Agent
3. **AI Analysis**: The agent analyzes patterns and generates insights
4. **Natural Language Response**: Results are displayed in plain language

### Example Cortex Insights

**For iROAS Analysis:**
> "Your Email Marketing channel shows the highest iROAS at 5.2x, significantly outperforming other channels. However, its budget allocation is only 8% of total spend. Consider reallocating 10-15% from lower-performing Display channels to Email Marketing to maximize overall ROI."

**For Budget Optimization:**
> "Based on the current model, reallocating $50,000 from Google Display to Facebook Ads could increase total incremental revenue by approximately 12%. The recommended allocation maintains minimum brand presence while optimizing for performance."

### Continuing the Conversation

Cortex AI supports multi-turn conversations:

1. Ask follow-up questions in the chat interface
2. Request specific analysis (e.g., "What about seasonality effects?")
3. Get recommendations tailored to your business context

<!-- ------------------------ -->

## Best Practices
Duration: 5

### Data Quality

| Practice | Why It Matters |
|----------|----------------|
| Use weekly aggregation | Optimal balance of granularity and statistical power |
| Include 1-3 years of data | Captures seasonality and long-term patterns |
| Validate spend data with finance | Ensures accuracy of channel attribution |
| Remove test/invalid data | Prevents model contamination |

### Model Configuration

| Practice | Why It Matters |
|----------|----------------|
| Set reasonable iROAS priors | Helps model convergence and accuracy |
| Include control variables | Accounts for external factors |
| Start with major channels | Focus on channels with significant spend |
| Group similar channels | Reduces multicollinearity issues |

### Interpretation

| Practice | Why It Matters |
|----------|----------------|
| Check R² and MAPE first | Validates model reliability |
| Review VIF for multicollinearity | Ensures independent channel effects |
| Consider confidence intervals | Accounts for uncertainty in estimates |
| Compare to business intuition | Validates results make sense |

### Optimization

| Practice | Why It Matters |
|----------|----------------|
| Set realistic constraints | Maintains brand presence and relationships |
| Test scenarios incrementally | Validates optimization recommendations |
| Re-run quarterly | Captures changing market dynamics |
| Document decisions | Creates audit trail for budget changes |

<!-- ------------------------ -->

## Troubleshooting
Duration: 5

### Common Issues and Solutions

#### Model Won't Run

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Minimum 2 channels required" | Less than 2 channels mapped | Add more marketing channels |
| "Insufficient data" | Less than 8 weeks | Extend date range or add more data |
| "Duplicate column mapping" | Same field used twice | Review and remove duplicate mappings |

#### Poor Model Quality

| Symptom | Cause | Solution |
|---------|-------|----------|
| Low R² (< 0.70) | Missing important variables | Add control variables |
| High MAPE (> 25%) | Data quality issues | Review and clean input data |
| High VIF (> 10) | Multicollinearity | Combine correlated channels |

#### Unexpected Results

| Symptom | Cause | Solution |
|---------|-------|----------|
| Negative iROAS | Data issues or wrong mapping | Verify spend/revenue mapping |
| All channels similar iROAS | Insufficient variation | Need more diverse spending patterns |
| Baseline dominates | Marketing has low impact | Normal for some businesses, or check data |

### Getting Help

If you encounter issues not covered here:

1. **Domo Support**: Contact through the Domo Help Center
2. **Documentation**: Review in-app help guides
3. **Community**: Post questions in Domo Community forums

<!-- ------------------------ -->

## Conclusion and Resources
Duration: 2

### Conclusion

With Domo MMM, you're now equipped to measure true marketing incrementality, optimize campaign performance, and maximize ROI through data-driven budget allocation. The Bayesian approach provides statistical confidence in your results, while Snowflake Cortex AI integration enables natural language insights for faster decision-making.

### What You Learned

By following this guide, you've learned how to:
- Request and deploy Domo MMM for your organization
- Prepare marketing data with proper structure and requirements
- Configure field mappings and set iROAS priors
- Run Bayesian Marketing Mix Model analysis
- Interpret iROAS, contribution, and diagnostic metrics
- Use AI-powered budget optimization recommendations
- Leverage Snowflake Cortex for natural language insights

### Related Resources

For further learning, explore the following resources:
- [Domo Knowledge Base](https://domo-support.domo.com/s/knowledge-base?language=en_US)
- [Snowflake Marketplace](https://www.snowflake.com/en/data-cloud/marketplace/)
- [Marketing Mix Modeling Overview](https://en.wikipedia.org/wiki/Marketing_mix_modeling)
- [PyMC Documentation](https://www.pymc.io/welcome.html)
- [Snowflake Cortex AI](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)
- [Domo Community](https://www.domo.com/domo-central/community)
- [Domo Community Forum](https://community-forums.domo.com/main)
- [Domo Support](https://www.domo.com/login/customer-community)
- Architecture
  ![Architecture](assets/architecture.png)
