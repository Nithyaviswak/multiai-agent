from langgraph.graph import StateGraph, END
from typing import Dict, Any, Callable, Awaitable
import time
import asyncio
import uuid

from app.agents.planner_agent import PlannerAgent
from app.agents.topology_agent import TopologyAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.netconf_agent import NETCONFAgent
from app.agents.configuration_agent import ConfigurationAgent
from app.agents.automation_agent import AutomationAgent
from app.agents.verification_agent import VerificationAgent
from app.agents.monitoring_agent import MonitoringAgent
from app.agents.compliance_checker_agent import ComplianceCheckerAgent
from app.agents.log_analyzer_agent import LogAnalyzerAgent
from app.agents.incident_response_agent import IncidentResponseAgent
from app.agents.report_generator_agent import ReportGeneratorAgent
from app.schemas.state import AgentState
from app.tools.memory import conversation_memory, project_memory
from app.tools.audit import audit_logger
from app.tools.evaluation import evaluation
from app.tools.guardrails import guardrails
from app.tools.calling.registry import tool_registry
from app.logging_config import logger
from app.config import settings


class NetworkWorkflow:
    """Enterprise LangGraph workflow with memory, human approval, and evaluation.

    Failure handling contract:
      - each staged agent runs inside ``_run_step`` which applies a bounded retry
        (``settings.MAX_RETRIES``) with a short delay on transient failures.
      - an agent that still fails records the error and returns ``*_complete=False``.
      - every node is followed by a failure-aware router that either continues to
        the next step or terminates with ``terminal_status="error"``.
      - mutating actions pause at the approval gate; ``resume_after_approval``
        re-enters the graph and all completed steps pass through as no-ops, so
        only report generation executes on resume.

    Determinism: completed steps are idempotent on resume, and ``run()`` always
    returns a serializable state with a truthful ``current_step``/``terminal_status``.
    """

    STEPS = [
        {"node": "plan", "field": "intent_complete"},
        {"node": "discover_topology", "field": "topology_complete"},
        {"node": "gather_knowledge", "field": "knowledge_complete"},
        {"node": "gather_netconf", "field": "netconf_complete"},
        {"node": "generate_config", "field": "config_complete"},
        {"node": "run_automation", "field": "automation_complete"},
        {"node": "verify_config", "field": "verification_complete"},
        {"node": "monitor", "field": "monitoring_complete"},
        {"node": "check_compliance", "field": "compliance_complete"},
        {"node": "analyze_logs", "field": "log_analysis_complete"},
        {"node": "respond_incident", "field": "incident_complete"},
    ]

    # Node names -> agents kept cached so we can reuse instances across runs.
    def __init__(self):
        self.agents = {
            "plan": PlannerAgent(),
            "discover_topology": TopologyAgent(),
            "gather_knowledge": KnowledgeAgent(),
            "gather_netconf": NETCONFAgent(),
            "generate_config": ConfigurationAgent(),
            "run_automation": AutomationAgent(),
            "verify_config": VerificationAgent(),
            "monitor": MonitoringAgent(),
            "check_compliance": ComplianceCheckerAgent(),
            "analyze_logs": LogAnalyzerAgent(),
            "respond_incident": IncidentResponseAgent(),
            "generate_report": ReportGeneratorAgent(),
        }
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        for step in self.STEPS:
            workflow.add_node(step["node"], self._make_step_node(step["node"]))

        workflow.add_node("approval_gate", self._approval_gate_node)
        workflow.add_node("generate_report", self._report_node)

        workflow.set_entry_point("plan")

        for i, step in enumerate(self.STEPS):
            _next = self.STEPS[i + 1]["node"] if i + 1 < len(self.STEPS) else "approval_gate"
            router = self._make_router(step["field"])
            workflow.add_conditional_edges(
                step["node"], router, {"continue": _next, "error": END}
            )

        workflow.add_conditional_edges(
            "approval_gate",
            self._route_approval,
            {"continue": "generate_report", "error": END, "awaiting": END},
        )

        workflow.add_edge("generate_report", END)
        return workflow.compile()

    # ── Node wrappers ────────────────────────────────────────────
    def _make_step_node(self, node: str) -> Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]:
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            step_cfg = next(s for s in self.STEPS if s["node"] == node)
            return await self._run_step(state, node, self.agents[node], step_cfg["field"])
        return wrapper

    async def _run_step(self, state: Dict[str, Any], node: str, agent: Any,
                        success_field: str) -> Dict[str, Any]:
        """Run one agent with bounded retry + timing; never raises.

        Idempotency: if the step already succeeded, return a no-op so resumed
        approval flows skip completed work instead of re-invoking the LLM.
        """
        # Already completed (resume pass-through) - record a lightweight trace entry.
        if state.get(success_field) is True:
            self._append_trace(state, node, time.time(), attempt=1, skipped=True)
            return {}

        if state.get("terminal_status") in ("error", "awaiting_approval"):
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

    async def _approval_gate_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Gate mutating actions behind human approval before report generation."""
        if state.get("terminal_status") in ("error", "awaiting_approval"):
            return {}

        action = (state.get("intent_data") or {}).get("action", "analyze")
        if action not in ("configure", "push", "delete"):
            return {"requires_approval": False, "current_step": "report"}

        # On resume the user already approved - proceed to report.
        if state.get("approved"):
            return {"approved": True, "current_step": "report"}

        approval_id = f"APR-{abs(hash(str(state.get('run_id', '')))) % 100000:05d}"
        config_summary = {
            "approval_id": approval_id,
            "action": action,
            "devices": (state.get("intent_data") or {}).get("target_devices", []),
            "technology": (state.get("config_data") or {}).get("technology", "N/A"),
        }
        audit_logger.log("approval_required", state.get("user_id", "unknown"), "config",
                         config_summary, "pending")
        return {
            "requires_approval": True,
            "approved": False,
            "approval_id": approval_id,
            "terminal_status": "awaiting_approval",
            "current_step": "awaiting_approval",
        }

    async def _report_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if state.get("terminal_status") == "error":
            return self._graceful_error_report(state)
        start = time.time()
        try:
            result = await self.agents["generate_report"].process(state)
            session_id = state.get("session_id", "default")
            conversation_memory.add_message(session_id, "assistant",
                                            str(result.get("summary_data", {})))
            self._append_trace(state, "generate_report", start)
            evaluation.track("generate_report", "step", True, (time.time() - start) * 1000)
            return {**result, "terminal_status": "complete", "current_step": "complete"}
        except Exception as e:
            self._append_trace(state, "generate_report", start, error=str(e))
            evaluation.track("generate_report", "step", False, (time.time() - start) * 1000)
            return self._graceful_error_report(state, error=str(e))

    def _graceful_error_report(self, state: Dict[str, Any], error: str = None) -> Dict[str, Any]:
        errors = list(state.get("errors", []))
        if error:
            errors.append(error)
        return {
            "summary_complete": True,
            "summary_data": {
                "workflow_status": "failed",
                "errors": errors,
                "message": "Workflow did not complete successfully. See errors for details.",
            },
            "terminal_status": "error",
            "current_step": "error",
            "errors": errors,
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

    def _route_approval(self, state: Dict[str, Any]) -> str:
        ts = state.get("terminal_status")
        if ts == "error":
            return "error"
        if ts == "awaiting_approval":
            return "awaiting"
        return "continue"

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
    async def run(self, intent: str, environment: str = "devnet-sandbox",
                  session_id: str = "default", user_id: str = "engineer",
                  project_id: str = None, run_id: str = None) -> Dict[str, Any]:
        pid = project_id or session_id
        run_id = run_id or str(uuid.uuid4())
        project_memory.create_project(pid, f"Project: {intent[:30]}", user_id)

        initial_state: Dict[str, Any] = {
            "intent": intent,
            "run_id": run_id,
            "intent_complete": False,
            "intent_data": None,
            "knowledge_data": None,
            "topology_complete": False,
            "topology_data": None,
            "netconf_complete": False,
            "netconf_data": None,
            "config_complete": False,
            "config_data": None,
            "automation_data": None,
            "verification_complete": False,
            "verification_data": None,
            "monitoring_data": None,
            "compliance_complete": False,
            "compliance_data": None,
            "log_analysis_complete": False,
            "log_analysis_data": None,
            "incident_response_data": None,
            "summary_data": None,
            "summary_complete": False,
            "session_id": session_id,
            "user_id": user_id,
            "requires_approval": False,
            "approved": False,
            "approval_id": None,
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
            _run_ctx.reset(token)

    async def resume_after_approval(self, state: Dict[str, Any], approved: bool) -> Dict[str, Any]:
        """Resume a paused workflow from the approval gate.

        - approved=True -> mark approved and re-enter the graph; completed steps
          pass through as no-ops and only report generation executes.
        - approved=False -> terminal state `denied`.
        """
        state = dict(state)
        overall_start = time.time()

        if not approved:
            logger.info("Approval denied", run_id=state.get("run_id"))
            return {
                **state,
                "approved": False,
                "terminal_status": "denied",
                "current_step": "denied",
                "summary_data": {
                    "workflow_status": "denied",
                    "message": "Configuration action was denied by the user.",
                },
                "metrics": self._summarize_metrics(state, overall_start),
            }

        logger.info("Approval granted, resuming", run_id=state.get("run_id"))
        state.update({
            "approved": True,
            "terminal_status": None,
            "current_step": "report",
            "errors": list(state.get("errors", [])),
        })
        try:
            result = await self.graph.ainvoke(state, {"recursion_limit": 50})
            result.setdefault("run_id", state.get("run_id"))
            result["approved"] = True
            result["metrics"] = self._summarize_metrics(result, overall_start)
            return result
        except Exception as e:
            logger.error("Approval resume failed", error=str(e), run_id=state.get("run_id"))
            return {
                **state,
                "terminal_status": "error",
                "current_step": "error",
                "errors": list(state.get("errors", [])) + [f"Approval resume failed: {str(e)}"],
                "metrics": self._summarize_metrics(state, overall_start),
            }

    def _summarize_metrics(self, state: Dict[str, Any], overall_start: float) -> Dict[str, Any]:
        trace = state.get("trace", [])
        total_tokens = sum(t.get("tokens", 0) for t in trace)
        total_cost = sum(t.get("cost_usd", 0.0) for t in trace)
        from app.tools.calling.registry import tool_registry
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


network_workflow = NetworkWorkflow()