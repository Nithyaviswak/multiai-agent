"""Keyring: holds API keys in memory.

Two kinds of keys are supported:
  - provider keys (Groq / OpenAI / Anthropic), seeded from settings at startup
    and reusable for any model of that provider;
  - per-model keys for runtime-registered custom (OpenAI-compatible) models,
    keyed by model id.

Keys are never returned to the client in full — only a status plus a masked
hint.
"""
from typing import Dict, Any, Optional
from app.config import settings
from app.tools.model_registry import PROVIDERS
from app.logging_config import logger

# Providers whose keys can be seeded from settings / added via Settings UI.
SCHEDULED_PROVIDERS = ("groq", "openai", "anthropic")


class Keyring:
    def __init__(self):
        self._keys: Dict[str, str] = {}
        self._seed_from_settings()

    def _seed_from_settings(self) -> None:
        env_keys = {
            "groq": settings.GROQ_API_KEY,
            "openai": getattr(settings, "OPENAI_API_KEY", "") or "",
            "anthropic": getattr(settings, "ANTHROPIC_API_KEY", "") or "",
        }
        for provider, key in env_keys.items():
            if key and not key.startswith("your_"):
                self._keys[provider] = key

    def set_key(self, provider: str, key: str) -> None:
        if provider not in SCHEDULED_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")
        key = key.strip()
        if not key:
            raise ValueError(f"API key for {provider} cannot be empty")
        self._keys[provider] = key
        logger.info("API key configured", provider=provider)

    def get_key(self, provider: str) -> Optional[str]:
        return self._keys.get(provider)

    def has_key(self, provider: str) -> bool:
        return bool(self._keys.get(provider))

    def status(self) -> Dict[str, Any]:
        out = {}
        for provider in SCHEDULED_PROVIDERS:
            meta = PROVIDERS.get(provider, {})
            key = self._keys.get(provider)
            if key:
                out[provider] = {
                    "configured": True,
                    "name": meta.get("name", provider),
                    "env_key": meta.get("env_key", ""),
                    "masked": key[:4] + "…" + key[-4:] if len(key) > 8 else "…",
                }
            else:
                out[provider] = {
                    "configured": False,
                    "name": meta.get("name", provider),
                    "env_key": meta.get("env_key", ""),
                    "masked": None,
                }
        return out

    def configured_providers(self) -> list[str]:
        return [p for p in SCHEDULED_PROVIDERS if self.has_key(p)]

    # ── Per-model keys (custom OpenAI-compatible models) ──────────
    def set_model_key(self, model_id: str, key: str) -> None:
        key = key.strip()
        self._keys[f"model:{model_id}"] = key

    def get_model_key(self, model_id: str) -> Optional[str]:
        return self._keys.get(f"model:{model_id}")

    def model_key_configured(self, model_id: str) -> bool:
        return bool(self._keys.get(f"model:{model_id}"))

    def clear_model_key(self, model_id: str) -> None:
        self._keys.pop(f"model:{model_id}", None)


keyring = Keyring()
