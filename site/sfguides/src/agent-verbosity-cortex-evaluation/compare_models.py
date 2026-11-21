"""
Cross-Model Verbosity Comparison Runner

Compares Claude Opus 4 vs Mistral Large 2 across all 8 verbosity levels.
"""

import snowflake.connector
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import json

# Configuration
DATABASE = "FANCYWORKS_DEMO_DB"
SCHEMA = "PUBLIC"

MODELS = {
    "claude": "claude-sonnet-4",
    "mistral": "mistral-large2"
}

VERBOSITY_LEVELS = {
    "minimal": {"max_lines": 1, "description": "1 line max"},
    "brief": {"max_lines": 3, "description": "3 lines max"},
    "standard": {"max_lines": 6, "description": "balanced"},
    "detailed": {"max_lines": 15, "description": "with context"},
    "verbose": {"max_lines": 50, "description": "comprehensive"},
    "code_only": {"max_lines": 20, "description": "code blocks only"},
    "explain": {"max_lines": 20, "description": "why + how"},
    "step_by_step": {"max_lines": 25, "description": "numbered walkthrough"}
}

TEST_QUERIES = [
    {"id": "Q1", "category": "factual", "text": "What is SQL injection?"},
    {"id": "Q2", "category": "code_fix", "text": 'Fix this: session.sql(f"SELECT * FROM users WHERE id={user_id}")'},
    {"id": "Q3", "category": "explanation", "text": "Why is parameterized SQL safer?"},
    {"id": "Q4", "category": "procedural", "text": "How do I set up Snowpark security?"},
    {"id": "Q5", "category": "binary", "text": "Is eval(user_input) safe in Python?"},
]


def get_connection():
    """Get Snowflake connection."""
    return snowflake.connector.connect(connection_name="myaccount")


def call_agent(conn, agent_name: str, query: str) -> Dict[str, Any]:
    """Call a Cortex Agent and return response with metrics."""
    cursor = conn.cursor()
    
    try:
        sql = f"""
        SELECT SNOWFLAKE.CORTEX.AGENT(
            '{DATABASE}.{SCHEMA}.{agent_name}', 
            '{query.replace("'", "''")}'
        )
        """
        cursor.execute(sql)
        response = cursor.fetchone()[0]
        
        lines = response.count('\n') + 1
        words = len(response.split())
        chars = len(response)
        
        return {
            "response": response,
            "line_count": lines,
            "word_count": words,
            "char_count": chars,
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "response": None,
            "line_count": 0,
            "word_count": 0,
            "char_count": 0,
            "success": False,
            "error": str(e)
        }
    finally:
        cursor.close()


def run_comparison(query: Dict, verbosity: str, conn) -> Dict[str, Any]:
    """Run comparison between models for a single query/verbosity combo."""
    results = {
        "query_id": query["id"],
        "query_text": query["text"],
        "category": query["category"],
        "verbosity": verbosity,
        "target_max_lines": VERBOSITY_LEVELS[verbosity]["max_lines"],
        "timestamp": datetime.now().isoformat(),
        "models": {}
    }
    
    for model_key, model_name in MODELS.items():
        agent_name = f"{model_key.upper()}_{verbosity.upper()}_AGENT"
        
        print(f"  Testing {agent_name}...", end=" ")
        result = call_agent(conn, agent_name, query["text"])
        
        result["model"] = model_name
        result["agent"] = agent_name
        result["line_compliant"] = result["line_count"] <= VERBOSITY_LEVELS[verbosity]["max_lines"]
        
        status = "OK" if result["line_compliant"] else f"OVER ({result['line_count']} lines)"
        print(status)
        
        results["models"][model_key] = result
    
    # Determine winner
    claude = results["models"]["claude"]
    mistral = results["models"]["mistral"]
    
    if claude["line_compliant"] and not mistral["line_compliant"]:
        results["winner"] = "claude"
    elif mistral["line_compliant"] and not claude["line_compliant"]:
        results["winner"] = "mistral"
    elif claude["line_count"] < mistral["line_count"]:
        results["winner"] = "claude"
    elif mistral["line_count"] < claude["line_count"]:
        results["winner"] = "mistral"
    else:
        results["winner"] = "tie"
    
    return results


def run_full_comparison() -> List[Dict]:
    """Run full comparison matrix."""
    conn = get_connection()
    all_results = []
    
    print("=" * 70)
    print("CROSS-MODEL VERBOSITY COMPARISON")
    print(f"Models: {', '.join(MODELS.values())}")
    print(f"Verbosity levels: {len(VERBOSITY_LEVELS)}")
    print(f"Test queries: {len(TEST_QUERIES)}")
    print(f"Total tests: {len(VERBOSITY_LEVELS) * len(TEST_QUERIES) * len(MODELS)}")
    print("=" * 70)
    
    for query in TEST_QUERIES:
        for verbosity in VERBOSITY_LEVELS:
            print(f"\n[{query['id']}] {verbosity}: {query['text'][:40]}...")
            
            result = run_comparison(query, verbosity, conn)
            all_results.append(result)
            
            print(f"  Winner: {result['winner']}")
    
    conn.close()
    return all_results


def generate_report(results: List[Dict]) -> str:
    """Generate comparison report."""
    lines = [
        "=" * 70,
        "MODEL COMPARISON REPORT",
        "=" * 70,
        "",
    ]
    
    # Summary stats
    claude_wins = sum(1 for r in results if r["winner"] == "claude")
    mistral_wins = sum(1 for r in results if r["winner"] == "mistral")
    ties = sum(1 for r in results if r["winner"] == "tie")
    
    lines.extend([
        "OVERALL RESULTS",
        "-" * 40,
        f"Claude wins:  {claude_wins}",
        f"Mistral wins: {mistral_wins}",
        f"Ties:         {ties}",
        "",
    ])
    
    # Compliance by model and verbosity
    lines.extend([
        "COMPLIANCE BY VERBOSITY",
        "-" * 40,
    ])
    
    for verbosity in VERBOSITY_LEVELS:
        verb_results = [r for r in results if r["verbosity"] == verbosity]
        
        claude_compliant = sum(1 for r in verb_results if r["models"]["claude"]["line_compliant"])
        mistral_compliant = sum(1 for r in verb_results if r["models"]["mistral"]["line_compliant"])
        total = len(verb_results)
        
        lines.append(f"{verbosity:15} | Claude: {claude_compliant}/{total} | Mistral: {mistral_compliant}/{total}")
    
    lines.extend(["", ""])
    
    # Detailed results by query
    lines.extend([
        "DETAILED RESULTS",
        "-" * 40,
    ])
    
    for result in results:
        claude = result["models"]["claude"]
        mistral = result["models"]["mistral"]
        
        lines.append(f"\n{result['query_id']} | {result['verbosity']} | Target: {result['target_max_lines']} lines")
        lines.append(f"  Claude:  {claude['line_count']} lines, {claude['word_count']} words {'[OK]' if claude['line_compliant'] else '[OVER]'}")
        lines.append(f"  Mistral: {mistral['line_count']} lines, {mistral['word_count']} words {'[OK]' if mistral['line_compliant'] else '[OVER]'}")
        lines.append(f"  Winner:  {result['winner']}")
    
    return "\n".join(lines)


def save_results(results: List[Dict], conn):
    """Save results to Snowflake table."""
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {DATABASE}.{SCHEMA}.MODEL_COMPARISON_RESULTS (
        run_id VARCHAR,
        timestamp TIMESTAMP,
        query_id VARCHAR,
        query_text VARCHAR,
        category VARCHAR,
        verbosity VARCHAR,
        model VARCHAR,
        agent_name VARCHAR,
        response VARCHAR,
        line_count INT,
        word_count INT,
        char_count INT,
        target_max_lines INT,
        line_compliant BOOLEAN,
        winner VARCHAR
    )
    """)
    
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for result in results:
        for model_key, model_data in result["models"].items():
            cursor.execute(f"""
            INSERT INTO {DATABASE}.{SCHEMA}.MODEL_COMPARISON_RESULTS VALUES (
                '{run_id}',
                CURRENT_TIMESTAMP(),
                '{result['query_id']}',
                '{result['query_text'].replace("'", "''")}',
                '{result['category']}',
                '{result['verbosity']}',
                '{model_data['model']}',
                '{model_data['agent']}',
                '{(model_data['response'] or '').replace("'", "''")}',
                {model_data['line_count']},
                {model_data['word_count']},
                {model_data['char_count']},
                {result['target_max_lines']},
                {model_data['line_compliant']},
                '{result['winner']}'
            )
            """)
    
    cursor.close()
    print(f"\nResults saved to {DATABASE}.{SCHEMA}.MODEL_COMPARISON_RESULTS")


if __name__ == "__main__":
    # Run comparison
    results = run_full_comparison()
    
    # Generate and print report
    report = generate_report(results)
    print("\n" + report)
    
    # Save to file
    with open("comparison_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nResults saved to comparison_results.json")
    
    # Optionally save to Snowflake
    # conn = get_connection()
    # save_results(results, conn)
    # conn.close()
