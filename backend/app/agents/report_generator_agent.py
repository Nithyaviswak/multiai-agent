from typing import Dict, Any
from app.agents.base import BaseAgent
from app.tools.calling.report_generator_tool import report_generator_tool
from app.logging_config import logger

class ReportGeneratorAgent(BaseAgent):
    """Report Generator Agent that creates executive summaries"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Report generator agent started")

        try:
            intent_data = state.get("intent_data", {})
            config_data = state.get("config_data", {})
            verification_data = state.get("verification_data", {})
            compliance_data = state.get("compliance_data", {})
            log_analysis_data = state.get("log_analysis_data", {})
            incident_data = state.get("incident_response_data", {})
            monitoring_data = state.get("monitoring_data", {})

            sections = {
                "Executive Summary": f"Network automation completed for intent: {intent_data.get('intent_summary', 'N/A')}. "
                                     f"Configuration generated: {config_data.get('total_devices', 0)} devices. "
                                     f"Verification: {'All passed' if verification_data.get('all_passed') else 'Some failed'}.",
                "Configuration Changes": f"Technology: {config_data.get('technology', 'N/A')}. "
                                         f"Devices configured: {config_data.get('total_devices', 0)}. "
                                         f"Status: {config_data.get('generation_status', 'N/A')}.",
                "Compliance Report": f"Standard: {compliance_data.get('standard', 'N/A')}. "
                                     f"Score: {compliance_data.get('overall_score', 0)}%. "
                                     f"Passed: {compliance_data.get('passed', 0)}/{compliance_data.get('total_checks', 0)}.",
                "Monitoring Summary": f"Devices: {monitoring_data.get('total_devices', 0)}. "
                                      f"Alerts: {monitoring_data.get('active_alerts', 0)}. "
                                      f"Health: {monitoring_data.get('overall_health', 'unknown')}.",
                "Log Analysis": f"Total errors: {log_analysis_data.get('total_errors', 0)}. "
                                f"Health score: {log_analysis_data.get('average_health_score', 0)}%.",
                "Incident Response": (f"Severity: {incident_data.get('severity', 'none')}. "
                                      f"Root cause: {incident_data.get('root_cause', 'N/A')}. "
                                      f"Escalation: {incident_data.get('escalation_required', False)}.")
                if incident_data and incident_data.get("incident_id") else "No incidents detected.",
            }

            metrics = {
                "devices_discovered": state.get("topology_data", {}).get("device_count", 0),
                "configs_generated": config_data.get("total_devices", 0),
                "compliance_score": compliance_data.get("overall_score", 0),
                "health_score": log_analysis_data.get("average_health_score", 0),
                "incidents": 1 if incident_data and incident_data.get("incident_id") else 0,
            }

            report = await report_generator_tool.execute(
                title=f"Network Automation Report: {intent_data.get('intent_summary', 'Network Operations')[:60]}",
                sections=sections,
                metrics=metrics,
            )

            return {
                "summary_complete": True,
                "summary_data": report,
                "current_step": "complete",
            }

        except Exception as e:
            logger.error("Report generator agent failed", error=str(e))
            return {
                "summary_complete": False,
                "summary_data": None,
                "errors": state.get("errors", []) + [f"Report generation failed: {str(e)}"],
            }
