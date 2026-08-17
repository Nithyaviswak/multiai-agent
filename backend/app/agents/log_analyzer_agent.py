from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.tools.validation import validation_tool
from app.schemas.network_log import LogAnalysisResponse
from app.logging_config import logger

class LogAnalyzerAgent(BaseAgent):
    """Log Analyzer Agent that parses and analyzes network device logs"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        netconf_data = state.get("netconf_data", {})
        device_states = netconf_data.get("device_states", [])
        logger.info("Log analyzer agent started", device_count=len(device_states))

        try:
            analyses = []

            for dev_state in device_states:
                hostname = dev_state["hostname"]
                logs = self._simulate_logs(hostname)

                error_count = sum(1 for log in logs if log["severity"] in ("error", "critical"))
                warning_count = sum(1 for log in logs if log["severity"] == "warning")
                critical_events = [log for log in logs if log["severity"] == "critical"]

                health_score = max(0, 100 - (error_count * 10 + warning_count * 3))

                patterns = self._detect_patterns(logs)
                recommendations = self._generate_recommendations(logs, patterns)

                analysis = {
                    "device": hostname,
                    "total_logs_analyzed": len(logs),
                    "errors_found": error_count,
                    "warnings_found": warning_count,
                    "critical_events": critical_events[:3],
                    "patterns_detected": patterns,
                    "recommendations": recommendations,
                    "health_score": health_score,
                }
                analyses.append(analysis)

            # Aggregate analysis for all devices
            total_errors = sum(a["errors_found"] for a in analyses)
            total_warnings = sum(a["warnings_found"] for a in analyses)
            avg_health = sum(a["health_score"] for a in analyses) / len(analyses) if analyses else 0

            return {
                "log_analysis_complete": True,
                "log_analysis_data": {
                    "device_analyses": analyses,
                    "total_errors": total_errors,
                    "total_warnings": total_warnings,
                    "average_health_score": round(avg_health, 1),
                    "overall_status": "healthy" if avg_health >= 80 else "degraded" if avg_health >= 50 else "critical",
                },
                "current_step": "log_analysis",
            }

        except Exception as e:
            logger.error("Log analyzer agent failed", error=str(e))
            return {
                "log_analysis_complete": False,
                "log_analysis_data": None,
                "errors": state.get("errors", []) + [f"Log analysis failed: {str(e)}"],
            }

    def _simulate_logs(self, hostname: str) -> List[Dict[str, str]]:
        from datetime import datetime, timedelta
        base = datetime.utcnow()
        logs = [
            {"timestamp": (base - timedelta(minutes=5)).isoformat(), "device": hostname,
             "severity": "info", "message": f"%LINEPROTO-5-UPDOWN: Line protocol on {hostname}, changed state to up",
             "log_source": "syslog"},
            {"timestamp": (base - timedelta(minutes=10)).isoformat(), "device": hostname,
             "severity": "info", "message": f"%LINK-3-UPDOWN: Interface GigabitEthernet0/0, changed state to up",
             "log_source": "syslog"},
            {"timestamp": (base - timedelta(hours=1)).isoformat(), "device": hostname,
             "severity": "warning", "message": "%OSPF-5-ADJCHG: Process 1, Nbr 10.0.1.2 on GigabitEthernet0/1 from FULL to DOWN",
             "log_source": "syslog"},
            {"timestamp": (base - timedelta(hours=2)).isoformat(), "device": hostname,
             "severity": "error", "message": "%SEC-6-IPACCESSLOGP: list ACL_IN denied tcp 10.0.0.5(54321) -> 10.0.1.10(80)",
             "log_source": "syslog"},
            {"timestamp": (base - timedelta(hours=3)).isoformat(), "device": hostname,
             "severity": "info", "message": "%SYS-5-CONFIG_I: Configured from console by admin on vty0",
             "log_source": "syslog"},
        ]
        if "core" in hostname:
            logs.append({"timestamp": (base - timedelta(minutes=30)).isoformat(), "device": hostname,
                         "severity": "critical", "message": "%BGP-3-NOTIFICATION: sent to neighbor 10.0.2.2 4/0",
                         "log_source": "syslog"})
        return logs

    def _detect_patterns(self, logs: List[Dict[str, str]]) -> List[str]:
        patterns = []
        error_count = sum(1 for log in logs if log["severity"] in ("error", "critical"))
        if error_count > 2:
            patterns.append("High error rate detected")
        ospf_events = [log for log in logs if "OSPF" in log["message"]]
        if ospf_events:
            patterns.append("OSPF adjacency instability detected")
        sec_events = [log for log in logs if "SEC" in log["message"]]
        if sec_events:
            patterns.append("Security policy violations detected")
        if not patterns:
            patterns.append("Normal operational pattern - no anomalies")
        return patterns

    def _generate_recommendations(self, logs: List[Dict[str, str]],
                                  patterns: List[str]) -> List[str]:
        recs = []
        if any("OSPF" in log["message"] for log in logs):
            recs.append("Investigate OSPF neighbor flapping - check Layer 1 and MTU")
        if any("SEC" in log["message"] for log in logs):
            recs.append("Review ACL rules - denied traffic may indicate policy issue")
        if any("BGP" in log["message"] for log in logs):
            recs.append("BGP notification received - check BGP configuration and peer reachability")
        if not recs:
            recs.append("No significant issues found. Continue monitoring.")
        return recs
