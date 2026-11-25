PUT 'file://<your home dir>/.snowflake/cortex/playground/workspace/live_financial_demo/generated/skills/waterfall-reconciliation-review/SKILL.md' @<your db>.<your schema>.DEMO_ASSETS/skills/5d5f00d67109a91404d94c68c271304b29045d05a0e6d5a728024c62bbfdad3d/waterfall-reconciliation-review/ AUTO_COMPRESS=FALSE OVERWRITE=FALSE;
PUT 'file://<your home dir>/.snowflake/cortex/playground/workspace/live_financial_demo/generated/evaluation.yaml' @<your db>.<your schema>.DEMO_ASSETS/evaluation/v1/ AUTO_COMPRESS=FALSE OVERWRITE=FALSE;
LIST @<your db>.<your schema>.DEMO_ASSETS/skills/5d5f00d67109a91404d94c68c271304b29045d05a0e6d5a728024c62bbfdad3d/waterfall-reconciliation-review/;
LIST @<your db>.<your schema>.DEMO_ASSETS/evaluation/v1/;
