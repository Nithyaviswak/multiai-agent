"""Model registry: providers, models, and client factories.

The platform is provider-agnostic. Each provider maps to a langchain chat
client. ``build_chat_model`` returns a fresh client for a model id using the
API key provided by the caller (usually from the keyring).

Besides the built-in catalog, users can register **custom models** at runtime
against any OpenAI-compatible endpoint (OpenRouter, Together, Mistral, Groq,
and local servers like Ollama). Each custom model carries its own name and API
key, so a user can add "model name + API key" directly from the UI.
"""
from typing import Any, Dict, List, Optional

from app.config import settings

# Provider -> display name and the env var that seeds its key.
PROVIDERS: Dict[str, Dict[str, str]] = {
    "groq": {
        "name": "Groq",
        "env_key": "GROQ_API_KEY",
        "note": "Fast inference on free open models (gpt-oss, qwen, allam, compound).",
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
    "custom": {
        "name": "Custom / OpenAI-compatible",
        "env_key": "",
        "note": "Add any model by name + API key, e.g. OpenRouter, Together, Ollama.",
    },
}

# Model catalog. Cost per 1M tokens (USD) used only for internal budgeting.
MODELS: List[Dict[str, Any]] = [
    # ── Groq (verified live 2026-08-17) ───────────────────────────
    {"id": "openai/gpt-oss-120b", "provider": "groq", "name": "GPT-OSS 120B",
     "input_per_1m": 0.24, "output_per_1m": 0.96, "fast": False, "free": True},
    {"id": "openai/gpt-oss-20b", "provider": "groq", "name": "GPT-OSS 20B",
     "input_per_1m": 0.06, "output_per_1m": 0.24, "fast": True, "free": True},
    {"id": "qwen/qwen3.6-27b", "provider": "groq", "name": "Qwen 3.6 27B",
     "input_per_1m": 0.10, "output_per_1m": 0.40, "fast": True, "free": True},
    {"id": "allam-2-7b", "provider": "groq", "name": "ALLAM 2 7B",
     "input_per_1m": 0.05, "output_per_1m": 0.20, "fast": True, "free": True},
    {"id": "groq/compound-mini", "provider": "groq", "name": "Compound Mini",
     "input_per_1m": 0.10, "output_per_1m": 0.40, "fast": True, "free": True},
    {"id": "groq/compound", "provider": "groq", "name": "Compound",
     "input_per_1m": 0.30, "output_per_1m": 1.20, "fast": False, "free": True},
    # ── OpenAI ───────────────────────────────────────────────────
    {"id": "gpt-4o", "provider": "openai", "name": "GPT-4o",
     "input_per_1m": 2.50, "output_per_1m": 10.00, "fast": False, "free": False},
    {"id": "gpt-4o-mini", "provider": "openai", "name": "GPT-4o mini",
     "input_per_1m": 0.15, "output_per_1m": 0.60, "fast": True, "free": False},
    # ── Anthropic ────────────────────────────────────────────────
    {"id": "claude-sonnet-4-20250514", "provider": "anthropic", "name": "Claude Sonnet 4",
     "input_per_1m": 3.00, "output_per_1m": 15.00, "fast": False, "free": False},
    {"id": "claude-haiku-4-5-20251001", "provider": "anthropic", "name": "Claude Haiku 4.5",
     "input_per_1m": 1.00, "output_per_1m": 5.00, "fast": True, "free": False},
]

# Runtime-registered custom models: model_id -> meta (includes the API key,
# stored in memory and never returned to the client).
CUSTOM_MODELS: Dict[str, Dict[str, Any]] = {}

MODEL_BY_ID = {m["id"]: m for m in MODELS}

DEFAULT_MODEL = settings.LLM_MODEL

# Common OpenAI-compatible endpoints offered in the "add a model" UI.
FAST_BASE_URLS = {
    "OpenRouter": "https://openrouter.ai/api/v1",
    "Groq": "https://api.groq.com/openai/v1",
    "Together AI": "https://api.together.xyz/v1",
    "Mistral": "https://api.mistral.ai/v1",
    "Ollama (local)": "http://localhost:11434/v1",
    "OpenAI": "https://api.openai.com/v1",
}


def list_base_urls() -> Dict[str, str]:
    return FAST_BASE_URLS


def list_models(provider: Optional[str] = None) -> List[Dict[str, Any]]:
    models = MODELS + list(CUSTOM_MODELS.values())
    if provider:
        models = [m for m in models if m["provider"] == provider]
    return models


def get_model(model_id: str) -> Optional[Dict[str, Any]]:
    if model_id in CUSTOM_MODELS:
        return CUSTOM_MODELS[model_id]
    return MODEL_BY_ID.get(model_id)


def register_custom_model(
    model_id: str, name: str, api_key: str, base_url: Optional[str] = None
) -> Dict[str, Any]:
    """Register a user-supplied model (name + API key) at runtime.

    ``base_url`` may point at any OpenAI-compatible endpoint (OpenRouter,
    Together, Mistral, Groq, an Ollama instance, etc.). Empty ``api_key`` is
    allowed for local endpoints that do not need one.
    """
    model_id = model_id.strip()
    if not model_id:
        raise ValueError("Model ID cannot be empty")
    meta = {
        "id": model_id,
        "name": name.strip() or model_id,
        "provider": "custom",
        "input_per_1m": 0.0,
        "output_per_1m": 0.0,
        "fast": False,
        "free": True,
        "custom": True,
        "base_url": (base_url or "").strip() or "https://api.openai.com/v1",
        "api_key": api_key.strip(),
    }
    CUSTOM_MODELS[model_id] = meta
    return meta


def unregister_custom_model(model_id: str) -> bool:
    return CUSTOM_MODELS.pop(model_id, None) is not None


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    m = get_model(model_id)
    if not m:
        return 0.0
    return (input_tokens / 1_000_000 * m["input_per_1m"]) + \
           (output_tokens / 1_000_000 * m["output_per_1m"])


def build_chat_model(model_id: str, api_key: str) -> Any:
    """Build a langchain chat client for a model id.

    Raises ValueError when the provider/model is unknown or a key is missing.
    """
    m = get_model(model_id)
    if not m:
        raise ValueError(f"Unknown model: {model_id}")
    provider = m["provider"]

    if provider == "custom":
        from langchain_community.chat_models import ChatOpenAI
        base_url = m.get("base_url") or "https://api.openai.com/v1"
        # Local endpoints (e.g. Ollama) may not require a key.
        return ChatOpenAI(
            model=model_id,
            api_key=api_key or "not-needed",
            base_url=base_url,
            temperature=0.7,
        )

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