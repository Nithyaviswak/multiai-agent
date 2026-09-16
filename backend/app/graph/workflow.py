from langgraph.graph import StateGraph, END
from typing import Dict, Any, Callable, Awaitable, Optional, List
import time
import asyncio
import uuid

from app.agents.travel_planner_agent import TravelPlannerAgent
from app.agents.mode_route_agent import CarRouteAgent, BusRouteAgent, TrainRouteAgent, BikeRouteAgent
from app.agents.route_comparator_agent import RouteComparatorAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.restaurant_agent import RestaurantAgent
from app.agents.places_agent import PlacesAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.report_generator_agent import ReportGeneratorAgent
from app.schemas.state import AgentState
from app.tools.memory import conversation_memory, project_memory
from app.tools.audit import audit_logger
from app.tools.evaluation import evaluation
from app.logging_config import logger
from app.config import settings


class TravelWorkflow:
    """LangGraph travel-planning workflow with memory and evaluation.

    The graph is a single sequential chain. (The pinned langgraph 0.0.30 has no
    ``Send``/fan-out support, so per-mode route agents and research agents run
    consecutively rather than in true parallel; the idempotency check in
    ``_run_step`` makes extra runs cheap.)

    Failure handling contract:
      - each staged agent runs inside ``_run_step`` which applies a bounded retry
        (``settings.MAX_RETRIES``) with a short delay on transient failures.
      - an agent that still fails records the error and returns ``*_complete=False``.
      - every node is followed by a failure-aware router that either continues to
        the next step or terminates with ``terminal_status="error"``.
    """

    # Node name -> completion field.
    FIELDS = {
        "plan": "plan_complete",
        "route_car": "route_car_complete",
        "route_bus": "route_bus_complete",
        "route_train": "route_train_complete",
        "route_bike": "route_bike_complete",
        "route_compare": "route_complete",
        "gather_knowledge": "knowledge_complete",
        "find_restaurants": "restaurants_complete",
        "find_places": "places_complete",
        "build_itinerary": "itinerary_complete",
        "generate_report": "summary_complete",
    }

    def __init__(self):
        self.agents = {
            "plan": TravelPlannerAgent(),
            "route_car": CarRouteAgent(),
            "route_bus": BusRouteAgent(),
            "route_train": TrainRouteAgent(),
            "route_bike": BikeRouteAgent(),
            "route_compare": RouteComparatorAgent(),
            "gather_knowledge": KnowledgeAgent(),
            "find_restaurants": RestaurantAgent(),
            "find_places": PlacesAgent(),
            "build_itinerary": ItineraryAgent(),
            "generate_report": ReportGeneratorAgent(),
        }
        self._on_step: Optional[Callable[[str], Awaitable[None]]] = None
        self.graph = self._build_graph()

    def set_model(self, model: str) -> None:
        """Apply a model to every agent in the workflow (used by /api/models)."""
        for agent in self.agents.values():
            agent.set_model(model)

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        for node in self.FIELDS:
            workflow.add_node(node, self._make_node(node))

        workflow.set_entry_point("plan")

        # Sequential chain with failure-aware routing after every node.
        chain = list(self.FIELDS.keys())
        for idx, node in enumerate(chain):
            if idx == len(chain) - 1:
                workflow.add_conditional_edges(
                    node, self._make_router(self.FIELDS[node]),
                    {"continue": END, "error": END},
                )
                continue
            workflow.add_conditional_edges(
                node, self._make_router(self.FIELDS[node]),
                {"continue": chain[idx + 1], "error": END},
            )

        return workflow.compile()

    # ── Node wrappers ────────────────────────────────────────────
    def _make_node(self, node: str) -> Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]:
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            if self._on_step:
                try:
                    await self._on_step(node)
                except Exception:
                    pass
            return await self._run_step(state, node, self.agents[node], self.FIELDS[node])
        return wrapper

    async def _run_step(self, state: Dict[str, Any], node: str, agent: Any,
                        success_field: str) -> Dict[str, Any]:
        """Run one agent with bounded retry + timing; never raises.

        Idempotency: if the step already succeeded, return a no-op.
        """
        if state.get(success_field) is True:
            self._append_trace(state, node, time.time(), attempt=1, skipped=True)
            return {}

        if state.get("terminal_status") == "error":
            return {}

        attempt = 0
        last_error = None
        start = time.time()

        while attempt <= settings.MAX_RETRIES:
            attempt += 1
            try:
                result = await agent.process(state)
                if result.get(success_field) is True:
                    usage = getattr(agent, "last_usage", None)
                    self._append_trace(state, node, start, attempt=attempt, usage=usage)
                    evaluation.track(node, "step", True, (time.time() - start) * 1000,
                                     tokens_used=(usage or {}).get("total_tokens", 0),
                                     cost_usd=(usage or {}).get("estimated_cost", 0.0),
                                     run_id=state.get("run_id"))
                    return result
                last_error = (result.get("errors") or [None])[-1] or f"{node} reported incomplete"
            except Exception as e:
                last_error = str(e)
                logger.warning("Step failed, retrying", node=node, attempt=attempt, error=str(e))

            if attempt <= settings.MAX_RETRIES:
                await asyncio.sleep(settings.RETRY_DELAY)

        evaluation.track(node, "step", False, (time.time() - start) * 1000,
                         metadata={"error": last_error}, run_id=state.get("run_id"))
        self._append_trace(state, node, start, attempt=attempt, error=last_error)
        audit_logger.log(f"{node}_failed", state.get("user_id", "unknown"), "workflow",
                         {"node": node, "error": last_error}, "failed")
        logger.error("Step failed after retries", node=node, error=last_error)
        return {
            success_field: False,
            "errors": list(state.get("errors", [])) + [f"{node} failed after {attempt} attempt(s): {last_error}"],
            "terminal_status": "error",
            "current_step": "error",
        }

    # ── Routers ──────────────────────────────────────────────────
    def _make_router(self, field: str) -> Callable[[Dict[str, Any]], str]:
        def route(state: Dict[str, Any]) -> str:
            if state.get("terminal_status") == "error":
                return "error"
            if not state.get(field, False):
                return "error"
            return "continue"
        return route

    # ── Observability helpers ────────────────────────────────────
    def _append_trace(self, state: Dict[str, Any], node: str, start: float,
                      attempt: int = 1, error: str = None, skipped: bool = False,
                      usage: Dict[str, Any] = None):
        entry = {
            "step": node,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(start)),
            "duration_ms": round((time.time() - start) * 1000, 2),
            "attempts": attempt,
            "skipped": skipped,
            "error": error,
            "tokens": (usage or {}).get("total_tokens", 0),
            "cost_usd": (usage or {}).get("estimated_cost", 0.0),
        }
        state.setdefault("trace", []).append(entry)

    # ── Public entrypoint ────────────────────────────────────────
    async def run(self, intent: str, *, origin: Optional[str] = None,
                  destination: Optional[str] = None, travel_modes: Optional[List[str]] = None,
                  meal_types: Optional[List[str]] = None,
                  time_budget_minutes: Optional[int] = None,
                  preferences: Optional[Dict[str, Any]] = None,
                  session_id: str = "default", user_id: str = "engineer",
                  project_id: str = None, run_id: str = None,
                  on_step: Optional[Callable[[str], Awaitable[None]]] = None) -> Dict[str, Any]:
        pid = project_id or session_id
        run_id = run_id or str(uuid.uuid4())
        project_memory.create_project(pid, f"Trip: {intent[:30]}", user_id)

        initial_state: Dict[str, Any] = {
            "intent": intent,
            "run_id": run_id,
            "origin": origin,
            "destination": destination,
            "travel_modes": list(travel_modes or []),
            "meal_types": list(meal_types or []),
            "time_budget_minutes": time_budget_minutes,
            "preferences": preferences or {},
            "plan_complete": False,
            "plan_data": None,
            "route_car_complete": False,
            "route_car_data": None,
            "route_bus_complete": False,
            "route_bus_data": None,
            "route_train_complete": False,
            "route_train_data": None,
            "route_bike_complete": False,
            "route_bike_data": None,
            "route_complete": False,
            "route_data": None,
            "knowledge_complete": False,
            "knowledge_data": None,
            "restaurants_complete": False,
            "restaurants_data": None,
            "places_complete": False,
            "places_data": None,
            "itinerary_complete": False,
            "itinerary_data": None,
            "summary_data": None,
            "summary_complete": False,
            "session_id": session_id,
            "user_id": user_id,
            "errors": [],
            "current_step": "plan",
            "retry_count": 0,
            "should_retry": False,
            "terminal_status": None,
            "trace": [],
            "metrics": None,
        }

        overall_start = time.time()
        from app.tools.calling.registry import current_run_id as _run_ctx
        token = _run_ctx.set(run_id)
        prev_hook = self._on_step
        self._on_step = on_step
        try:
            result = await self.graph.ainvoke(initial_state, {"recursion_limit": 50})
            result.setdefault("run_id", run_id)
            result["metrics"] = self._summarize_metrics(result, overall_start)
            evaluation.record_run(run_id, result["metrics"], trace=result.get("trace"))
            status = result.get("terminal_status") or "complete"
            audit_logger.log("workflow_complete", user_id, "workflow",
                             {"intent": intent, "step": result.get("current_step"),
                              "status": status, "run_id": run_id})
            return result
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            audit_logger.log("workflow_failed", user_id, "workflow",
                             {"intent": intent, "error": str(e), "run_id": run_id}, "failed")
            return {
                **initial_state,
                "errors": [f"Workflow failed: {str(e)}"],
                "current_step": "error",
                "terminal_status": "error",
                "metrics": {"total_latency_ms": round((time.time() - overall_start) * 1000, 2)},
            }
        finally:
            self._on_step = prev_hook
            _run_ctx.reset(token)

    def _summarize_metrics(self, state: Dict[str, Any], overall_start: float) -> Dict[str, Any]:
        trace = state.get("trace", [])
        total_tokens = sum(t.get("tokens", 0) for t in trace)
        total_cost = sum(t.get("cost_usd", 0.0) for t in trace)
        tool_calls = sum(1 for t in trace if str(t.get("step", "")).startswith("tool:"))
        return {
            "run_id": state.get("run_id"),
            "total_latency_ms": round((time.time() - overall_start) * 1000, 2),
            "steps": len(trace),
            "failed_steps": sum(1 for t in trace if t.get("error")),
            "retries_total": sum(max(0, (t.get("attempts") or 1) - 1) for t in trace),
            "skipped_steps": sum(1 for t in trace if t.get("skipped")),
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(total_cost, 6),
            "tool_calls": tool_calls,
            "terminal_status": state.get("terminal_status") or "complete",
        }


travel_workflow = TravelWorkflow()