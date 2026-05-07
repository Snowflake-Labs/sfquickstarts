import json
import time
import uuid
import logging
from typing import AsyncGenerator

import httpx
from app.core.config import settings

logger = logging.getLogger("coco.cortex")


class CortexAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class CortexClient:
    def __init__(self):
        self.base_url = settings.cortex_base_url
        self.http_client = httpx.AsyncClient(timeout=60.0)
        logger.info("Cortex base URL: %s", self.base_url)

    def _build_headers(self, auth_token: str) -> dict:
        return {
            "Authorization": f"Bearer {auth_token}",
            "X-Snowflake-Authorization-Token-Type": "KEYPAIR_JWT",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

    async def chat_complete_stream(
        self,
        request,
        tenant_id: str,
        default_model: str,
        auth_token: str,
        system_prompt: str = "",
    ) -> AsyncGenerator[str, None]:
        model = request.model or default_model
        request_id = f"coco_req_{uuid.uuid4().hex[:8]}"
        url = f"{self.base_url}/v1/chat/completions"

        messages = request.get_messages(system_prompt=system_prompt)
        body = {
            "model": model,
            "messages": messages,
            "max_completion_tokens": request.max_tokens,
            "stream": True,
            "temperature": request.temperature,
        }

        logger.info("Stream request | id=%s tenant=%s model=%s",
                    request_id, tenant_id, model)
        start = time.time()

        async with self.http_client.stream(
            "POST", url,
            headers=self._build_headers(auth_token),
            json=body,
        ) as response:
            if response.status_code != 200:
                error_text = (await response.aread()).decode()
                logger.error("Cortex error | id=%s status=%d body=%s",
                             request_id, response.status_code, error_text)
                yield (
                    f"event: error\n"
                    f"data: {json.dumps({'status_code': response.status_code, 'message': error_text})}\n\n"
                )
                return

            yield (
                f"event: meta\n"
                f"data: {json.dumps({'id': request_id, 'model': model, 'tenant_id': tenant_id})}\n\n"
            )

            total_content = ""
            usage = {}

            async for raw_line in response.aiter_lines():
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                json_str = line[len("data:"):].strip()
                if not json_str or json_str == "[DONE]":
                    continue

                chunk = json.loads(json_str)

                choices = chunk.get("choices", [])
                if choices:
                    text = choices[0].get("delta", {}).get("content", "")
                    if text:
                        total_content += text
                        yield f"event: delta\ndata: {json.dumps({'content': text})}\n\n"

                raw_usage = chunk.get("usage", {})
                if raw_usage.get("prompt_tokens") is not None:
                    usage = raw_usage

            latency_ms = int((time.time() - start) * 1000)
            yield (
                f"event: done\n"
                f"data: {json.dumps({'id': request_id, 'latency_ms': latency_ms, 'usage': usage})}\n\n"
            )
            logger.info("Stream success | id=%s latency=%dms", request_id, latency_ms)

    async def close(self):
        await self.http_client.aclose()


cortex_client = CortexClient()
