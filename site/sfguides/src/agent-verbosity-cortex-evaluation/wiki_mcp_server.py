#!/usr/bin/env python3
"""
MCP Server for Wikipedia Q&A Generation
Exposes Wikipedia fetching and Vine Copula Q&A generation as MCP tools.

Run with: python wiki_mcp_server.py
Default port: 8503
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import numpy as np
from scipy import stats

# Server configuration
MCP_PORT = 8503
SERVER_NAME = "wiki-qa-mcp"
SERVER_VERSION = "1.0.0"

# ============================================================
# Vine Copula Implementation
# ============================================================
class VineCopula:
    def __init__(self, seed=42):
        np.random.seed(seed)
        self.tau = {
            ('factual', 'numerical'): 0.6,
            ('numerical', 'comparison'): 0.4,
            ('comparison', 'causal'): 0.5,
            ('causal', 'list'): 0.3
        }
        self.categories = ['factual', 'numerical', 'comparison', 'causal', 'list']
    
    def sample_category_weights(self, n_questions=5):
        u = np.random.uniform(0, 1, len(self.categories))
        for i in range(1, len(self.categories)):
            pair = (self.categories[i-1], self.categories[i])
            if pair in self.tau:
                rho = np.sin(np.pi * self.tau[pair] / 2)
                z_prev = stats.norm.ppf(np.clip(u[i-1], 0.001, 0.999))
                z_curr = rho * z_prev + np.sqrt(1 - rho**2) * stats.norm.ppf(u[i])
                u[i] = stats.norm.cdf(z_curr)
        
        weights = u / u.sum()
        counts = np.round(weights * n_questions).astype(int)
        while counts.sum() != n_questions:
            if counts.sum() < n_questions:
                counts[np.argmax(weights)] += 1
            else:
                counts[np.argmax(counts)] -= 1
        return dict(zip(self.categories, counts))

# ============================================================
# Wikipedia Fetcher
# ============================================================
class WikiFetcher:
    BASE_URL = "https://en.wikipedia.org/w/api.php"
    HEADERS = {'User-Agent': 'WikiMCPServer/1.0'}
    
    @classmethod
    def fetch_article(cls, title):
        params = {'action': 'query', 'titles': title, 'prop': 'extracts', 
                  'explaintext': True, 'redirects': 1, 'format': 'json'}
        try:
            resp = requests.get(cls.BASE_URL, params=params, headers=cls.HEADERS, timeout=10)
            pages = resp.json().get('query', {}).get('pages', {})
            for pid, page in pages.items():
                if pid != '-1':
                    return {'title': page.get('title', title), 'content': page.get('extract', ''), 'success': True}
            return {'title': title, 'success': False, 'error': 'Not found'}
        except Exception as e:
            return {'title': title, 'success': False, 'error': str(e)}
    
    @classmethod
    def search(cls, query, limit=5):
        params = {'action': 'opensearch', 'search': query, 'limit': limit, 'format': 'json'}
        try:
            data = requests.get(cls.BASE_URL, params=params, headers=cls.HEADERS, timeout=10).json()
            return [{'title': t} for t in data[1]] if len(data) > 1 else []
        except:
            return []

# ============================================================
# Q&A Generator
# ============================================================
class QAGenerator:
    TEMPLATES = {
        'factual': ["What is {topic}?", "Who was involved in {topic}?"],
        'numerical': ["What numbers are associated with {topic}?", "How many aspects of {topic}?"],
        'comparison': ["How does {topic} compare to similar subjects?"],
        'causal': ["Why is {topic} significant?", "What caused events in {topic}?"],
        'list': ["List the main components of {topic}.", "What are key elements of {topic}?"]
    }
    
    def __init__(self):
        self.copula = VineCopula()
    
    def generate(self, article, n=5):
        if not article.get('success'):
            return []
        title, content = article['title'], article['content'][:2000]
        counts = self.copula.sample_category_weights(n)
        questions = []
        for cat, count in counts.items():
            for i in range(count):
                tmpl = self.TEMPLATES[cat][i % len(self.TEMPLATES[cat])]
                questions.append({'question': tmpl.format(topic=title), 'category': cat, 
                                 'context': content[:500], 'article': title})
        return questions

# ============================================================
# MCP Handler
# ============================================================
class MCPHandler(BaseHTTPRequestHandler):
    qa_gen = QAGenerator()
    
    def log_message(self, *args): pass
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path, params = parsed.path, parse_qs(parsed.query)
        
        if path == '/health':
            self._json({'status': 'healthy', 'server': SERVER_NAME, 'version': SERVER_VERSION})
        elif path == '/tools':
            self._json({'tools': ['fetch_article', 'search', 'generate_qa']})
        elif path == '/fetch_article':
            title = params.get('title', [''])[0]
            self._json(WikiFetcher.fetch_article(title) if title else {'error': 'title required'})
        elif path == '/search':
            query = params.get('query', [''])[0]
            self._json({'results': WikiFetcher.search(query)} if query else {'error': 'query required'})
        elif path == '/generate_qa':
            title = params.get('title', [''])[0]
            n = int(params.get('n', ['5'])[0])
            if not title:
                self._json({'error': 'title required'}, 400)
            else:
                article = WikiFetcher.fetch_article(title)
                self._json({'article': title, 'questions': self.qa_gen.generate(article, n), 'copula': 'D-vine'})
        else:
            self._json({'error': 'Unknown', 'endpoints': ['/health', '/tools', '/fetch_article', '/search', '/generate_qa']}, 404)

def run_server(port=MCP_PORT):
    server = HTTPServer(('0.0.0.0', port), MCPHandler)
    print(f"🌐 Wiki MCP Server v{SERVER_VERSION} on http://localhost:{port}")
    print(f"   /health - Health check\n   /tools - List tools\n   /fetch_article?title=X\n   /search?query=X\n   /generate_qa?title=X&n=5")
    server.serve_forever()

if __name__ == "__main__":
    import sys
    run_server(int(sys.argv[1]) if len(sys.argv) > 1 else MCP_PORT)
