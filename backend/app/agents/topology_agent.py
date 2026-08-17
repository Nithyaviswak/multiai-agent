from typing import Dict, Any
from app.agents.base import BaseAgent
from app.tools.network.device_simulator import device_simulator
from app.tools.validation import validation_tool
from app.schemas.network_topology import TopologyResponse, TopologyDevice, TopologyLink
from app.logging_config import logger

class TopologyAgent(BaseAgent):
    """Topology Agent that discovers and maps network topology"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        intent_data = state.get("intent_data", {})
        environment = intent_data.get("environment", "devnet-sandbox")
        logger.info("Topology agent started", environment=environment)

        try:
            env_info = device_simulator.get_environments().get(environment, {})
            topology = device_simulator.get_topology()

            devices = []
            for dev in topology["devices"]:
                devices.append({
                    "hostname": dev["hostname"],
                    "vendor": dev["vendor"],
                    "platform": dev["platform"],
                    "model": dev["model"],
                    "os_version": dev["os_version"],
                    "role": dev["role"],
                    "site": dev["site"],
                    "mgmt_ip": dev["mgmt_ip"],
                    "interfaces": dev["interfaces"],
                })

            topology_data = {
                "environment": environment,
                "environment_type": env_info.get("type", "sandbox"),
                "devices": devices,
                "links": topology["links"],
                "device_count": len(devices),
                "health_summary": self._assess_health(topology),
            }

            is_valid, validated, error_msg = await validation_tool.validate_output(
                topology_data, TopologyResponse
            )

            if not is_valid:
                raise ValueError(f"Topology validation failed: {error_msg}")

            return {
                "topology_complete": True,
                "topology_data": validated.dict(),
                "current_step": "topology",
            }

        except Exception as e:
            logger.error("Topology agent failed", error=str(e))
            return {
                "topology_complete": False,
                "topology_data": None,
                "errors": state.get("errors", []) + [f"Topology discovery failed: {str(e)}"],
            }

    def _assess_health(self, topology: Dict[str, Any]) -> str:
        up_count = 0
        total = 0
        for dev in topology["devices"]:
            for iface in dev["interfaces"].values():
                total += 1
                if iface["status"] == "up":
                    up_count += 1
        ratio = up_count / total if total > 0 else 0
        if ratio >= 0.95:
            return "Healthy - all devices operational"
        elif ratio >= 0.8:
            return "Degraded - some interfaces down"
        return "Critical - multiple failures detected"
