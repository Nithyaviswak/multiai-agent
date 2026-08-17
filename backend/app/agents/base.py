from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.config import settings
from app.logging_config import logger


class BaseAgent(ABC):
    """Base class for all AI agents.

    The LLM client is provider-agnostic: ``_ensure_llm`` builds a client for
    ``self.model`` using the keyring's key for that model's provider. Agent
    logic can be unit-tested without credentials because the client is only
    built lazily on the first call.
    """

    def __init__(self, model: str = None):
        self.model = model or settings.LLM_MODEL
        self.llm = None
        self.max_retries = settings.MAX_RETRIES
        self.last_usage: Dict[str, Any] = {
            "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
            "estimated_cost": 0.0,
        }

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def set_model(self, model: str) -> None:
        """Hot-swap the model (and provider) for this agent."""
        if model == self.model and self.llm is not None:
            return
        self.model = model
        self.llm = None  # rebuilt lazily with the new provider's key

    def _ensure_llm(self) -> Any:
        from app.tools.model_registry import build_chat_model, get_model
        from app.tools.keyring import keyring
        if self.llm is not None:
            return self.llm
        model_meta = get_model(self.model)
        if not model_meta:
            raise RuntimeError(f"Unknown model: {self.model}")
        provider = model_meta["provider"]
        if provider == "custom":
            api_key = model_meta.get("api_key", "")
        else:
            api_key = keyring.get_key(provider)
        if not api_key and provider != "custom":
            raise RuntimeError(
                f"No API key configured for provider '{provider}'. "
                f"Add it in Settings or set the {keyring.status()[provider]['env_key']} env var."
            )
        self.llm = build_chat_model(self.model, api_key)
        return self.llm

    async def _call_llm(self, prompt: str, system_message: str = "") -> Dict[str, Any]:
        """Call the LLM and return ``{"content", "input_tokens", "output_tokens",
        "total_tokens", "estimated_cost"}``.

        The wrapper no longer raises: transient failures are surfaced in the
        result dict so the caller (and the workflow retry loop) can react.
        """
        from langchain_core.messages import HumanMessage, SystemMessage
        from app.tools.model_registry import estimate_cost

        try:
            llm = self._ensure_llm()
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
            response = await llm.ainvoke(messages)

            usage_metadata = getattr(response, "usage_metadata", None)
            if not usage_metadata:
                # Older langchain-core exposes usage under response_metadata.token_usage
                usage_metadata = (getattr(response, "response_metadata", {}) or {}).get("token_usage") or {}
            input_tokens = int(usage_metadata.get("input_tokens") or usage_metadata.get("prompt_tokens") or 0)
            output_tokens = int(usage_metadata.get("output_tokens") or usage_metadata.get("completion_tokens") or 0)
            self.last_usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "estimated_cost": round(estimate_cost(self.model, input_tokens, output_tokens), 6),
                "model": self.model,
            }

            return {
                "content": response.content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "estimated_cost": round(estimate_cost(self.model, input_tokens, output_tokens), 6),
                "model": self.model,
                "error": None,
            }
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            self.last_usage = {
                "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                "estimated_cost": 0.0, "model": self.model,
            }
            return {
                "content": "",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
                "model": self.model,
                "error": str(e),
            }
