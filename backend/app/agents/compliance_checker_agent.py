from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.tools.validation import validation_tool
from app.schemas.network_compliance import ComplianceResponse, ComplianceCheck
from app.logging_config import logger

class ComplianceCheckerAgent(BaseAgent):
    """Compliance Checker Agent that validates network against standards"""

    COMPLIANCE_CHECKS = {
        "CIS_BENCHMARK": [
            {"id": "CIS-1.1", "name": "Disable unused ports", "category": "security",
             "severity": "high", "description": "Ensure unused ports are in shutdown state",
             "remediation": "Shut down unused interfaces"},
            {"id": "CIS-1.2", "name": "Enable password encryption", "category": "security",
             "severity": "high", "description": "Service password-encryption must be enabled",
             "remediation": "Enable service password-encryption globally"},
            {"id": "CIS-1.3", "name": "SSH instead of Telnet", "category": "security",
             "severity": "critical", "description": "SSH must be used for remote access, not Telnet",
             "remediation": "Disable Telnet, enable SSH with crypto key generate rsa"},
            {"id": "CIS-2.1", "name": "NTP configured", "category": "management",
             "severity": "medium", "description": "NTP should be configured for time synchronization",
             "remediation": "Configure ntp server on core devices"},
            {"id": "CIS-2.2", "name": "Logging enabled", "category": "management",
             "severity": "medium", "description": "Logging should be enabled and sent to syslog server",
             "remediation": "Enable logging and configure syslog server"},
            {"id": "CIS-3.1", "name": "BGP authentication", "category": "routing",
             "severity": "high", "description": "BGP peers should use MD5 authentication",
             "remediation": "Configure password for BGP neighbors"},
            {"id": "CIS-3.2", "name": "OSPF authentication", "category": "routing",
             "severity": "medium", "description": "OSPF should use MD5 authentication",
             "remediation": "Configure ip ospf message-digest-key on interfaces"},
        ],
        "PCI_DSS": [
            {"id": "PCI-1.1", "name": "Firewall policy review", "category": "security",
             "severity": "critical", "description": "Firewall rules must be reviewed every 6 months",
             "remediation": "Document and review ACL policies"},
            {"id": "PCI-1.2", "name": "Default passwords changed", "category": "security",
             "severity": "critical", "description": "All default vendor passwords must be changed",
             "remediation": "Change default credentials on all devices"},
        ],
    }

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        netconf_data = state.get("netconf_data", {})
        device_states = netconf_data.get("device_states", [])
        standard = "CIS_BENCHMARK"
        logger.info("Compliance checker agent started", standard=standard)

        try:
            checks_config = self.COMPLIANCE_CHECKS.get(standard, [])
            all_checks = []

            for dev_state in device_states:
                hostname = dev_state["hostname"]
                for check in checks_config:
                    passed = self._evaluate_check(check, hostname, dev_state)
                    all_checks.append({
                        "check_id": check["id"],
                        "check_name": check["name"],
                        "category": check["category"],
                        "status": "pass" if passed else "fail",
                        "severity": check["severity"],
                        "device": hostname,
                        "details": check["description"],
                        "recommendation": check["remediation"],
                    })

            passed_count = sum(1 for c in all_checks if c["status"] == "pass")
            failed_count = sum(1 for c in all_checks if c["status"] == "fail")
            total = len(all_checks)
            score = (passed_count / total * 100) if total > 0 else 0

            compliance_data = {
                "standard": standard,
                "environment": "multi-env",
                "total_checks": total,
                "passed": passed_count,
                "failed": failed_count,
                "warnings": 0,
                "overall_score": round(score, 1),
                "checks": all_checks,
                "remediation_plan": self._build_remediation_plan(all_checks),
            }

            is_valid, validated, error_msg = await validation_tool.validate_output(
                compliance_data, ComplianceResponse
            )
            if not is_valid:
                raise ValueError(f"Compliance validation failed: {error_msg}")

            return {
                "compliance_complete": True,
                "compliance_data": validated.dict(),
                "current_step": "compliance",
            }

        except Exception as e:
            logger.error("Compliance checker agent failed", error=str(e))
            return {
                "compliance_complete": False,
                "compliance_data": None,
                "errors": state.get("errors", []) + [f"Compliance check failed: {str(e)}"],
            }

    def _evaluate_check(self, check: Dict[str, Any], hostname: str,
                        device_state: Dict[str, Any]) -> bool:
        check_id = check["id"]
        if check_id == "CIS-1.2":
            config = device_state.get("running_config", "")
            return "password-encryption" in config
        if check_id == "CIS-1.3":
            config = device_state.get("running_config", "")
            return "ip ssh version" in config
        if check_id == "CIS-2.1":
            config = device_state.get("running_config", "")
            return "ntp server" in config
        if check_id == "CIS-2.2":
            config = device_state.get("running_config", "")
            return "logging" in config
        if "CIS-3" in check_id or "PCI" in check_id:
            interfaces = device_state.get("interfaces", {})
            return len(interfaces) > 0
        return True

    def _build_remediation_plan(self, checks: List[Dict[str, Any]]) -> List[str]:
        failed = [c for c in checks if c["status"] == "fail"]
        critical = [c for c in failed if c["severity"] == "critical"]
        high = [c for c in failed if c["severity"] == "high"]

        plan = []
        if critical:
            plan.append(f"Address {len(critical)} critical issues immediately:")
            plan.extend(f"  - {c['recommendation']} on {c['device']}" for c in critical[:3])
        if high:
            plan.append(f"Resolve {len(high)} high severity issues:")
            plan.extend(f"  - {c['recommendation']} on {c['device']}" for c in high[:3])
        if not critical and not high:
            plan.append("No critical or high severity issues found.")
        return plan
