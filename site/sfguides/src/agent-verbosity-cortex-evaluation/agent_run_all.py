#!/usr/bin/env python3
"""
/run_all_comparisons Agent
Invoke with: /run_all_comparisons

This agent restarts the Model Comparison Dashboard and runs all comparison
tabs with default settings.
"""
import sys
import os

# Add the directory to path - uses current directory or environment variable
SCRIPT_DIR = os.environ.get("AGENT_SCRIPT_DIR", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)
os.chdir(SCRIPT_DIR)

def run_agent(args=None):
    """Main agent entry point."""
    from run_all_comparisons import (
        restart_streamlit, 
        run_all_defaults,
        run_comparison,
        run_wiki,
        run_persona,
        run_agent,
        get_connection
    )
    
    args = args or sys.argv[1:]
    
    print("🤖 /run_all_comparisons Agent")
    print("=" * 60)
    
    # Parse simple flags
    streamlit_only = "--streamlit-only" in args
    do_restart = "--restart" in args or len(args) == 0
    tab = None
    
    for i, arg in enumerate(args):
        if arg == "--tab" and i + 1 < len(args):
            tab = args[i + 1]
    
    # Restart Streamlit
    if do_restart or streamlit_only:
        restart_streamlit()
        print("✅ Streamlit restarted at http://localhost:8508")
        
        if streamlit_only:
            return {"status": "streamlit_restarted", "url": "http://localhost:8508"}
    
    # Run comparisons
    if tab:
        print(f"\n🏃 Running tab: {tab}")
        conn = get_connection()
        
        if tab == "comparison":
            results = run_comparison(conn)
        elif tab == "wiki":
            results = run_wiki(conn)
        elif tab == "persona":
            results = run_persona(conn)
        elif tab == "agent":
            results = run_agent(conn)
        else:
            print(f"❌ Unknown tab: {tab}")
            return {"status": "error", "message": f"Unknown tab: {tab}"}
        
        conn.close()
        
        # Summary
        claude_ok = sum(1 for r in results if r.get("claude_compliant", True))
        mistral_ok = sum(1 for r in results if r.get("mistral_compliant", True))
        
        print(f"\n✅ Completed: {len(results)} tests")
        print(f"   Claude: {claude_ok}/{len(results)} compliant")
        print(f"   Mistral: {mistral_ok}/{len(results)} compliant")
        
        return {
            "status": "success",
            "tab": tab,
            "tests": len(results),
            "claude_compliant": claude_ok,
            "mistral_compliant": mistral_ok
        }
    else:
        # Run all
        print("\n🏃 Running ALL tabs with defaults...")
        all_results = run_all_defaults()
        
        print("\n" + "=" * 60)
        print("✅ ALL COMPARISONS COMPLETE")
        print("=" * 60)
        print(f"📊 Dashboard: http://localhost:8508")
        print(f"📁 Results saved to: {SCRIPT_DIR}/results/")
        
        return {
            "status": "success",
            "tabs_run": list(all_results.keys()),
            "total_tests": sum(len(r) for r in all_results.values()),
            "dashboard_url": "http://localhost:8508"
        }


if __name__ == "__main__":
    result = run_agent()
    print(f"\n📋 Result: {result}")
