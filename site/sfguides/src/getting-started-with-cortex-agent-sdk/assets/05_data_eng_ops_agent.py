"""
05_data_eng_ops_agent.py — Automated Data Engineering Ops Agent

An all-in-one ops agent that:
  1. Checks pipeline health (task failures, stuck tasks)
  2. Checks data quality (DMF violations, stale tables)
  3. Diagnoses incidents and suggests fixes

Uses the coding agent with thread persistence so all checks
share context for smarter incident diagnosis.
"""

import os
from datetime import datetime
from cortex_agent_sdk import CortexAgentClient
from cortex_agent_sdk.auth import PatAuth

client = CortexAgentClient(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    auth=PatAuth(os.environ["SNOWFLAKE_PAT"]),
)

CODING_OPTS = {
    "model": "auto",
    "permission_policy": "always_allow",
}


def extract_text(stream):
    """Extract text content from coding agent stream events."""
    text_parts = []
    for event in stream:
        delta = event.get("delta", {})
        for item in delta.get("content", []):
            if item.get("type") == "text":
                text = item.get("text", {})
                val = text.get("value", text) if isinstance(text, dict) else text
                text_parts.append(str(val))
            elif item.get("type") == "tool_results":
                tr = item.get("tool_results", {})
                for c in tr.get("content", []):
                    if c.get("type") == "text":
                        text_parts.append(c.get("text", ""))

        evt = event.get("event", event.get("object", ""))
        if "text" in str(evt).lower() and "delta" in str(evt).lower():
            d = event.get("data", {})
            if d.get("delta"):
                text_parts.append(d["delta"])

    return "".join(text_parts) if text_parts else "(No text response — check raw events)"


def run_check(client, thread_id, prompt):
    """Run a coding agent turn on a thread and return the text response."""
    body = {
        **CODING_OPTS,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
        "thread_id": thread_id,
    }
    stream = client.coding_agent.stream(body)
    return extract_text(stream)


def main():
    print("=" * 70)
    print("  DAILY DATA ENGINEERING OPS REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Create a thread so all checks share context
    thread = client.threads.create(origin_application="ops-agent")
    thread_id = thread.get("thread_id") or thread.get("id")

    # --- Pipeline Health ---
    print("\n[1/3] Running pipeline health check...\n")
    pipeline_report = run_check(
        client,
        thread_id,
        """You are a data engineering ops agent. Perform a pipeline health check:

1. Query SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY for tasks that FAILED or were
   CANCELLED in the last 24 hours. Show the task name, database, schema,
   error message, and scheduled time.

2. Check if any tasks are stuck by looking for tasks that have been running
   for more than 30 minutes.

3. Summarize your findings in this exact format:
   - Total failures in last 24h: <count>
   - Critical failures (list each with task name, error, and database.schema)
   - Stuck tasks (if any)
   - Overall pipeline health: HEALTHY / DEGRADED / CRITICAL

If there are no failures, report HEALTHY status.""",
    )
    print(pipeline_report)

    # --- Data Quality ---
    print("\n" + "-" * 70)
    print("\n[2/3] Running data quality check...\n")
    quality_report = run_check(
        client,
        thread_id,
        """You are a data engineering ops agent. Perform a data quality check:

1. Query SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_RESULTS for any
   DMF violations in the last 24 hours. If this view is not available or
   returns no results, note that and move on.

2. Check table freshness: query SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
   or INFORMATION_SCHEMA.TABLES to find tables that haven't been updated
   in the last 48 hours (look at last_altered or similar columns) in
   databases that are NOT system databases (skip SNOWFLAKE, SNOWFLAKE_SAMPLE_DATA).
   Limit to 10 stalest tables.

3. Summarize your findings:
   - DMF violations: <count> (list each with table, metric, value)
   - Stale tables: <count> (list the top 5 stalest with last update time)
   - Overall data quality: GOOD / WARNING / CRITICAL""",
    )
    print(quality_report)

    # --- Incident Diagnosis ---
    needs_diagnosis = any(
        keyword in pipeline_report.lower() + quality_report.lower()
        for keyword in ["critical", "degraded", "failed", "violation"]
    )

    if needs_diagnosis:
        print("\n" + "-" * 70)
        print("\n[3/3] Critical issues detected — running incident diagnosis...\n")
        incident_report = run_check(
            client,
            thread_id,
            f"""You are a senior data engineering ops agent. Based on the pipeline
health and data quality checks you just ran, diagnose root causes and
suggest concrete fixes.

For each critical or degraded finding:
1. Investigate the root cause — run additional queries if needed
   (check object dependencies, recent DDL changes, permission issues)
2. Suggest a specific fix (SQL command, configuration change, or escalation)
3. Rate the urgency: P1 (fix now), P2 (fix today), P3 (fix this week)

Format your response as an incident report with clear sections.""",
        )
        print(incident_report)
    else:
        print("\n" + "-" * 70)
        print("\n[3/3] No critical issues detected. Skipping incident diagnosis.")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("  OPS REPORT COMPLETE")
    print("=" * 70)

    client.threads.delete(thread_id)
    client.close()


if __name__ == "__main__":
    main()
