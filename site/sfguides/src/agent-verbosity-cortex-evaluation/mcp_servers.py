#!/usr/bin/env python3
"""
Config-driven MCP servers for Agent Verbosity Evaluation.
Reads configuration from mcp_config.json and starts servers on specified ports.
"""

import json
import os
import asyncio
import uvicorn
from fastapi import FastAPI
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import wikipedia
import random

# Load configuration
CONFIG_PATH = Path(__file__).parent / "mcp_config.json"

def load_config() -> dict:
    """Load MCP configuration from JSON file."""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

CONFIG = load_config()

# ============================================================
# WikiMCP - Wikipedia Document Retrieval (Port 8531)
# ============================================================
wiki_app = FastAPI(title="WikiMCP", description=CONFIG["mcp_servers"]["WikiMCP"]["description"])

@wiki_app.get("/search")
async def wiki_search(query: str, limit: int = 3):
    """Search Wikipedia articles."""
    try:
        results = wikipedia.search(query, results=limit)
        return {"articles": results, "query": query}
    except Exception as e:
        return {"error": str(e), "articles": []}

@wiki_app.get("/content")
async def wiki_content(title: str):
    """Get article content."""
    try:
        page = wikipedia.page(title)
        return {
            "title": page.title,
            "content": page.content[:5000],
            "summary": page.summary,
            "url": page.url
        }
    except wikipedia.exceptions.DisambiguationError as e:
        return {"error": "disambiguation", "options": e.options[:5]}
    except wikipedia.exceptions.PageError:
        return {"error": "page_not_found", "title": title}
    except Exception as e:
        return {"error": str(e)}

@wiki_app.get("/health")
async def wiki_health():
    return {"status": "healthy", "service": "WikiMCP", "port": CONFIG["mcp_servers"]["WikiMCP"]["port"]}


# ============================================================
# ABTestMCP - A/B Testing Framework (Port 8532)
# ============================================================
ab_app = FastAPI(title="ABTestMCP", description=CONFIG["mcp_servers"]["ABTestMCP"]["description"])

# In-memory experiment storage
experiments = {}
experiment_results = {}

@ab_app.post("/experiment/create")
async def create_experiment(name: str, variants: str, traffic_split: str):
    """Create new A/B experiment.
    
    Args:
        name: Experiment name
        variants: Comma-separated variant names (e.g., "minimal,brief,standard")
        traffic_split: Comma-separated traffic splits (e.g., "0.33,0.33,0.34")
    """
    variant_list = [v.strip() for v in variants.split(",")]
    split_list = [float(s.strip()) for s in traffic_split.split(",")]
    
    if len(variant_list) != len(split_list):
        return {"error": "variants and traffic_split must have same length"}
    
    if abs(sum(split_list) - 1.0) > 0.01:
        return {"error": "traffic_split must sum to 1.0"}
    
    experiments[name] = {
        "variants": variant_list,
        "traffic_split": split_list
    }
    experiment_results[name] = []
    
    return {"status": "created", "experiment": name, "variants": variant_list}

@ab_app.get("/experiment/assign/{name}/{user_id}")
async def assign_variant(name: str, user_id: str):
    """Assign user to experiment variant deterministically."""
    if name not in experiments:
        return {"error": "experiment_not_found", "name": name}
    
    exp = experiments[name]
    
    # Deterministic assignment based on user_id hash
    hash_val = (hash(user_id) % 100) / 100
    cumulative = 0
    
    for variant, split in zip(exp["variants"], exp["traffic_split"]):
        cumulative += split
        if hash_val < cumulative:
            return {"variant": variant, "user_id": user_id, "experiment": name}
    
    return {"variant": exp["variants"][-1], "user_id": user_id, "experiment": name}

@ab_app.post("/experiment/{name}/record")
async def record_result(name: str, user_id: str, metric: str, value: float):
    """Record experiment metric for a user."""
    if name not in experiments:
        return {"error": "experiment_not_found"}
    
    experiment_results[name].append({
        "user_id": user_id,
        "metric": metric,
        "value": value
    })
    
    return {"status": "recorded", "experiment": name, "metric": metric}

@ab_app.get("/experiment/{name}/results")
async def get_results(name: str):
    """Get experiment results summary."""
    if name not in experiments:
        return {"error": "experiment_not_found"}
    
    return {
        "experiment": name,
        "config": experiments[name],
        "results": experiment_results.get(name, []),
        "count": len(experiment_results.get(name, []))
    }

@ab_app.get("/health")
async def ab_health():
    return {"status": "healthy", "service": "ABTestMCP", "port": CONFIG["mcp_servers"]["ABTestMCP"]["port"]}


# ============================================================
# VerbosityMCP - Verbosity Evaluation (Port 8533)
# ============================================================
verbosity_app = FastAPI(title="VerbosityMCP", description=CONFIG["mcp_servers"]["VerbosityMCP"]["description"])

@verbosity_app.post("/evaluate")
async def evaluate_verbosity(response: str, verbosity_level: str):
    """Evaluate if response complies with verbosity constraints."""
    if verbosity_level not in CONFIG["verbosity_levels"]:
        return {"error": f"Unknown verbosity level: {verbosity_level}"}
    
    config = CONFIG["verbosity_levels"][verbosity_level]
    max_lines = config["max_lines"]
    
    lines = response.strip().split("\n")
    line_count = len(lines)
    word_count = len(response.split())
    
    compliant = line_count <= max_lines
    
    return {
        "verbosity_level": verbosity_level,
        "max_lines": max_lines,
        "actual_lines": line_count,
        "word_count": word_count,
        "compliant": compliant,
        "over_by": max(0, line_count - max_lines)
    }

@verbosity_app.get("/compliance")
async def check_compliance(response: str):
    """Check compliance across all verbosity levels."""
    results = {}
    lines = response.strip().split("\n")
    line_count = len(lines)
    
    for level, config in CONFIG["verbosity_levels"].items():
        max_lines = config["max_lines"]
        results[level] = {
            "compliant": line_count <= max_lines,
            "max_lines": max_lines
        }
    
    # Find best matching level
    best_match = None
    for level, config in sorted(CONFIG["verbosity_levels"].items(), key=lambda x: x[1]["max_lines"]):
        if line_count <= config["max_lines"]:
            best_match = level
            break
    
    return {
        "line_count": line_count,
        "compliance": results,
        "best_match": best_match or "verbose"
    }

@verbosity_app.get("/config")
async def get_verbosity_config():
    """Return verbosity configuration."""
    return CONFIG["verbosity_levels"]

@verbosity_app.get("/health")
async def verbosity_health():
    return {"status": "healthy", "service": "VerbosityMCP", "port": CONFIG["mcp_servers"]["VerbosityMCP"]["port"]}


# ============================================================
# Server Runner
# ============================================================
def run_server(app: FastAPI, port: int, name: str):
    """Run a single server."""
    print(f"Starting {name} on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def main():
    """Run all MCP servers (for testing one at a time)."""
    import sys
    
    servers = {
        "WikiMCP": (wiki_app, CONFIG["mcp_servers"]["WikiMCP"]["port"]),
        "ABTestMCP": (ab_app, CONFIG["mcp_servers"]["ABTestMCP"]["port"]),
        "VerbosityMCP": (verbosity_app, CONFIG["mcp_servers"]["VerbosityMCP"]["port"]),
    }
    
    if len(sys.argv) > 1:
        server_name = sys.argv[1]
        if server_name in servers:
            app, port = servers[server_name]
            run_server(app, port, server_name)
        else:
            print(f"Unknown server: {server_name}")
            print(f"Available: {list(servers.keys())}")
    else:
        print("MCP Server Configuration:")
        print("-" * 40)
        for name, (app, port) in servers.items():
            print(f"  {name}: http://localhost:{port}")
        print("-" * 40)
        print("\nUsage: python mcp_servers.py <server_name>")
        print("Example: python mcp_servers.py WikiMCP")


if __name__ == "__main__":
    main()
