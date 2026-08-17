from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import math
from app.logging_config import logger


class EvaluationTracker:
    """Tracks metrics for agent evaluation.

    In-memory metric store:
      - ``_metrics``: flat per-agent (success, latency, tokens, cost) events.
      - ``_runs``: per-run summaries (run_id -> metrics) so end-to-end runs are
        reproducible and queryable by run id.
    """

    def __init__(self):
        self._metrics: List[Dict[str, Any]] = []
        self._runs: Dict[str, Dict[str, Any]] = {}
        self._max_metrics = 100_000  # bound memory

    def track(self, agent: str, action: str, success: bool, latency_ms: float,
              tokens_used: int = 0, cost_usd: float = 0.0, run_id: str = None,
              metadata: Dict = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "action": action,
            "success": success,
            "latency_ms": round(latency_ms, 2),
            "tokens_used": tokens_used,
            "cost_usd": round(cost_usd, 6),
            "run_id": run_id,
            "metadata": metadata or {},
        }
        self._metrics.append(entry)
        if len(self._metrics) > self._max_metrics:
            self._metrics = self._metrics[-self._max_metrics:]

        if run_id:
            run = self._runs.setdefault(run_id, {
                "run_id": run_id,
                "events": [],
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "successes": 0,
                "failures": 0,
            })
            run["events"].append(entry["agent"])
            run["total_tokens"] += tokens_used
            run["total_cost_usd"] = round(run["total_cost_usd"] + cost_usd, 6)
            run["successes"] += 1 if success else 0
            run["failures"] += 0 if success else 1

    def record_run(self, run_id: str, metrics: Dict[str, Any], trace: Optional[List] = None):
        """Attach end-to-end run metrics (latency, trace length, etc.)."""
        run = self._runs.setdefault(run_id, {"run_id": run_id, "events": [],
                                             "total_tokens": 0, "total_cost_usd": 0.0,
                                             "successes": 0, "failures": 0})
        run.update(metrics)
        if trace:
            run["trace"] = trace

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self._runs.get(run_id)

    def get_agent_stats(self, agent: str = None) -> Dict[str, Any]:
        metrics = self._metrics
        if agent:
            metrics = [m for m in metrics if m["agent"] == agent]
        if not metrics:
            return {}
        total = len(metrics)
        success = sum(1 for m in metrics if m["success"])
        avg_latency = sum(m["latency_ms"] for m in metrics) / total if total else 0
        total_tokens = sum(m.get("tokens_used", 0) for m in metrics)
        total_cost = sum(m.get("cost_usd", 0.0) for m in metrics)
        return {
            "total_calls": total,
            "success_rate": round(success / total * 100, 1) if total else 0,
            "avg_latency_ms": round(avg_latency, 2),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
        }

    def get_summary(self) -> Dict[str, Any]:
        agents = set(m["agent"] for m in self._metrics)
        return {
            "total_actions": len(self._metrics),
            "agents_monitored": sorted(agents),
            "agent_stats": {a: self.get_agent_stats(a) for a in agents},
            "total_runs": len(self._runs),
        }


evaluation = EvaluationTracker()