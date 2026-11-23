#!/usr/bin/env python3
"""
MCP Server for A/B Testing with Agent Spawning
Spawns competing agents to evaluate model performance head-to-head.

Run with: python ab_mcp_server.py
Default port: 8517
"""
import json
import uuid
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import snowflake.connector

# Server configuration
MCP_PORT = 8517
SERVER_NAME = "ab-testing-mcp"
SERVER_VERSION = "1.0.0"

# Agent configuration
MAX_AGENTS = 10
EXECUTOR = ThreadPoolExecutor(max_workers=MAX_AGENTS)


class AgentRole(Enum):
    RESPONDER = "responder"
    EVALUATOR = "evaluator"
    JUDGE = "judge"


class TestType(Enum):
    BLIND_AB = "blind_ab"
    RANKED_PREFERENCE = "ranked_preference"
    ELO_RATING = "elo_rating"


@dataclass
class Agent:
    agent_id: str
    role: str
    model: str
    system_prompt: str
    status: str = "idle"
    created_at: float = 0.0
    last_response: Optional[str] = None
    metrics: Optional[Dict] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ABTestResult:
    test_id: str
    model_a: str
    model_b: str
    query: str
    response_a: str
    response_b: str
    judge_model: str
    winner: str  # "A", "B", or "tie"
    judge_reasoning: str
    scores: Dict
    latency_a: float
    latency_b: float
    timestamp: float
    
    def to_dict(self):
        return asdict(self)


# ============================================================
# Agent Manager
# ============================================================
class AgentManager:
    """Manages spawned agents and their lifecycle."""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self._conn = None
        self._lock = threading.Lock()
        self._conn_lock = threading.Lock()  # Separate lock for connection management
    
    def get_connection(self):
        """Get or create Snowflake connection. Thread-safe with auto-reconnect."""
        with self._conn_lock:
            if self._conn is None:
                self._conn = snowflake.connector.connect(connection_name='myaccount')
                self._conn.cursor().execute("USE WAREHOUSE SNOW_INTELLIGENCE_DEMO_WH")
            return self._conn
    
    def reset_connection(self):
        """Reset connection (call after auth errors). Thread-safe."""
        with self._conn_lock:
            if self._conn:
                try:
                    self._conn.close()
                except:
                    pass
            self._conn = None
    
    def get_fresh_connection(self):
        """Force a fresh connection. Thread-safe."""
        with self._conn_lock:
            if self._conn:
                try:
                    self._conn.close()
                except:
                    pass
            self._conn = snowflake.connector.connect(connection_name='myaccount')
            self._conn.cursor().execute("USE WAREHOUSE SNOW_INTELLIGENCE_DEMO_WH")
            return self._conn
    
    def spawn_agent(self, role: str, model: str, system_prompt: str = None) -> Agent:
        """Spawn a new agent with specified configuration."""
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        default_prompts = {
            "responder": "You are a helpful AI assistant. Provide clear, accurate responses.",
            "evaluator": "You are an AI evaluator. Assess responses for quality, accuracy, and helpfulness.",
            "judge": """You are an impartial judge evaluating AI responses.
Compare two responses and determine which is better based on:
1. Accuracy and correctness
2. Clarity and coherence  
3. Helpfulness and relevance
4. Completeness

Output your verdict as: WINNER: A, WINNER: B, or WINNER: TIE
Then explain your reasoning briefly."""
        }
        
        agent = Agent(
            agent_id=agent_id,
            role=role,
            model=model,
            system_prompt=system_prompt or default_prompts.get(role, ""),
            status="ready",
            created_at=time.time()
        )
        
        with self._lock:
            if len(self.agents) >= MAX_AGENTS:
                # Remove oldest idle agent
                oldest = min(
                    [a for a in self.agents.values() if a.status == "idle"],
                    key=lambda x: x.created_at,
                    default=None
                )
                if oldest:
                    del self.agents[oldest.agent_id]
            
            self.agents[agent_id] = agent
        
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict]:
        return [a.to_dict() for a in self.agents.values()]
    
    def call_model(self, model: str, prompt: str, system_prompt: str = "") -> Dict:
        """Call Cortex COMPLETE with the specified model. Auto-reconnects on auth errors."""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        full_prompt_escaped = full_prompt.replace("'", "''")
        sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{full_prompt_escaped}') AS response"
        
        last_error = None
        # Try up to 2 times (initial + retry after reconnect)
        for attempt in range(2):
            try:
                # On retry, force a fresh connection
                if attempt > 0:
                    conn = self.get_fresh_connection()
                else:
                    conn = self.get_connection()
                
                cursor = conn.cursor()
                start = time.time()
                cursor.execute(sql)
                response = cursor.fetchone()[0]
                duration = time.time() - start
                cursor.close()
                
                return {
                    "response": response,
                    "latency": duration,
                    "success": True,
                    "model": model
                }
            except Exception as e:
                last_error = str(e)
                # Check for auth/token expiry errors - retry once
                if ("390114" in last_error or "Authentication token has expired" in last_error) and attempt == 0:
                    continue
                # Other error or second attempt failed - break out
                break
        
        return {
            "response": last_error or "Max retries exceeded",
            "latency": 0,
            "success": False,
            "model": model,
            "error": last_error or "Max retries exceeded"
        }
    
    def run_agent(self, agent_id: str, query: str) -> Dict:
        """Run an agent with a query."""
        agent = self.get_agent(agent_id)
        if not agent:
            return {"error": f"Agent {agent_id} not found"}
        
        agent.status = "running"
        result = self.call_model(agent.model, query, agent.system_prompt)
        agent.status = "idle"
        agent.last_response = result.get("response")
        agent.metrics = {"latency": result.get("latency", 0)}
        
        return {
            "agent_id": agent_id,
            "role": agent.role,
            "model": agent.model,
            **result
        }
    
    def terminate_agent(self, agent_id: str) -> bool:
        """Terminate an agent."""
        with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                return True
        return False


# ============================================================
# A/B Test Runner
# ============================================================
class ABTestRunner:
    """Runs A/B tests between models using spawned agents."""
    
    def __init__(self, agent_manager: AgentManager):
        self.manager = agent_manager
        self.results: Dict[str, ABTestResult] = {}
        self._lock = threading.Lock()
    
    def run_ab_test(
        self,
        query: str,
        model_a: str,
        model_b: str,
        judge_model: str = "claude-3-5-sonnet",
        system_prompt_a: str = None,
        system_prompt_b: str = None
    ) -> ABTestResult:
        """Run a single A/B test between two models."""
        test_id = f"test_{uuid.uuid4().hex[:8]}"
        
        # Spawn responder agents
        agent_a = self.manager.spawn_agent("responder", model_a, system_prompt_a)
        agent_b = self.manager.spawn_agent("responder", model_b, system_prompt_b)
        
        # Run both agents concurrently
        futures = {}
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures['a'] = executor.submit(self.manager.run_agent, agent_a.agent_id, query)
            futures['b'] = executor.submit(self.manager.run_agent, agent_b.agent_id, query)
        
        result_a = futures['a'].result()
        result_b = futures['b'].result()
        
        response_a = result_a.get("response", "")
        response_b = result_b.get("response", "")
        
        # Spawn judge agent and evaluate
        judge_agent = self.manager.spawn_agent("judge", judge_model)
        judge_prompt = f"""Question: {query}

Response A:
{response_a}

Response B:
{response_b}

Which response is better? Output WINNER: A, WINNER: B, or WINNER: TIE, then explain."""
        
        judge_result = self.manager.run_agent(judge_agent.agent_id, judge_prompt)
        judge_response = judge_result.get("response", "")
        
        # Parse winner
        winner = "tie"
        if "WINNER: A" in judge_response.upper():
            winner = "A"
        elif "WINNER: B" in judge_response.upper():
            winner = "B"
        
        # Calculate scores
        scores = {
            "model_a_latency": result_a.get("latency", 0),
            "model_b_latency": result_b.get("latency", 0),
            "model_a_length": len(response_a),
            "model_b_length": len(response_b),
            "judge_latency": judge_result.get("latency", 0)
        }
        
        test_result = ABTestResult(
            test_id=test_id,
            model_a=model_a,
            model_b=model_b,
            query=query,
            response_a=response_a,
            response_b=response_b,
            judge_model=judge_model,
            winner=winner,
            judge_reasoning=judge_response,
            scores=scores,
            latency_a=result_a.get("latency", 0),
            latency_b=result_b.get("latency", 0),
            timestamp=time.time()
        )
        
        with self._lock:
            self.results[test_id] = test_result
        
        # Cleanup agents
        self.manager.terminate_agent(agent_a.agent_id)
        self.manager.terminate_agent(agent_b.agent_id)
        self.manager.terminate_agent(judge_agent.agent_id)
        
        return test_result
    
    def run_batch_ab_test(
        self,
        queries: List[str],
        model_a: str,
        model_b: str,
        judge_model: str = "claude-3-5-sonnet"
    ) -> List[ABTestResult]:
        """Run multiple A/B tests."""
        results = []
        for query in queries:
            result = self.run_ab_test(query, model_a, model_b, judge_model)
            results.append(result)
        return results
    
    def get_results(self, test_id: str = None) -> List[Dict]:
        """Get test results."""
        if test_id:
            result = self.results.get(test_id)
            return [result.to_dict()] if result else []
        return [r.to_dict() for r in self.results.values()]
    
    def get_statistics(self) -> Dict:
        """Get aggregate statistics from all tests."""
        if not self.results:
            return {"total_tests": 0}
        
        results = list(self.results.values())
        
        wins_a = sum(1 for r in results if r.winner == "A")
        wins_b = sum(1 for r in results if r.winner == "B")
        ties = sum(1 for r in results if r.winner == "tie")
        
        avg_latency_a = sum(r.latency_a for r in results) / len(results)
        avg_latency_b = sum(r.latency_b for r in results) / len(results)
        
        return {
            "total_tests": len(results),
            "model_a_wins": wins_a,
            "model_b_wins": wins_b,
            "ties": ties,
            "model_a_win_rate": wins_a / len(results) if results else 0,
            "model_b_win_rate": wins_b / len(results) if results else 0,
            "avg_latency_a": avg_latency_a,
            "avg_latency_b": avg_latency_b
        }


# ============================================================
# Multi-Judge Evaluation
# ============================================================
class MultiJudgePanel:
    """Run evaluations with multiple judge models for consensus."""
    
    def __init__(self, agent_manager: AgentManager):
        self.manager = agent_manager
    
    def evaluate_with_panel(
        self,
        query: str,
        response_a: str,
        response_b: str,
        judge_models: List[str] = None
    ) -> Dict:
        """Evaluate responses with multiple judges."""
        if judge_models is None:
            judge_models = ["claude-sonnet-4-6", "gpt-5.2"]
        
        judge_prompt = f"""Question: {query}

Response A:
{response_a}

Response B:
{response_b}

Which response is better? Consider accuracy, clarity, helpfulness, and completeness.
Output exactly: WINNER: A, WINNER: B, or WINNER: TIE
Then explain your reasoning in 2-3 sentences."""
        
        verdicts = {}
        futures = {}
        
        with ThreadPoolExecutor(max_workers=len(judge_models)) as executor:
            for model in judge_models:
                agent = self.manager.spawn_agent("judge", model)
                futures[model] = executor.submit(
                    self.manager.run_agent, agent.agent_id, judge_prompt
                )
        
        for model, future in futures.items():
            result = future.result()
            response = result.get("response", "")
            
            winner = "tie"
            if "WINNER: A" in response.upper():
                winner = "A"
            elif "WINNER: B" in response.upper():
                winner = "B"
            
            verdicts[model] = {
                "winner": winner,
                "reasoning": response,
                "latency": result.get("latency", 0)
            }
        
        # Calculate consensus
        winners = [v["winner"] for v in verdicts.values()]
        consensus = max(set(winners), key=winners.count)
        agreement = winners.count(consensus) / len(winners)
        
        return {
            "verdicts": verdicts,
            "consensus": consensus,
            "agreement_rate": agreement,
            "judge_models": judge_models
        }


# ============================================================
# Global instances
# ============================================================
agent_manager = AgentManager()
ab_runner = ABTestRunner(agent_manager)
judge_panel = MultiJudgePanel(agent_manager)


# ============================================================
# MCP Handler
# ============================================================
class MCPHandler(BaseHTTPRequestHandler):
    
    def log_message(self, *args):
        pass
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            return json.loads(self.rfile.read(content_length).decode())
        return {}
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        if path == '/health':
            self._json({
                'status': 'healthy',
                'server': SERVER_NAME,
                'version': SERVER_VERSION,
                'active_agents': len(agent_manager.agents)
            })
        
        elif path == '/tools':
            self._json({
                'tools': [
                    'spawn_agent', 'list_agents', 'run_agent', 'terminate_agent',
                    'run_ab_test', 'run_batch_ab_test', 'get_results', 'get_statistics',
                    'multi_judge'
                ]
            })
        
        elif path == '/list_agents':
            self._json({'agents': agent_manager.list_agents()})
        
        elif path == '/get_results':
            test_id = params.get('test_id', [None])[0]
            self._json({'results': ab_runner.get_results(test_id)})
        
        elif path == '/get_statistics':
            self._json(ab_runner.get_statistics())
        
        else:
            self._json({
                'error': 'Unknown endpoint',
                'endpoints': [
                    'GET /health', 'GET /tools', 'GET /list_agents',
                    'GET /get_results', 'GET /get_statistics',
                    'POST /spawn_agent', 'POST /run_agent', 'POST /terminate_agent',
                    'POST /run_ab_test', 'POST /run_batch_ab_test', 'POST /multi_judge'
                ]
            }, 404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._parse_body()
        
        if path == '/spawn_agent':
            role = body.get('role', 'responder')
            model = body.get('model', 'claude-3-5-sonnet')
            system_prompt = body.get('system_prompt')
            
            agent = agent_manager.spawn_agent(role, model, system_prompt)
            self._json({'agent': agent.to_dict()})
        
        elif path == '/run_agent':
            agent_id = body.get('agent_id')
            query = body.get('query')
            
            if not agent_id or not query:
                self._json({'error': 'agent_id and query required'}, 400)
            else:
                result = agent_manager.run_agent(agent_id, query)
                self._json(result)
        
        elif path == '/terminate_agent':
            agent_id = body.get('agent_id')
            if not agent_id:
                self._json({'error': 'agent_id required'}, 400)
            else:
                success = agent_manager.terminate_agent(agent_id)
                self._json({'success': success, 'agent_id': agent_id})
        
        elif path == '/run_ab_test':
            query = body.get('query')
            model_a = body.get('model_a', 'claude-3-5-sonnet')
            model_b = body.get('model_b', 'mistral-large2')
            judge_model = body.get('judge_model', 'claude-3-5-sonnet')
            system_prompt_a = body.get('system_prompt_a')
            system_prompt_b = body.get('system_prompt_b')
            
            if not query:
                self._json({'error': 'query required'}, 400)
            else:
                result = ab_runner.run_ab_test(
                    query, model_a, model_b, judge_model,
                    system_prompt_a, system_prompt_b
                )
                self._json({'result': result.to_dict()})
        
        elif path == '/run_batch_ab_test':
            queries = body.get('queries', [])
            model_a = body.get('model_a', 'claude-3-5-sonnet')
            model_b = body.get('model_b', 'mistral-large2')
            judge_model = body.get('judge_model', 'claude-3-5-sonnet')
            
            if not queries:
                self._json({'error': 'queries list required'}, 400)
            else:
                results = ab_runner.run_batch_ab_test(queries, model_a, model_b, judge_model)
                self._json({
                    'results': [r.to_dict() for r in results],
                    'statistics': ab_runner.get_statistics()
                })
        
        elif path == '/multi_judge':
            query = body.get('query')
            response_a = body.get('response_a')
            response_b = body.get('response_b')
            judge_models = body.get('judge_models')
            
            if not all([query, response_a, response_b]):
                self._json({'error': 'query, response_a, and response_b required'}, 400)
            else:
                result = judge_panel.evaluate_with_panel(
                    query, response_a, response_b, judge_models
                )
                self._json(result)
        
        else:
            self._json({'error': 'Unknown endpoint'}, 404)


def run_server(port=MCP_PORT):
    server = HTTPServer(('0.0.0.0', port), MCPHandler)
    print(f"🔬 A/B Testing MCP Server v{SERVER_VERSION} on http://localhost:{port}")
    print(f"   Endpoints:")
    print(f"   GET  /health           - Server health")
    print(f"   GET  /tools            - List available tools")
    print(f"   GET  /list_agents      - List active agents")
    print(f"   GET  /get_results      - Get test results")
    print(f"   GET  /get_statistics   - Get aggregate stats")
    print(f"   POST /spawn_agent      - Spawn new agent")
    print(f"   POST /run_agent        - Run agent with query")
    print(f"   POST /terminate_agent  - Terminate agent")
    print(f"   POST /run_ab_test      - Run single A/B test")
    print(f"   POST /run_batch_ab_test - Run batch A/B tests")
    print(f"   POST /multi_judge      - Multi-judge evaluation")
    server.serve_forever()


if __name__ == "__main__":
    import sys
    run_server(int(sys.argv[1]) if len(sys.argv) > 1 else MCP_PORT)
