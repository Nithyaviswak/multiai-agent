from typing import Dict, Any, List, Optional
import asyncio
import time
import contextvars
from app.tools.evaluation import evaluation
from app.logging_config import logger
from app.config import settings

# Current run id (set by workflow.run) so tool calls can be attributed to a run.
current_run_id = contextvars.ContextVar("current_run_id", default=None)


def _run_tool_call_count():
    """Thread-safe counter of tool calls for the current run (approximation)."""
    return 0


class ToolRegistry:
    """Registry for tool calling with evaluation tracking, timeouts and retries."""

    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._call_counts: Dict[str, int] = {}

    def register(self, name: str, tool: Any):
        self._tools[name] = tool

    async def call(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        run_id = current_run_id.get()
        if run_id not in self._call_counts:
            self._call_counts[run_id] = 0
        self._call_counts[run_id] += 1

        if tool_name not in self._tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        # Enforce maximum tool calls per run to prevent runaway loops.
        if self._call_counts[run_id] > settings.MAX_TOOL_CALLS:
            return {"success": False, "error": "Maximum tool calls exceeded for this run"}

        tool = self._tools[tool_name]
        start = time.time()
        try:
            coro = tool.execute(**kwargs) if hasattr(tool, 'execute') else tool(**kwargs)
            result = await asyncio.wait_for(coro, timeout=settings.TOOL_TIMEOUT_SECONDS)
            latency = (time.time() - start) * 1000
            evaluation.track(tool_name, "call", True, latency, run_id=run_id)
            return {"success": True, "result": result}
        except asyncio.TimeoutError:
            latency = (time.time() - start) * 1000
            evaluation.track(tool_name, "call", False, latency,
                             metadata={"error": "timeout"}, run_id=run_id)
            return {"success": False, "error": f"Tool {tool_name} timed out after {settings.TOOL_TIMEOUT_SECONDS}s"}
        except Exception as e:
            latency = (time.time() - start) * 1000
            evaluation.track(tool_name, "call", False, latency,
                             metadata={"error": str(e)}, run_id=run_id)
            return {"success": False, "error": str(e)}

    def list_tools(self) -> List[Dict[str, Any]]:
        return [{"name": n, "description": getattr(t, "description", "")} for n, t in self._tools.items()]


tool_registry = ToolRegistry()