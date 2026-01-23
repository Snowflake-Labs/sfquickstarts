#!/usr/bin/env python3
"""
Snowflake SQL Validator - Hybrid validation using snow sql + cortex

Fast validation: Uses `snow sql` to run EXPLAIN on SQL blocks
Deep analysis: Uses `cortex` to analyze syntax errors and review full guide content

Usage:
    python snowflake_sql_validator.py --guide <path-to-guide.md>
    python snowflake_sql_validator.py --batch <guides-dir> --limit 10
    python snowflake_sql_validator.py --guide <path> --deep-review  # Full cortex analysis
"""

import argparse
import csv
import json
import re
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


class ProgressLogger:
    """Thread-safe progress logger that writes to both console and file."""
    
    def __init__(self, log_path: str = "reports/progress.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._start_time = datetime.now()
        
        # Initialize log file
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write(f"=" * 60 + "\n")
            f.write(f"SNOWFLAKE SQL VALIDATION - PROGRESS LOG\n")
            f.write(f"Started: {self._start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=" * 60 + "\n\n")
    
    def log(self, message: str, also_print: bool = True):
        """Log a message to file and optionally to console."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        elapsed = datetime.now() - self._start_time
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
        
        log_line = f"[{timestamp}] [{elapsed_str}] {message}"
        
        with self._lock:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line + "\n")
                f.flush()  # Ensure immediate write
            
            if also_print:
                print(log_line)
    
    def log_guide_start(self, index: int, total: int, guide_name: str):
        """Log the start of processing a guide."""
        self.log(f"\n{'─' * 50}")
        self.log(f"[{index}/{total}] Starting: {guide_name}")
    
    def log_guide_complete(self, guide_name: str, stats: dict):
        """Log completion of a guide with stats."""
        parts = [f"Completed: {guide_name}"]
        if stats.get('sql_blocks', 0) > 0:
            parts.append(f"SQL blocks: {stats['sql_blocks']}")
        if stats.get('syntax_errors', 0) > 0:
            parts.append(f"❌ Syntax errors: {stats['syntax_errors']}")
        if stats.get('context_errors', 0) > 0:
            parts.append(f"⚠️ Context errors: {stats['context_errors']}")
        if stats.get('deep_review', False):
            parts.append("🔍 Deep reviewed")
        self.log(" | ".join(parts))
    
    def log_command(self, command: str):
        """Log a command being executed."""
        self.log(f"  → Running: {command[:80]}...")
    
    def log_save(self, file_path: str, count: int):
        """Log that results were saved."""
        self.log(f"  💾 Saved {count} results to: {file_path}")
    
    def log_summary(self, total_guides: int, total_errors: int, total_time: str):
        """Log final summary."""
        self.log(f"\n{'=' * 60}")
        self.log(f"VALIDATION COMPLETE")
        self.log(f"  Total guides: {total_guides}")
        self.log(f"  Syntax errors found: {total_errors}")
        self.log(f"  Total time: {total_time}")
        self.log(f"{'=' * 60}")


# Global progress logger (initialized in main)
progress_logger: ProgressLogger = None


def get_guide_language(guide_path: str) -> str:
    """
    Extract language from guide front matter (e.g., 'language: fr').
    Returns 'en' if not specified or not found.
    """
    path = Path(guide_path)
    if not path.exists():
        return 'en'
    
    try:
        content = path.read_text(encoding='utf-8')
        # Look for language field in front matter (first 30 lines)
        for line in content.split('\n')[:30]:
            if line.lower().startswith('language:'):
                lang = line.split(':', 1)[1].strip().lower()
                return lang if lang else 'en'
        return 'en'
    except Exception:
        return 'en'


def run_spell_check(guide_path: str) -> list:
    """
    Run codespell on a guide to find spelling errors.
    Skips non-English guides based on front matter language field.
    
    Returns a list of SpellingError objects.
    """
    path = Path(guide_path)
    if not path.exists():
        return []
    
    # Skip spell check for non-English guides
    language = get_guide_language(guide_path)
    if language != 'en':
        return []  # Skip spell check for non-English guides
    
    # Find codespell executable in venv
    venv_codespell = Path(__file__).parent / '.venv' / 'bin' / 'codespell'
    codespell_cmd = str(venv_codespell) if venv_codespell.exists() else 'codespell'
    
    try:
        # Run codespell with machine-readable output
        result = subprocess.run(
            [
                codespell_cmd,
                '--quiet-level', '2',  # Less verbose
                '--ignore-words-list', 'nd,te,ue,fo,fle,ba,ist,als,ot,wil,ans,bu,mor,ned,ser,ths,tre,hel,inout,pullrequest',  # Common false positives
                str(path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        errors = []
        # Parse codespell output: "filename:line: word ==> suggestion"
        for line in result.stdout.strip().split('\n'):
            if not line or '==>' not in line:
                continue
            
            try:
                # Format: "path/file.md:123: misspeling ==> misspelling"
                parts = line.split(':')
                if len(parts) >= 3:
                    line_num = int(parts[1])
                    error_part = ':'.join(parts[2:]).strip()
                    
                    if '==>' in error_part:
                        word_part, suggestion = error_part.split('==>')
                        word = word_part.strip()
                        suggestion = suggestion.strip()
                        
                        errors.append(SpellingError(
                            line_number=line_num,
                            word=word,
                            suggestion=suggestion,
                            context=""
                        ))
            except (ValueError, IndexError):
                continue
        
        return errors
        
    except subprocess.TimeoutExpired:
        return []
    except Exception as e:
        if progress_logger:
            progress_logger.log(f"  ⚠️ Spell check error: {e}", also_print=False)
        return []


def sanitize_for_csv(value: str, max_length: int = 500) -> str:
    """
    Sanitize a string for safe CSV output.
    - Replaces newlines with a visible marker (preserves code structure info)
    - Truncates to max length
    - Python's csv module handles quoting/escaping automatically
    
    Note: We do NOT replace pipes or quotes - the csv module handles those correctly.
    """
    if not value:
        return ""
    
    # Convert to string if not already
    value = str(value)
    
    # Replace newlines with visible marker to preserve structure info
    # This makes it clear where line breaks were without breaking CSV
    value = value.replace('\r\n', ' ↵ ').replace('\n', ' ↵ ').replace('\r', ' ↵ ')
    
    # Replace multiple spaces with single space (but preserve the markers)
    value = re.sub(r' +', ' ', value)
    
    # Strip leading/trailing whitespace
    value = value.strip()
    
    # Truncate to max length
    if len(value) > max_length:
        value = value[:max_length-3] + "..."
    
    return value


@dataclass
class SQLValidationResult:
    """Result of validating a single SQL block."""
    block_index: int
    line_in_guide: int
    context: str
    sql_preview: str
    full_sql: str
    valid: bool
    error_message: str = ""
    skipped: bool = False
    skip_reason: str = ""
    is_syntax_error: bool = False
    is_tagged: bool = True
    needs_cortex_analysis: bool = False


@dataclass
class SpellingError:
    """A spelling error found in a guide."""
    line_number: int
    word: str
    suggestion: str
    context: str


@dataclass
class GuideValidationResult:
    """Complete validation result for a guide."""
    guide_path: str
    guide_name: str
    total_sql_blocks: int
    valid_blocks: int
    invalid_blocks: int
    skipped_blocks: int
    syntax_errors: int = 0
    context_errors: int = 0
    untagged_sql_blocks: int = 0
    cortex_analysis: str = ""
    cortex_guide_review: str = ""  # Full guide review
    results: list = field(default_factory=list)
    spelling_errors: list = field(default_factory=list)  # List of SpellingError


class SnowflakeSQLValidator:
    """Validates SQL using snow sql EXPLAIN, with cortex for deep analysis."""
    
    # SQL statements that can't be EXPLAINed but cortex can analyze
    NON_EXPLAINABLE = [
        'USE', 'SET', 'ALTER SESSION', 'SHOW', 'DESCRIBE', 'DESC',
        'LIST', 'PUT', 'GET', 'REMOVE', 'GRANT', 'REVOKE',
        'CREATE USER', 'ALTER USER', 'DROP USER',
        'CREATE ROLE', 'ALTER ROLE', 'DROP ROLE', 
        'CREATE DATABASE', 'ALTER DATABASE', 'DROP DATABASE',
        'CREATE SCHEMA', 'ALTER SCHEMA', 'DROP SCHEMA',
        'CREATE WAREHOUSE', 'ALTER WAREHOUSE', 'DROP WAREHOUSE',
        'CALL', 'EXECUTE',
    ]
    
    def __init__(self, connection: str = "default", timeout: int = 30):
        self.connection = connection
        self.timeout = timeout
        self._snow_path = self._find_snow_cli()
    
    def _find_snow_cli(self) -> str:
        """Find the snow CLI executable."""
        if '.venv' in sys.executable:
            snow_path = Path(sys.executable).parent / 'snow'
            if snow_path.exists():
                return str(snow_path)
        
        for path in ['/Users/afilippova/.local/bin/snow', '/usr/local/bin/snow']:
            if Path(path).exists():
                return path
        
        venv_snow = Path(__file__).parent / '.venv' / 'bin' / 'snow'
        if venv_snow.exists():
            return str(venv_snow)
        
        return 'snow'
    
    def validate_sql(self, sql: str) -> tuple[bool, str, bool, str, bool, bool]:
        """
        Validate SQL syntax using EXPLAIN via snow sql.
        
        Returns:
            (is_valid, error_message, was_skipped, skip_reason, is_syntax_error, needs_cortex)
        """
        # Check if this is a multi-statement block BEFORE cleaning
        raw_statements = [s.strip() for s in sql.split(';') if s.strip()]
        is_multi_statement = len(raw_statements) > 1
        
        sql_clean = self._prepare_sql(sql)
        
        if not sql_clean.strip():
            if is_multi_statement:
                # First statement was empty/comment, rest has content - needs Cortex review
                return True, "", True, "Multi-statement block (needs Cortex review)", False, True
            return True, "", True, "Empty or comment-only SQL", False, False
        
        # Check for pseudocode indicators (not real SQL)
        if '...' in sql_clean or '...' in sql:
            return True, "", True, "Pseudocode example (contains ...)", False, False
        
        # Check for JSON configs mistakenly tagged as SQL
        if sql_clean.strip().startswith('{') and ':' in sql_clean:
            return True, "", True, "JSON config (not SQL)", False, False
        
        # Check for dbt/Jinja templates that weren't fully replaced
        if '{{ ref(' in sql or '{{ source(' in sql or '{{ref(' in sql:
            return True, "", True, "dbt/Jinja template (needs compilation)", False, False
        
        # Check for Python code mistakenly tagged as SQL
        if sql_clean.strip().startswith('def ') or sql_clean.strip().startswith('class '):
            return True, "", True, "Python code (wrong language tag)", False, False
        
        # Check for shell prompts in SQL blocks
        if sql_clean.strip().startswith('> ') or sql_clean.strip().startswith('$ '):
            return True, "", True, "Shell prompt (not SQL)", False, False
        
        # Check for PostgreSQL-specific syntax
        if 'LANGUAGE plpgsql' in sql or 'language plpgsql' in sql:
            return True, "", True, "PostgreSQL syntax (not Snowflake)", False, False
        
        # Check for Python comments in SQL blocks
        if sql_clean.strip().startswith('# '):
            return True, "", True, "Python comment (wrong language tag)", False, False
        
        # Check for terminal output
        if sql_clean.strip().startswith('(base)') or sql_clean.strip().startswith('(snowpark)'):
            return True, "", True, "Terminal output (not SQL)", False, False
        
        # Check for Jinja macros
        if sql_clean.strip().startswith('{%'):
            return True, "", True, "Jinja macro (needs compilation)", False, False
        
        # Check for shell commands in SQL blocks
        if sql_clean.strip().startswith('snowsql ') or sql_clean.strip().startswith('snow '):
            return True, "", True, "CLI command (not SQL)", False, False
        
        # Check for Snowflake Scripting blocks (DECLARE can't be EXPLAINed)
        if sql_clean.strip().upper().startswith('DECLARE '):
            return True, "", True, "Snowflake Scripting block", False, True
        
        # Check for partial SQL expressions (not full statements)
        first_word = sql_clean.strip().split()[0].upper() if sql_clean.strip() else ""
        if first_word in ('CASE', 'AVG', 'SUM', 'COUNT', 'MAX', 'MIN', 'SPLIT_PART', 'ORDER', 'GROUP', 'WHERE', 'AND', 'OR'):
            return True, "", True, "Partial SQL expression (not full statement)", False, False
        
        first_word = sql_clean.strip().split()[0].upper() if sql_clean.strip() else ""
        first_two = ' '.join(sql_clean.strip().split()[:2]).upper() if sql_clean.strip() else ""
        
        for pattern in self.NON_EXPLAINABLE:
            if first_word == pattern or first_two.startswith(pattern):
                return True, "", True, f"Cannot EXPLAIN {pattern} statements", False, True
        
        try:
            result = subprocess.run(
                [
                    self._snow_path,
                    'sql', '-q', f"EXPLAIN {sql_clean}",
                    '-c', self.connection,
                    '--format', 'JSON'
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                return True, "", False, "", False, False
            else:
                error = self._parse_error(result.stderr or result.stdout)
                is_syntax = '[Syntax Error]' in error
                
                # Check if this looks like a multi-statement error (unexpected keyword at line 2+)
                # These are NOT real syntax errors - just EXPLAIN limitation
                multi_stmt_patterns = [
                    r'line [2-9]\d* at position 0 unexpected',  # Error at start of line 2+
                    r"unexpected 'USE'",
                    r"unexpected 'CALL'", 
                    r"unexpected 'GRANT'",
                    r"unexpected 'EXECUTE'",
                    r"unexpected 'ALTER'",
                    r"unexpected 'DROP'",
                    r"unexpected 'CREATE'",
                    r"unexpected 'SET'",
                    r"unexpected 'SHOW'",
                    r"unexpected 'BEGIN'",
                    r"unexpected 'begin'",
                ]
                
                is_multi_stmt_error = any(re.search(p, error) for p in multi_stmt_patterns)
                
                if is_multi_stmt_error:
                    # Not a real syntax error - just EXPLAIN can only handle one statement
                    # Skip EXPLAIN but flag for Cortex to review
                    return True, "", True, "Multi-statement block (needs Cortex review)", False, True
                
                # Check if this is a placeholder error (users are expected to replace these)
                placeholder_patterns = [
                    r"unexpected '<'",  # <PLACEHOLDER> syntax
                    r"unexpected '-'",  # your-database type names
                    r"invalid value '\s*'",  # Empty string values like ''
                    r"invalid value \[''\]",  # Empty array values
                    r"placeholder",  # Our own placeholder substitution
                ]
                
                is_placeholder_error = any(re.search(p, error, re.IGNORECASE) for p in placeholder_patterns)
                
                if is_placeholder_error:
                    # Not a real syntax error - users need to replace placeholder values
                    return True, "", True, "Placeholder values (users must replace)", False, False
                
                return False, error, False, "", is_syntax, is_syntax
                
        except subprocess.TimeoutExpired:
            return False, "Query validation timed out", False, "", False, False
        except FileNotFoundError:
            return False, f"snow CLI not found at {self._snow_path}", False, "", False, False
        except Exception as e:
            return False, str(e), False, "", False, False
    
    def _prepare_sql(self, sql: str) -> str:
        """Clean SQL for validation."""
        sql = re.sub(r'<[a-zA-Z_][a-zA-Z0-9_-]*>', "'placeholder'", sql)
        sql = re.sub(r'\$\{[^}]+\}', "'placeholder'", sql)
        sql = re.sub(r'\{\{[^}]+\}\}', "'placeholder'", sql)
        # Single curly brace variables like {prevValue}, {varName}
        sql = re.sub(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', "'placeholder'", sql)
        
        # Strip leading comment lines
        lines = sql.split('\n')
        while lines and lines[0].strip().startswith('--'):
            lines.pop(0)
        sql = '\n'.join(lines)
        
        statements = sql.split(';')
        sql = statements[0].strip()
        
        return sql
    
    def _parse_error(self, output: str) -> str:
        """Extract the most useful error message."""
        output = re.sub(r'[╭╮╰╯│─]+', '', output)
        output = re.sub(r'\s+', ' ', output).strip()
        
        if 'does not exist' in output.lower() or 'not have a current database' in output.lower():
            return f"[Object/Context Error] {output[:150]}"
        
        match = re.search(r'SQL compilation error[:\s]*(.*?)(?:\.|$)', output, re.IGNORECASE)
        if match:
            return f"[Syntax Error] {match.group(1).strip()[:150]}"
        
        match = re.search(r'syntax error[:\s]*(.*?)(?:\.|$)', output, re.IGNORECASE)
        if match:
            return f"[Syntax Error] {match.group(1).strip()[:150]}"
        
        match = re.search(r'(\d{6})[^:]*:\s*([^:]+):\s*(.*)', output)
        if match:
            return f"[{match.group(1)}] {match.group(3).strip()[:150]}"
        
        return output[:150] if output else "Unknown error"


def run_cortex_analysis(guide_name: str, issues: list[dict], timeout: int = 120) -> str:
    """Use cortex to analyze SQL issues and suggest fixes."""
    if not issues:
        return ""
    
    prompt_parts = [f"Analyze these SQL issues from guide '{guide_name}' and suggest fixes:\n"]
    
    for i, issue in enumerate(issues[:10], 1):
        prompt_parts.append(f"\n{i}. Line {issue['line']}:")
        prompt_parts.append(f"   Error: {issue['error']}")
        prompt_parts.append(f"   SQL: {issue['sql'][:200]}")
    
    prompt_parts.append("\n\nFor each, briefly explain what's wrong and how to fix it.")
    prompt = '\n'.join(prompt_parts)
    
    return _run_cortex_prompt(prompt, timeout)


def run_cortex_guide_review(guide_path: str, timeout: int = 300, known_untagged_lines: list[int] = None, explain_results: list = None) -> str:
    """
    Use cortex to review the entire guide for outdated content and issues.
    
    Args:
        guide_path: Path to the guide markdown file
        timeout: Timeout in seconds
        known_untagged_lines: Line numbers of already-detected untagged SQL blocks (to avoid duplicates)
        explain_results: List of SQLValidationResult from EXPLAIN validation (source of truth for syntax)
    
    Returns:
        Review text from cortex in structured format
    """
    path = Path(guide_path)
    if not path.exists():
        return "Guide file not found"
    
    content = path.read_text(encoding='utf-8')
    known_untagged_lines = known_untagged_lines or []
    explain_results = explain_results or []
    
    # Extract code blocks with line numbers and language
    # Pass full code blocks to Cortex for accurate analysis
    code_blocks = []
    # Handle optional space between ``` and language (e.g., "``` bash" or "```sql")
    for match in re.finditer(r'``` ?(\w*)\n(.*?)```', content, re.DOTALL):
        lang = match.group(1).lower() or 'unknown'
        code = match.group(2).strip()
        line_num = content[:match.start()].count('\n') + 1
        if lang in ('sql', 'python', 'py', 'yaml', 'json', 'toml', 'snowflake', 'bash', 'sh', '') and code:
            code_blocks.append(f"[Line {line_num}, {lang}]\n```{lang}\n{code}\n```")
    
    # Build the prompt requesting structured output
    untagged_note = ""
    if known_untagged_lines:
        untagged_note = f"\n\nNote: Lines {', '.join(map(str, known_untagged_lines))} already flagged as untagged SQL blocks - skip those."
    
    # Build EXPLAIN validation summary - this is the source of truth for SQL syntax
    explain_note = ""
    multi_stmt_lines = []
    context_error_lines = []
    syntax_error_lines = []
    
    if explain_results:
        validated_sql = []
        for r in explain_results:
            if r.valid and not r.skipped:
                validated_sql.append(f"  - Line {r.line_in_guide}: ✅ SYNTAX VALID (passed Snowflake EXPLAIN)")
            elif r.skipped:
                if "Multi-statement" in (r.skip_reason or ""):
                    validated_sql.append(f"  - Line {r.line_in_guide}: 🔍 MULTI-STATEMENT (needs your review)")
                    multi_stmt_lines.append(r.line_in_guide)
                elif "wrong language" in (r.skip_reason or "").lower() or "not SQL" in (r.skip_reason or ""):
                    validated_sql.append(f"  - Line {r.line_in_guide}: 🏷️ WRONG TAG ({r.skip_reason}) - check for issues in actual content")
                else:
                    validated_sql.append(f"  - Line {r.line_in_guide}: ⏭️ Skipped ({r.skip_reason})")
            elif r.is_syntax_error:
                validated_sql.append(f"  - Line {r.line_in_guide}: ❌ SYNTAX ERROR (already detected): {r.error_message[:60]}")
                syntax_error_lines.append(r.line_in_guide)
            else:
                # Context error = EXPLAIN failed because objects don't exist, syntax NOT fully validated
                validated_sql.append(f"  - Line {r.line_in_guide}: ⚠️ CONTEXT ERROR (syntax NOT validated - needs your review)")
                context_error_lines.append(r.line_in_guide)
        
        multi_stmt_note = ""
        if multi_stmt_lines:
            multi_stmt_note = f"""

MULTI-STATEMENT BLOCKS (Lines {', '.join(map(str, multi_stmt_lines))}):
These blocks contain multiple SQL statements. EXPLAIN can only validate one statement.
Review EACH statement for syntax errors and flag as CRITICAL if broken."""

        context_error_note = ""
        if context_error_lines:
            context_error_note = f"""

CONTEXT ERROR BLOCKS (Lines {', '.join(map(str, context_error_lines))}):
EXPLAIN failed because referenced objects (databases, tables, etc.) don't exist in our test account.
This means the SQL SYNTAX WAS NOT FULLY VALIDATED. Please review these carefully for:
- Trailing commas, missing keywords, typos
- Invalid syntax that EXPLAIN couldn't catch
Flag definite syntax errors as CRITICAL."""

        syntax_error_note = ""
        if syntax_error_lines:
            syntax_error_note = f"""

ALREADY DETECTED SYNTAX ERRORS (Lines {', '.join(map(str, syntax_error_lines))}):
These blocks have syntax errors already detected by EXPLAIN. DO NOT report these again."""
        
        if validated_sql:
            explain_note = f"""

SNOWFLAKE EXPLAIN VALIDATION RESULTS:
{chr(10).join(validated_sql)}

RULES:
- ✅ SYNTAX VALID blocks: Do NOT flag syntax errors. Only flag as SUGGESTION for best practices.
- ⚠️ CONTEXT ERROR blocks: Review carefully for syntax issues - flag real errors as CRITICAL.
- ❌ SYNTAX ERROR blocks: Already detected - DO NOT report again.
- 🔍 MULTI-STATEMENT blocks: Review each statement for issues.
- 🏷️ WRONG TAG blocks: These have wrong language tags (e.g., Python tagged as SQL). Check the ACTUAL content for issues.{multi_stmt_note}{context_error_note}{syntax_error_note}"""
    
    prompt = f"""Review this Snowflake guide for issues. The guide is: {path.stem}

Focus on finding:
1. **Deprecated features** - SQL syntax, functions, or APIs that Snowflake has deprecated
2. **Outdated patterns** - Old ways of doing things that have better modern alternatives
3. **Things that won't work** - Code that would fail or produce unexpected results
4. **Missing best practices** - Important security, performance, or reliability concerns

SEVERITY GUIDELINES:
- CRITICAL: Only for code that will DEFINITELY fail (syntax errors, wrong object names, invalid keywords)
- OUTDATED: Deprecated features that still work but should be updated
- SUGGESTION: Best practices, edge cases, and recommendations

IGNORE COMPLETELY (do not report at all):
- USE ROLE ACCOUNTADMIN or any ACCOUNTADMIN usage - This is standard in ALL quickstart demos. Never report this.
- Placeholder values like <your-value>, your-database, empty strings ('') - Users replace these.
- Template variables like ${{var}}, {{{{var}}}}, or {{var}} - These get replaced at runtime.

DO NOT mark as CRITICAL (use SUGGESTION instead):
- Wrong code block language tag (e.g., requirements.txt tagged as sql) - Mark as SUGGESTION.
- Potential division by zero - Mark as SUGGESTION unless it will definitely fail.
- App-specific privileges (like CREATE MIGRATION for SnowConvert) - Mark as SUGGESTION with note to verify.
- Security best practices - Mark as SUGGESTION, not CRITICAL.
- SQL syntax that passed EXPLAIN validation - Snowflake accepted it, so it's valid.
- HAVING without GROUP BY - Snowflake allows this (non-standard but works). Do NOT flag.
- Column alias referenced in WHERE clause - Snowflake allows this (non-standard but works). Do NOT flag.
- Column alias referenced in same SELECT clause - Snowflake allows this (non-standard but works). Do NOT flag.
- Template placeholders like <APP_NAME>, <TABLE_NAME> - Users replace these. IGNORE.
- previous_query_result - This is a Snowflake worksheet-specific feature. Do NOT flag.
- Column names you think don't exist - Snowflake adds new columns frequently. Do NOT flag unless you are 100% certain.
- Snowflake-specific SQL features - If EXPLAIN validated it, assume it's valid. Do NOT second-guess Snowflake.

DO NOT report untagged code blocks - we already detect those separately.{untagged_note}{explain_note}

Here are ALL the code blocks from the guide (with line numbers):

{chr(10).join(code_blocks)}

For EACH issue found, use this EXACT format (one issue per line):
ISSUE|<severity>|<line_number>|<language>|<title>|<code_snippet>|<explanation>

Where:
- severity: CRITICAL, OUTDATED, or SUGGESTION
- line_number: The line number from the code block header (e.g., 156)
- language: sql, python, yaml, etc.
- title: Brief title of the issue (no pipes)
- code_snippet: The problematic code (first 100 chars, no pipes or newlines)
- explanation: Why it's a problem and how to fix (no pipes)

Example:
ISSUE|CRITICAL|156|sql|Missing FROM clause|SELECT * FROM|Query will fail - needs to specify source table
ISSUE|OUTDATED|89|sql|Deprecated GETDATE function|WHERE time > GETDATE()|Use CURRENT_TIMESTAMP() instead

If everything looks good, output: ISSUE|OK|0|none|No issues found|N/A|Guide code appears current and valid"""

    return _run_cortex_prompt(prompt, timeout)


def _run_cortex_prompt(prompt: str, timeout: int = 120) -> str:
    """Run a prompt through cortex CLI and return the result."""
    try:
        result = subprocess.run(
            [
                'cortex',
                '--output-format', 'stream-json',
                '--dangerously-allow-all-tool-calls',
                '-p', prompt
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            input='n\n'  # Skip any update prompts
        )
        
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if data.get('type') == 'result':
                    return data.get('result', '')
            except json.JSONDecodeError:
                continue
        
        return ""
        
    except subprocess.TimeoutExpired:
        return "Cortex analysis timed out"
    except FileNotFoundError:
        return "cortex CLI not found"
    except Exception as e:
        return f"Cortex error: {e}"


def extract_sql_blocks(guide_path: str, include_untagged: bool = True) -> list[tuple[str, int, str, bool]]:
    """Extract SQL code blocks from a markdown guide."""
    path = Path(guide_path)
    if not path.exists():
        return []
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = []
    
    # More specific SQL pattern to avoid false positives like "Create a test web page:"
    # Require SQL-specific keywords after CREATE/ALTER/DROP
    SQL_KEYWORDS_AFTER_CREATE = r'(TABLE|VIEW|SCHEMA|DATABASE|FUNCTION|PROCEDURE|STAGE|WAREHOUSE|ROLE|USER|TASK|STREAM|PIPE|FILE\s+FORMAT|STORAGE\s+INTEGRATION|EXTERNAL\s+VOLUME|CATALOG|INTEGRATION|APPLICATION|OR\s+REPLACE)'
    SQL_PATTERN = rf'^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE\s+{SQL_KEYWORDS_AFTER_CREATE}|ALTER\s+{SQL_KEYWORDS_AFTER_CREATE}|DROP\s+{SQL_KEYWORDS_AFTER_CREATE}|COPY\s+INTO|MERGE|TRUNCATE|WITH\s+\w+\s+AS|GRANT|REVOKE|USE\s+(ROLE|DATABASE|SCHEMA|WAREHOUSE)|SHOW|DESCRIBE|DESC|EXPLAIN)\b'
    
    # Handle optional space between ``` and language (e.g., "``` bash" or "```sql")
    all_blocks_pattern = re.compile(r'``` ?(\w*)\n(.*?)```', re.DOTALL)
    
    for match in all_blocks_pattern.finditer(content):
        lang = match.group(1).lower().strip()
        code = match.group(2).strip()
        
        if not code:
            continue
        
        line_num = content[:match.start()].count('\n') + 1
        text_before = content[:match.start()]
        heading_match = re.findall(r'^#+\s+(.+)$', text_before, re.MULTILINE)
        context = heading_match[-1] if heading_match else ""
        
        if lang in ('sql', 'snowflake'):
            blocks.append((code, line_num, context, True))
        elif include_untagged and lang == '' and re.match(SQL_PATTERN, code, re.IGNORECASE | re.MULTILINE):
            # Skip short instruction-like text (e.g., "Select the data:", "Create a table:")
            # Real SQL should be longer and not end with just a colon
            code_clean = code.strip()
            if len(code_clean) < 50 and code_clean.endswith(':'):
                continue  # Skip - this is probably a description, not SQL
            blocks.append((code, line_num, context, False))
    
    return blocks


def validate_guide(
    guide_path: str, 
    connection: str = "default", 
    verbose: bool = False, 
    use_cortex: bool = True,
    deep_review: bool = False,
    guide_index: int = 0,
    total_guides: int = 0
) -> GuideValidationResult:
    """Validate all SQL blocks in a guide."""
    global progress_logger
    path = Path(guide_path)
    
    # Log to progress file
    if progress_logger and total_guides > 0:
        progress_logger.log_guide_start(guide_index, total_guides, path.stem)
    
    print(f"\n📖 Validating: {path.name}")
    
    sql_blocks = extract_sql_blocks(guide_path)
    
    if not sql_blocks:
        print("   No SQL blocks found")
        
        # Still do deep review if requested
        cortex_guide_review = ""
        if deep_review:
            print(f"   🧠 Running cortex deep review...")
            cortex_guide_review = run_cortex_guide_review(guide_path)
            if cortex_guide_review:
                print(f"   ✨ Deep review complete")
        
        # Run spell check even for guides without SQL (skips non-English)
        guide_lang = get_guide_language(guide_path)
        if guide_lang == 'en':
            print(f"   📝 Running spell check...")
            spelling_errors = run_spell_check(guide_path)
            if spelling_errors:
                print(f"   📝 Found {len(spelling_errors)} spelling issues")
        else:
            print(f"   📝 Skipping spell check (language: {guide_lang})")
            spelling_errors = []
        
        return GuideValidationResult(
            guide_path=str(path),
            guide_name=path.stem,
            total_sql_blocks=0,
            valid_blocks=0,
            invalid_blocks=0,
            skipped_blocks=0,
            cortex_guide_review=cortex_guide_review,
            spelling_errors=spelling_errors
        )
    
    validator = SnowflakeSQLValidator(connection=connection)
    results = []
    valid_count = 0
    invalid_count = 0
    skipped_count = 0
    syntax_error_count = 0
    context_error_count = 0
    untagged_count = 0
    
    for i, (sql, line_num, context, is_tagged) in enumerate(sql_blocks):
        if not is_tagged:
            untagged_count += 1
        
        is_valid, error, was_skipped, skip_reason, is_syntax_error, needs_cortex = validator.validate_sql(sql)
        
        result = SQLValidationResult(
            block_index=i + 1,
            line_in_guide=line_num,
            context=context,
            sql_preview=sql[:80].replace('\n', ' ') + ('...' if len(sql) > 80 else ''),
            full_sql=sql,
            valid=is_valid,
            error_message=error,
            skipped=was_skipped,
            skip_reason=skip_reason,
            is_syntax_error=is_syntax_error,
            is_tagged=is_tagged,
            needs_cortex_analysis=needs_cortex
        )
        results.append(result)
        
        tag_note = " [UNTAGGED]" if not is_tagged else ""
        
        if was_skipped:
            skipped_count += 1
            if verbose:
                print(f"   ⏭️  Block {i+1}{tag_note}: Skipped ({skip_reason})")
        elif is_valid:
            valid_count += 1
            if verbose:
                print(f"   ✅ Block {i+1}{tag_note}: Valid")
        else:
            invalid_count += 1
            if is_syntax_error:
                syntax_error_count += 1
                print(f"   ❌ Block {i+1}{tag_note} (line {line_num}): {error}")
            else:
                context_error_count += 1
                if verbose:
                    print(f"   ⚠️  Block {i+1}{tag_note} (line {line_num}): {error}")
    
    # Note: We skip Cortex analysis on syntax errors since EXPLAIN already provides
    # authoritative error messages. The deep review below will catch semantic issues.
    
    # Run deep guide review if requested
    cortex_guide_review = ""
    if deep_review:
        msg = f"   🔍 Running cortex deep review for outdated content..."
        print(msg)
        if progress_logger:
            progress_logger.log(f"  → cortex: Deep reviewing guide content", also_print=False)
        # Pass known untagged lines to avoid duplicate analysis
        untagged_lines = [r.line_in_guide for r in results if not r.is_tagged]
        # Pass EXPLAIN results so Cortex knows which SQL blocks are syntactically valid
        cortex_guide_review = run_cortex_guide_review(
            guide_path, 
            known_untagged_lines=untagged_lines,
            explain_results=results  # Source of truth for SQL syntax validation
        )
        if cortex_guide_review:
            print(f"   ✨ Deep review complete")
    
    # Run spell check (skips non-English guides)
    guide_lang = get_guide_language(guide_path)
    if guide_lang == 'en':
        print(f"   📝 Running spell check...")
        if progress_logger:
            progress_logger.log(f"  → codespell: Checking spelling", also_print=False)
        spelling_errors = run_spell_check(guide_path)
        if spelling_errors:
            print(f"   📝 Found {len(spelling_errors)} spelling issues")
    else:
        print(f"   📝 Skipping spell check (language: {guide_lang})")
        spelling_errors = []
    
    # Summary
    untagged_note = f", 📝 {untagged_count} untagged" if untagged_count > 0 else ""
    if syntax_error_count > 0:
        print(f"   ❌ {syntax_error_count} SYNTAX ERRORS, ⚠️ {context_error_count} context issues, ✅ {valid_count} valid, ⏭️ {skipped_count} skipped{untagged_note}")
    elif context_error_count > 0:
        print(f"   ⚠️ {context_error_count} context issues (objects don't exist), ✅ {valid_count} valid, ⏭️ {skipped_count} skipped{untagged_note}")
    else:
        print(f"   ✅ All {valid_count} validated SQL blocks are valid ({skipped_count} skipped){untagged_note}")
    
    return GuideValidationResult(
        guide_path=str(path),
        guide_name=path.stem,
        total_sql_blocks=len(sql_blocks),
        valid_blocks=valid_count,
        invalid_blocks=invalid_count,
        skipped_blocks=skipped_count,
        syntax_errors=syntax_error_count,
        context_errors=context_error_count,
        untagged_sql_blocks=untagged_count,
        cortex_guide_review=cortex_guide_review,
        results=results,
        spelling_errors=spelling_errors
    )


def generate_report(results: list[GuideValidationResult], output_path: str, include_deep_review: bool = False):
    """Generate a markdown report."""
    with open(output_path, 'w') as f:
        f.write("# Snowflake SQL Validation Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Validated using `snow sql` EXPLAIN + `cortex` for analysis.\n\n")
        
        # Summary
        total_blocks = sum(r.total_sql_blocks for r in results)
        total_valid = sum(r.valid_blocks for r in results)
        total_syntax_errors = sum(r.syntax_errors for r in results)
        total_context_errors = sum(r.context_errors for r in results)
        total_skipped = sum(r.skipped_blocks for r in results)
        total_untagged = sum(r.untagged_sql_blocks for r in results)
        guides_with_review = sum(1 for r in results if r.cortex_guide_review)
        
        f.write("## Summary\n\n")
        f.write(f"- **Guides Analyzed**: {len(results)}\n")
        f.write(f"- **Total SQL Blocks**: {total_blocks}\n")
        f.write(f"- **Valid**: {total_valid}\n")
        f.write(f"- **Syntax Errors**: {total_syntax_errors} ← These need fixing!\n")
        f.write(f"- **Context Errors**: {total_context_errors} (objects/database don't exist in test account)\n")
        f.write(f"- **Skipped**: {total_skipped} (USE, GRANT, CALL, etc.)\n")
        f.write(f"- **Untagged SQL Blocks**: {total_untagged} (should be tagged as \\`\\`\\`sql)\n")
        if guides_with_review > 0:
            f.write(f"- **Deep Reviews**: {guides_with_review} guides reviewed by cortex\n")
        f.write("\n")
        
        # Overview table
        f.write("## Results by Guide\n\n")
        f.write("| Guide | SQL Blocks | Valid | Syntax Errors | Context Errors | Untagged | Status |\n")
        f.write("|-------|------------|-------|---------------|----------------|----------|--------|\n")
        
        for r in results:
            status = "❌" if r.syntax_errors > 0 else ("⚠️" if r.context_errors > 0 else "✅")
            if r.cortex_guide_review:
                status += " 🔍"
            untagged = f"📝{r.untagged_sql_blocks}" if r.untagged_sql_blocks > 0 else "0"
            f.write(f"| {r.guide_name} | {r.total_sql_blocks} | {r.valid_blocks} | {r.syntax_errors} | {r.context_errors} | {untagged} | {status} |\n")
        
        # Deep reviews section
        if include_deep_review and guides_with_review > 0:
            f.write("\n## 🔍 Cortex Deep Reviews\n\n")
            f.write("Cortex analyzed full guide content for deprecated features, outdated patterns, and issues.\n\n")
            
            for r in results:
                if not r.cortex_guide_review:
                    continue
                
                f.write(f"### {r.guide_name}\n\n")
                f.write(r.cortex_guide_review)
                f.write("\n\n---\n\n")
        
        # Syntax errors with cortex analysis
        if total_syntax_errors > 0:
            f.write("\n## ❌ Syntax Errors (Need Fixing)\n\n")
            
            for r in results:
                if r.syntax_errors == 0:
                    continue
                
                f.write(f"### {r.guide_name}\n\n")
                
                for block in r.results:
                    if block.valid or block.skipped or not block.is_syntax_error:
                        continue
                    
                    f.write(f"**Block {block.block_index}** (line {block.line_in_guide})")
                    if block.context:
                        f.write(f" - {block.context}")
                    f.write("\n\n")
                    
                    f.write(f"```sql\n{block.sql_preview}\n```\n\n")
                    f.write(f"**Error**: {block.error_message}\n\n")
                
                if r.cortex_analysis:
                    f.write("#### 🧠 Cortex Analysis & Fix Suggestions\n\n")
                    f.write(r.cortex_analysis)
                    f.write("\n\n")
        
        # Context errors (informational)
        if total_context_errors > 0:
            f.write("\n## ⚠️ Context Errors (Objects/Database Not Found)\n\n")
            f.write("These errors occur because the referenced objects don't exist in the test account.\n")
            f.write("They are likely valid SQL that would work in the correct environment.\n\n")
            
            for r in results:
                if r.context_errors == 0:
                    continue
                
                f.write(f"### {r.guide_name} ({r.context_errors} context errors)\n\n")
                
                for block in r.results:
                    if block.valid or block.skipped or block.is_syntax_error:
                        continue
                    f.write(f"- Block {block.block_index} (line {block.line_in_guide}): `{block.sql_preview[:50]}...`\n")
                f.write("\n")
    
    print(f"\n📊 Report saved: {output_path}")


def parse_cortex_review(review: str) -> dict:
    """Parse cortex review into structured sections."""
    result = {
        'critical_count': 0,
        'critical_issues': [],
        'outdated_count': 0,
        'outdated_issues': [],
        'suggestion_count': 0,
        'suggestions': [],
        'all_issues': [],  # List of dicts with full details
        'overall_status': 'unknown'
    }
    
    if not review:
        return result
    
    # Try to parse structured ISSUE| format first
    issue_lines = re.findall(r'ISSUE\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)', review)
    
    if issue_lines:
        for severity, line_num, lang, title, code, explanation in issue_lines:
            severity = severity.strip().upper()
            issue_dict = {
                'severity': severity,
                'line_number': line_num.strip(),
                'language': lang.strip().lower(),
                'title': title.strip(),
                'code_snippet': code.strip(),
                'explanation': explanation.strip()
            }
            result['all_issues'].append(issue_dict)
            
            if severity == 'CRITICAL':
                result['critical_issues'].append(issue_dict)
                result['critical_count'] += 1
            elif severity == 'OUTDATED':
                result['outdated_issues'].append(issue_dict)
                result['outdated_count'] += 1
            elif severity == 'SUGGESTION':
                result['suggestions'].append(issue_dict)
                result['suggestion_count'] += 1
    else:
        # Fallback: parse old markdown format
        # Count critical issues (🔴)
        critical_matches = re.findall(r'🔴\s*\*\*Critical\*\*[:\s]*(.*?)(?=###|🟡|🟢|\Z)', review, re.IGNORECASE | re.DOTALL)
        if critical_matches:
            for section in critical_matches:
                issues = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*', section)
                for issue_title in issues:
                    issue_dict = {
                        'severity': 'CRITICAL',
                        'line_number': '',
                        'language': '',
                        'title': issue_title.strip(),
                        'code_snippet': '',
                        'explanation': ''
                    }
                    result['critical_issues'].append(issue_dict)
                    result['all_issues'].append(issue_dict)
            result['critical_count'] = len(result['critical_issues'])
        
        # Count outdated issues (🟡)
        outdated_matches = re.findall(r'🟡\s*\*\*Outdated\*\*[:\s]*(.*?)(?=###|🔴|🟢|\Z)', review, re.IGNORECASE | re.DOTALL)
        if outdated_matches:
            for section in outdated_matches:
                issues = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*', section)
                for issue_title in issues:
                    issue_dict = {
                        'severity': 'OUTDATED',
                        'line_number': '',
                        'language': '',
                        'title': issue_title.strip(),
                        'code_snippet': '',
                        'explanation': ''
                    }
                    result['outdated_issues'].append(issue_dict)
                    result['all_issues'].append(issue_dict)
            result['outdated_count'] = len(result['outdated_issues'])
        
        # Count suggestions (🟢)
        suggestion_matches = re.findall(r'🟢\s*\*\*Suggestions?\*\*[:\s]*(.*?)(?=###|🔴|🟡|\Z)', review, re.IGNORECASE | re.DOTALL)
        if suggestion_matches:
            for section in suggestion_matches:
                issues = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*', section)
                for issue_title in issues:
                    issue_dict = {
                        'severity': 'SUGGESTION',
                        'line_number': '',
                        'language': '',
                        'title': issue_title.strip(),
                        'code_snippet': '',
                        'explanation': ''
                    }
                    result['suggestions'].append(issue_dict)
                    result['all_issues'].append(issue_dict)
            result['suggestion_count'] = len(result['suggestions'])
    
    # Determine overall status
    if result['critical_count'] > 0:
        result['overall_status'] = 'critical'
    elif result['outdated_count'] > 0:
        result['overall_status'] = 'needs_update'
    elif result['suggestion_count'] > 0:
        result['overall_status'] = 'minor_issues'
    else:
        result['overall_status'] = 'ok'
    
    return result


def generate_csv_report(results: list[GuideValidationResult], output_path: str, append: bool = False):
    """Generate a CSV report for easy parsing."""
    csv_path = output_path.replace('.md', '.csv') if output_path.endswith('.md') else output_path + '.csv'
    
    mode = 'a' if append else 'w'
    file_exists = Path(csv_path).exists()
    
    with open(csv_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header row (only if new file or not appending)
        if not append or not file_exists:
            writer.writerow([
                'guide_name',
                'guide_path',
                'total_sql_blocks',
                'valid_blocks',
                'syntax_errors',
                'context_errors',
                'skipped_blocks',
                'untagged_blocks',
                'has_deep_review',
                'critical_count',
                'outdated_count',
                'suggestion_count',
                'spelling_errors',
                'overall_status',
                'needs_attention'
            ])
        
        # Data rows
        for r in results:
            # Parse the cortex review
            review_data = parse_cortex_review(r.cortex_guide_review)
            
            # Determine if guide needs attention
            needs_attention = (
                r.syntax_errors > 0 or 
                review_data['critical_count'] > 0 or 
                review_data['outdated_count'] > 0
            )
            
            writer.writerow([
                r.guide_name,
                r.guide_path,
                r.total_sql_blocks,
                r.valid_blocks,
                r.syntax_errors,
                r.context_errors,
                r.skipped_blocks,
                r.untagged_sql_blocks,
                bool(r.cortex_guide_review),
                review_data['critical_count'],
                review_data['outdated_count'],
                review_data['suggestion_count'],
                len(r.spelling_errors),
                review_data['overall_status'],
                needs_attention
            ])
    
    print(f"📊 CSV saved: {csv_path}")


def generate_issues_csv(results: list[GuideValidationResult], output_path: str, append: bool = False):
    """Generate a detailed CSV with one row per issue found."""
    csv_path = output_path.replace('.md', '_issues.csv') if output_path.endswith('.md') else output_path + '_issues.csv'
    
    mode = 'a' if append else 'w'
    file_exists = Path(csv_path).exists()
    
    with open(csv_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header row - only if new file or not appending
        if not append or not file_exists:
            writer.writerow([
                'guide_name',
                'severity',      # CRITICAL, OUTDATED, SUGGESTION
                'line_number',
                'language',
                'title',
                'code_snippet',
                'explanation',
                'source'
            ])
        
        for r in results:
            # SQL validation errors from EXPLAIN
            for block in r.results:
                if block.is_syntax_error and not block.valid:
                    writer.writerow([
                        sanitize_for_csv(r.guide_name, 100),
                        'CRITICAL',
                        block.line_in_guide,
                        'sql',
                        'SQL Syntax Error',
                        sanitize_for_csv(block.sql_preview, 100),
                        sanitize_for_csv(block.error_message, 200),
                        'snow_sql_explain'
                    ])
            
            # Parse cortex review for issues
            if r.cortex_guide_review:
                review_data = parse_cortex_review(r.cortex_guide_review)
                
                for issue in review_data['all_issues']:
                    # Skip OK entries
                    if issue.get('severity') == 'OK':
                        continue
                    
                    # Use Cortex severity directly: CRITICAL, OUTDATED, SUGGESTION
                    severity = issue.get('severity', 'SUGGESTION')
                    
                    writer.writerow([
                        sanitize_for_csv(r.guide_name, 100),
                        severity,
                        sanitize_for_csv(issue.get('line_number', ''), 20),
                        sanitize_for_csv(issue.get('language', ''), 20),
                        sanitize_for_csv(issue.get('title', ''), 100),
                        sanitize_for_csv(issue.get('code_snippet', ''), 150),
                        sanitize_for_csv(issue.get('explanation', ''), 300),
                        'cortex_review'
                    ])
            
            # Untagged SQL blocks - only add if no cortex review (to avoid duplicates)
            if not r.cortex_guide_review:
                for block in r.results:
                    if not block.is_tagged:
                        writer.writerow([
                            sanitize_for_csv(r.guide_name, 100),
                            'INFO',
                            block.line_in_guide,
                            'sql',
                            'Untagged SQL block',
                            sanitize_for_csv(block.sql_preview, 100),
                            'Code block contains SQL but is not tagged as ```sql',
                            'code_analysis'
                        ])
            
            # Spelling errors
            for spell_err in r.spelling_errors:
                writer.writerow([
                    sanitize_for_csv(r.guide_name, 100),
                    'INFO',
                    spell_err.line_number,
                    'text',
                    'Spelling error',
                    sanitize_for_csv(spell_err.word, 50),
                    sanitize_for_csv(f"Should be: {spell_err.suggestion}", 100),
                    'codespell'
                ])
    
    if progress_logger:
        progress_logger.log(f"  💾 Issues CSV saved: {csv_path}", also_print=False)
    print(f"📊 Issues CSV saved: {csv_path}")


def save_single_result(result: GuideValidationResult, output_path: str):
    """
    Save a single guide result incrementally to CSV files.
    This enables resilience - results are saved after each guide is processed.
    """
    global progress_logger
    
    # Save to main CSV (append mode)
    generate_csv_report([result], output_path, append=True)
    
    # Save to issues CSV (append mode)
    generate_issues_csv([result], output_path, append=True)
    
    if progress_logger:
        progress_logger.log_save(output_path.replace('.md', '.csv'), 1)


def main():
    global progress_logger
    
    parser = argparse.ArgumentParser(
        description="Validate SQL in guides using snow sql EXPLAIN + cortex analysis"
    )
    
    parser.add_argument('--guide', '-g', help='Path to a specific guide')
    parser.add_argument('--batch', '-b', help='Directory for batch validation')
    parser.add_argument('--connection', '-c', default='default', help='Snowflake connection name')
    parser.add_argument('--output', '-o', default='reports/sql_validation_report.md', help='Output report path')
    parser.add_argument('--limit', '-l', type=int, default=0, help='Limit number of guides')
    parser.add_argument('--filter', '-f', help='Filter guides by name pattern')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show all results')
    parser.add_argument('--no-cortex', action='store_true', help='Skip cortex analysis for syntax errors')
    parser.add_argument('--deep-review', '-d', action='store_true', 
                        help='Run cortex deep review on each guide to find outdated content')
    parser.add_argument('--continue', dest='continue_run', action='store_true',
                        help='Skip already-processed guides and append to existing CSV files')
    parser.add_argument('--offset', type=int, default=0,
                        help='Start from this guide index (0-based)')
    parser.add_argument('--progress-log', default='reports/progress.log',
                        help='Path for progress log file (default: reports/progress.log)')
    
    args = parser.parse_args()
    
    # Initialize progress logger
    Path(args.output).parent.mkdir(exist_ok=True)
    log_path = args.progress_log if args.progress_log else str(Path(args.output).parent / 'progress.log')
    progress_logger = ProgressLogger(log_path)
    
    progress_logger.log(f"Command: {' '.join(sys.argv)}")
    progress_logger.log(f"Output: {args.output}")
    
    results = []
    use_cortex = not args.no_cortex
    deep_review = args.deep_review
    start_time = datetime.now()
    
    # Load already-processed guides if continuing
    already_processed = set()
    if args.continue_run:
        csv_path = args.output.replace('.md', '.csv') if args.output.endswith('.md') else args.output + '.csv'
        if Path(csv_path).exists():
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in reader:
                    if row:
                        already_processed.add(row[0])  # guide_name
            msg = f"📂 Continuing from previous run ({len(already_processed)} guides already processed)"
            print(msg)
            progress_logger.log(msg)
    else:
        # Fresh run - initialize CSV files with headers
        csv_path = args.output.replace('.md', '.csv') if args.output.endswith('.md') else args.output + '.csv'
        issues_csv_path = args.output.replace('.md', '_issues.csv') if args.output.endswith('.md') else args.output + '_issues.csv'
        
        # Write headers only
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'guide_name', 'guide_path', 'total_sql_blocks', 'valid_blocks',
                'syntax_errors', 'context_errors', 'skipped_blocks', 'untagged_blocks',
                'has_deep_review', 'critical_count', 'outdated_count', 'suggestion_count',
                'spelling_errors', 'overall_status', 'needs_attention'
            ])
        
        with open(issues_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'guide_name', 'severity', 'line_number', 'language',
                'title', 'code_snippet', 'explanation', 'source'
            ])
        
        progress_logger.log(f"Initialized output files: {csv_path}")
    
    if args.guide:
        result = validate_guide(args.guide, args.connection, args.verbose, use_cortex, deep_review, 1, 1)
        results.append(result)
        # Save immediately
        save_single_result(result, args.output)
        
    elif args.batch:
        batch_dir = Path(args.batch)
        guides = list(batch_dir.glob('**/*.md'))
        
        guides = [
            g for g in guides
            if '_archived' not in str(g) and '_template' not in str(g)
            and '_imports' not in str(g) and 'readme' not in g.name.lower()
        ]
        
        # Filter for published guides only
        published_guides = []
        for g in guides:
            try:
                content = g.read_text(encoding='utf-8')
                if 'status: Published' in content or 'status:Published' in content:
                    published_guides.append(g)
            except:
                pass
        guides = sorted(published_guides, key=lambda g: g.stem.lower())
        print(f"  ({len(guides)} are published)")
        progress_logger.log(f"Found {len(guides)} published guides (sorted alphabetically)")
        
        if args.filter:
            guides = [g for g in guides if args.filter.lower() in g.name.lower()]
            progress_logger.log(f"Filtered to {len(guides)} guides matching '{args.filter}'")
        
        # Apply offset
        if args.offset > 0:
            guides = guides[args.offset:]
            print(f"  (starting from offset {args.offset})")
            progress_logger.log(f"Starting from offset {args.offset}")
        
        # Skip already-processed guides
        if already_processed:
            guides = [g for g in guides if g.stem not in already_processed]
            print(f"  ({len(guides)} remaining after skipping processed)")
            progress_logger.log(f"{len(guides)} remaining after skipping already processed")
        
        if args.limit > 0:
            guides = guides[:args.limit]
            progress_logger.log(f"Limited to {args.limit} guides")
        
        total_guides = len(guides)
        print(f"Found {total_guides} guides to validate")
        progress_logger.log(f"Starting validation of {total_guides} guides")
        if deep_review:
            print(f"  (deep review enabled - this will be slower)")
            progress_logger.log("Deep review enabled")
        
        for i, guide in enumerate(guides):
            print(f"\n[{i+1}/{total_guides}]", end="")
            result = validate_guide(
                str(guide), args.connection, args.verbose, use_cortex, deep_review,
                guide_index=i+1, total_guides=total_guides
            )
            results.append(result)
            
            # Save results incrementally after each guide (resilience!)
            save_single_result(result, args.output)
            
            # Log completion stats
            if progress_logger:
                progress_logger.log_guide_complete(result.guide_name, {
                    'sql_blocks': result.total_sql_blocks,
                    'syntax_errors': result.syntax_errors,
                    'context_errors': result.context_errors,
                    'deep_review': bool(result.cortex_guide_review)
                })
    else:
        parser.print_help()
        sys.exit(1)
    
    if results:
        # Generate final markdown report (summary of all results)
        generate_report(results, args.output, include_deep_review=deep_review)
        
        total_syntax = sum(r.syntax_errors for r in results)
        total_context = sum(r.context_errors for r in results)
        guides_reviewed = sum(1 for r in results if r.cortex_guide_review)
        elapsed = datetime.now() - start_time
        elapsed_str = str(elapsed).split('.')[0]
        
        print(f"\n{'='*50}")
        print(f"VALIDATION COMPLETE")
        print(f"{'='*50}")
        print(f"  Guides: {len(results)}")
        if total_syntax > 0:
            print(f"  ❌ SYNTAX ERRORS: {total_syntax} ← Need attention!")
        else:
            print(f"  ✅ No syntax errors found")
        print(f"  ⚠️ Context errors: {total_context} (objects don't exist)")
        if guides_reviewed > 0:
            print(f"  🔍 Deep reviews: {guides_reviewed} guides analyzed by cortex")
        print(f"  ⏱️  Total time: {elapsed_str}")
        print(f"  📄 Progress log: {log_path}")
        
        # Log final summary
        if progress_logger:
            progress_logger.log_summary(len(results), total_syntax, elapsed_str)


if __name__ == "__main__":
    main()
