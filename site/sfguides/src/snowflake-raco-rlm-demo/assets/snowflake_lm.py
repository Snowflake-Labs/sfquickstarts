"""Text-only DSPy 3.5 engine backed by the active Snowpark session."""

import json

from dspy.lm15 import Message, Response, Usage


class SnowflakeCompleteEngine:
    """Run model calls through Snowflake AI_COMPLETE, without REST credentials."""

    def __init__(self, session, model="openai-gpt-6-luna", max_tokens=1500):
        self.session = session
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, request):
        if request.tools or request.model != "custom/snowflake-ai-complete":
            raise ValueError("This engine supports only its text-only model label")
        if request.system is not None and not isinstance(request.system, str):
            raise ValueError("System instructions must be text")
        conversation = []
        if request.system:
            conversation.append("System instructions:\n" + request.system)
        for message in request.messages:
            if message.role not in ("user", "assistant") or message.text is None:
                raise ValueError("Only user and assistant text messages are supported")
            conversation.append(f"{message.role.upper()}:\n{message.text}")
        if not conversation:
            raise ValueError("An empty conversation cannot be completed")
        conversation.append("ASSISTANT:\n")
        prompt = "\n\n".join(conversation)
        if len(prompt) > 40000:
            raise ValueError("Prompt exceeds the demo's 40,000 character cap")
        requested_tokens = request.config.max_tokens
        tokens = min(requested_tokens or self.max_tokens, self.max_tokens)
        if tokens < 1:
            raise ValueError("max_tokens must be positive")
        # Snowflake requires the model argument to be a SQL literal at compile time.
        # Select only from the closed model allowlist; bind the untrusted prompt.
        if self.model != "openai-gpt-6-luna":
            raise ValueError("Unapproved model for this demo")
        response = self.session.sql(
            "SELECT AI_COMPLETE('openai-gpt-6-luna', ?, OBJECT_CONSTRUCT('max_tokens', ?)) AS COMPLETION",
            params=[prompt, tokens],
        ).collect()[0][0]
        # AI_COMPLETE returns a VARIANT, which Snowpark surfaces as JSON-quoted text; unwrap it.
        if isinstance(response, str) and response.startswith('"'):
            try:
                decoded = json.loads(response)
            except ValueError:
                decoded = None
            if isinstance(decoded, str):
                response = decoded
        if not isinstance(response, str) or not response.strip():
            raise RuntimeError("AI_COMPLETE returned no text")
        return Response(
            id=None,
            model=request.model,
            message=Message.assistant(response),
            finish_reason="stop",
            usage=Usage(),
        )