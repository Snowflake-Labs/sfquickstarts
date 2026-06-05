"""
LiteLLM proxy pre-call / post-call hook for the Cursor → Cortex bridge.

Wired in via litellm_config.yaml:

    litellm_settings:
      callbacks: pre_call_hook.proxy_handler_instance

What it does:
  1. Strips `temperature`, `top_p`, `top_k` for Anthropic models that no longer
     accept them (Claude Opus 4.7+ returns 400 if any non-default value is sent).
  2. Caps `max_tokens` so a runaway agent can't blow the budget.
  3. Logs a one-line summary per request (model, msg count, max_tokens, latency).
  4. Adds a hard guard that rejects requests for models not in an allow-list.

Drop this file next to litellm_config.yaml; LiteLLM imports it by module path.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional, Union

from litellm.integrations.custom_logger import CustomLogger

log = logging.getLogger("cortex-bridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

# Models where Anthropic removed sampling params (returns 400 on any non-default value).
SAMPLING_PARAM_REMOVED_PREFIXES = (
    "claude-opus-4-7",
    "claude-opus-4-8",
)

# Hard cap so a hung agent can't burn through tokens.
MAX_TOKENS_CEILING = 4096

# Optional allow-list. Empty set = allow everything.
MODEL_ALLOW_LIST: set[str] = {
    "cortex-claude-4-sonnet",
}


class CortexBridgeHook(CustomLogger):
    """Pre/post-call hook for the Cursor → Cortex LiteLLM proxy."""

    async def async_pre_call_hook(
        self,
        user_api_key_dict,  # UserAPIKeyAuth
        cache,              # DualCache
        data: dict,
        call_type: str,
    ) -> Optional[Union[Exception, str, dict]]:
        model = data.get("model", "")
        data["_t_start"] = time.perf_counter()

        # 1. Allow-list check
        if MODEL_ALLOW_LIST and model not in MODEL_ALLOW_LIST:
            log.warning("rejecting model=%s not in allow-list", model)
            return f"Model '{model}' is not enabled on this proxy."

        # 2. Strip sampling params for models that no longer accept them.
        underlying = data.get("metadata", {}).get("model_group") or model
        if any(underlying.startswith(p) for p in SAMPLING_PARAM_REMOVED_PREFIXES):
            removed = [k for k in ("temperature", "top_p", "top_k") if k in data]
            for k in removed:
                data.pop(k, None)
            if removed:
                log.info("stripped %s for model=%s", removed, model)

        # 3. Cap max_tokens.
        if data.get("max_tokens") and data["max_tokens"] > MAX_TOKENS_CEILING:
            log.info(
                "capping max_tokens %s -> %s for model=%s",
                data["max_tokens"], MAX_TOKENS_CEILING, model,
            )
            data["max_tokens"] = MAX_TOKENS_CEILING

        # 4. Log incoming request.
        msgs = data.get("messages") or []
        log.info(
            "PRE  model=%s call_type=%s msgs=%d max_tokens=%s",
            model, call_type, len(msgs), data.get("max_tokens"),
        )
        return data

    async def async_log_success_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        usage = getattr(response_obj, "usage", None)
        elapsed_ms = (end_time - start_time).total_seconds() * 1000
        log.info(
            "POST model=%s status=ok latency_ms=%.0f tokens=%s",
            kwargs.get("model"),
            elapsed_ms,
            getattr(usage, "total_tokens", None),
        )

    async def async_log_failure_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        elapsed_ms = (end_time - start_time).total_seconds() * 1000
        err = kwargs.get("exception") or response_obj
        log.error(
            "POST model=%s status=err latency_ms=%.0f err=%s",
            kwargs.get("model"), elapsed_ms, err,
        )


# LiteLLM imports this symbol when the YAML references `pre_call_hook.proxy_handler_instance`.
proxy_handler_instance = CortexBridgeHook()
