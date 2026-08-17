"""Model registry: providers, models, and client factories.

The platform is provider-agnostic. Each provider maps to a langchain chat
client. ``build_chat_model`` returns a fresh client for a model id using the
API key provided by the caller (usually from the keyring).
"""
from typing import Any, Dict, List, Optional

from app.config import settings

# Provider -> display name and the env var that seeds its key.
PROVIDERS: Dict[str, Dict[str, str]] = {
    "groq": {
        "name": "Groq",
        "env_key": "GROQ_API_KEY",
        "note": "Fast inference on open models (gpt-oss, qwen, allam).",
    },
    "openai": {
        "name": "OpenAI",
        "env_key": "OPENAI_API_KEY",
        "note": "GPT-4o / GPT-4o mini hosted by OpenAI.",
    },
    "anthropic": {
        "name": "Anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "note": "Claude models hosted by Anthropic.",
    },
}

# Model catalog. Cost per 1M tokens (USD) used only for internal budgeting.
MODELS: List[Dict[str, Any]] = [
    # ── Groq (verified reachable 2026-08-17) ─────────────────────
    {"id": "openai/gpt-oss-120b", "provider": "groq", "name": "GPT-OSS 120B",
     "input_per_1m": 0.24, "output_per_1m": 0.96, "fast": False},
    {"id": "openai/gpt-oss-20b", "provider": "groq", "name": "GPT-OSS 20B",
     "input_per_1m": 0.06, "output_per_1m": 0.24, "fast": True},
    {"id": "qwen/qwen3.6-27b", "provider": "groq", "name": "Qwen 3.6 27B",
     "input_per_1m": 0.10, "output_per_1m": 0.40, "fast": True},
    {"id": "allam-2-7b", "provider": "groq", "name": "ALLAM 2 7B",
     "input_per_1m": 0.05, "output_per_1m": 0.20, "fast": True},
    # ── OpenAI ───────────────────────────────────────────────────
    {"id": "gpt-4o", "provider": "openai", "name": "GPT-4o",
     "input_per_1m": 2.50, "output_per_1m": 10.00, "fast": False},
    {"id": "gpt-4o-mini", "provider": "openai", "name": "GPT-4o mini",
     "input_per_1m": 0.15, "output_per_1m": 0.60, "fast": True},
    # ── Anthropic ────────────────────────────────────────────────
    {"id": "claude-sonnet-4-20250514", "provider": "anthropic", "name": "Claude Sonnet 4",
     "input_per_1m": 3.00, "output_per_1m": 15.00, "fast": False},
    {"id": "claude-haiku-4-5-20251001", "provider": "anthropic", "name": "Claude Haiku 4.5",
     "input_per_1m": 1.00, "output_per_1m": 5.00, "fast": True},
]

MODEL_BY_ID = {m["id"]: m for m in MODELS}

DEFAULT_MODEL = settings.LLM_MODEL


def list_models(provider: Optional[str] = None) -> List[Dict[str, Any]]:
    models = MODELS
    if provider:
        models = [m for m in models if m["provider"] == provider]
    return models


def get_model(model_id: str) -> Optional[Dict[str, Any]]:
    return MODEL_BY_ID.get(model_id)


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    m = MODEL_BY_ID.get(model_id)
    if not m:
        return 0.0
    return (input_tokens / 1_000_000 * m["input_per_1m"]) + \
           (output_tokens / 1_000_000 * m["output_per_1m"])


def build_chat_model(model_id: str, api_key: str) -> Any:
    """Build a langchain chat client for a model id.

    Raises ValueError when the provider/model is unknown or a key is missing.
    """
    m = MODEL_BY_ID.get(model_id)
    if not m:
        raise ValueError(f"Unknown model: {model_id}")
    provider = m["provider"]
    if not api_key:
        raise ValueError(
            f"No API key configured for {PROVIDERS[provider]['name']}. "
            f"Add it via Settings or set {PROVIDERS[provider]['env_key']} in backend/.env."
        )

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(groq_api_key=api_key, model_name=model_id, temperature=0.7)

    if provider == "openai":
        from langchain_community.chat_models import ChatOpenAI
        return ChatOpenAI(model=model_id, api_key=api_key, temperature=0.7)

    if provider == "anthropic":
        from langchain_community.chat_models import ChatAnthropic
        return ChatAnthropic(model=model_id, anthropic_api_key=api_key, temperature=0.7)

    raise ValueError(f"Unsupported provider: {provider}")
