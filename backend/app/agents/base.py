from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_groq import ChatGroq
from app.config import settings
from app.logging_config import logger

# Estimated cost per 1M tokens (USD) for Groq-hosted models. These are list
# prices used for internal budgeting; real cost depends on the provider bill.
MODEL_COST_PER_1M = {
    "openai/gpt-oss-120b": {"input": 0.24, "output": 0.96},
    "openai/gpt-oss-20b": {"input": 0.06, "output": 0.24},
    "qwen/qwen3.6-27b": {"input": 0.10, "output": 0.40},
    "allam-2-7b": {"input": 0.05, "output": 0.20},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for a single call using the built-in pricing table."""
    rates = MODEL_COST_PER_1M.get(model, {"input": 0.10, "output": 0.40})
    return (input_tokens / 1_000_000 * rates["input"]) + (output_tokens / 1_000_000 * rates["output"])


class BaseAgent(ABC):
    """Base class for all AI agents"""

    def __init__(self):
        # Only construct the LLM client when a key is configured, so agent logic
        # can be unit-tested without credentials. Startup validation fails fast
        # when a key is genuinely missing at runtime.
        if settings.GROQ_API_KEY:
            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=settings.LLM_MODEL,
                temperature=0.7
            )
        else:
            self.llm = None
        self.model = settings.LLM_MODEL
        self.max_retries = settings.MAX_RETRIES
        self.last_usage: Dict[str, Any] = {
            "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
            "estimated_cost": 0.0,
        }

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass

    async def _call_llm(self, prompt: str, system_message: str = "") -> Dict[str, Any]:
        """Call the LLM and return ``{"content", "input_tokens", "output_tokens",
        "total_tokens", "estimated_cost"}``.

        The wrapper no longer raises: transient failures are surfaced in the
        result dict so the caller (and the workflow retry loop) can react.
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        try:
            if not self.llm:
                raise RuntimeError(
                    "GROQ_API_KEY is not configured; cannot call LLM. "
                    "Set it in backend/.env and restart."
                )
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
            response = await self.llm.ainvoke(messages)

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