#!/usr/bin/env python3
"""
Validate MCP servers configuration and endpoints locally.
Tests all MCP servers defined in mcp_config.json.
"""

import json
import requests
import subprocess
import time
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "mcp_config.json"

def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def test_wiki_mcp(base_url: str) -> dict:
    """Test WikiMCP endpoints."""
    results = {"service": "WikiMCP", "tests": []}
    
    # Test /health
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        results["tests"].append({
            "endpoint": "/health",
            "status": "PASS" if r.status_code == 200 else "FAIL",
            "response": r.json()
        })
    except Exception as e:
        results["tests"].append({"endpoint": "/health", "status": "FAIL", "error": str(e)})
    
    # Test /search
    try:
        r = requests.get(f"{base_url}/search", params={"query": "SQL injection", "limit": 2}, timeout=10)
        results["tests"].append({
            "endpoint": "/search",
            "status": "PASS" if r.status_code == 200 and "articles" in r.json() else "FAIL",
            "response": r.json()
        })
    except Exception as e:
        results["tests"].append({"endpoint": "/search", "status": "FAIL", "error": str(e)})
    
    return results

def test_ab_test_mcp(base_url: str) -> dict:
    """Test ABTestMCP endpoints."""
    results = {"service": "ABTestMCP", "tests": []}
    
    # Test /health
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        results["tests"].append({
            "endpoint": "/health",
            "status": "PASS" if r.status_code == 200 else "FAIL",
            "response": r.json()
        })
    except Exception as e:
        results["tests"].append({"endpoint": "/health", "status": "FAIL", "error": str(e)})
    
    # Test create experiment
    try:
        r = requests.post(f"{base_url}/experiment/create", params={
            "name": "verbosity_test",
            "variants": "minimal,brief,standard",
            "traffic_split": "0.33,0.33,0.34"
        }, timeout=5)
        results["tests"].append({
            "endpoint": "/experiment/create",
            "status": "PASS" if r.status_code == 200 else "FAIL",
            "response": r.json()
        })
    except Exception as e:
        results["tests"].append({"endpoint": "/experiment/create", "status": "FAIL", "error": str(e)})
    
    # Test assign variant
    try:
        r = requests.get(f"{base_url}/experiment/assign/verbosity_test/user123", timeout=5)
        results["tests"].append({
            "endpoint": "/experiment/assign",
            "status": "PASS" if r.status_code == 200 and "variant" in r.json() else "FAIL",
            "response": r.json()
        })
    except Exception as e:
        results["tests"].append({"endpoint": "/experiment/assign", "status": "FAIL", "error": str(e)})
    
    return results

def test_verbosity_mcp(base_url: str) -> dict:
    """Test VerbosityMCP endpoints."""
    results = {"service": "VerbosityMCP", "tests": []}
    
    # Test /health
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        results["tests"].append({
            "endpoint": "/health",
            "status": "PASS" if r.status_code == 200 else "FAIL",
            "response": r.json()
        })
    except Exception as e:
        results["tests"].append({"endpoint": "/health", "status": "FAIL", "error": str(e)})
    
    # Test /config
    try:
        r = requests.get(f"{base_url}/config", timeout=5)
        results["tests"].append({
            "endpoint": "/config",
            "status": "PASS" if r.status_code == 200 else "FAIL",
            "response": r.json()
        })
    except Exception as e:
        results["tests"].append({"endpoint": "/config", "status": "FAIL", "error": str(e)})
    
    # Test /evaluate
    try:
        test_response = "SQL injection is a vulnerability.\nIt allows attackers to execute SQL."
        r = requests.post(f"{base_url}/evaluate", params={
            "response": test_response,
            "verbosity_level": "brief"
        }, timeout=5)
        results["tests"].append({
            "endpoint": "/evaluate",
            "status": "PASS" if r.status_code == 200 and "compliant" in r.json() else "FAIL",
            "response": r.json()
        })
    except Exception as e:
        results["tests"].append({"endpoint": "/evaluate", "status": "FAIL", "error": str(e)})
    
    # Test /compliance
    try:
        r = requests.get(f"{base_url}/compliance", params={"response": "Short answer."}, timeout=5)
        results["tests"].append({
            "endpoint": "/compliance",
            "status": "PASS" if r.status_code == 200 and "compliance" in r.json() else "FAIL",
            "response": r.json()
        })
    except Exception as e:
        results["tests"].append({"endpoint": "/compliance", "status": "FAIL", "error": str(e)})
    
    return results

def validate_config():
    """Validate the MCP configuration file."""
    print("=" * 60)
    print("MCP Configuration Validation")
    print("=" * 60)
    
    config = load_config()
    
    print("\n🖥️  Dashboard:")
    print(f"   Port {config['dashboard']['port']}: {config['dashboard']['description']}")
    
    print("\n📋 MCP Servers from config:")
    for name, cfg in config["mcp_servers"].items():
        print(f"   {name}: port {cfg['port']} - {cfg['description']}")
    
    print("\n🤖 Models configured:")
    for name, cfg in config["models"].items():
        thinking = "✓ thinking" if cfg.get("supports_thinking") else ""
        print(f"   {name}: {cfg['model_id']} {thinking}")
    
    print("\n⚖️ Judge models:")
    for name, model_id in config["judge_models"].items():
        print(f"   {name}: {model_id}")
    
    print("\n📊 Verbosity levels:")
    for level, cfg in config["verbosity_levels"].items():
        print(f"   {level}: max {cfg['max_lines']} lines")
    
    return config

def test_servers(config: dict):
    """Test all MCP servers."""
    print("\n" + "=" * 60)
    print("MCP Server Tests (requires servers to be running)")
    print("=" * 60)
    
    all_results = []
    
    for name, cfg in config["mcp_servers"].items():
        port = cfg["port"]
        base_url = f"http://localhost:{port}"
        
        print(f"\n🔍 Testing {name} at {base_url}...")
        
        if name == "WikiMCP":
            results = test_wiki_mcp(base_url)
        elif name == "ABTestMCP":
            results = test_ab_test_mcp(base_url)
        elif name == "VerbosityMCP":
            results = test_verbosity_mcp(base_url)
        else:
            results = {"service": name, "tests": [{"status": "SKIP", "reason": "No test defined"}]}
        
        all_results.append(results)
        
        for test in results["tests"]:
            status = "✅" if test["status"] == "PASS" else "❌"
            print(f"   {status} {test['endpoint']}: {test['status']}")
    
    return all_results

def main():
    """Main validation entry point."""
    config = validate_config()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        results = test_servers(config)
        
        # Summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        
        total_pass = 0
        total_fail = 0
        
        for result in results:
            passes = sum(1 for t in result["tests"] if t["status"] == "PASS")
            fails = sum(1 for t in result["tests"] if t["status"] == "FAIL")
            total_pass += passes
            total_fail += fails
            print(f"   {result['service']}: {passes} passed, {fails} failed")
        
        print(f"\n   Total: {total_pass} passed, {total_fail} failed")
        
        sys.exit(0 if total_fail == 0 else 1)
    else:
        print("\n💡 To test running servers, use: python validate_mcp.py --test")
        print("\n📖 Start servers first:")
        for name, cfg in config["mcp_servers"].items():
            print(f"   python mcp_servers.py {name}")

if __name__ == "__main__":
    main()
