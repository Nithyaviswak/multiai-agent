from typing import Dict, Any
from app.agents.base import BaseAgent
from app.tools.network.pyats_mock import pyats_mock
from app.tools.validation import validation_tool
from app.schemas.network_config import ConfigVerificationResponse
from app.logging_config import logger

class VerificationAgent(BaseAgent):
    """Verification Agent that validates configuration changes"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        config_data = state.get("config_data", {})
        configurations = config_data.get("configurations", [])
        logger.info("Verification agent started", config_count=len(configurations))

        try:
            verifications = []

            for cfg in configurations:
                hostname = cfg["hostname"]
                checks = []

                ping_check = await pyats_mock.run_test(hostname, "verify_connectivity")
                checks.append({
                    "check": "Connectivity",
                    "status": ping_check["passed"],
                    "details": ping_check["message"],
                })

                config_check = await pyats_mock.run_test(hostname, "verify_config")
                checks.append({
                    "check": "Configuration Applied",
                    "status": config_check["passed"],
                    "details": config_check["message"],
                })

                ospf_check = await pyats_mock.run_test(hostname, "verify_ospf_neighbors")
                checks.append({
                    "check": "OSPF Neighbors",
                    "status": ospf_check["passed"],
                    "details": ospf_check["message"],
                })

                iface_check = await pyats_mock.run_test(hostname, "verify_interfaces")
                checks.append({
                    "check": "Interface Status",
                    "status": iface_check["passed"],
                    "details": iface_check["message"],
                })

                all_passed = all(c["status"] for c in checks)
                verifications.append({
                    "device": hostname,
                    "config_applied": True,
                    "verification_checks": checks,
                    "overall_status": "pass" if all_passed else "fail",
                    "rollback_required": not all_passed,
                })

            return {
                "verification_complete": True,
                "verification_data": {
                    "verifications": verifications,
                    "total_verified": len(verifications),
                    "all_passed": all(v["overall_status"] == "pass" for v in verifications),
                },
                "current_step": "verification",
            }

        except Exception as e:
            logger.error("Verification agent failed", error=str(e))
            return {
                "verification_complete": False,
                "verification_data": None,
                "errors": state.get("errors", []) + [f"Verification failed: {str(e)}"],
            }
