"""
OpenAI-Compatible PE Agent Client

Supports:
1. OpenAI API (direct)
2. Bedrock AgentCore (OpenAI-compatible mode)
3. Cortex via OpenAI-compatible interface (fallback)

Designed for portability across platforms while maintaining PE domain expertise.

Model selection is CONFIG-DRIVEN (config/models.yaml -> config/models_loader.py),
so you can swap Claude <-> GPT <-> Mistral per platform without touching code.
"""

import os
import json
from typing import List, Dict, Any, Optional, Iterator, Union
from dataclasses import dataclass
from enum import Enum

try:
    from config.models_loader import ModelRouter, get_router
except Exception:  # pragma: no cover - fallback if config package not importable
    ModelRouter = None
    get_router = None


class Provider(Enum):
    OPENAI = "openai"
    BEDROCK = "bedrock"
    CORTEX = "cortex"


@dataclass
class PEAgentConfig:
    """Configuration for PE agent clients"""
    provider: Provider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    region: Optional[str] = None  # For Bedrock

    # PE-specific defaults
    default_model: str = "claude-sonnet-4-5"
    temperature: float = 0.0
    max_tokens: int = 4096


class PEAgentClient:
    """
    Unified client for PE agents across OpenAI, Bedrock, and Cortex.

    Features:
    - Consistent interface across providers
    - PE domain-specific prompt engineering
    - Automatic fallback and retry logic
    - Structured output support
    - Config-driven model routing (task -> tier -> platform model)
    """

    # Model routing now comes from config/models.yaml via the ModelRouter.
    # The legacy mapping is kept only as a fallback if the config loader is
    # unavailable, so existing callers keep working unchanged.
    _LEGACY_MODEL_RECOMMENDATIONS = {
        Provider.OPENAI: {
            "reasoning": "openai-gpt-5.6",
            "modeling": "openai-gpt-sol",
            "extraction": "openai-gpt-5.1",
            "default": "openai-gpt-5.1",
        },
        Provider.BEDROCK: {
            "reasoning": "anthropic.claude-3-opus-20240229-v1",
            "modeling": "anthropic.claude-3-sonnet-20240229-v1",
            "extraction": "anthropic.claude-3-haiku-20240307-v1",
            "default": "anthropic.claude-3-sonnet-20240229-v1",
        },
        Provider.CORTEX: {
            "reasoning": "openai-gpt-5.6",
            "modeling": "openai-gpt-sol",
            "extraction": None,  # cheap tier, resolved from config
            "default": "claude-sonnet-4-5",
        },
    }

    def __init__(self, config: PEAgentConfig):
        self.config = config
        self.provider = config.provider
        self.router: Optional[ModelRouter] = get_router() if get_router else None

        # Initialize provider-specific client
        if self.provider == Provider.OPENAI:
            from openai import OpenAI
            self.client = OpenAI(api_key=config.api_key or os.getenv("OPENAI_API_KEY"))

        elif self.provider == Provider.BEDROCK:
            import boto3
            self.bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name=config.region or os.getenv("AWS_REGION", "us-east-1")
            )

        elif self.provider == Provider.CORTEX:
            # Import our custom Cortex client
            from .cortex_client import CortexRESTClient
            self.cortex_client_class = CortexRESTClient

    @classmethod
    def for_openai(cls, api_key: Optional[str] = None, model: str = "openai-gpt-5.1") -> "PEAgentClient":
        """
        Create client for OpenAI.

        Example:
            client = PEAgentClient.for_openai()
            response = client.analyze_deal(cim_text)
        """
        config = PEAgentConfig(
            provider=Provider.OPENAI,
            api_key=api_key,
            default_model=model
        )
        return cls(config)

    @classmethod
    def for_bedrock(cls, region: str = "us-east-1", model: str = None) -> "PEAgentClient":
        """
        Create client for Bedrock AgentCore.

        Example:
            client = PEAgentClient.for_bedrock()
            response = client.analyze_deal(cim_text)
        """
        default_model = model or "anthropic.claude-3-sonnet-20240229-v1"
        config = PEAgentConfig(
            provider=Provider.BEDROCK,
            region=region,
            default_model=default_model
        )
        return cls(config)

    @classmethod
    def for_cortex(cls, session, model: str = "claude-sonnet-4-5") -> "PEAgentClient":
        """
        Create client for Cortex (from Snowflake session).

        Example:
            from snowflake.snowpark import Session
            session = Session.builder.getOrCreate()
            client = PEAgentClient.for_cortex(session)
            response = client.analyze_deal(cim_text)
        """
        config = PEAgentConfig(
            provider=Provider.CORTEX,
            default_model=model
        )
        instance = cls(config)
        instance.session = session  # Store session for Cortex client creation
        return instance

    def _platform_name(self) -> str:
        return self.provider.value  # "openai" | "bedrock" | "cortex"

    def get_model(self, task: str = "default", preferred_family: Optional[str] = None) -> str:
        """
        Get recommended model for a specific PE task.

        Resolves from config/models.yaml (task -> tier -> platform model).
        Falls back to the legacy mapping if the config route is unavailable.
        """
        model = None
        if self.router is not None:
            try:
                model = self.router.resolve(
                    task,
                    platform=self._platform_name(),
                    preferred_family=preferred_family,
                )
            except Exception:
                model = None

        if model:
            return model

        # Legacy fallback
        table = self._LEGACY_MODEL_RECOMMENDATIONS.get(self.provider, {})
        return table.get(task, self.config.default_model)

    def get_model_info(self, task: str = "default",
                       preferred_family: Optional[str] = None) -> Dict[str, Any]:
        """
        Return routing decision with the WHY: tier, cost, max tokens.

        Example:
            info = client.get_model_info("extraction")
            # {'task': 'extraction', 'tier': 'cheap', 'model': 'llama-4.1-nemotron', ...}
        """
        if self.router is not None:
            try:
                return self.router.tier_for(
                    task,
                    preferred_family=preferred_family,
                    default_platform=self._platform_name(),
                )
            except Exception:
                pass
        model = self.get_model(task, preferred_family)
        return {"task": task, "tier": "unknown", "model": model}

    def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Unified completion interface across providers.

        Returns just the text content for simplicity.
        """
        model = model or self.config.default_model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        if self.provider == Provider.OPENAI:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content

        elif self.provider == Provider.BEDROCK:
            # Convert to Bedrock format
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            })

            response = self.bedrock.invoke_model(
                modelId=model,
                body=body
            )

            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']

        elif self.provider == Provider.CORTEX:
            from .cortex_client import CortexRESTClient
            client = CortexRESTClient.from_session(self.session, model)
            response = client.complete(
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens
            )
            return response["choices"][0]["message"]["content"]

    def complete_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Iterator[str]:
        """
        Streaming completion across providers.

        Yields text chunks as they arrive.
        """
        model = model or self.config.default_model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        if self.provider == Provider.OPENAI:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        elif self.provider == Provider.BEDROCK:
            # Bedrock streaming
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            })

            response = self.bedrock.invoke_model_with_response_stream(
                modelId=model,
                body=body
            )

            for event in response['body']:
                chunk = json.loads(event['chunk']['bytes'])
                if chunk['type'] == 'content_block_delta':
                    yield chunk['delta']['text']

        elif self.provider == Provider.CORTEX:
            from .cortex_client import CortexRESTClient
            client = CortexRESTClient.from_session(self.session, model)
            yield from client.complete_stream(
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens
            )

    # High-level PE-specific methods

    def analyze_deal(
        self,
        document: str,
        task: str = "Extract key investment metrics and red flags",
        model: Optional[str] = None
    ) -> str:
        """
        Analyze a deal document (CIM, teaser, financials).

        Example:
            analysis = client.analyze_deal(cim_text)
        """
        model = model or self.get_model("extraction")

        system_prompt = """You are an expert Private Equity analyst. 
Analyze the provided document with institutional rigor.
Focus on: investment thesis, key metrics, risks, and quality of information.
Be concise but thorough. Flag missing or questionable data."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {task}\n\nDocument:\n{document}"}
        ]

        return self.complete(messages, model=model)

    def build_model(
        self,
        model_type: str,
        inputs: Dict[str, Any],
        model: Optional[str] = None
    ) -> str:
        """
        Generate financial model code (DCF, LBO, etc.).

        Example:
            code = client.build_model("DCF", {
                "revenue": 100_000_000,
                "growth_rate": 0.08,
                "ebitda_margin": 0.25
            })
        """
        model = model or self.get_model("modeling")

        system_prompt = """You are an expert financial modeler.
Generate clean, executable Python code using pandas, numpy, and proper financial practices.
Always use Decimal for financial calculations.
Include assumptions table, sensitivity analysis, and clear documentation."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Build a {model_type} model with these inputs:\n{json.dumps(inputs, indent=2)}"}
        ]

        return self.complete(messages, model=model, max_tokens=8192)

    def generate_ic_memo(
        self,
        deal_name: str,
        analysis: Dict[str, Any],
        model: Optional[str] = None
    ) -> str:
        """
        Generate Investment Committee memo.

        Example:
            memo = client.generate_ic_memo("Acme Corp", {
                "thesis": "...",
                "valuation": {...},
                "risks": [...]
            })
        """
        model = model or self.get_model("reasoning")

        system_prompt = """You are an expert PE investment professional.
Generate a professional IC memo with:
1. Executive Summary
2. Investment Thesis
3. Financial Analysis
4. Key Risks & Mitigants
5. Recommendation

Be concise, data-driven, and professional. Use bullet points and tables."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate IC memo for {deal_name}\n\nAnalysis:\n{json.dumps(analysis, indent=2)}"}
        ]

        return self.complete(messages, model=model, max_tokens=8192)

    def portfolio_report(
        self,
        company_data: Dict[str, Any],
        model: Optional[str] = None
    ) -> str:
        """
        Generate portfolio company performance report.

        Example:
            report = client.portfolio_report({
                "company": "Acme",
                "kpis": {...},
                "financials": {...}
            })
        """
        model = model or self.get_model("extraction")

        system_prompt = """You are a PE portfolio monitoring specialist.
Generate a clear, actionable performance report highlighting:
- Performance vs plan
- Key risks/opportunities  
- Recommended actions

Use traffic-light status indicators (Green/Yellow/Red)."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate report:\n{json.dumps(company_data, indent=2)}"}
        ]

        return self.complete(messages, model=model)


# Convenience function for quick setup
def create_pe_agent(
    provider: str = "openai",
    **kwargs
) -> PEAgentClient:
    """
    Quick PE agent creation.

    Example:
        # OpenAI
        agent = create_pe_agent("openai")

        # Bedrock
        agent = create_pe_agent("bedrock", region="us-east-1")

        # Cortex (requires session)
        agent = create_pe_agent("cortex", session=session)

    Model choice is config-driven (config/models.yaml). Add `model=` to pin one.
    """
    if provider == "openai":
        return PEAgentClient.for_openai(**kwargs)
    elif provider == "bedrock":
        return PEAgentClient.for_bedrock(**kwargs)
    elif provider == "cortex":
        return PEAgentClient.for_cortex(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# Example usage
if __name__ == "__main__":
    print("PE Agent Client - Multi-Platform Support (config-driven)")
    print("")
    print("# OpenAI")
    print("agent = create_pe_agent('openai')")
    print("analysis = agent.analyze_deal(cim_text)")
    print("")
    print("# Bedrock")
    print("agent = create_pe_agent('bedrock')")
    print("memo = agent.generate_ic_memo('Deal X', analysis_dict)")
    print("")
    print("# Cortex")
    print("agent = create_pe_agent('cortex', session=snowflake_session)")
    print("code = agent.build_model('DCF', inputs_dict)")
    print("")
    print("# Showcase routing decisions:")
    from config.models_loader import get_router
    r = get_router()
    for task in ("reasoning", "modeling", "extraction", "summarization", "default"):
        info = r.tier_for(task, default_platform="cortex")
        print(f"  {task:<14} cortex -> {info['model']:<28} tier={info['tier']} cost={info['cost_rank']}")
