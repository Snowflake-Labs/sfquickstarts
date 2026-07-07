# Run this in a Python cell in your Snowflake Workspace notebook
# after 01_setup.sql has completed.
# Uploads CSV data files and agent skills to their respective stages.

from snowflake.snowpark.context import get_active_session

session = get_active_session()
session.sql("USE ROLE ACCOUNTADMIN").collect()
session.sql("USE DATABASE HOL_COCO_COWORK").collect()
session.sql("USE SCHEMA DATA").collect()

# Upload data files
files = [
    ("data/dim_store.csv", "@HOL_STAGE/dim_store"),
    ("data/dim_item.csv", "@HOL_STAGE/dim_item"),
    ("data/fact_item_sales.csv", "@HOL_STAGE/fact_item_sales"),
]

for local_path, stage_path in files:
    result = session.file.put(local_path, stage_path, auto_compress=True, overwrite=True)
    print(f"Uploaded {local_path} -> {stage_path}: {result}")

print("Data files uploaded.\n")

# Upload agent skills
session.sql("USE SCHEMA TOOLS").collect()

skills = [
    ("../Skills/anomaly_detection/SKILL.md", "@SKILLS_STAGE/skills/anomaly_detection/"),
    ("../Skills/sales_report/SKILL.md", "@SKILLS_STAGE/skills/sales_report/"),
]

for local_path, stage_path in skills:
    result = session.file.put(local_path, stage_path, auto_compress=False, overwrite=True)
    print(f"Uploaded {local_path} -> {stage_path}: {result}")

session.sql("USE SCHEMA DATA").collect()
print("\nAll files and skills uploaded.")
