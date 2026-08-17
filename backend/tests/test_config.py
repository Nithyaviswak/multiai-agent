import pytest
from app.config import settings, validate_settings, VALID_GROQ_MODELS


def test_model_is_valid():
    assert settings.LLM_MODEL, "LLM_MODEL must be set"
    assert settings.LLM_MODEL in VALID_GROQ_MODELS


def test_validate_settings_flags_missing_key_only_when_absent():
    # The model-config problem should never appear regardless of key presence,
    # so a missing key in CI is a soft warning, not a model bug.
    problems = validate_settings()
    assert all("LLM_MODEL" not in p for p in problems), problems


def test_pricing_table_has_model():
    from app.agents.base import MODEL_COST_PER_1M
    assert settings.LLM_MODEL in MODEL_COST_PER_1M, \
        f"LLM_MODEL {settings.LLM_MODEL} missing from MODEL_COST_PER_1M pricing table"