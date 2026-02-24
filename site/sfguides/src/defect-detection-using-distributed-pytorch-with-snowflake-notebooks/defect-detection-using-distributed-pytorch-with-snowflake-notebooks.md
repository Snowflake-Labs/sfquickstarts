author: Tripp Smith, Dureti Shemsi
language: en
id: defect-detection-using-distributed-pytorch-with-snowflake-notebooks
summary: Train a custom YOLOv12 defect detection model on GPU compute directly inside Snowflake to eliminate PCB quality control silos, reduce false positives, and cut scrap costs.
categories: snowflake-site:taxonomy/solution-center/certification/certified-solution, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/model-development, snowflake-site:taxonomy/snowflake-feature/snowpark-container-services, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/industry/manufacturing
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-defect-detection-using-distributed-pytorch-with-snowflake-notebooks


# PCB Defect Detection for Electronics Manufacturing: Achieve Zero-Defect Quality with Snowflake

Quality engineers and data scientists struggle to deploy modern AI inspection systems because factory floor image data is locked in silos, legacy AOI systems generate excessive false positives, and security policies block open-source ML models from running inside the corporate firewall.

## The Cost of Inaction

![Problem Impact](assets/problem-impact.svg)

**Samsung Galaxy Note 7 Recall (2016)**: A defective battery component passed inspection and made it to market, triggering a $5.3 billion recall, 2.5 million devices scrapped, and a permanent brand reputation hit. The root cause? Manufacturing defects that existing AOI systems failed to catch consistently.

This pattern repeats across electronics manufacturing. According to McKinsey, poor quality costs electronics manufacturers **2-4% of revenue annually**—that's $200-400M for a $10B operation. The irony: better inspection technology exists, but data silos and rigid systems prevent its adoption.

## The Problem in Context

- **Excessive False Positives.** Legacy AOI systems flag 15-25% of boards as defective when they're actually fine, requiring expensive manual re-inspection that slows production and inflates labor costs.

- **Data Silos Block ML Teams.** Factory floor image data sits in isolated systems that data scientists cannot access. Without this data, teams cannot train adaptive models that learn from production reality.

- **Security Policies Block Innovation.** Modern computer vision models like YOLO require GPU infrastructure and pip packages that corporate security policies prohibit from running on-premises.

- **Reactive Quality Control.** By the time defects are detected, boards have already progressed through multiple production stages, compounding rework costs and scrap rates.

- **No Root Cause Intelligence.** Operators lack contextual guidance when defects appear. They must manually search through IPC standards and repair manuals to determine the correct remediation procedure.

## The Transformation

![Before After](assets/before-after.svg)

With Snowflake, manufacturers shift from reactive, siloed quality control to proactive, AI-powered inspection—training custom YOLO models on GPU compute directly inside the data platform where images are already secured and governed.

## What We'll Achieve

- **25% Reduction in False Positive Rate.** Custom YOLOv12 models trained on your actual production data learn what defects really look like on your boards, not generic samples.

- **15% Reduction in Scrap Cost.** Earlier, more accurate detection catches defects before boards progress through expensive downstream operations.

- **Real-Time Visibility.** Move from weekly Excel-based quality reports to live dashboards showing defect density, yield rates, and Pareto analysis by defect class.

- **Interactive Model Validation.** Vision Lab enables operators to compare model predictions against ground truth labels, validating detection accuracy before production deployment.

## Business Value

![ROI Value](assets/roi-value.svg)

For a mid-size electronics manufacturer producing 1 million boards annually with a 3% defect rate and $50 average board cost:
- **$750K annual savings** from 15% scrap reduction
- **$200K labor savings** from 25% fewer false positive re-inspections
- **$150K opportunity cost recovered** from real-time vs. weekly reporting cycles

## Why Snowflake

- **Unified Data Foundation.** A single, governed platform unifies factory images, defect logs, and equipment telemetry—so ML teams finally have access to the data they need without risky data movement.

- **Performance That Scales.** GPU compute pools scale training jobs from prototype to production without capacity planning friction. Train YOLOv12 on thousands of images in hours, not days.

- **Collaboration Without Compromise.** Secure data sharing lets quality teams across factories collaborate on model training and defect taxonomies while governance policies stay intact.

- **Built-in AI/ML and Apps.** Native Notebooks, Container Runtime, and Streamlit let data scientists train, deploy, and operationalize models without leaving the platform—no external MLOps infrastructure required.

## The Data

![Data ERD](assets/data-erd.svg)

### Source Tables

| Table | Type | Records | Purpose |
|-------|------|---------|---------|
| PCB_METADATA | Dimension | ~1M | Board identification, manufacturing date, factory line, product type |
| DEFECT_LOGS | Fact | ~30K | Inference results with class, confidence, bounding boxes |
| MODEL_STAGE | Stage | ~500MB | Raw images, trained model weights, YOLO configuration |

### Data Characteristics

- **Freshness:** Images ingested per-batch during production; inference results written in real-time during inspection.
- **Trust:** Images governed by role-based access; model weights versioned in stage; inference audit trail in DEFECT_LOGS.
- **Relationships:** Each defect log links to a board (board_id) and includes spatial coordinates for visualization.

## Solution Architecture

![Architecture](assets/architecture.svg)

The solution follows a left-to-right data journey:

- **Data Ingestion:** Deep PCB images uploaded to internal stage (`@MODEL_STAGE/raw/deeppcb`)
- **Training Pipeline:** Snowflake Notebook on Container Runtime with GPU compute pool trains YOLOv12
- **Model Persistence:** Trained weights saved back to stage (`@MODEL_STAGE/models/yolov12_pcb`)
- **Inference & Logging:** Predictions written to DEFECT_LOGS with structured schema
- **Visualization:** Streamlit dashboard surfaces defect analytics and interactive inspection

## How It Comes Together

1. **Admin Setup.** Platform team configures GPU compute pool, network rules for PyPI/GitHub egress, and external access integration.

2. **Data Preparation.** Deep PCB images downloaded from stage, converted to YOLO format with normalized bounding boxes and class mappings.

3. **Model Training.** YOLOv12 trained on GPU using Container Runtime. Epochs, batch size, and augmentation configured for production-quality detection.

4. **Model Persistence.** Best model weights saved to `@MODEL_STAGE/models/yolov12_pcb/yolo_best.pt` for versioned storage and downstream inference.

5. **Interactive Inference.** Streamlit Vision Lab lets operators upload board images and see defect predictions in real-time.

6. **Defect Analytics.** Executive dashboard shows yield rates, defect Pareto, confidence distribution, and factory line performance.

7. **Model Registry Integration.** Trained model logged to Snowflake Model Registry for versioning, SQL-based inference, and SPCS deployment.

## Key Visualizations

### Defect Class Distribution

The YOLOv12 model detects 6 defect classes common in PCB manufacturing:

| Class ID | Defect Type | Description |
|----------|-------------|-------------|
| 0 | Open | Broken trace or missing connection |
| 1 | Short | Unintended connection between traces |
| 2 | Mousebite | Irregular edge defect on trace |
| 3 | Spur | Unwanted protrusion from trace |
| 4 | Copper | Excess copper where none should exist |
| 5 | Pin-hole | Small void in copper plane |

### Dashboard Preview

![Dashboard](assets/dashboard-preview.png)

The Streamlit application provides:

- **Executive Overview:** High-level yield rate cards, defect Pareto chart, and factory line performance heatmap
- **Vision Lab:** Interactive stage browser with ground truth comparison and confidence threshold filtering
- **Defect Examples:** Sample images for each defect class with bounding box visualization
- **Real-Time Results:** Inference results from DEFECT_LOGS with confidence scores and spatial coordinates

## Get Started

Ready to deploy PCB defect detection in your Snowflake account? This guide includes everything you need to get up and running quickly.

**[GitHub Repository →](https://github.com/Snowflake-Labs/sfguide-defect-detection-using-distributed-pytorch-with-snowflake-notebooks)**

The repository contains the complete setup script, GPU notebook, Streamlit dashboard, and teardown script for deploying the full solution.

*Transform quality control from reactive firefighting to proactive intelligence—with your data secure, your models custom-trained, and your insights instant.*

## Resources

- [Source Code on GitHub](https://github.com/Snowflake-Labs/sfguide-defect-detection-using-distributed-pytorch-with-snowflake-notebooks)
- [Docs: Snowflake Notebooks on Container Runtime](https://docs.snowflake.com/en/developer-guide/snowflake-ml/notebooks-on-spcs)
- [Docs: Snowflake Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [Snowflake ML Overview](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)


### Attribution
- **YOLOv12** is developed by [Ultralytics](https://www.ultralytics.com/yolo) and licensed under [AGPL-3.0](https://github.com/ultralytics/ultralytics/blob/main/LICENSE). Commercial use requires a separate enterprise license from Ultralytics. This guide uses YOLOv12 for educational and open-source demonstration purposes only.
- **PyTorch**, the PyTorch logo and any related marks are trademarks of The Linux Foundation.
- **Deep PCB dataset** by Tang, Sanli et al. — [arXiv:1902.06197](https://arxiv.org/abs/1902.06197), MIT License.
