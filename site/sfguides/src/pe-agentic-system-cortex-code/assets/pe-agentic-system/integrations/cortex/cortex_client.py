"""
Cortex REST API Client for Private Equity Agents

Supports three authentication modes:
1. from_session() - In-Snowflake (Notebooks/SiS) - PREFERRED
2. from_toml() - External development
3. from_key_file() - Production/CI with JWT

Based on learnings from memory:
- NEVER include 'logprobs' parameter (not in Cortex allowlist)
- Omit 'stop' parameter entirely if not needed (don't pass null)
- Use session token for in-Snowflake workloads (simplest auth)
"""

import os
import json
import requests
import time
from typing import Optional, Dict, Any, List, Iterator
from dataclasses import dataclass
from enum import Enum

try:
    from config.models_loader import get_router
except Exception:  # pragma: no cover - config package optional
    get_router = None


class AuthMode(Enum):
    SESSION = "session"
    TOML = "toml"
    JWT = "jwt"


@dataclass
class CortexConfig:
    """Configuration for Cortex REST API client"""
    account: str
    host: str
    token: str
    auth_mode: AuthMode


# Module-level model output-token limits.
# Base values (fallback), then enriched from config/models.yaml (config-driven).
_FALLBACK_MAX_TOKENS = {
    "claude-opus-4-6": 16384,
    "claude-sonnet-4-5": 16384,
    "openai-gpt-5.1": 16384,
    "openai-gpt-5.4": 32768,
    "openai-gpt-5.6": 32768,
    "openai-gpt-sol": 32768,
    "mistral-large-2-2": 32768,
    "llama-4.1-nemotron": 4096,
}


def _build_max_tokens():
    merged = dict(_FALLBACK_MAX_TOKENS)
    if get_router is not None:
        try:
            router = get_router()
            for mid in router.model_catalog:
                merged[mid] = router.max_output_tokens(mid, merged.get(mid, 4096))
        except Exception:
            pass
    return merged


class CortexRESTClient:
    """
    Cortex REST API client optimized for PE workflows.
    
    Features:
    - Three auth modes (session, toml, JWT)
    - Streaming and non-streaming support
    - Proper error handling for common Cortex gotchas
    - Model-specific parameter validation
    """

    # Config-driven model output-token limits (from config/models.yaml)
    MODEL_MAX_TOKENS = _build_max_tokens()

    def __init__(self, config: CortexConfig, model: str):
        self.config = config
        self.model = model
        self.base_url = f"https://{config.host}/api/v2/cortex/inference:complete"
        self.headers = {
            "Authorization": f'Snowflake Token="{config.token}"',
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        
    @classmethod
    def from_session(cls, session, model: str) -> "CortexRESTClient":
        """
        Create client from active Snowflake session (PREFERRED for Notebooks/SiS).
        
        Example:
            from snowflake.snowpark import Session
            session = Session.builder.getOrCreate()
            client = CortexRESTClient.from_session(session, "claude-opus-4-6")
        """
        token = session.connection.rest._token
        host = session.connection.host
        account = session.connection.account
        
        config = CortexConfig(
            account=account,
            host=host,
            token=token,
            auth_mode=AuthMode.SESSION
        )
        return cls(config, model)
    
    @classmethod
    def from_toml(cls, account: str, model: str, config_path: Optional[str] = None) -> "CortexRESTClient":
        """
        Create client from ~/.snowflake/config.toml (for external development).
        
        Example:
            client = CortexRESTClient.from_toml("<your connection>", "claude-opus-4-6")
        """
        import tomli
        
        if config_path is None:
            config_path = os.path.expanduser("~/.snowflake/config.toml")
        
        with open(config_path, "rb") as f:
            config_data = tomli.load(f)
        
        # Find connection config
        conn_config = config_data.get("connections", {}).get(account, {})
        if not conn_config:
            raise ValueError(f"Connection '{account}' not found in {config_path}")
        
        # CRITICAL: Use 'host' field directly (don't reconstruct from account)
        # Reconstructing can fail with underscores in account identifiers
        host = conn_config.get("host")
        if not host:
            raise ValueError(f"'host' field missing in connection '{account}'")
        
        # Get token (would need separate token generation for toml - simplified here)
        # In practice, use JWT or OAuth flow
        raise NotImplementedError("TOML auth requires JWT implementation - use from_key_file() instead")
    
    @classmethod
    def from_key_file(
        cls,
        account: str,
        user: str,
        private_key_path: str,
        model: str,
        passphrase: Optional[str] = None
    ) -> "CortexRESTClient":
        """
        Create client from JWT keypair (for production/CI).
        
        Example:
            client = CortexRESTClient.from_key_file(
                account="<your account>",
                user="pe_agent",
                private_key_path="~/.ssh/snowflake_rsa_key.p8",
                model="claude-opus-4-6"
            )
        """
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        import snowflake.connector
        
        # Load private key
        key_path = os.path.expanduser(private_key_path)
        with open(key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=passphrase.encode() if passphrase else None,
                backend=default_backend()
            )
        
        pkb = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Create connection to get token
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            private_key=pkb
        )
        
        token = conn.rest.token
        host = conn.host
        
        config = CortexConfig(
            account=account,
            host=host,
            token=token,
            auth_mode=AuthMode.JWT
        )
        return cls(config, model)
    
    def _validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean parameters to avoid common Cortex 400 errors.
        
        Critical validations based on memory:
        - Remove 'logprobs' (not in Cortex allowlist)
        - Remove 'stop' if null (gateway distinguishes absent vs null)
        - Check max_completion_tokens against model limits
        """
        cleaned = params.copy()
        
        # CRITICAL: Remove logprobs entirely
        if "logprobs" in cleaned:
            del cleaned["logprobs"]
        
        # CRITICAL: Remove stop if null or empty
        if "stop" in cleaned and (cleaned["stop"] is None or cleaned["stop"] == []):
            del cleaned["stop"]
        
        # Validate max_completion_tokens
        if "max_completion_tokens" in cleaned:
            max_allowed = self.MODEL_MAX_TOKENS.get(self.model, 4096)
            if cleaned["max_completion_tokens"] > max_allowed:
                raise ValueError(
                    f"max_completion_tokens ({cleaned['max_completion_tokens']}) "
                    f"exceeds model limit ({max_allowed}) for {self.model}"
                )
        
        return cleaned
    
    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_completion_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Non-streaming completion.
        
        Example:
            response = client.complete(
                messages=[{"role": "user", "content": "Build a DCF model"}],
                temperature=0.0,
                max_completion_tokens=4096
            )
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_completion_tokens:
            payload["max_completion_tokens"] = max_completion_tokens
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        # Validate and clean
        payload = self._validate_params(payload)
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=180
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
            
            raise RuntimeError(
                f"Cortex API error (status {e.response.status_code}): {error_detail}\n"
                f"Common fixes:\n"
                f"- Remove 'logprobs' parameter\n"
                f"- Omit 'stop' parameter if not needed\n"
                f"- Check max_completion_tokens is within model limit ({self.MODEL_MAX_TOKENS.get(self.model, 'unknown')})"
            ) from e
    
    def complete_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_completion_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Streaming completion (SSE).
        
        Example:
            for chunk in client.complete_stream(messages=[...]):
                print(chunk, end="", flush=True)
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_completion_tokens:
            payload["max_completion_tokens"] = max_completion_tokens
        
        payload.update(kwargs)
        payload = self._validate_params(payload)
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=180
            )
            response.raise_for_status()
            
            # Parse SSE stream
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
                            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
            
            raise RuntimeError(
                f"Cortex API streaming error (status {e.response.status_code}): {error_detail}"
            ) from e


# Convenience functions for common PE tasks

def quick_analysis(
    session,
    prompt: str,
    model: str = "claude-sonnet-4-5",
    context: Optional[str] = None
) -> str:
    """
    Quick analysis for PE workflows (one-shot completion).
    
    Example:
        result = quick_analysis(
            session,
            "Analyze this CIM and extract key metrics",
            context=cim_text
        )
    """
    client = CortexRESTClient.from_session(session, model)
    
    messages = [{"role": "user", "content": prompt}]
    if context:
        messages.insert(0, {"role": "user", "content": f"Context:\n{context}"})
    
    response = client.complete(messages)
    return response["choices"][0]["message"]["content"]


def streaming_analysis(
    session,
    prompt: str,
    model: str = "claude-opus-4-6",
    context: Optional[str] = None
) -> Iterator[str]:
    """
    Streaming analysis for long-form PE outputs (IC memos, DD reports).
    
    Example:
        for chunk in streaming_analysis(session, "Generate IC memo for Deal X"):
            print(chunk, end="", flush=True)
    """
    client = CortexRESTClient.from_session(session, model)
    
    messages = [{"role": "user", "content": prompt}]
    if context:
        messages.insert(0, {"role": "user", "content": f"Context:\n{context}"})
    
    yield from client.complete_stream(messages)


# Example usage
if __name__ == "__main__":
    # This would typically run in a Snowflake Notebook
    print("Cortex REST API Client for PE Agents")
    print("Import this module in your Snowflake Notebook:")
    print("")
    print("  from cortex_client import CortexRESTClient")
    print("  from snowflake.snowpark import Session")
    print("  ")
    print("  session = Session.builder.getOrCreate()")
    print("  client = CortexRESTClient.from_session(session, 'claude-opus-4-6')")
    print("  ")
    print("  response = client.complete(")
    print("      messages=[{'role': 'user', 'content': 'Build a DCF model'}]")
    print("  )")
