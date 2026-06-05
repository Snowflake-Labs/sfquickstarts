#!/usr/bin/env python3
"""
MCP Client for Wiki Q&A Server
Provides health check and API consumption utilities.
"""
import requests
import subprocess
import time
import os
from typing import Optional, List, Dict

MCP_DEFAULT_PORT = 8503
MCP_DEFAULT_URL = f"http://localhost:{MCP_DEFAULT_PORT}"

class WikiMCPClient:
    """Client for Wiki MCP Server with auto-start capability."""
    
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
            print(f"✅ Wiki MCP Server already running at {self.url}")
            return True
        
        print(f"🚀 Starting Wiki MCP Server...")
        
        # Find the server script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        server_script = os.path.join(script_dir, "wiki_mcp_server.py")
        
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
            print(f"✅ Wiki MCP Server started at {self.url}")
            return True
        else:
            print(f"❌ Failed to start Wiki MCP Server")
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
            print("👋 Wiki MCP Server stopped")
    
    # ==================== API Methods ====================
    
    def fetch_article(self, title: str) -> Dict:
        """Fetch a Wikipedia article."""
        if not self.ensure_running():
            return {'error': 'MCP server not available', 'success': False}
        
        try:
            resp = requests.get(f"{self.url}/fetch_article", params={'title': title}, timeout=15)
            return resp.json()
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search Wikipedia articles."""
        if not self.ensure_running():
            return []
        
        try:
            resp = requests.get(f"{self.url}/search", params={'query': query, 'limit': limit}, timeout=10)
            return resp.json().get('results', [])
        except:
            return []
    
    def generate_qa(self, title: str, n_questions: int = 5) -> Dict:
        """Generate Q&A pairs for an article using Vine Copula."""
        if not self.ensure_running():
            return {'error': 'MCP server not available', 'questions': []}
        
        try:
            resp = requests.get(f"{self.url}/generate_qa", params={'title': title, 'n': n_questions}, timeout=20)
            return resp.json()
        except Exception as e:
            return {'error': str(e), 'questions': []}
    
    def generate_qa_batch(self, titles: List[str], n_per_article: int = 5) -> List[Dict]:
        """Generate Q&A for multiple articles."""
        all_questions = []
        for title in titles:
            result = self.generate_qa(title, n_per_article)
            if 'questions' in result:
                all_questions.extend(result['questions'])
        return all_questions


# ==================== Convenience Functions ====================

def check_mcp_server(url: str = MCP_DEFAULT_URL) -> bool:
    """Check if Wiki MCP server is running."""
    client = WikiMCPClient(url, auto_start=False)
    return client.is_up()

def ensure_mcp_server(url: str = MCP_DEFAULT_URL) -> bool:
    """Ensure Wiki MCP server is running, start if needed."""
    client = WikiMCPClient(url, auto_start=True)
    return client.ensure_running()

def get_mcp_client(url: str = MCP_DEFAULT_URL) -> WikiMCPClient:
    """Get a Wiki MCP client instance."""
    return WikiMCPClient(url, auto_start=True)


# ==================== CLI ====================

if __name__ == "__main__":
    import sys
    
    client = WikiMCPClient()
    
    if len(sys.argv) < 2:
        print("Usage: python mcp_client.py <command> [args]")
        print("Commands: health, start, fetch <title>, search <query>, qa <title> [n]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "health":
        result = client.health_check()
        print(f"{'✅' if result['healthy'] else '❌'} {result}")
    
    elif cmd == "start":
        client.start_server()
    
    elif cmd == "fetch" and len(sys.argv) > 2:
        title = sys.argv[2]
        result = client.fetch_article(title)
        print(f"Title: {result.get('title')}")
        print(f"Content: {result.get('content', '')[:500]}...")
    
    elif cmd == "search" and len(sys.argv) > 2:
        query = sys.argv[2]
        results = client.search(query)
        for r in results:
            print(f"  - {r['title']}")
    
    elif cmd == "qa" and len(sys.argv) > 2:
        title = sys.argv[2]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        result = client.generate_qa(title, n)
        print(f"Article: {result.get('article')}")
        print(f"Copula: {result.get('copula')}")
        for q in result.get('questions', []):
            print(f"  [{q['category']}] {q['question']}")
    
    else:
        print(f"Unknown command: {cmd}")
