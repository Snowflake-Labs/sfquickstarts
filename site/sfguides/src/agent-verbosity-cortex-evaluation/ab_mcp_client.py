#!/usr/bin/env python3
"""
MCP Client for A/B Testing Server
Provides agent spawning, A/B test execution, and multi-judge evaluation.
"""
import requests
import subprocess
import time
import os
from typing import Optional, List, Dict

MCP_DEFAULT_PORT = 8517
MCP_DEFAULT_URL = f"http://localhost:{MCP_DEFAULT_PORT}"


class ABTestingMCPClient:
    """Client for A/B Testing MCP Server with auto-start capability."""
    
    def __init__(self, url: str = MCP_DEFAULT_URL, auto_start: bool = True):
        self.url = url.rstrip('/')
        self.auto_start = auto_start
        self._server_process = None
    
    def health_check(self, timeout: float = 2.0) -> Dict:
        """Check if MCP server is healthy."""
        try:
            resp = requests.get(f"{self.url}/health", timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'healthy': data.get('status') == 'healthy',
                    'server': data.get('server'),
                    'version': data.get('version'),
                    'active_agents': data.get('active_agents', 0),
                    'url': self.url
                }
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            return {'healthy': False, 'error': str(e), 'url': self.url}
        
        return {'healthy': False, 'error': 'Connection failed', 'url': self.url}
    
    def is_up(self) -> bool:
        """Quick check if server is up."""
        return self.health_check().get('healthy', False)
    
    def start_server(self, wait: float = 3.0) -> bool:
        """Start the MCP server if not running."""
        if self.is_up():
            print(f"✅ A/B Testing MCP Server already running at {self.url}")
            return True
        
        print(f"🚀 Starting A/B Testing MCP Server...")
        
        # Find the server script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        server_script = os.path.join(script_dir, "ab_mcp_server.py")
        
        if not os.path.exists(server_script):
            print(f"❌ Server script not found: {server_script}")
            return False
        
        # Extract port from URL
        port = MCP_DEFAULT_PORT
        if ':' in self.url.split('/')[-1]:
            try:
                port = int(self.url.split(':')[-1])
            except:
                pass
        
        # Start server
        self._server_process = subprocess.Popen(
            ["python", server_script, str(port)],
            cwd=script_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait for startup
        time.sleep(wait)
        
        if self.is_up():
            print(f"✅ A/B Testing MCP Server started at {self.url}")
            return True
        else:
            print(f"❌ Failed to start A/B Testing MCP Server")
            return False
    
    def ensure_running(self) -> bool:
        """Ensure server is running, start if needed."""
        if self.is_up():
            return True
        if self.auto_start:
            return self.start_server()
        return False
    
    def stop_server(self):
        """Stop the server if we started it."""
        if self._server_process:
            self._server_process.terminate()
            self._server_process = None
            print("👋 A/B Testing MCP Server stopped")
    
    # ==================== Agent Management ====================
    
    def spawn_agent(self, role: str = "responder", model: str = "claude-3-5-sonnet", 
                    system_prompt: str = None) -> Dict:
        """Spawn a new agent."""
        if not self.ensure_running():
            return {'error': 'MCP server not available'}
        
        try:
            resp = requests.post(
                f"{self.url}/spawn_agent",
                json={'role': role, 'model': model, 'system_prompt': system_prompt},
                timeout=10
            )
            return resp.json()
        except Exception as e:
            return {'error': str(e)}
    
    def list_agents(self) -> List[Dict]:
        """List all active agents."""
        if not self.ensure_running():
            return []
        
        try:
            resp = requests.get(f"{self.url}/list_agents", timeout=5)
            return resp.json().get('agents', [])
        except:
            return []
    
    def run_agent(self, agent_id: str, query: str) -> Dict:
        """Run an agent with a query."""
        if not self.ensure_running():
            return {'error': 'MCP server not available'}
        
        try:
            resp = requests.post(
                f"{self.url}/run_agent",
                json={'agent_id': agent_id, 'query': query},
                timeout=60
            )
            return resp.json()
        except Exception as e:
            return {'error': str(e)}
    
    def terminate_agent(self, agent_id: str) -> bool:
        """Terminate an agent."""
        if not self.ensure_running():
            return False
        
        try:
            resp = requests.post(
                f"{self.url}/terminate_agent",
                json={'agent_id': agent_id},
                timeout=5
            )
            return resp.json().get('success', False)
        except:
            return False
    
    # ==================== A/B Testing ====================
    
    def run_ab_test(
        self,
        query: str,
        model_a: str = "claude-3-5-sonnet",
        model_b: str = "mistral-large2",
        judge_model: str = "claude-3-5-sonnet",
        system_prompt_a: str = None,
        system_prompt_b: str = None
    ) -> Dict:
        """Run a single A/B test."""
        if not self.ensure_running():
            return {'error': 'MCP server not available'}
        
        try:
            resp = requests.post(
                f"{self.url}/run_ab_test",
                json={
                    'query': query,
                    'model_a': model_a,
                    'model_b': model_b,
                    'judge_model': judge_model,
                    'system_prompt_a': system_prompt_a,
                    'system_prompt_b': system_prompt_b
                },
                timeout=120
            )
            return resp.json()
        except Exception as e:
            return {'error': str(e)}
    
    def run_batch_ab_test(
        self,
        queries: List[str],
        model_a: str = "claude-3-5-sonnet",
        model_b: str = "mistral-large2",
        judge_model: str = "claude-3-5-sonnet"
    ) -> Dict:
        """Run multiple A/B tests."""
        if not self.ensure_running():
            return {'error': 'MCP server not available', 'results': []}
        
        try:
            resp = requests.post(
                f"{self.url}/run_batch_ab_test",
                json={
                    'queries': queries,
                    'model_a': model_a,
                    'model_b': model_b,
                    'judge_model': judge_model
                },
                timeout=300
            )
            return resp.json()
        except Exception as e:
            return {'error': str(e), 'results': []}
    
    def get_results(self, test_id: str = None) -> List[Dict]:
        """Get test results."""
        if not self.ensure_running():
            return []
        
        try:
            params = {'test_id': test_id} if test_id else {}
            resp = requests.get(f"{self.url}/get_results", params=params, timeout=10)
            return resp.json().get('results', [])
        except:
            return []
    
    def get_statistics(self) -> Dict:
        """Get aggregate statistics."""
        if not self.ensure_running():
            return {'total_tests': 0}
        
        try:
            resp = requests.get(f"{self.url}/get_statistics", timeout=10)
            return resp.json()
        except:
            return {'total_tests': 0}
    
    # ==================== Multi-Judge Evaluation ====================
    
    def multi_judge(
        self,
        query: str,
        response_a: str,
        response_b: str,
        judge_models: List[str] = None
    ) -> Dict:
        """Evaluate responses with multiple judges."""
        if not self.ensure_running():
            return {'error': 'MCP server not available'}
        
        try:
            resp = requests.post(
                f"{self.url}/multi_judge",
                json={
                    'query': query,
                    'response_a': response_a,
                    'response_b': response_b,
                    'judge_models': judge_models
                },
                timeout=120
            )
            return resp.json()
        except Exception as e:
            return {'error': str(e)}


# ==================== Convenience Functions ====================

def check_ab_mcp_server(url: str = MCP_DEFAULT_URL) -> bool:
    """Check if A/B Testing MCP server is running."""
    client = ABTestingMCPClient(url, auto_start=False)
    return client.is_up()

def ensure_ab_mcp_server(url: str = MCP_DEFAULT_URL) -> bool:
    """Ensure A/B Testing MCP server is running, start if needed."""
    client = ABTestingMCPClient(url, auto_start=True)
    return client.ensure_running()

def get_ab_mcp_client(url: str = MCP_DEFAULT_URL) -> ABTestingMCPClient:
    """Get an A/B Testing MCP client instance."""
    return ABTestingMCPClient(url, auto_start=True)


# ==================== CLI ====================

if __name__ == "__main__":
    import sys
    import json as json_module
    
    client = ABTestingMCPClient()
    
    if len(sys.argv) < 2:
        print("Usage: python ab_mcp_client.py <command> [args]")
        print("Commands:")
        print("  health                    - Check server health")
        print("  start                     - Start MCP server")
        print("  agents                    - List active agents")
        print("  spawn <role> <model>      - Spawn new agent")
        print("  run <agent_id> <query>    - Run agent with query")
        print("  ab <query>                - Run A/B test (Claude vs Mistral)")
        print("  stats                     - Get statistics")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "health":
        result = client.health_check()
        status = '✅' if result['healthy'] else '❌'
        print(f"{status} {result}")
    
    elif cmd == "start":
        client.start_server()
    
    elif cmd == "agents":
        agents = client.list_agents()
        print(f"Active agents: {len(agents)}")
        for a in agents:
            print(f"  {a['agent_id']} | {a['role']} | {a['model']} | {a['status']}")
    
    elif cmd == "spawn" and len(sys.argv) >= 3:
        role = sys.argv[2]
        model = sys.argv[3] if len(sys.argv) > 3 else "claude-3-5-sonnet"
        result = client.spawn_agent(role, model)
        print(f"Spawned: {result}")
    
    elif cmd == "run" and len(sys.argv) >= 4:
        agent_id = sys.argv[2]
        query = " ".join(sys.argv[3:])
        result = client.run_agent(agent_id, query)
        print(f"Response: {result.get('response', '')[:500]}")
        print(f"Latency: {result.get('latency', 0):.2f}s")
    
    elif cmd == "ab" and len(sys.argv) >= 3:
        query = " ".join(sys.argv[2:])
        print(f"Running A/B test: {query}")
        result = client.run_ab_test(query)
        if 'result' in result:
            r = result['result']
            print(f"\n🏆 Winner: {r['winner']}")
            print(f"Model A ({r['model_a']}): {r['latency_a']:.2f}s")
            print(f"Model B ({r['model_b']}): {r['latency_b']:.2f}s")
            print(f"\nJudge reasoning:\n{r['judge_reasoning'][:500]}")
        else:
            print(f"Error: {result}")
    
    elif cmd == "stats":
        stats = client.get_statistics()
        print(json_module.dumps(stats, indent=2))
    
    else:
        print(f"Unknown command: {cmd}")
