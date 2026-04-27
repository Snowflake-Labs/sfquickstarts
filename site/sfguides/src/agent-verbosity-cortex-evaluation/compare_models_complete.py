"""
Cross-Model Verbosity Comparison - Using CORTEX.COMPLETE
Works without CREATE CORTEX AGENT syntax.
"""

import snowflake.connector
import json
from datetime import datetime
from typing import Dict, List

# Configuration
DATABASE = "FANCYWORKS_DEMO_DB"
SCHEMA = "PUBLIC"
WAREHOUSE = "SNOW_INTELLIGENCE_DEMO_WH"

MODELS = {
    "claude": "claude-3-5-sonnet",
    "mistral": "mistral-large2"
}

VERBOSITY_PROMPTS = {
    "minimal": """You provide absolute minimum responses.
RULES: 1 line maximum. Single word/number when possible. No punctuation unless required. No formatting.""",
    
    "brief": """You provide brief, direct responses.
RULES: Maximum 3 lines. No preamble or postamble. Essential information only.""",
    
    "standard": """You provide balanced responses with appropriate detail.
RULES: 3-6 lines typical. Include context when helpful. Brief explanation with code. Skip obvious details.""",
    
    "detailed": """You provide detailed responses with full context.
STRUCTURE: 1. Issue 2. Location 3. Risk 4. Fix 5. Related considerations.""",
    
    "verbose": """You provide comprehensive, educational responses.
INCLUDE: Full technical context, background, multiple options with tradeoffs, edge cases, best practices, references.""",
    
    "code_only": """You respond with code only, no prose.
RULES: Return ONLY code blocks. No explanatory text. No markdown headers. Comments in code only if essential.""",
    
    "explain": """You explain the "why" and "how" behind everything.
STRUCTURE: What's Happening → Why It Happens → How It Works → Why The Fix Works.""",
    
    "step_by_step": """You provide numbered, sequential walkthroughs.
RULES: Every response is numbered steps. One action per step. Clear completion criteria. Verification checkpoints."""
}

VERBOSITY_MAX_LINES = {
    "minimal": 1,
    "brief": 3,
    "standard": 6,
    "detailed": 15,
    "verbose": 50,
    "code_only": 20,
    "explain": 20,
    "step_by_step": 25
}

TEST_QUERIES = [
    {"id": "Q1", "category": "factual", "text": "What is SQL injection?"},
    {"id": "Q2", "category": "code_fix", "text": "Fix this: session.sql(f\"SELECT * FROM users WHERE id={user_id}\")"},
    {"id": "Q3", "category": "explanation", "text": "Why is parameterized SQL safer?"},
    {"id": "Q4", "category": "binary", "text": "Is eval(user_input) safe in Python?"},
]


def get_connection():
    return snowflake.connector.connect(connection_name="myaccount")


def call_model(conn, model: str, verbosity: str, query: str) -> Dict:
    """Call Cortex COMPLETE with verbosity prompt."""
    cursor = conn.cursor()
    
    system_prompt = VERBOSITY_PROMPTS[verbosity]
    full_prompt = f"{system_prompt}\n\nUser question: {query}"
    
    # Escape single quotes
    full_prompt_escaped = full_prompt.replace("'", "''")
    
    sql = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        '{model}',
        '{full_prompt_escaped}'
    ) AS response
    """
    
    try:
        start = datetime.now()
        cursor.execute(sql)
        response = cursor.fetchone()[0]
        duration = (datetime.now() - start).total_seconds()
        
        lines = response.strip().count('\n') + 1
        words = len(response.split())
        
        return {
            "response": response,
            "line_count": lines,
            "word_count": words,
            "char_count": len(response),
            "duration": duration,
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "response": None,
            "line_count": 0,
            "word_count": 0,
            "char_count": 0,
            "duration": 0,
            "success": False,
            "error": str(e)
        }
    finally:
        cursor.close()


def run_comparison(conn, query: Dict, verbosity: str) -> Dict:
    """Compare models on single query/verbosity."""
    results = {
        "query_id": query["id"],
        "query_text": query["text"],
        "verbosity": verbosity,
        "target_max_lines": VERBOSITY_MAX_LINES[verbosity],
        "models": {}
    }
    
    for model_key, model_name in MODELS.items():
        print(f"    {model_key}...", end=" ", flush=True)
        result = call_model(conn, model_name, verbosity, query["text"])
        result["model"] = model_name
        result["line_compliant"] = result["line_count"] <= VERBOSITY_MAX_LINES[verbosity]
        
        status = "OK" if result["line_compliant"] else f"OVER({result['line_count']})"
        print(f"{status} ({result['duration']:.1f}s)")
        
        results["models"][model_key] = result
    
    # Determine winner
    c = results["models"]["claude"]
    m = results["models"]["mistral"]
    
    if c["line_compliant"] and not m["line_compliant"]:
        results["winner"] = "claude"
    elif m["line_compliant"] and not c["line_compliant"]:
        results["winner"] = "mistral"
    elif c["line_count"] < m["line_count"]:
        results["winner"] = "claude"
    elif m["line_count"] < c["line_count"]:
        results["winner"] = "mistral"
    else:
        results["winner"] = "tie"
    
    return results


def run_full_comparison(verbosities=None, queries=None):
    """Run full comparison matrix."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"USE WAREHOUSE {WAREHOUSE}")
    cursor.close()
    
    verbosities = verbosities or list(VERBOSITY_PROMPTS.keys())
    queries = queries or TEST_QUERIES
    
    print("=" * 60)
    print("CROSS-MODEL VERBOSITY COMPARISON")
    print(f"Models: {', '.join(MODELS.values())}")
    print(f"Verbosity levels: {len(verbosities)}")
    print(f"Queries: {len(queries)}")
    print("=" * 60)
    
    all_results = []
    
    for query in queries:
        print(f"\n[{query['id']}] {query['text'][:50]}...")
        for verbosity in verbosities:
            print(f"  {verbosity}:")
            result = run_comparison(conn, query, verbosity)
            all_results.append(result)
    
    conn.close()
    return all_results


def print_report(results: List[Dict]):
    """Print comparison report."""
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    claude_wins = sum(1 for r in results if r["winner"] == "claude")
    mistral_wins = sum(1 for r in results if r["winner"] == "mistral")
    ties = sum(1 for r in results if r["winner"] == "tie")
    
    print(f"\nOverall: Claude {claude_wins} | Mistral {mistral_wins} | Tie {ties}")
    
    print("\nBy Verbosity Level:")
    print("-" * 40)
    
    for v in VERBOSITY_PROMPTS.keys():
        v_results = [r for r in results if r["verbosity"] == v]
        if not v_results:
            continue
        
        c_ok = sum(1 for r in v_results if r["models"]["claude"]["line_compliant"])
        m_ok = sum(1 for r in v_results if r["models"]["mistral"]["line_compliant"])
        total = len(v_results)
        
        c_avg = sum(r["models"]["claude"]["line_count"] for r in v_results) / total
        m_avg = sum(r["models"]["mistral"]["line_count"] for r in v_results) / total
        
        print(f"{v:15} | Claude: {c_ok}/{total} (avg {c_avg:.1f} lines) | Mistral: {m_ok}/{total} (avg {m_avg:.1f} lines)")
    
    print("\nDetailed Results:")
    print("-" * 40)
    for r in results:
        c = r["models"]["claude"]
        m = r["models"]["mistral"]
        print(f"{r['query_id']} {r['verbosity']:12} | C:{c['line_count']:2} {'OK' if c['line_compliant'] else 'X ':2} | M:{m['line_count']:2} {'OK' if m['line_compliant'] else 'X ':2} | Winner: {r['winner']}")


if __name__ == "__main__":
    # Quick test with minimal subset
    # results = run_full_comparison(verbosities=["minimal", "brief"], queries=TEST_QUERIES[:2])
    
    # Full comparison
    results = run_full_comparison()
    
    print_report(results)
    
    # Save results
    with open("comparison_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nSaved to comparison_results.json")
