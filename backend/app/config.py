from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Groq models verified reachable via the API as of 2026-08-17.
# NOTE: `llama-3.1-8b-instant` returned HTTP 404 (model no longer served).
VALID_GROQ_MODELS = {
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "allam-2-7b",
}

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GROQ_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    # Default must be a model that currently exists on Groq (verified 2026-08-17).
    LLM_MODEL: str = "openai/gpt-oss-20b"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600

    MAX_RETRIES: int = 2
    RETRY_DELAY: int = 1

    LOG_LEVEL: str = "INFO"

    # Travel Planning Settings
    DEFAULT_TIME_BUDGET_MINUTES: int = 360
    DEFAULT_TRAVEL_MODES: str = "car,bus,train,bike"
    DEFAULT_MEAL_TYPES: str = "tiffin,lunch,dinner"
    MEAL_DURATION_MINUTES: int = 45
    MAX_PLACES_TO_COVER: int = 5
    PLACES_RADIUS_METERS: int = 15000
    RESTAURANT_RADIUS_METERS: int = 5000

    # Guardrails
    ALLOW_PYTHON_EXEC: bool = False
    MAX_AGENT_ITERATIONS: int = 6
    MAX_TOOL_CALLS: int = 50
    TOOL_TIMEOUT_SECONDS: float = 15.0

    # Observability / retention
    MAX_WORKFLOW_STATE_ENTRIES: int = 500

settings = Settings()


def validate_settings() -> Optional[list[str]]:
    """Fail-fast validation of required settings.

    Returns a list of human-readable problems (empty when OK). This lets the
    API surface a clear, actionable error instead of a confusing 404/500 from
    an unknown model or a missing key.
    """
    problems: list[str] = []

    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("your_"):
        problems.append(
            "GROQ_API_KEY is missing. Set it in backend/.env (see .env.example)."
        )

    if settings.LLM_MODEL and settings.LLM_MODEL not in VALID_GROQ_MODELS:
        problems.append(
            f"LLM_MODEL={settings.LLM_MODEL!r} is not in the list of models verified "
            f"to exist on Groq: {sorted(VALID_GROQ_MODELS)}. Update LLM_MODEL in backend/.env."
        )

    return problems


def validate_optional() -> Optional[list[str]]:
    """Warnings for soft-optional settings that degrade functionality, not fail it.

    The API still boots without a Google Maps key — routing, restaurant and
    place agents report step failures gracefully and the UI surfaces an honest
    "maps not configured" state. Supplying the key later re-enables live data.
    """
    problems: list[str] = []

    if not settings.GOOGLE_MAPS_API_KEY or settings.GOOGLE_MAPS_API_KEY.startswith("your_"):
        problems.append(
            "GOOGLE_MAPS_API_KEY is not set — live route, restaurant and place "
            "data from Google Maps will be unavailable. Add it to backend/.env "
            "to enable real map data."
        )

    return problems
