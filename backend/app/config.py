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

    # Network Automation Settings
    MOCK_ENVIRONMENT: str = "devnet-sandbox"
    CONFIG_BACKUP_PATH: str = "./backups"
    COMPLIANCE_STANDARD: str = "CIS_BENCHMARK"

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
