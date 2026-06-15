"""
Test all 8 verbosity agents with the query: "What is needle in the haystack benchmark?"
"""
import snowflake.connector
import requests
import json
import os

# Configuration
DATABASE = "FANCYWORKS_DEMO_DB"
SCHEMA = "PUBLIC"
QUERY = "What is needle in the haystack benchmark?"

AGENTS = [
    ("MINIMAL_AGENT", "--minimal", "1 line max"),
    ("BRIEF_AGENT", "--brief", "3 lines max"),
    ("STANDARD_AGENT", "--standard", "balanced"),
    ("DETAILED_AGENT", "--detailed", "with context"),
    ("VERBOSE_AGENT", "--verbose", "comprehensive"),
    ("CODE_ONLY_AGENT", "--code", "code only"),
    ("EXPLAIN_AGENT", "--explain", "why + how"),
    ("STEP_BY_STEP_AGENT", "--steps", "numbered walkthrough"),
]

def get_snowflake_connection():
    """Get Snowflake connection using default config."""
    return snowflake.connector.connect(
        connection_name="myaccount"
    )

def call_agent_rest_api(account_url: str, token: str, agent_name: str, query: str) -> str:
    """Call a Cortex Agent via REST API."""
    url = f"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{agent_name}:run"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": query
                    }
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload, stream=True)
    
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"
    
    # Parse streaming response
    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8').replace('data: ', ''))
                if 'delta' in data and 'content' in data['delta']:
                    for content in data['delta']['content']:
                        if content.get('type') == 'text':
                            full_response += content.get('text', '')
            except:
                pass
    
    return full_response

def main():
    print("=" * 80)
    print(f"Testing 8 Verbosity Agents")
    print(f"Query: {QUERY}")
    print("=" * 80)
    
    # Get connection details
    conn = get_snowflake_connection()
    account_url = f"https://{conn.account}.snowflakecomputing.com"
    
    # Get PAT token (you'll need to set this)
    token = os.environ.get("SNOWFLAKE_PAT_TOKEN")
    
    if not token:
        print("\nNote: Set SNOWFLAKE_PAT_TOKEN environment variable to run this script.")
        print("\nTo test agents manually, use the REST API:")
        print(f"\ncurl -X POST \"{account_url}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/<AGENT_NAME>:run\" \\")
        print('  --header "Content-Type: application/json" \\')
        print('  --header "Accept: application/json" \\')
        print('  --header "Authorization: Bearer $PAT" \\')
        print('  --data \'{"messages": [{"role": "user", "content": [{"type": "text", "text": "' + QUERY + '"}]}]}\'')
        return
    
    for agent_name, flag, description in AGENTS:
        print(f"\n{'=' * 80}")
        print(f"Agent: {agent_name} ({flag}) - {description}")
        print("-" * 80)
        
        response = call_agent_rest_api(account_url, token, agent_name, QUERY)
        print(response)
    
    conn.close()

if __name__ == "__main__":
    main()
