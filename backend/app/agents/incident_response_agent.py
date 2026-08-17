from typing import Dict, Any
from app.agents.base import BaseAgent
from app.tools.validation import validation_tool
from app.schemas.network_incident import IncidentResponse
from app.logging_config import logger

class IncidentResponseAgent(BaseAgent):
    """Incident Response Agent that analyzes and responds to network incidents"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        compliance_data = state.get("compliance_data", {})
        log_analysis_data = state.get("log_analysis_data", {})
        logger.info("Incident response agent started")

        try:
            device_analyses = log_analysis_data.get("device_analyses", [])
            compliance_checks = compliance_data.get("checks", [])

            affected_devices = set()
            critical_findings = []

            for analysis in device_analyses:
                if analysis.get("health_score", 100) < 60:
                    affected_devices.add(analysis["device"])
                    for event in analysis.get("critical_events", []):
                        critical_findings.append(event)

            for check in compliance_checks:
                if check.get("status") == "fail" and check.get("severity") in ("critical", "high"):
                    affected_devices.add(check.get("device", ""))

            if not affected_devices:
                return {
                    "incident_response_data": {
                        "incident_id": None,
                        "title": "No incidents detected",
                        "severity": "info",
                        "affected_devices": [],
                        "root_cause": "All devices operating normally",
                        "impact_analysis": "No impact - network is stable",
                        "recommended_actions": ["Continue monitoring"],
                        "auto_remediation": False,
                        "auto_remediation_result": None,
                        "escalation_required": False,
                    },
                    "incident_complete": True,
                    "current_step": "incident_response",
                }

            severity = "critical" if len(affected_devices) >= 2 else "high"
            incident_data = {
                "incident_id": f"INC-{hash(str(affected_devices)) % 100000:05d}",
                "title": f"Network incident affecting {', '.join(affected_devices)}",
                "severity": severity,
                "affected_devices": list(affected_devices),
                "root_cause": self._determine_root_cause(critical_findings, compliance_checks),
                "impact_analysis": self._analyze_impact(affected_devices),
                "recommended_actions": self._build_actions(critical_findings, compliance_checks),
                "auto_remediation": False,
                "auto_remediation_result": None,
                "escalation_required": severity == "critical",
            }

            is_valid, validated, error_msg = await validation_tool.validate_output(
                incident_data, IncidentResponse
            )
            if not is_valid:
                raise ValueError(f"Incident validation failed: {error_msg}")

            return {
                "incident_response_data": validated.dict(),
                "incident_complete": True,
                "current_step": "incident_response",
            }

        except Exception as e:
            logger.error("Incident response agent failed", error=str(e))
            return {
                "incident_response_data": None,
                "incident_complete": False,
                "errors": state.get("errors", []) + [f"Incident response failed: {str(e)}"],
            }

    def _determine_root_cause(self, critical_events: list, compliance_checks: list) -> str:
        if critical_events:
            for event in critical_events:
                if "BGP" in event.get("message", ""):
                    return "BGP session flapping detected between core and edge routers"
                if "OSPF" in event.get("message", ""):
                    return "OSPF adjacency instability due to Layer 1 issues or MTU mismatch"
            return "Multiple critical events detected across devices"
        return "Compliance violations detected that require remediation"

    def _analyze_impact(self, affected_devices: set) -> str:
        if len(affected_devices) >= 2:
            return ("Redundant paths may be affected. "
                    f"{len(affected_devices)} devices impacted. "
                    "Potential service disruption for dependent networks.")
        return (f"Single device {list(affected_devices)[0]} impacted. "
                "Service may be degraded for connected endpoints.")

    def _build_actions(self, critical_events: list, compliance_checks: list) -> list:
        actions = []
        seen = set()

        for event in critical_events:
            msg = event.get("message", "")
            if "BGP" in msg and "BGP" not in seen:
                actions.append("Immediate: Restart BGP session and verify configuration")
                seen.add("BGP")
            if "OSPF" in msg and "OSPF" not in seen:
                actions.append("Verify OSPF interface parameters (MTU, timers, authentication)")
                seen.add("OSPF")

        for check in compliance_checks:
            if check.get("status") == "fail" and check.get("severity") == "critical":
                rec = check.get("recommendation", "")
                if rec and rec not in seen:
                    actions.append(f"Remediate: {rec}")
                    seen.add(rec)

        if not actions:
            actions.append("Monitor affected devices for 15 minutes")
            actions.append("Collect additional diagnostic data")
            actions.append("Escalate if condition persists")

        return actions[:5]
