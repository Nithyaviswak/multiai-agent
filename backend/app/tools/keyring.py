"""Keyring: holds API keys per provider in memory.

Keys are seeded from settings (env / .env) at startup and can be added or
overwritten at runtime via ``/api/providers/keys``. Keys are never returned to
the client in full - only a status ("configured", "missing") plus a masked hint.
"""
from typing import Dict, Any, Optional
from app.config import settings
from app.tools.model_registry import PROVIDERS
from app.logging_config import logger


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
        if provider not in PROVIDERS:
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
        for provider, meta in PROVIDERS.items():
            key = self._keys.get(provider)
            if key:
                out[provider] = {
                    "configured": True,
                    "name": meta["name"],
                    "env_key": meta["env_key"],
                    "masked": key[:4] + "…" + key[-4:] if len(key) > 8 else "…",
                }
            else:
                out[provider] = {
                    "configured": False,
                    "name": meta["name"],
                    "env_key": meta["env_key"],
                    "masked": None,
                }
        return out

    def configured_providers(self) -> list[str]:
        return [p for p in PROVIDERS if self.has_key(p)]


keyring = Keyring()
