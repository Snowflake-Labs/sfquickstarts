author: Tripp Smith, Dureti Shemsi
language: en
id: multi-echelon-inventory-optimization-with-nvidia-cuopt
summary: AI-driven multi-echelon inventory optimization using GPU-accelerated analytics, Cortex Agent, and Streamlit on Snowflake to reduce working capital while improving service levels.
categories: snowflake-site:taxonomy/solution-center/certification/certified-solution, snowflake-site:taxonomy/industry/manufacturing, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/model-development, snowflake-site:taxonomy/snowflake-feature/applied-analytics, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/snowpark-container-services, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search, snowflake-site:taxonomy/snowflake-feature/snowflake-intelligence, snowflake-site:taxonomy/snowflake-feature/marketplace-and-integrations
environments: web
status: Published
feedback_link: https://github.com/Snowflake-Labs/sfguides/issues
fork_repo_link: https://github.com/Snowflake-Labs/sfguide-multi-echelon-inventory-optimization-with-nvidia-cuopt


# Multi-Echelon Inventory Optimization with NVIDIA cuOpt on Snowflake

## Overview

In aerospace and defense alone, inventories grew by over $70 billion since 2016 while inventory turns fell 35% ([McKinsey, 2025](https://www.mckinsey.com/industries/aerospace-and-defense/our-insights/fly-high-stock-higher-managing-a-and-d-inventory-to-save-60-billion-dollars)). The pattern repeats across manufacturing sectors. The problem is not how much companies stock, but where they stock it. Legacy planning tools optimize each tier in isolation: the factory optimizes production, the regional DC optimizes stocking, and the dealer optimizes reorders. Each makes locally optimal decisions that collectively produce globally suboptimal outcomes, amplifying demand signals through the bullwhip effect.

This solution replaces isolated planning with simultaneous network-wide optimization. It integrates ERP transaction data, supply chain master data, and external demand signals in a unified Snowflake platform. The solution demonstrates GPU-accelerated demand forecasting with XGBoost and cuDF, solves the multi-echelon inventory problem with a linear programming formulation, and surfaces results through a Streamlit dashboard with a Cortex Agent copilot. The entire pipeline runs natively on Snowflake with no data movement or external infrastructure.

## The Business Challenge

Traditional inventory management is impacted by the bullwhip effect, where sudden demand swings lead to poor supply decisions that result in excess inventory, stockouts, or both.

- **Misplaced capital.** Working capital is trapped in excess inventory at some locations while finished goods are stocked out at others. For a $5B manufacturer, this can mean $1.0B tied up in inventory while achieving only a 95% customer service level.

- **Reactive firefighting.** Planners spend days responding to disruptions using manual reorder point calculations in spreadsheets. By the time the analysis is complete, the situation has changed.

- **Limited network visibility.** While ERP systems track raw materials and finished goods inventory at owned facilities, dealer and supplier inventory positions are typically not visible. Each tier optimizes independently, creating amplified demand signals and suboptimal global allocation.

- **Blind to external signals.** Weather events, disaster declarations, and macroeconomic shifts affect demand and lead times, but legacy tools cannot incorporate these signals into planning decisions.

## The Solution

This solution treats the entire distribution network as a single system, optimizing inventory positioning across all locations simultaneously. The demo uses synthetic data generated to mirror production schemas. In production, ERP feeds and Snowflake Marketplace data shares replace the synthetic sources with no changes to downstream logic.

The platform implements a layered data architecture across four schemas: RAW_ERP for ingested transaction data, ATOMIC_SCM for cleansed supply chain master data, MMEIO_INV for optimization results and AI components, and PUBLIC_DATA for external macroeconomic and weather signals.

1. **Data Foundation.** ERP transactions, network topology, and material master data flow into Snowflake alongside external demand signals from Marketplace sources including Industrial Production Index, weather, and disaster declarations. Storage follows a RAW to ATOMIC to DATA_MART layered architecture.

2. **Demand Forecasting.** XGBoost models trained on GPU with CuPy arrays demonstrate GPU-accelerated demand forecasting across the network. The `cudf.pandas` accelerator handles DataFrame operations transparently on GPU. The notebook evaluates forecast accuracy and correlates external macro signals with demand patterns, establishing a foundation for production-grade forecast integration.

3. **Network Optimization.** A PuLP-based linear programming formulation on Snowflake Container Runtime optimizes inventory positioning across the network simultaneously. The optimizer uses historical demand statistics to determine flow, safety stock, and reorder quantities across all nodes and SKUs in a single solve. The `cudf.pandas` accelerator handles tabular preprocessing on GPU, and the solver uses NVIDIA cuOpt when available or falls back to CBC.

4. **Intelligent Interface.** A Streamlit application provides a Network Command Center, What-If Simulator, Action Planner, and Model Studio. A Cortex Agent (Inventory Copilot) enables natural language queries that span inventory, weather, disaster, economic data, and SLA contract terms.

5. **Action Execution.** The platform generates transfer orders, reorder recommendations, and safety stock adjustments with a full audit trail in Snowflake. In production, these integrate with ERP and WMS systems via API.

## Business Value

Multi-echelon optimization delivers measurable incremental value over traditional planning methods. The following estimates represent projected first-year impact for a representative $5B manufacturer. Inventory reductions reflect prevented excess through optimized positioning. Existing excess inventory is reduced through sell-through or planned write-down.

| Value Driver | Annual Impact | Basis |
|---|---|---|
| Working Capital Release | $150M | 15% inventory reduction on $1.0B baseline at 95% CSL |
| Service Revenue Protected | $45M | 3-point service level improvement (95% to 98%) on premium contracts |
| Expedite Cost Reduction | $24M | 50% fewer emergency shipments through proactive positioning |
| Planner Productivity | $4.5M | 40% reduction in manual planning effort |
| Total Annual Value | $223.5M | Approximately 4.5% of revenue |

## The Discovery Moment

A Supply Chain Planner adjusts risk tolerance and service level sliders to simulate a disruption scenario. The What-If Simulator projects the impact on KPIs and network risk across the distribution map. For deeper analysis, the Inventory Copilot answers complex questions that span inventory, weather, and disaster data. In Model Studio, planners can rerun the optimization with new parameters via the `RUN_OPTIMIZATION` procedure.

**Before:** "We need days to model this disruption. By then the situation will have changed."

**After:** "I adjusted the risk tolerance, saw the projected network impact, asked the Copilot which regions are most exposed, and triggered a reoptimization with updated parameters."

## Why Snowflake

**Unified Data Foundation.** ERP data, WMS data, and external Marketplace signals join seamlessly in a governed platform with no ETL pipelines, no data copies, and full lineage.

**GPU Acceleration.** NVIDIA cuDF runs natively in Snowflake notebooks. The `cudf.pandas` accelerator speeds up pandas operations on GPU with zero code changes, while XGBoost trains directly on CUDA with CuPy arrays.

**AI-Powered Decision Support.** Cortex Agent orchestrates queries across inventory, weather, disaster, and economic data from a single natural language question. Cortex Search retrieves relevant SLA contract clauses. Cortex Analyst converts questions to SQL via a semantic model.

**Secure Collaboration.** Share optimization results with dealers and suppliers without copying data. Consume external demand signals from Marketplace providers with zero integration effort.

## The Data

The solution integrates internal supply chain data with external signals to produce network-aware inventory recommendations. The following data represents the demo environment and is representative of production supply chain systems.

| Data Source | Type | Purpose |
|---|---|---|
| ERP Transactions | Internal | Historical demand patterns across the network |
| Network Topology | Internal | Distribution network structure covering factories, DCs, depots, and dealers |
| Material Master | Internal | SKU catalog with criticality, cost, and lead time attributes |
| Demand Forecast | Computed | GPU-accelerated demand predictions with confidence intervals |
| Optimized Plan | Computed | Recommended inventory positioning across all scenarios |
| SLA Contracts | Internal | Service level agreements for Cortex Search retrieval |

- **Network Scale.** Multi-tier distribution network spanning factories, regional DCs, depots, and dealers with a representative SKU catalog and historical transaction data.
- **Freshness.** In the demo, all data is synthetic CSV loaded at setup. In production, ERP feeds refresh via batch or Snowpipe streaming and Marketplace shares update automatically.
- **Trust.** All data stays within Snowflake's governance boundary with role-based access controls and a full audit trail.

## External Data Enrichment

The solution incorporates public data sources to enhance planning decisions with real-world signals. The demo uses simulated data that mirrors Marketplace schemas. In production, customers point views at actual Marketplace shares with no changes to downstream logic.

| Data Source | Use Case | Value |
|---|---|---|
| Industrial Production Index | Macro demand correlation | Anticipate demand shifts based on manufacturing sector trends |
| NOAA Weather Data | Weather-adjusted lead times | Lead time adjustments for regions with severe weather patterns |
| FEMA Disaster Declarations | Disruption alerts | Safety stock triggers for active disaster zones |

### Snowflake Marketplace Providers

| Category | Provider | Cost | What You Get |
|---|---|---|---|
| Economic Indicators | Cybersyn Financial & Economic Essentials | Free | FRED economic data including IPI, employment, GDP |
| Economic Indicators | Knoema Economy Data Atlas | Paid | Global macro indicators, industry-specific indices |
| Weather | Weather Source | Paid | Historical and forecast weather by location |
| Weather | NOAA via Cybersyn | Free | US weather station data, precipitation, temperature |
| Disaster and Risk | FEMA via Cybersyn | Free | Disaster declarations, affected regions |
| Supply Chain Risk | Resilinc | Paid | Supplier risk scores, disruption alerts |
| Logistics | Project44 / FreightWaves SONAR | Paid | Port congestion, carrier capacity, freight rates |

**Why Marketplace Data Matters**

- **Zero ETL.** Data lives in Snowflake. Join to your tables with SQL and no data movement required.
- **Always current.** Providers update their datasets and you automatically get fresh intelligence.
- **Governed access.** Marketplace shares respect your Snowflake RBAC. Sensitive enrichments stay protected.
- **Rapid time to value.** Skip months of data licensing negotiations and pipeline engineering.

## Personas and Value

| Persona | Key Need | How This Solution Helps |
|---|---|---|
| VP of Supply Chain | Network-wide working capital visibility | See capital allocation across all tiers and scenarios. Quantify the impact of optimization decisions. |
| Inventory Planner | Faster disruption response | Simulate disruption scenarios and see projected impact. Get AI-recommended transfer and reorder actions. |
| Operations Researcher | Complex what-if modeling | Run disruption scenarios interactively. Adjust risk tolerance and see projected network-wide impact. |
| Service Manager | Eliminate finished goods stockouts | Safety stock recommendations by location tied to service level targets and SLA tiers. |
| CFO | Release trapped working capital | Quantified capital reduction with service level trade-offs. Scenario-based investment planning. |

## How It Comes Together

| Component | Role |
|---|---|
| Snowflake Tables | Store ERP data, network topology, forecasts, and optimization results across four schemas |
| GPU Compute Pool | NVIDIA GPU for cuDF and XGBoost acceleration in notebooks |
| Snowflake Notebooks | GPU notebook for demand forecasting, network optimization, and scenario analysis |
| cuDF and CuPy | GPU-accelerated DataFrames via `cudf.pandas` and GPU array operations for XGBoost training |
| PuLP | LP formulation for multi-echelon inventory optimization with CBC solver and cuOpt GPU solver when available |
| Cortex Agent | Inventory Copilot with analytical and contract search tools spanning multiple data domains |
| Cortex Search | SLA contract retrieval using Arctic embeddings |
| Cortex Analyst | Semantic views for text-to-SQL conversion across multiple data domains |
| Snowflake Intelligence | Conversational interface for the Cortex Agent |
| Streamlit in Snowflake | Interactive dashboard for command center, simulation, action planning, and model studio |

## Key Visualizations

The Streamlit application guides users from executive overview to actionable recommendations.

| View | What You See |
|---|---|
| Network Command Center | KPI cards, quarterly working capital projections, DC budget allocation, interactive US map with inventory and risk overlays, regional comparison |
| What-If Simulator | Risk tolerance and service level sliders, disruption scenario selection, projected KPIs and network risk map, Inventory Copilot chat powered by Cortex Agent |
| Action Planner | Prioritized reorder recommendations, transfer suggestions between nodes, inventory flow arc map, CSV and text export |
| Model Studio | Solver configuration, reoptimization via `RUN_OPTIMIZATION` procedure, forecast model performance metrics, Pareto frontier visualization |

### AI-Powered Decision Support

The Inventory Copilot enables complex analytical questions that span multiple data domains.

| Question Type | Example Query |
|---|---|
| Risk Assessment | "What is our stockout risk for regions with active hurricane declarations?" |
| Scenario Planning | "How should we adjust safety stock for states expecting severe winter weather?" |
| Demand Correlation | "Is the declining industrial production index affecting our order patterns?" |
| Service Level Analysis | "Which dealer tiers have the lowest predicted service levels?" |
| Multi-Factor Analysis | "Create a risk dashboard showing regions with high stockout risk, recent weather events, and disaster declarations" |

## Get Started

Ready to optimize inventory positioning across your distribution network? This guide includes everything needed to deploy the full solution.

**[GitHub Repository](https://github.com/Snowflake-Labs/sfguide-multi-echelon-inventory-optimization-with-nvidia-cuopt)**

## Resources

- [Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Snowflake Intelligence](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence)
- [NVIDIA GPU Acceleration in Snowflake](https://www.snowflake.com/en/blog/nvidia-gpu-acceleration/)
- [Notebooks in Workspaces](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-in-workspaces/notebooks-in-workspaces-overview)
- [Notebooks on Container Runtime](https://docs.snowflake.com/en/developer-guide/snowflake-ml/notebooks-on-spcs)
- [Snowflake ML Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)
- [Streamlit in Snowflake Documentation](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
