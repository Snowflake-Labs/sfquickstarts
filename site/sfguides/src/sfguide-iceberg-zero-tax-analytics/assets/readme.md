This directory contains assets for the sfguide-iceberg-zero-tax-analytics quickstart.

Files:
- architecture.png — End-to-end architecture diagram
- 00_setup.sql — Module 0: environment setup
- 01_create_tables.sql — Module 1: Iceberg table creation
- 02_ssv2_streaming_setup.sql — Module 2: SSV2 streaming + VARIANT
- 03_horizon_governance.sql — Module 3: governance (Path A / Path B)
- 04_databricks_read.ipynb — Module 4: Databricks multi-engine read
- 05_semantic_view.sql — Module 5: Semantic View + Cortex Agent
- 06_cortex_code_prompts.sql — Module 6: Cortex Code prompts (optional)
- teardown_governance.sql — Teardown: governance objects only
- teardown_full.sql — Teardown: full reset
- pom.xml — Maven project for Java SSV2 ingest app
- SSV2WeatherIngest.java — Java SSV2 weather ingest application
