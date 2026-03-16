author: Tripp Smith, Dureti Shemsi
language: en
id: supply-chain-risk-intelligence-with-snowflake
summary: AI-driven N-tier supply chain risk intelligence using graph neural networks on Snowflake to uncover hidden supplier dependencies and concentration risks.
categories: snowflake-site:taxonomy/solution-center/certification/certified-solution, snowflake-site:taxonomy/industry/manufacturing, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/model-development, snowflake-site:taxonomy/snowflake-feature/snowpark
environments: web
status: Published
feedback_link: https://github.com/Snowflake-Labs/sfguides/issues
fork_repo_link: https://github.com/Snowflake-Labs/sfguide-supply-chain-risk-intelligence-with-snowflake


# Supply Chain Risk Intelligence for Manufacturing: Achieve N-Tier Visibility with Snowflake

Procurement and supply chain teams believe they have diversified sourcing because their Enterprise Resource Planning (ERP) system shows multiple Tier-1 suppliers across different countries. But that data is incomplete — visibility ends at the first tier. When a disruption occurs at Tier-3, organizations are blindsided weeks later by sudden shortages, leaving no time to qualify alternatives.

## The Business Challenge

![Tier-N Visibility Gap](assets/tier_visibility_gap.png)

Traditional ERP visibility ends at Tier-1. Risks fester unseen in deeper layers of the supply network, creating costly blind spots for procurement teams.

- **Tier-N blindness costs time and money.** When a disruption occurs at Tier-3, organizations are blindsided weeks later by sudden shortages, leaving no time to qualify alternatives.

- **Single points of failure hide in plain sight.** Three Tier-1 vendors across three countries may unknowingly source raw materials from the same refinery in a geologically unstable region.

- **Reactive firefighting replaces strategic planning.** Without predictive risk signals, procurement teams spend time managing crises instead of building resilient supply networks.

- **Compliance and audit gaps create exposure.** Regulations like the Uyghur Forced Labor Prevention Act (UFLPA) require traceability beyond Tier-1, but current systems cannot provide that visibility.

## The Solution

This solution transforms supply chain management from reactive response to proactive resilience by fusing internal ERP data with external trade intelligence into a knowledge graph that reveals what your ERP cannot see.

![Data Architecture](assets/data_architecture.png)

The platform constructs a heterogeneous knowledge graph with suppliers, parts, and regions as nodes and transactions and trade flows as edges. A GraphSAGE model trained on trade patterns predicts likely Tier-2+ supplier relationships, then propagates risk scores through the network so that a shock at Tier-3 surfaces its impact on Tier-1 and final products.

![Solution Flow](assets/solution_flow.png)

1. **Ingest.** Load ERP exports (vendors, materials, purchase orders, Bills of Materials) and external trade data into Snowflake tables.

2. **Build the Graph.** Construct a heterogeneous knowledge graph with suppliers, parts, and regions as nodes; transactions and trade flows as edges.

3. **Infer Hidden Links.** Train a GraphSAGE model on trade patterns to predict likely Tier-2+ supplier relationships with probability scores.

4. **Propagate Risk.** Calculate risk scores that flow through the network — a shock at Tier-3 propagates to impact Tier-1 and final products.

5. **Visualize and Act.** Explore the supply network graph, analyze concentration points, and prioritize mitigation actions in an interactive dashboard.

## Business Value

- **Predictive risk scoring.** Alerts for latent risks before they manifest — for example, identifying that a part has a high risk score because its estimated Tier-2 source is in a sanction zone.

- **Automatic concentration discovery.** Identify hidden bottlenecks where multiple Tier-1 suppliers converge on the same Tier-2+ source.

- **Proactive supplier qualification.** Find and qualify backup suppliers months before a crisis, not during one.

- **Faster time to insight.** Reduce supply chain due diligence from weeks of manual research to minutes of AI-powered analysis.

![Concentration Risk](assets/concentration_alert.png)

Traditional analytics show a diversified supply base. Graph intelligence reveals the convergence: multiple seemingly independent Tier-1 suppliers may all depend on the same hidden Tier-2 refinery.

## Why Snowflake

**Unified Data Foundation**: Internal ERP data and external trade intelligence join seamlessly in a governed platform — no data movement, no pipeline complexity.

**Performance That Scales**: GPU-enabled notebooks train graph neural networks on millions of trade records without infrastructure friction.

**Collaboration Without Compromise**: Share risk insights with sourcing partners and internal teams while maintaining data governance and access controls.

**Built-in AI/ML and Apps**: From PyTorch Geometric models to interactive Streamlit dashboards, build and deploy intelligence closer to where decisions happen.

## The Data

The solution fuses internal ERP data with external trade intelligence into a knowledge graph that reveals what your ERP cannot see. The following data represents the demo environment and is representative of production supply chain data.

![Data ERD](assets/gnn_supply_chain_risk_data_erd.png)

| Data Source | Type | Purpose |
|---|---|---|
| Vendor Master (ERP) | Internal | Known Tier-1 supplier nodes |
| Purchase Orders (ERP) | Internal | Supplier-to-material transaction edges |
| Bill of Materials (ERP) | Internal | Product assembly hierarchy |
| Trade Data (External) | Enrichment | Hidden Tier-2+ relationship inference |
| Regional Risk (External) | Enrichment | Geopolitical and disaster risk factors |

- **Domains:** Vendors (Tier-1 suppliers), Materials (parts and BOMs), Regions (geographic risk factors), Trade Data (bills of lading linking shippers to consignees).
- **Freshness:** Batch ingestion for ERP data; continuous refresh for trade intelligence via Snowflake Marketplace.
- **Trust:** All data stays within Snowflake's governance boundary with role-based access controls.

## Snowflake Marketplace Integration

Moving from demo to production requires high-quality external data. These Snowflake Marketplace providers deliver the trade intelligence and entity data needed to operationalize N-tier visibility — no data pipelines to build, no contracts to negotiate outside your Snowflake account.

![Marketplace Integration](assets/marketplace_integration.png)

**S&P Global Market Intelligence — Panjiva Supply Chain Intelligence**: The gold standard for inferring hidden Tier-2+ relationships. Customs-based bill-of-lading shipment records with shipper/consignee entities, HS codes, origin/destination ports, volumes, and values. When your Tier-1 supplier appears as a consignee, Panjiva reveals who shipped to them — your likely Tier-2 suppliers. [Panjiva Micro](https://www.snowflake.com/datasets/sp-global-market-intelligence-panjiva-supply-chain-intelligence/) | [Panjiva Macro (UN Comtrade)](https://www.snowflake.com/datasets/sp-global-market-intelligence-panjiva-macro-un-comtrade/)

**Oxford Economics — TradePrism**: Forward-looking trade forecasts and scenario modeling. Global trade forecasts at HS4 level across ~170 economies, including tariff scenarios, sanction impacts, and trade rerouting projections. Combine historical shipment data with TradePrism forecasts to answer: "If sanctions expand to Region X, which of my supply chains are exposed?" [TradePrism Full Dataset](https://app.snowflake.com/marketplace/listing/GZ1M7ZCX4H2/oxford-economics-group-tradeprism-full-dataset)

**FactSet — Supply Chain Linkages & Entity Data**: Entity resolution and corporate relationship mapping. Map shipper/consignee names from trade data to actual vendor entities in your ERP and build supplier/geo exposure roll-ups at the corporate parent level. [FactSet on Snowflake Marketplace](https://app.snowflake.com/marketplace/providers/GZT0Z28ANYN/FactSet)

**Resilinc — EventWatch AI**: Real-time disruption monitoring and supplier risk signals. AI-powered monitoring of global events (natural disasters, geopolitical incidents, factory fires, labor actions) mapped to supplier locations and impact zones. [Resilinc EventWatch AI](https://app.snowflake.com/marketplace/listing/GZSTZO0V7VR/resilinc-eventwatch-ai)

| Marketplace Provider | Graph Node/Edge Type | Integration Point |
|---|---|---|
| **Panjiva** | Trade flow edges (shipper → consignee) | GNN link prediction training |
| **TradePrism** | Region risk attributes | Node feature enrichment |
| **FactSet** | Entity resolution, corporate hierarchy | Supplier node canonicalization |
| **Resilinc** | Real-time event signals | Dynamic risk score updates |

## How It Comes Together

![Technology Stack](assets/technology_stack.png)

| Component | Role |
|---|---|
| **Snowflake Tables** | Store ERP data, trade intelligence, and model outputs |
| **Snowflake Notebooks (GPU)** | Execute Graph Neural Network (GNN) training with GPU acceleration |
| **PyTorch Geometric** | GraphSAGE model for link prediction and risk propagation |
| **Streamlit in Snowflake** | Interactive dashboard for exploration and action planning |
| **Snowflake Notebooks** | SQL setup and environment configuration |

## Key Visualizations

The Streamlit application guides users from executive summary to prioritized actions.

| View | What You See |
|---|---|
| **Home** | Key metrics: nodes analyzed, critical risks, bottlenecks discovered |
| **Supply Network** | Interactive graph to filter, zoom, and trace dependency paths |
| **Tier-2 Analysis** | Predicted links, probability scores, and concentration impacts |
| **Risk Mitigation** | Prioritized actions ranked by impact with AI-assisted context |

![Home Dashboard](assets/dashboard_home.png)

![Supply Network Graph](assets/dashboard_network.png)

![Tier-2 Analysis](assets/dashboard_tier2.png)

![Risk Mitigation](assets/dashboard_mitigation.png)

## Get Started

Ready to uncover hidden supplier dependencies and concentration risks in your supply chain? This guide includes everything you need to get up and running quickly.

**[GitHub Repository →](https://github.com/Snowflake-Labs/sfguide-supply-chain-risk-intelligence-with-snowflake)**

The repository contains SQL setup scripts, a GNN training notebook, a multi-page Streamlit dashboard, and step-by-step instructions for deploying the full solution.

## Resources

- [Notebooks on Container Runtime Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/notebooks-on-spcs)
- [Streamlit in Snowflake Documentation](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Snowflake ML Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)