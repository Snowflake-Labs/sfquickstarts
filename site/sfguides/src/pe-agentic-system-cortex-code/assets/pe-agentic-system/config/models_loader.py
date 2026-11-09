"""
Config-driven model routing loader.

Reads config/models.yaml (or a path passed in) and exposes a ModelRouter that
maps a PE task to the right model tier, and a tier to a concrete model ID for a
given platform. This replaces the hardcoded MODEL_RECOMMENDATIONS dict.

The loader is dependency-cautious:
  - Uses `yaml` if PyYAML is installed (recommended, most readable format).
  - Falls back to JSON if the config is provided as .json and yaml is missing.

Usage:
    from config.models_loader import ModelRouter

    router = ModelRouter()                                   # auto-loads models.yaml
    model = router.for_task("extraction", platform="cortex")  # -> cheap-tier model
    tier  = router.task_tier("extraction")                    # -> "cheap"
    info  = router.model_info("openai-gpt-5.6")               # metadata dict
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, Optional

try:
    import yaml as _yaml
except Exception:  # pragma: no cover - yaml optional
    _yaml = None

# Default search order relative to this file: ../config/models.yaml
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(_HERE, "models.yaml")


class ModelRouter:
    """Task -> tier -> platform model resolution from an external config file."""

    def __init__(self, config_path: Optional[str] = None, data: Optional[dict] = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._data: Dict[str, Any] = data if data is not None else self._load()

        self.model_catalog: Dict[str, dict] = self._data.get("model_catalog", {})
        self.task_routing: Dict[str, dict] = self._data.get("task_routing", {})
        self.platforms: Dict[str, dict] = self._data.get("platforms", {})
        self.platform_tiers: Dict[str, dict] = self._data.get("platform_tiers", {})
        self.family_defaults: Dict[str, dict] = self._data.get("family_defaults", {})
        self.showcase: dict = self._data.get("showcase", {})

    # ------------------------------------------------------------------ load

    def _load(self) -> dict:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Model config not found: {self.config_path}. "
                "Create config/models.yaml (see plan) or pass data=dict."
            )
        ext = os.path.splitext(self.config_path)[1].lower()
        if ext in (".json",):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        with open(self.config_path, "r", encoding="utf-8") as f:
            if _yaml is None:
                raise RuntimeError(
                    "PyYAML is required to load .yaml model config. "
                    "`pip install pyyaml` or provide a .json config."
                )
            return _yaml.safe_load(f) or {}

    # -------------------------------------------------------------- tier logic

    def task_tier(self, task: str) -> str:
        """Map a PE task name to a tier (reasoning|balanced|cheap)."""
        entry = self.task_routing.get(task) or self.task_routing.get("default", {})
        return entry.get("tier", "balanced")

    def tier_for(self, task: str, preferred_family: Optional[str] = None,
                 default_platform: str = "cortex") -> Dict[str, Any]:
        """
        Resolve a task to a concrete model + metadata.

        Returns a dict with keys: task, tier, platform, family, model, cost_rank,
        max_output_tokens, description. This is the primary "why" surface:
        - task_tier explains what kind of model the task needs.
        - cost_rank / max_output_tokens show cost & context implications.
        """
        tier = self.task_tier(task)
        platform = self._normalize_platform(default_platform)
        family = preferred_family or self.platforms.get(platform, {}).get("family", "gpt")
        model = self._resolve_model(platform, tier, family)

        meta = self.model_catalog.get(model, {})
        return {
            "task": task,
            "tier": tier,
            "platform": platform,
            "family": meta.get("family", family),
            "model": model,
            "cost_rank": meta.get("cost_rank", "mid"),
            "max_output_tokens": meta.get("max_output_tokens", 4096),
            "description": meta.get("description", ""),
        }

    # -------------------------------------------------------------- resolution

    def resolve(self, task: str, platform: str = "cortex",
                preferred_family: Optional[str] = None) -> str:
        """Return the model ID string for a task on a given platform."""
        return self.tier_for(task, preferred_family, platform)["model"]

    def _normalize_platform(self, platform: str) -> str:
        p = platform.lower()
        if p == "cortex":
            return "cortex"
        if p in ("openai", "open_ai"):
            return "openai"
        if p in ("bedrock", "aws"):
            return "bedrock"
        # Unknown -> default to first known platform
        return next(iter(self.platform_tiers), "cortex")

    def _is_available(self, model: str) -> bool:
        """Return False when the catalog explicitly marks a model unavailable."""
        meta = self.model_catalog.get(model, {})
        return meta.get("available", True) is not False

    def _resolve_model(self, platform: str, tier: str, family: str) -> str:
        def usable(candidate):
            return candidate and self._is_available(candidate)

        # 1. Platform-specific override for this tier
        pt = self.platform_tiers.get(platform, {})
        if tier in pt and usable(pt[tier]):
            return pt[tier]

        # 2. Preferred family default for this tier
        fam = self.family_defaults.get(family, {})
        if tier in fam and usable(fam[tier]):
            return fam[tier]

        # 3. Any family default for this tier
        for fam_cfg in self.family_defaults.values():
            if tier in fam_cfg and usable(fam_cfg[tier]):
                return fam_cfg[tier]

        # 4. Last resort - any AVAILABLE model in the catalog with this tier
        for mid, meta in self.model_catalog.items():
            if meta.get("tier") == tier and self._is_available(mid):
                return mid

        # 5. Any available model at all (fallback)
        for mid, meta in self.model_catalog.items():
            if self._is_available(mid):
                return mid

        raise ValueError(f"No available model configured for tier '{tier}' on platform '{platform}'")

    # ---------------------------------------------------------------- helpers

    def model_info(self, model: str) -> dict:
        """Return catalog metadata for a model ID (empty dict if unknown)."""
        return self.model_catalog.get(model, {})

    def max_output_tokens(self, model: str, default: int = 4096) -> int:
        """Max output tokens for a model, with safe default."""
        return self.model_catalog.get(model, {}).get("max_output_tokens", default)

    def list_models(self, tier: Optional[str] = None, family: Optional[str] = None) -> list:
        """List model IDs, optionally filtered by tier and/or family."""
        result = []
        for mid, meta in self.model_catalog.items():
            if tier and meta.get("tier") != tier:
                continue
            if family and meta.get("family") != family:
                continue
            result.append(mid)
        return sorted(result)


# Convenience singleton
_default_router: Optional[ModelRouter] = None


def get_router(config_path: Optional[str] = None) -> ModelRouter:
    """Return a cached ModelRouter (create on first call)."""
    global _default_router
    if _default_router is None:
        _default_router = ModelRouter(config_path=config_path)
    return _default_router


if __name__ == "__main__":
    r = get_router()
    print("=== Showcase: model routing (config-driven) ===")
    for task in ("reasoning", "modeling", "extraction", "summarization", "default"):
        for plat in ("cortex", "openai", "bedrock"):
            info = r.tier_for(task, default_platform=plat)
            print(f"  {task:<14} {plat:<8} -> {info['model']:<45} tier={info['tier']} cost={info['cost_rank']}")
    print()
    print("Showcase title:", r.showcase.get("title"))
    print("Reasoning tasks:", r.showcase.get("reasoning_tasks"))
    print("Cheap tasks:    ", r.showcase.get("cheap_tasks"))
