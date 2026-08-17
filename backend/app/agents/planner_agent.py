from typing import Dict, Any, List
import re
from app.agents.base import BaseAgent
from app.logging_config import logger

# Deterministic intent -> action classifier. The LLM decomposition is advisory;
# routing decisions (approval gating, config generation) must be deterministic,
# so we override the LLM's action with keyword rules when a clear match exists.
ACTION_KEYWORDS = {
    "configure": ["configure", "setup", "set up", "enable ospf", "enable bgp",
                  "implement", "deploy", "apply config", "apply configuration", "push config",
                  "create vlan", "add vlan", "install", "start ospf", "start bgp", "convert"],
    "verify": ["verify", "check", "validate", "confirm", "ensure", "test", "ping",
               "reachability", "is it up", "show status"],
    "troubleshoot": ["troubleshoot", "fix", "diagnos", "why is", "not working",
                     "connectivity issue", "outage", "problem", "slow"],
    "backup": ["backup", "save config", "archive", "export config", "snapshot"],
    "audit": ["audit", "compliance", "security check", "hardening", "benchmark",
              "policy check", "review security"],
    "generate_report": ["report", "summarize", "summary", "generate report"],
}


def classify_action(intent: str) -> str:
    """Deterministic keyword classifier; returns a default when nothing matches.

    ``configure`` keywords come second-to-last so that "config" appearing inside
    phrases like "Backup the running config" or "validate the applied config"
    does not hijack the action. Explicit configure verbs are matched first.
    """
    text = " " + intent.lower() + " "
    # Explicit verification/backup/audit verbs take precedence before generic
    # substrings, so "validate ... config" is verify and "Backup ... config" is backup.
    for action in ("verify", "backup", "troubleshoot", "audit", "generate_report"):
        for keyword in ACTION_KEYWORDS[action]:
            if re.search(r"\b" + re.escape(keyword) + r"\b", text):
                return action
    for keyword in ACTION_KEYWORDS["configure"]:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text):
            return "configure"
    return "analyze"

class PlannerAgent(BaseAgent):
    """Planner Agent that breaks complex requests into subtasks"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        intent = state.get("intent", "")
        logger.info("Planner agent started", intent=intent)

        try:
            prompt = f"""
            Break this network operations request into a list of subtasks:

            Request: {intent}

            For each subtask, specify:
            - task_id: unique identifier
            - action: what to do (configure, analyze, verify, audit, generate_report)
            - target: target devices or systems
            - depends_on: list of task_ids this depends on (empty for first tasks)
            - description: short description

            Return a JSON object with:
            - tasks: list of task objects
            - reasoning: brief explanation of the plan
            """

            system_message = "You are a network operations planner. Break complex requests into sequential subtasks."

            llm_result = await self._call_llm(prompt, system_message)
            if llm_result["error"]:
                raise RuntimeError(llm_result["error"])

            response = llm_result["content"]

            from app.tools.validation import validation_tool
            extracted = await validation_tool.extract_json_from_text(response)

            tasks = extracted.get("tasks", [])
            reasoning = extracted.get("reasoning", "")

            # Deterministic action/targets: never trust the LLM alone for routing.
            action = classify_action(intent)
            if action == "analyze" and tasks:
                action = tasks[0].get("action", "analyze")
            def _norm_target(t):
                v = t.get("target", "")
                if isinstance(v, list):
                    return ", ".join(str(x) for x in v)
                return str(v or "")
            llm_targets = list(set(
                _norm_target(t) for t in tasks if t.get("target")
            ))
            targets = llm_targets or self._extract_devices(intent)
            priority = "high" if action in ("configure", "troubleshoot") else "medium"

            return {
                "intent_complete": True,
                "intent_data": {
                    "intent_summary": intent[:200],
                    "action": action,
                    "target_devices": targets,
                    "technology": self._extract_technology(intent) or "multi",
                    "parameters": {"tasks": tasks, "reasoning": reasoning},
                    "environment": state.get("intent", "").lower().replace(" ", "-")[:20],
                    "priority": priority,
                },
                "current_step": "plan",
            }

        except Exception as e:
            logger.error("Planner agent failed", error=str(e))
            return {
                "intent_complete": False,
                "intent_data": None,
                "errors": state.get("errors", []) + [f"Planning failed: {str(e)}"],
            }

    def _extract_devices(self, intent: str) -> List[str]:
        """Fallback device extraction from known device hostnames in the intent."""
        from app.tools.network.device_simulator import device_simulator
        known = [d["hostname"] for d in device_simulator.get_all_devices()]
        found = [d for d in known if d in intent]
        if not found and "all devices" in intent:
            return known
        return found

    def _extract_technology(self, intent: str) -> str:
        text = intent.upper()
        if "ACCESS CONTROL" in text or "ACL" in text:
            return "ACL"
        for tech in ("OSPF", "BGP", "VLAN", "NTP", "SNMP", "SSH", "EIGRP", "STP"):
            if tech in text:
                return tech
        return ""
