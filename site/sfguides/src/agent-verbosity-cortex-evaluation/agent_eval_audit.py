"""
Agent Verbosity Evaluation Audit Loop
Uses LLM-as-judge to evaluate if each agent adheres to its verbosity constraints.
"""
import snowflake.connector
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

DATABASE = "FANCYWORKS_DEMO_DB"
SCHEMA = "PUBLIC"

# Agent definitions with evaluation criteria
AGENTS = {
    "MINIMAL_AGENT": {
        "flag": "--minimal",
        "description": "1 line max, single word/number when possible",
        "criteria": """
        - Response must be 1 line maximum (no line breaks)
        - Single word or very short phrase preferred
        - No formatting, no punctuation unless required
        - No explanations or context
        """,
        "max_lines": 1,
        "max_words": 15
    },
    "BRIEF_AGENT": {
        "flag": "--brief",
        "description": "3 lines max, essential info only",
        "criteria": """
        - Response must be 3 lines or fewer
        - No preamble (e.g., "Sure!", "Of course!")
        - No postamble (e.g., "Let me know if you need more!")
        - Essential information only
        """,
        "max_lines": 3,
        "max_words": 75
    },
    "STANDARD_AGENT": {
        "flag": "--standard",
        "description": "3-6 lines, balanced with context",
        "criteria": """
        - Response should be 3-6 lines typically
        - Includes brief context when helpful
        - Balanced explanation with examples if relevant
        - Skips obvious details
        """,
        "max_lines": 8,
        "max_words": 150
    },
    "DETAILED_AGENT": {
        "flag": "--detailed",
        "description": "Full context with structured sections",
        "criteria": """
        - Includes problem context
        - Uses structured format (numbered points, sections)
        - Explains mechanisms and implications
        - Mentions related considerations
        """,
        "max_lines": 25,
        "max_words": 400
    },
    "VERBOSE_AGENT": {
        "flag": "--verbose",
        "description": "Comprehensive educational response",
        "criteria": """
        - Full technical context and background
        - Multiple sections covering different aspects
        - Edge cases and caveats mentioned
        - References and related patterns included
        - Educational tone with thorough explanations
        """,
        "max_lines": 50,
        "max_words": 800
    },
    "CODE_ONLY_AGENT": {
        "flag": "--code",
        "description": "Code blocks only, no prose",
        "criteria": """
        - Response contains ONLY code blocks
        - No explanatory text outside code blocks
        - No markdown headers or prose
        - Comments within code are acceptable
        """,
        "max_lines": None,
        "max_words": None
    },
    "EXPLAIN_AGENT": {
        "flag": "--explain",
        "description": "Why and how explanations",
        "criteria": """
        - Focuses on understanding, not just facts
        - Explains mechanisms and root causes
        - Uses analogies when helpful
        - Connects to broader concepts
        - Answers "why" and "how" questions
        """,
        "max_lines": 30,
        "max_words": 500
    },
    "STEP_BY_STEP_AGENT": {
        "flag": "--steps",
        "description": "Numbered sequential walkthrough",
        "criteria": """
        - Uses numbered steps (1, 2, 3...)
        - One action per step
        - Clear progression from start to finish
        - Verification checkpoints included
        """,
        "max_lines": 30,
        "max_words": 500
    }
}

# Test query suite covering different scenarios
TEST_QUERIES = [
    {
        "id": "Q1",
        "query": "What is needle in the haystack benchmark?",
        "category": "factual",
        "description": "Tests factual knowledge explanation"
    },
    {
        "id": "Q2", 
        "query": "Is SELECT * FROM users WHERE id = '{user_input}' vulnerable?",
        "category": "security",
        "description": "Tests security analysis response"
    },
    {
        "id": "Q3",
        "query": "How do I connect to Snowflake using Python?",
        "category": "how-to",
        "description": "Tests instructional response"
    },
    {
        "id": "Q4",
        "query": "What causes a deadlock in databases?",
        "category": "conceptual",
        "description": "Tests conceptual explanation"
    },
    {
        "id": "Q5",
        "query": "Fix this: df.filter(col('status') = 'active')",
        "category": "debug",
        "description": "Tests code fix response"
    }
]

# ============================================================================
# JUDGE PROMPT TEMPLATE
# ============================================================================

JUDGE_PROMPT = """You are an expert evaluator assessing if an AI agent's response adheres to its verbosity constraints.

## Agent Being Evaluated
Agent: {agent_name}
Flag: {flag}
Description: {description}

## Verbosity Criteria
{criteria}

## User Query
{query}

## Agent Response
{response}

## Evaluation Task
Evaluate whether the response adheres to the verbosity criteria above.

Rate each dimension from 1-5:
1. **Length Compliance** (1-5): Does the response length match the expected verbosity level?
2. **Format Compliance** (1-5): Does the response follow the expected format/structure?
3. **Content Appropriateness** (1-5): Is the content appropriate for this verbosity level (not too much, not too little)?
4. **Style Adherence** (1-5): Does the response style match expectations (e.g., no preamble for brief, educational for verbose)?

Respond in this exact JSON format:
{{
    "length_compliance": <1-5>,
    "format_compliance": <1-5>,
    "content_appropriateness": <1-5>,
    "style_adherence": <1-5>,
    "overall_pass": <true/false>,
    "reasoning": "<brief explanation of your evaluation>"
}}
"""

# ============================================================================
# EVALUATION FUNCTIONS
# ============================================================================

@dataclass
class EvalResult:
    agent_name: str
    query_id: str
    query: str
    response: str
    length_compliance: int
    format_compliance: int
    content_appropriateness: int
    style_adherence: int
    overall_pass: bool
    reasoning: str
    line_count: int
    word_count: int
    timestamp: str


def count_metrics(text: str) -> Dict[str, int]:
    """Count lines and words in response."""
    lines = len([l for l in text.strip().split('\n') if l.strip()])
    words = len(text.split())
    return {"lines": lines, "words": words}


def call_llm_judge(conn, agent_name: str, query: str, response: str) -> Dict:
    """Use Cortex LLM to judge the response."""
    agent_config = AGENTS[agent_name]
    
    prompt = JUDGE_PROMPT.format(
        agent_name=agent_name,
        flag=agent_config["flag"],
        description=agent_config["description"],
        criteria=agent_config["criteria"],
        query=query,
        response=response
    )
    
    # Use COMPLETE to call the judge LLM
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'claude-3-5-sonnet',
                %s
            ) AS judgment
        """, (prompt,))
        
        result = cursor.fetchone()[0]
        
        # Parse JSON from response
        # Handle potential markdown code blocks in response
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
            
        return json.loads(result.strip())
    except Exception as e:
        return {
            "length_compliance": 0,
            "format_compliance": 0,
            "content_appropriateness": 0,
            "style_adherence": 0,
            "overall_pass": False,
            "reasoning": f"Judge error: {str(e)}"
        }
    finally:
        cursor.close()


def simulate_agent_response(conn, agent_name: str, query: str) -> str:
    """
    Simulate agent response using COMPLETE with the agent's instructions.
    (Since agents require REST API, we simulate using COMPLETE with same prompts)
    """
    agent_config = AGENTS[agent_name]
    
    system_prompt = f"""You are {agent_name}. {agent_config['description']}.

Rules:
{agent_config['criteria']}

Respond to the user's query following these rules exactly."""

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large2',
                ARRAY_CONSTRUCT(
                    OBJECT_CONSTRUCT('role', 'system', 'content', %s),
                    OBJECT_CONSTRUCT('role', 'user', 'content', %s)
                ),
                OBJECT_CONSTRUCT('temperature', 0.3)
            ) AS response
        """, (system_prompt, query))
        
        result = cursor.fetchone()[0]
        # Parse the response
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                return parsed.get('choices', [{}])[0].get('messages', parsed.get('message', result))
            except:
                return result
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cursor.close()


def run_audit_loop(conn) -> List[EvalResult]:
    """Run the full audit loop across all agents and queries."""
    results = []
    total_tests = len(AGENTS) * len(TEST_QUERIES)
    current_test = 0
    
    print(f"\n{'='*80}")
    print(f"AGENT VERBOSITY AUDIT LOOP")
    print(f"Testing {len(AGENTS)} agents x {len(TEST_QUERIES)} queries = {total_tests} evaluations")
    print(f"{'='*80}\n")
    
    for agent_name in AGENTS:
        print(f"\n{'─'*60}")
        print(f"Testing: {agent_name} ({AGENTS[agent_name]['flag']})")
        print(f"{'─'*60}")
        
        for test_case in TEST_QUERIES:
            current_test += 1
            query_id = test_case["id"]
            query = test_case["query"]
            
            print(f"\n  [{current_test}/{total_tests}] {query_id}: {query[:50]}...")
            
            # Get agent response (simulated)
            response = simulate_agent_response(conn, agent_name, query)
            metrics = count_metrics(response)
            
            print(f"    Response: {metrics['lines']} lines, {metrics['words']} words")
            
            # Judge the response
            judgment = call_llm_judge(conn, agent_name, query, response)
            
            result = EvalResult(
                agent_name=agent_name,
                query_id=query_id,
                query=query,
                response=response,
                length_compliance=judgment.get("length_compliance", 0),
                format_compliance=judgment.get("format_compliance", 0),
                content_appropriateness=judgment.get("content_appropriateness", 0),
                style_adherence=judgment.get("style_adherence", 0),
                overall_pass=judgment.get("overall_pass", False),
                reasoning=judgment.get("reasoning", ""),
                line_count=metrics["lines"],
                word_count=metrics["words"],
                timestamp=datetime.now().isoformat()
            )
            
            status = "✓ PASS" if result.overall_pass else "✗ FAIL"
            avg_score = (result.length_compliance + result.format_compliance + 
                        result.content_appropriateness + result.style_adherence) / 4
            print(f"    {status} (avg score: {avg_score:.1f}/5)")
            
            results.append(result)
    
    return results


def generate_audit_report(results: List[EvalResult]) -> str:
    """Generate a summary audit report."""
    report = []
    report.append("\n" + "="*80)
    report.append("AUDIT REPORT SUMMARY")
    report.append("="*80)
    
    # Overall stats
    total = len(results)
    passed = sum(1 for r in results if r.overall_pass)
    report.append(f"\nOverall: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
    
    # Per-agent breakdown
    report.append("\n" + "-"*60)
    report.append("PER-AGENT RESULTS")
    report.append("-"*60)
    
    for agent_name in AGENTS:
        agent_results = [r for r in results if r.agent_name == agent_name]
        agent_passed = sum(1 for r in agent_results if r.overall_pass)
        avg_scores = {
            "length": sum(r.length_compliance for r in agent_results) / len(agent_results),
            "format": sum(r.format_compliance for r in agent_results) / len(agent_results),
            "content": sum(r.content_appropriateness for r in agent_results) / len(agent_results),
            "style": sum(r.style_adherence for r in agent_results) / len(agent_results)
        }
        
        status = "✓" if agent_passed == len(agent_results) else "○" if agent_passed > 0 else "✗"
        report.append(f"\n{status} {agent_name}: {agent_passed}/{len(agent_results)} passed")
        report.append(f"   Scores - Length: {avg_scores['length']:.1f}, Format: {avg_scores['format']:.1f}, "
                     f"Content: {avg_scores['content']:.1f}, Style: {avg_scores['style']:.1f}")
    
    # Failed tests detail
    failed = [r for r in results if not r.overall_pass]
    if failed:
        report.append("\n" + "-"*60)
        report.append("FAILED TESTS")
        report.append("-"*60)
        for r in failed:
            report.append(f"\n  {r.agent_name} | {r.query_id}")
            report.append(f"    Query: {r.query[:50]}...")
            report.append(f"    Reason: {r.reasoning[:100]}...")
    
    report.append("\n" + "="*80)
    
    return "\n".join(report)


def save_results_to_snowflake(conn, results: List[EvalResult]):
    """Save audit results to a Snowflake table."""
    cursor = conn.cursor()
    try:
        # Create results table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DATABASE}.{SCHEMA}.AGENT_EVAL_RESULTS (
                eval_id STRING,
                agent_name STRING,
                query_id STRING,
                query STRING,
                response STRING,
                length_compliance INT,
                format_compliance INT,
                content_appropriateness INT,
                style_adherence INT,
                overall_pass BOOLEAN,
                reasoning STRING,
                line_count INT,
                word_count INT,
                eval_timestamp TIMESTAMP_NTZ
            )
        """)
        
        # Insert results
        for r in results:
            cursor.execute(f"""
                INSERT INTO {DATABASE}.{SCHEMA}.AGENT_EVAL_RESULTS
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"{r.agent_name}_{r.query_id}_{r.timestamp}",
                r.agent_name, r.query_id, r.query, r.response,
                r.length_compliance, r.format_compliance,
                r.content_appropriateness, r.style_adherence,
                r.overall_pass, r.reasoning,
                r.line_count, r.word_count, r.timestamp
            ))
        
        print(f"\n✓ Results saved to {DATABASE}.{SCHEMA}.AGENT_EVAL_RESULTS")
    finally:
        cursor.close()


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("Connecting to Snowflake...")
    conn = snowflake.connector.connect(connection_name="myaccount")
    
    try:
        # Set context
        conn.cursor().execute("USE WAREHOUSE SNOW_INTELLIGENCE_DEMO_WH")
        conn.cursor().execute(f"USE DATABASE {DATABASE}")
        conn.cursor().execute(f"USE SCHEMA {SCHEMA}")
        
        # Run audit loop
        results = run_audit_loop(conn)
        
        # Generate and print report
        report = generate_audit_report(results)
        print(report)
        
        # Save results
        save_results_to_snowflake(conn, results)
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
