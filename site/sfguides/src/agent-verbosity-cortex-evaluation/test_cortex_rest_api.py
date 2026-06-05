"""
Test Cortex REST API with streaming response handling
Usage: python test_cortex_rest_api.py -m <model> -q <question>

Examples:
  python test_cortex_rest_api.py -m openai-gpt-5.2 -q "Who won the super bowl in 2025?"
  python test_cortex_rest_api.py --model claude-sonnet-4-5 --question "What is Python?"
  python test_cortex_rest_api.py  # Uses defaults
"""

import requests
import tomllib
import os
import time
import json
import sys
import argparse

def get_pat():
    """Get PAT from config.toml"""
    with open(os.path.expanduser('~/.snowflake/config.toml'), 'rb') as f:
        config = tomllib.load(f)
    return config['connections']['myaccount']['password']

def test_cortex_rest_api(model: str, question: str):
    """Test Cortex REST API with streaming response"""
    pat = get_pat()
    
    url = 'https://YOUR_ACCOUNT.snowflakecomputing.com/api/v2/cortex/inference:complete'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {pat}',
    }
    
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': question}],
        'stream': True,
    }
    
    print(f'Question: {question}')
    print(f'Model: {model}')
    print(f'Endpoint: Cortex REST API (streaming)')
    print('-' * 50)
    
    start = time.time()
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120, stream=True)
        
        print(f'Status: {r.status_code}')
        print(f'\nResponse Headers:')
        for k, v in r.headers.items():
            print(f'  {k}: {v}')
        print()
        
        if r.status_code != 200:
            print(f'Error: {r.text}')
            return
        
        full_text = ''
        finish_reason = None
        usage = {}
        request_id = None

        # Get request ID from SSE header
        request_id = r.headers.get('X-Snowflake-Request-Id')

        for line in r.iter_lines():
            if not line:
                continue

            line_str = line.decode('utf-8')

            if not line_str.startswith('data: '):
                continue

            payload_str = line_str[6:].strip()

            if payload_str == '[DONE]':
                break

            try:
                data = json.loads(payload_str)
            except json.JSONDecodeError as exc:
                print(f'\n[warn] Could not parse SSE chunk: {exc}', file=sys.stderr)
                continue

            choice = data.get('choices', [{}])[0]
            delta = choice.get('delta', {})
            content = delta.get('content', '')

            if content:
                full_text += content
                print(content, end='', flush=True)

            if choice.get('finish_reason'):
                finish_reason = choice['finish_reason']

            if data.get('usage'):
                usage = data['usage']

        duration = time.time() - start
        print(f'\n\n' + '-' * 50)
        print(f'Duration:      {duration:.2f}s')
        print(f'Total chars:   {len(full_text)}')
        if request_id:
            print(f'Request ID:    {request_id}')
        if finish_reason:
            print(f'Finish reason: {finish_reason}')
        if usage:
            print(f'Usage:         {usage}')
        
    except requests.exceptions.Timeout:
        print('Request timed out')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test Cortex REST API with streaming response',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available models:
  OpenAI:    openai-gpt-5.2, openai-gpt-5-chat, openai-gpt-4o
  Anthropic: claude-sonnet-4-5, claude-sonnet-4-6, claude-opus-4-5, claude-haiku-4-5
  Meta:      llama3.1-70b, llama3.1-405b
  Mistral:   mistral-large2
        """
    )
    parser.add_argument('-m', '--model', type=str, default='openai-gpt-5.2',
                        help='Model to use (default: openai-gpt-5.2)')
    parser.add_argument('-q', '--question', type=str, default='Who won the Super Bowl in 2025?',
                        help='Question to ask (default: Who won the Super Bowl in 2025?)')
    
    args = parser.parse_args()
    
    test_cortex_rest_api(args.model, args.question)
