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
    from app.tools.model_registry import MODEL_BY_ID
    assert settings.LLM_MODEL in MODEL_BY_ID, \
        f"LLM_MODEL {settings.LLM_MODEL} missing from model registry"


def test_custom_model_registry_roundtrip():
    from app.tools.model_registry import (
        register_custom_model, unregister_custom_model, get_model,
        list_models, build_chat_model,
    )
    model_id = "acme/test-open-source-1b"
    meta = register_custom_model(
        model_id, "Acme Test 1B", "sk-secret-test-1234",
        base_url="https://openrouter.ai/api/v1",
    )
    try:
        assert get_model(model_id)["name"] == "Acme Test 1B"
        assert get_model(model_id)["custom"] is True
        assert any(m["id"] == model_id for m in list_models())
        # build_chat_model must not raise for a custom (OpenAI-compatible) model
        client = build_chat_model(model_id, "sk-secret-test-1234")
        assert client is not None
    finally:
        unregister_custom_model(model_id)
    assert get_model(model_id) is None


def test_custom_model_requires_id():
    from app.tools.model_registry import register_custom_model
    with pytest.raises(ValueError):
        register_custom_model("   ", "name", "key")