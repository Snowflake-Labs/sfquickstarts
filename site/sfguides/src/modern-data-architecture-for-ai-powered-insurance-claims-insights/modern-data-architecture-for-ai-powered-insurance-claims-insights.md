# Unlocking Hidden Value: The Modern Data Architecture for AI-Powered Insurance Claims Insights

## Overview

This guide walks through how to build a modern data architecture on Snowflake and AWS that reads open table format Iceberg data from AWS and combines it with Snowflake Native tables, transforms and enriches the data using Snowpark Connect for Apache Spark, and delivers AI-powered insights through Cortex Analyst and Snowflake Intelligence. It provides an end-to-end blueprint for combining open table formats, feature engineering, and natural language analytics to accelerate fraud detection and claims processing.

## Prerequisites

- Snowflake account with ACCOUNTADMIN role
- AWS account with permissions to create and manage S3 buckets, IAM roles/policies, AWS Glue Data Catalog, and Lake Formation
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) (CoCo) installed and configured with a valid connection to the Snowflake account

## What You'll Learn

- **Snowflake Horizon Catalog** — How the unified catalog now enables discovery and governance of both external Apache Iceberg tables and Snowflake Native tables from a single pane of glass, without moving data
- **Snowpark Connect for Apache Spark** — How to use familiar PySpark APIs to join, enrich, and score data across external Iceberg tables and internal Native tables in a single Spark job running on Snowflake compute
- **Snowflake Intelligence** — How to publish a Cortex Agent that lets business users ask natural language questions on the aggregated, fraud-scored claims data without writing SQL
- **Cortex Code (CoCo)** — How to use CoCo and interactively deploy the entire solution end-to-end, from creating Snowflake objects and running Spark jobs to setting up Cortex Analyst and Snowflake Intelligence


## Solution Architecture

![Solution Architecture](assets/Modern%20Data%20Architecture%20for%20AI-Powered%20Insurance%20Claims%20Insights.jpeg)

## Architecture Overview

This solution leverages AWS and Snowflake services to create an end-to-end data pipeline for insurance claims analytics.

### Components

**AWS Account (US-West-2)**
- **Amazon S3** - Raw data storage in Apache Iceberg format
- **AWS Glue Data Catalog** - Metadata management for Iceberg tables

**Snowflake (US-West-2)**
- **Catalog Linked Database** - Connects to AWS Glue Catalog for accessing external Iceberg data
- **Snowflake Native Tables** - Persistent storage for transformed data
- **Snowflake Horizon Catalog** - Central governance layer
- **Snowpark Connect for Apache Spark** - Data transformation and feature engineering
- **Snowflake Intelligence** - AI-powered agent interactions
- **Cortex Analyst** - Natural language to SQL generation

### Phase 1: Data Ingestion & External Cataloging (AWS to Snowflake)

| Step | Component | Claims Scenario |
|------|-----------|-----------------|
| Claims Data Landing | Amazon S3 | Raw claims data (e.g., FNOL reports, adjuster notes, images, etc.) is stored in the data lake using Apache Iceberg table format |
| Metadata Registration | AWS Glue Data Catalog | The Glue Catalog is updated with Iceberg table metadata, acting as the "source of truth" pointer to the Iceberg data files in S3 |
| Catalog Synchronization | Catalog Linked Database | Snowflake's Catalog Linked Database connects to AWS Glue Catalog, ingesting the Iceberg metadata and creating a schema and table that points directly to the external Iceberg data in S3 |

### Phase 2: Data Transformation & Feature Engineering

| Step | Component | Claims Scenario |
|------|-----------|-----------------|
| Data Processing & Feature Creation | Snowpark Connect for Apache Spark | The Spark job reads claims data from the Catalog Linked Database, performs ML-based feature engineering (e.g., NLP for claims description, embeddings, calculating loss ratios, geo-spatial analysis, etc.) and writes the enriched features to a Snowflake Native Table using the Iceberg REST API |
| Data Persistence | Snowpark Connect for Apache Spark (Write-back) | The resulting enriched and curated data is written back to a new Snowflake Native Table. This table is optimized for querying and AI/ML workloads |

### Phase 3: Insight Generation & Agent Interaction

| Step | Component | Claims Scenario |
|------|-----------|-----------------|
| Agent Query & Query Orchestration | Snowflake Intelligence, Cortex Agents | A claims agent, without writing SQL, asks a natural language question (e.g., "Show me the top 5 high-risk claims filed this week"). Cortex Analyst receives the request, understands the context, and generates the appropriate SQL query to Cortex Analyst |
| SQL Generation & Execution | Cortex Analyst | The Cortex Analyst component receives a user question, translates it into an optimized Snowflake SQL query, and executes it against the Snowflake Native Tables |
| Insight Delivery | Snowflake Intelligence | The end-to-end flow delivers instant answers to complex analytical questions, allowing users to act quickly by converting them to summary alerts or remediation actions |

### Cross-Cutting Layer: Governance

The **Snowflake Horizon Catalog** acts as the central governance layer throughout this entire process, ensuring every user and component (from Snowpark job to Snowflake Intelligence) only accesses data according to defined security policies.

## Solution Deployment

### Step 1: Configure AWS Infrastructure (S3, Glue, IAM, Lake Formation)

### Step 2: Connect Snowflake to AWS Glue via Catalog Integration

### Step 3: Provision Snowflake Objects (Database, Schema, Stages, Tables)

### Step 4: Stage Data and the Fraud Detection Model

### Step 5: Run Feature Engineering with Snowpark Connect for Apache Spark

### Step 6: Enable Cortex Analyst, Cortex Agent, and Snowflake Intelligence








