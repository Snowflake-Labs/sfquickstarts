# Snowflake SQL Validator

Validates SQL code blocks in Snowflake guides using `snow sql` EXPLAIN + `cortex` for deep analysis.

## Overview

This tool:
- **Extracts** SQL code blocks from markdown guides (tagged and untagged)
- **Validates** syntax using `snow sql` to run `EXPLAIN <query>` against Snowflake
- **Deep Reviews** guides with Cortex AI to find deprecated features and outdated patterns
- **Reports** syntax errors, context issues, and untagged SQL blocks
- **Saves incrementally** after each guide for resilience to interruptions

## Prerequisites

### Required Tools

1. **Snowflake CLI (`snow`)** - For SQL validation via EXPLAIN
2. **Cortex CLI (`cortex`)** - For AI-powered deep review
3. **codespell** - For spell checking

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install codespell

# Verify CLI tools are installed
snow --version
cortex --version
codespell --version
```

### Snowflake Connection

Configure a Snowflake connection for the `snow` CLI:

```bash
snow connection add
snow connection test --connection default
```

## Usage

### Validate a Single Guide

```bash
python snowflake_sql_validator.py --guide ../../site/sfguides/src/your-guide/your-guide.md
```

### Batch Validate Multiple Guides

```bash
# Validate first 10 published guides
python snowflake_sql_validator.py --batch ../../site/sfguides/src --limit 10

# Filter by name pattern
python snowflake_sql_validator.py --batch ../../site/sfguides/src --filter cortex --limit 20

# Verbose output (show all blocks, not just errors)
python snowflake_sql_validator.py --batch ../../site/sfguides/src --limit 10 --verbose
```

### Deep Review with Cortex AI

Use `--deep-review` to have Cortex AI analyze each guide for deprecated features, outdated patterns, and issues:

```bash
python snowflake_sql_validator.py --batch ../../site/sfguides/src --deep-review --limit 20
```

### Monitor Progress in Real-Time

The script writes progress to a log file. Monitor it in a separate terminal:

```bash
# In terminal 1: Run validation
python snowflake_sql_validator.py --batch ../../site/sfguides/src --deep-review --output reports/guide_validation_report.md

# In terminal 2: Watch progress
tail -f reports/progress.log
```

Sample progress log output:
```
============================================================
SNOWFLAKE SQL VALIDATION - PROGRESS LOG
Started: 2026-01-20 19:20:13
============================================================

[19:20:13] [0:00:00] Command: snowflake_sql_validator.py --batch ...
[19:20:13] [0:00:00] Found 476 published guides
[19:20:13] [0:00:00] Starting validation of 476 guides

──────────────────────────────────────────────────
[19:20:16] [0:00:03] [1/476] Starting: neo4j-fraud
[19:20:18] [0:00:05]   → cortex: Deep reviewing guide content
[19:20:42] [0:00:29]   💾 Saved 1 results to: reports/guide_validation_report.csv
[19:20:42] [0:00:29] Completed: neo4j-fraud | SQL blocks: 8 | ⚠️ Context errors: 5 | 🔍 Deep reviewed
```

### Resume After Interruption

Results are saved **after each guide** to CSV files. If the script is cancelled or crashes, resume with `--continue`:

```bash
# Resume from where you left off
python snowflake_sql_validator.py --batch ../../site/sfguides/src --deep-review --continue --output reports/guide_validation_report.md
```

The `--continue` flag will:
1. Read the existing CSV to find already-processed guides
2. Skip those guides
3. Append new results to the same files

### Options

| Option | Description |
|--------|-------------|
| `--guide, -g` | Path to a specific guide to validate |
| `--batch, -b` | Directory for batch validation |
| `--connection, -c` | Snowflake connection name (default: "default") |
| `--output, -o` | Output report path (default: reports/sql_validation_report.md) |
| `--limit, -l` | Limit number of guides to process |
| `--filter, -f` | Filter guides by name pattern |
| `--offset` | Start from this guide index (0-based) |
| `--verbose, -v` | Show all results, not just errors |
| `--deep-review, -d` | Run Cortex AI analysis for deprecated/outdated content |
| `--continue` | Skip already-processed guides, append to existing CSVs |
| `--progress-log` | Custom path for progress log (default: reports/progress.log) |
| `--no-cortex` | Skip Cortex analysis for syntax errors |

## Output Files

The script generates several output files:

| File | Description |
|------|-------------|
| `reports/guide_validation_report.md` | Full markdown report with all details |
| `reports/guide_validation_report.csv` | Summary CSV with one row per guide |
| `reports/guide_validation_report_issues.csv` | Detailed CSV with one row per issue |
| `reports/progress.log` | Real-time progress log for monitoring |

## Console Output

```
📖 Validating: zero-to-snowflake.md
   🔍 Running cortex deep review for outdated content...
   ✨ Deep review complete
   ⚠️ 48 context issues (objects don't exist), ✅ 0 valid, ⏭️ 23 skipped, 📝 2 untagged

==================================================
VALIDATION COMPLETE
==================================================
  Guides: 1
  ✅ No syntax errors found
  ⚠️ Context errors: 48 (objects don't exist)
  🔍 Deep reviews: 1 guides analyzed by cortex
  ⏱️  Total time: 0:01:27
  📄 Progress log: reports/progress.log
```

## Report Categories

| Category | Description |
|----------|-------------|
| ✅ Valid | SQL validated successfully against Snowflake |
| ❌ Syntax Error | Actual SQL syntax problem that needs fixing |
| ⚠️ Context Error | Objects/database don't exist in test account (expected) |
| ⏭️ Skipped | Statements that can't be EXPLAINed (USE, GRANT, CALL, etc.) |
| 📝 Untagged | SQL blocks not tagged as ` ```sql ` |
| 🔍 Deep Reviewed | Guide analyzed by Cortex AI for issues |

## Issue Severities

| Severity | Description | Examples |
|----------|-------------|----------|
| 🔴 CRITICAL | Code that will definitely fail | Syntax errors, wrong table names, missing keywords |
| 🟠 OUTDATED | Deprecated features that still work | Old functions, deprecated APIs |
| 🟡 SUGGESTION | Best practices and recommendations | Security improvements, edge cases |
| ⚪ INFO | Minor issues | Spelling errors |

### What's NOT marked as CRITICAL

The validator is tuned to avoid false positives. These are **ignored or downgraded**:

- `USE ROLE ACCOUNTADMIN` - Standard in demos
- Placeholder values (`<your-value>`, `{{var}}`)
- Column alias in same SELECT - Snowflake allows this
- `previous_query_result` - Worksheet-specific feature
- Wrong code block language tags - Marked as SUGGESTION
- dbt/Jinja templates - Need compilation first
- PostgreSQL syntax - Different database

## How It Works

### High-Level Flow

1. **Extracts code blocks** from markdown files
2. **Identifies SQL** by looking for:
   - Blocks tagged as ` ```sql ` or ` ```snowflake `
   - Untagged blocks starting with SQL keywords (SELECT, CREATE, etc.)
3. **Pre-filters non-SQL content** (JSON, Python, dbt templates, shell prompts)
4. **Validates syntax** by running `snow sql -q "EXPLAIN <query>"` 
5. **Categorizes errors**:
   - Syntax errors = real problems to fix
   - Context errors = "object not found" (expected when tables don't exist)
6. **Deep review** (optional): Cortex AI analyzes ALL code blocks for issues
7. **Spell check**: codespell checks for typos (skips non-English guides)
8. **Saves incrementally** to CSV after each guide (resilient to interruptions)

### Validation Flow Diagram

```
SQL Block Found
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Pre-checks (skip EXPLAIN if matches):                          │
│  - Pseudocode (contains ...)                                    │
│  - JSON configs (starts with {)                                 │
│  - dbt/Jinja templates ({{ ref(...) }})                         │
│  - Python/shell code in SQL block                               │
│  - PostgreSQL syntax (LANGUAGE plpgsql)                         │
│  - Shell prompts (> or $)                                       │
└─────────────────────────────────────────────────────────────────┘
     │                              │
     │ Passes pre-checks            │ Skipped (wrong language)
     ▼                              ▼
┌──────────────────┐    ┌──────────────────────────────────────────┐
│  EXPLAIN SQL     │    │  Marked for Cortex review:               │
│  via snow sql    │    │  🏷️ WRONG TAG - check actual content     │
└──────────────────┘    └──────────────────────────────────────────┘
     │
     ├── ✅ Valid ──────────────► Cortex: Don't flag syntax errors
     │
     ├── ⚠️ Context Error ──────► Cortex: Review carefully for syntax
     │   (objects don't exist)
     │
     ├── ❌ Syntax Error ───────► Already flagged, Cortex skips
     │
     └── 🔍 Multi-statement ────► Cortex: Review each statement
                                          │
                                          ▼
                              ┌──────────────────────────┐
                              │  CORTEX DEEP REVIEW      │
                              │  - Sees ALL code blocks  │
                              │  - Has EXPLAIN results   │
                              │  - Reviews with context  │
                              └──────────────────────────┘
                                          │
                                          ▼
                              ┌──────────────────────────┐
                              │  SPELL CHECK (codespell) │
                              │  - English guides only   │
                              └──────────────────────────┘
```

### What Cortex Reviews

| Block Status | Cortex Action |
|--------------|---------------|
| ✅ SYNTAX VALID | Only flag best practices (SUGGESTION) |
| ⚠️ CONTEXT ERROR | Review carefully for syntax issues - may flag CRITICAL |
| ❌ SYNTAX ERROR | Skip - already detected by EXPLAIN |
| 🔍 MULTI-STATEMENT | Review each statement for issues |
| 🏷️ WRONG TAG | Check actual content for issues |
| ⏭️ Skipped (other) | Still visible to Cortex in code blocks |

## Statements That Can't Be EXPLAINed

These statement types are skipped (they can't be validated with EXPLAIN):
- USE, SET, ALTER SESSION
- SHOW, DESCRIBE, DESC
- GRANT, REVOKE
- CREATE/ALTER/DROP USER, ROLE, DATABASE, SCHEMA, WAREHOUSE
- CALL, EXECUTE
- PUT, GET, REMOVE, LIST

## Example Workflow

```bash
# 1. Run validation in batches of 80 guides (runs in background)
cd scripts/guide-testing
source .venv/bin/activate

python -u snowflake_sql_validator.py \
  --batch ../../site/sfguides/src \
  --limit 80 \
  --deep-review \
  --output reports/batch_validation.md \
  --progress-log reports/batch_validation_progress.log \
  2>&1 &

# 2. Monitor progress in real-time
tail -f reports/batch_validation_progress.log

# 3. Check current status
wc -l reports/batch_validation.csv           # Guides processed
grep -c "CRITICAL" reports/batch_validation_issues.csv  # Critical issues

# 4. Resume after interruption (processes next 80)
python -u snowflake_sql_validator.py \
  --batch ../../site/sfguides/src \
  --limit 80 \
  --deep-review \
  --continue \
  --output reports/batch_validation.md \
  --progress-log reports/batch_validation_progress.log \
  2>&1 &

# 5. Review results
cat reports/batch_validation.csv        # Summary per guide
cat reports/batch_validation_issues.csv # All issues found

# 6. Kill background process if needed
pkill -f "snowflake_sql_validator.py"
```

### Batch Processing Notes

- `--limit 80` processes 80 guides per batch (recommended for ~40 min runs)
- `--continue` skips already-processed guides and appends to existing CSVs
- Use `&` to run in background, `2>&1` to capture all output
- Progress is saved after each guide - safe to interrupt anytime

## Validation Statistics

Based on validation of 120+ guides:

| Metric | Value |
|--------|-------|
| Guides with critical issues | ~36% |
| Average issues per guide | ~4 |
| False positive rate | <5% (after tuning) |

### Common Issue Types Found

| Issue Type | Frequency |
|------------|-----------|
| `INFORMATION_SCHEMA` missing `SNOWFLAKE.` prefix | Common |
| Table/database name typos | Common |
| Trailing commas in SQL | Occasional |
| Wrong code block language tags | Occasional |
| Deprecated package versions | Common |
| PEM key formatting errors | Rare |
