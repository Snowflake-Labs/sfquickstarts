#!/usr/bin/env python3
"""
Run All Comparisons - Automated runner for Model Comparison Dashboard
Executes all tabs with default settings and saves results.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import snowflake.connector

# ============== CONFIGURATION ==============

DEFAULTS = {
    "comparison": {
        "verbosities": ["minimal", "brief", "standard"],
        "queries": [
            {"id": "Q1", "text": "What is SQL injection?"},
            {"id": "Q2", "text": "Fix this: session.sql(f\"SELECT * FROM users WHERE id={user_id}\")"}
        ]
    },
    "wiki": {
        "articles": ["The_Lord_of_the_Rings", "New_England_Patriots", "Apollo_program"],
        "n_questions": 8,
        "verbosities": ["minimal", "brief"]
    },
    "persona": {
        "domains": ["shakespeare", "worldcup", "finance"],
        "personas": ["5th_grade", "compute"],
        "n_questions": 4
    },
    "agent": {
        "agents": ["MINIMAL", "BRIEF", "STANDARD", "CODE_ONLY"],
        "queries": [
            {"id": "SEC1", "text": "Is this safe: session.sql(f\"SELECT * FROM users WHERE id={user_id}\")?"},
            {"id": "SEC2", "text": "What's wrong with: eval(user_input)?"},
            {"id": "SEC3", "text": "Fix this SQL injection vulnerability"}
        ]
    }
}

MODELS = {
    "claude": "claude-3-5-sonnet",
    "mistral": "mistral-large2"
}

VERBOSITY_MAX_LINES = {
    "minimal": 1, "brief": 3, "standard": 6, "detailed": 15,
    "verbose": 50, "code_only": 20, "explain": 20, "step_by_step": 25
}

AGENT_MAX_LINES = {
    "MINIMAL": 1, "BRIEF": 3, "STANDARD": 6, "DETAILED": 15,
    "VERBOSE": 50, "CODE_ONLY": 20, "EXPLAIN": 20, "STEP_BY_STEP": 25
}

VERBOSITY_PROMPTS = {
    "minimal": "1 line maximum. Single word/number when possible.",
    "brief": "Maximum 3 lines. No preamble or postamble.",
    "standard": "3-6 lines typical. Include context when helpful."
}

AGENT_PROMPTS = {
    "MINIMAL": "You provide absolute minimum responses. 1 line maximum. Single word/number when possible.",
    "BRIEF": "You provide brief, direct responses. Maximum 3 lines. Essential information only.",
    "STANDARD": "You provide balanced responses. 3-6 lines typical. Include context when helpful.",
    "CODE_ONLY": "You respond with code only, no prose. Return ONLY code blocks."
}

# ============== HELPERS ==============

def get_connection():
    """Get Snowflake connection."""
    conn = snowflake.connector.connect(connection_name='myaccount')
    conn.cursor().execute("USE WAREHOUSE SNOW_INTELLIGENCE_DEMO_WH")
    return conn


def call_model(conn, model: str, prompt: str) -> dict:
    """Call Cortex COMPLETE."""
    cursor = conn.cursor()
    prompt_escaped = prompt.replace("'", "''")
    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{prompt_escaped}') AS response"
    
    try:
        start = datetime.now()
        cursor.execute(sql)
        response = cursor.fetchone()[0]
        duration = (datetime.now() - start).total_seconds()
        
        return {
            "response": response,
            "lines": response.strip().count('\n') + 1,
            "words": len(response.split()),
            "duration": duration,
            "success": True
        }
    except Exception as e:
        return {"response": str(e), "lines": 0, "words": 0, "duration": 0, "success": False}
    finally:
        cursor.close()


def save_results(results: list, filename: str):
    """Save results to JSON file."""
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    filepath = results_dir / filename
    with open(filepath, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"  Saved to {filepath}")


# ============== RUNNERS ==============

def run_comparison(conn) -> list:
    """Run Tab 1: Basic Comparison."""
    print("\n" + "="*60)
    print("TAB 1: RUN COMPARISON")
    print("="*60)
    
    config = DEFAULTS["comparison"]
    results = []
    
    for query in config["queries"]:
        for verbosity in config["verbosities"]:
            row = {
                "query_id": query["id"],
                "query": query["text"],
                "verbosity": verbosity,
                "max_lines": VERBOSITY_MAX_LINES[verbosity]
            }
            
            for model_key, model_name in MODELS.items():
                print(f"  {model_key} | {verbosity} | {query['id']}...", end=" ")
                
                prompt = f"You provide {verbosity} responses. RULES: {VERBOSITY_PROMPTS[verbosity]}\n\nQuestion: {query['text']}"
                result = call_model(conn, model_name, prompt)
                
                row[f"{model_key}_response"] = result["response"]
                row[f"{model_key}_lines"] = result["lines"]
                row[f"{model_key}_compliant"] = result["lines"] <= VERBOSITY_MAX_LINES[verbosity]
                row[f"{model_key}_time"] = result["duration"]
                
                status = "✓" if row[f"{model_key}_compliant"] else f"✗({result['lines']})"
                print(status)
            
            results.append(row)
    
    save_results(results, "comparison_results.json")
    return results


def run_wiki(conn) -> list:
    """Run Tab 4: Wiki Compare."""
    print("\n" + "="*60)
    print("TAB 4: WIKI COMPARE")
    print("="*60)
    
    from wiki_qa_generator import generate_wiki_qa
    
    config = DEFAULTS["wiki"]
    
    print("  Generating Q&A from Wikipedia...")
    qa_pairs = generate_wiki_qa(config["articles"], config["n_questions"])
    print(f"  Generated {len(qa_pairs)} questions")
    
    results = []
    
    for qa in qa_pairs:
        for verbosity in config["verbosities"]:
            row = {
                **qa,
                "verbosity": verbosity,
                "max_lines": VERBOSITY_MAX_LINES[verbosity]
            }
            
            for model_key, model_name in MODELS.items():
                print(f"  {model_key} | {verbosity} | {qa['article'][:15]}...", end=" ")
                
                prompt = f"You provide {verbosity} responses. RULES: {VERBOSITY_PROMPTS[verbosity]}\n\nQuestion: {qa['question']}"
                result = call_model(conn, model_name, prompt)
                
                row[f"{model_key}_response"] = result["response"]
                row[f"{model_key}_lines"] = result["lines"]
                row[f"{model_key}_compliant"] = result["lines"] <= VERBOSITY_MAX_LINES[verbosity]
                row[f"{model_key}_time"] = result["duration"]
                
                status = "✓" if row[f"{model_key}_compliant"] else f"✗({result['lines']})"
                print(status)
            
            results.append(row)
    
    save_results(results, "wiki_results.json")
    return results


def run_persona(conn) -> list:
    """Run Tab 5: Persona Compare."""
    print("\n" + "="*60)
    print("TAB 5: PERSONA COMPARE")
    print("="*60)
    
    from persona_qa_generator import generate_persona_qa, PERSONAS
    
    config = DEFAULTS["persona"]
    
    print("  Generating Q&A from domains...")
    qa_pairs = generate_persona_qa(config["domains"], config["n_questions"])
    print(f"  Generated {len(qa_pairs)} questions")
    
    results = []
    
    for qa in qa_pairs:
        for persona_key in config["personas"]:
            persona = PERSONAS[persona_key]
            
            row = {
                **qa,
                "persona": persona_key,
                "persona_name": persona["name"]
            }
            
            for model_key, model_name in MODELS.items():
                print(f"  {model_key} | {persona_key} | {qa['domain'][:10]}...", end=" ")
                
                prompt = f"{persona['prompt']}\n\nQuestion: {qa['question']}"
                result = call_model(conn, model_name, prompt)
                
                row[f"{model_key}_response"] = result["response"]
                row[f"{model_key}_lines"] = result["lines"]
                row[f"{model_key}_time"] = result["duration"]
                
                print(f"({result['lines']} lines)")
            
            results.append(row)
    
    save_results(results, "persona_results.json")
    return results


def run_agent(conn) -> list:
    """Run Tab 6: Agent Verbosity."""
    print("\n" + "="*60)
    print("TAB 6: AGENT VERBOSITY")
    print("="*60)
    
    config = DEFAULTS["agent"]
    results = []
    
    for query in config["queries"]:
        for agent in config["agents"]:
            row = {
                "query_id": query["id"],
                "query": query["text"],
                "agent": agent,
                "max_lines": AGENT_MAX_LINES[agent]
            }
            
            for model_key, model_name in MODELS.items():
                print(f"  {model_key} | {agent} | {query['id']}...", end=" ")
                
                prompt = f"{AGENT_PROMPTS[agent]}\n\nQuestion: {query['text']}"
                result = call_model(conn, model_name, prompt)
                
                row[f"{model_key}_response"] = result["response"]
                row[f"{model_key}_lines"] = result["lines"]
                row[f"{model_key}_compliant"] = result["lines"] <= AGENT_MAX_LINES[agent]
                row[f"{model_key}_time"] = result["duration"]
                
                status = "✓" if row[f"{model_key}_compliant"] else f"✗({result['lines']})"
                print(status)
            
            results.append(row)
    
    save_results(results, "agent_results.json")
    return results


def run_all_defaults() -> dict:
    """Run all tabs with defaults."""
    conn = get_connection()
    
    all_results = {
        "comparison": run_comparison(conn),
        "wiki": run_wiki(conn),
        "persona": run_persona(conn),
        "agent": run_agent(conn)
    }
    
    conn.close()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for tab, results in all_results.items():
        if results:
            claude_ok = sum(1 for r in results if r.get("claude_compliant", True))
            mistral_ok = sum(1 for r in results if r.get("mistral_compliant", True))
            print(f"  {tab}: {len(results)} tests | Claude: {claude_ok}/{len(results)} | Mistral: {mistral_ok}/{len(results)}")
    
    return all_results


def restart_streamlit():
    """Restart Streamlit dashboard."""
    print("Restarting Streamlit dashboard...")
    
    # Kill existing
    subprocess.run(["pkill", "-f", "streamlit run compare_models_dashboard.py"], 
                   capture_output=True)
    time.sleep(2)
    
    # Start new
    script_dir = Path(__file__).parent
    subprocess.Popen(
        ["streamlit", "run", "compare_models_dashboard.py", 
         "--server.port", "8508", "--server.headless", "true"],
        cwd=script_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print("Dashboard started at http://localhost:8508")
    time.sleep(3)


# ============== MAIN ==============

def main():
    parser = argparse.ArgumentParser(description="Run Model Comparison with defaults")
    parser.add_argument("--all", action="store_true", help="Run all tabs")
    parser.add_argument("--tab", choices=["comparison", "wiki", "persona", "agent"],
                        help="Run specific tab")
    parser.add_argument("--restart", action="store_true", help="Restart Streamlit first")
    parser.add_argument("--streamlit-only", action="store_true", help="Only restart Streamlit")
    
    args = parser.parse_args()
    
    if args.streamlit_only:
        restart_streamlit()
        return
    
    if args.restart:
        restart_streamlit()
    
    conn = get_connection()
    
    if args.tab:
        if args.tab == "comparison":
            run_comparison(conn)
        elif args.tab == "wiki":
            run_wiki(conn)
        elif args.tab == "persona":
            run_persona(conn)
        elif args.tab == "agent":
            run_agent(conn)
    elif args.all:
        run_all_defaults()
    else:
        # Default: run all
        run_all_defaults()
    
    conn.close()


if __name__ == "__main__":
    main()
