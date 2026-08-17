from typing import Dict, Any, List

LOG_PATTERNS = {
    "ospf_down": {"keywords": ["OSPF", "DOWN", "FULL to"], "severity": "high",
                  "suggestion": "Check OSPF neighbor interface status and MTU"},
    "bgp_reset": {"keywords": ["BGP", "NOTIFICATION", "RESET"], "severity": "critical",
                  "suggestion": "Verify BGP configuration and peer reachability"},
    "interface_down": {"keywords": ["LINEPROTO", "UPDOWN", "changed state to down"], "severity": "high",
                       "suggestion": "Check physical layer and interface configuration"},
    "auth_failure": {"keywords": ["AUTH", "FAILURE", "LOGIN"], "severity": "medium",
                     "suggestion": "Verify credentials and AAA configuration"},
}

class LogParserTool:
    description = "Parse and analyze network device logs"

    async def execute(self, logs: List[str]) -> Dict[str, Any]:
        findings = []
        for log in logs:
            log_lower = log.lower()
            for pattern_name, pattern in LOG_PATTERNS.items():
                if all(kw.lower() in log_lower for kw in pattern["keywords"]):
                    findings.append({
                        "pattern": pattern_name,
                        "severity": pattern["severity"],
                        "suggestion": pattern["suggestion"],
                        "log": log,
                    })
                    break
        return {
            "total_logs": len(logs),
            "findings": findings,
            "has_issues": len(findings) > 0,
            "critical_count": sum(1 for f in findings if f["severity"] == "critical"),
        }


log_parser_tool = LogParserTool()
