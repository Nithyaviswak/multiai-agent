from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.tools.network.netmiko_mock import netmiko_mock
from app.tools.network.device_simulator import device_simulator
from app.tools.validation import validation_tool
from app.schemas.network_config import ConfigGenerationResponse, DeviceConfig
from app.logging_config import logger

TEMPLATES = {
    "OSPF": {
        "core-router-01": [
            "router ospf 1",
            " router-id 10.0.0.1",
            " network 10.0.0.0 0.0.0.255 area 0",
            " network 10.0.1.0 0.0.0.255 area 0",
            " network 10.0.2.0 0.0.0.255 area 0",
        ],
        "distribution-sw-01": [
            "router ospf 1",
            " router-id 10.0.1.2",
            " network 10.0.1.0 0.0.0.255 area 0",
            " network 10.20.0.0 0.0.0.255 area 0",
            " passive-interface default",
            " no passive-interface GigabitEthernet0/1",
        ],
        "edge-router-01": [
            "router ospf 1",
            " router-id 203.0.113.1",
            " network 10.0.2.0 0.0.0.255 area 0",
            " network 10.10.0.0 0.0.0.255 area 0",
            " default-information originate always",
        ],
    },
    "BGP": {
        "core-router-01": [
            "router bgp 65001",
            " bgp router-id 10.0.0.1",
            " neighbor 10.0.2.2 remote-as 65001",
            " neighbor 10.0.2.2 update-source Loopback0",
            " address-family ipv4",
            "  neighbor 10.0.2.2 activate",
        ],
    },
    "VLAN": {
        "distribution-sw-01": [
            "vlan 30",
            " name Wireless",
            "vlan 40",
            " name IoT",
            "interface Vlan30",
            " ip address 192.168.30.1 255.255.255.0",
            " no shutdown",
            "interface Vlan40",
            " ip address 192.168.40.1 255.255.255.0",
            " no shutdown",
        ],
        "access-sw-01": [
            "vlan 30",
            " name Wireless",
            "vlan 40",
            " name IoT",
            "interface GigabitEthernet0/2",
            " switchport mode access",
            " switchport access vlan 30",
            "interface GigabitEthernet0/3",
            " switchport mode access",
            " switchport access vlan 40",
        ],
    },
    "ACL": {
        "edge-router-01": [
            "ip access-list extended BLOCK_INTERNAL",
            " deny ip 10.0.0.0 0.255.255.255 any",
            " permit ip any any",
            "interface GigabitEthernet0/0",
            " ip access-group BLOCK_INTERNAL in",
        ],
    },
}

class ConfigurationAgent(BaseAgent):
    """Configuration Agent that generates and applies network configurations"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        intent_data = state.get("intent_data", {})
        netconf_data = state.get("netconf_data", {})
        technology = intent_data.get("technology", "OSPF")
        target_devices = intent_data.get("target_devices", [])
        params = intent_data.get("parameters", {})

        logger.info("Configuration agent started", technology=technology, targets=target_devices)

        try:
            device_states = netconf_data.get("device_states", [])
            generated_configs = []

            for dev_state in device_states:
                hostname = dev_state["hostname"]
                if target_devices and hostname not in target_devices:
                    continue

                config_lines = self._generate_config(hostname, technology, params, dev_state)
                if config_lines:
                    config_text = "\n".join(config_lines)
                    generated_configs.append({
                        "hostname": hostname,
                        "config_lines": config_lines,
                        "config_text": config_text,
                        "config_type": "candidate",
                    })

            for cfg in generated_configs:
                hostname = cfg["hostname"]
                await netmiko_mock.connect(hostname)
                result = await netmiko_mock.send_config_set(hostname, cfg["config_lines"])
                await netmiko_mock.save_config(hostname)
                await netmiko_mock.disconnect(hostname)
                cfg["apply_result"] = result

            config_data = {
                "technology": technology,
                "configurations": generated_configs,
                "total_devices": len(generated_configs),
                "generation_status": "success" if generated_configs else "partial",
                "warnings": [],
            }

            is_valid, validated, error_msg = await validation_tool.validate_output(
                config_data, ConfigGenerationResponse
            )
            if not is_valid:
                raise ValueError(f"Config validation failed: {error_msg}")

            return {
                "config_complete": True,
                "config_data": validated.dict(),
                "current_step": "configuration",
            }

        except Exception as e:
            logger.error("Configuration agent failed", error=str(e))
            return {
                "config_complete": False,
                "config_data": None,
                "errors": state.get("errors", []) + [f"Configuration failed: {str(e)}"],
            }

    def _generate_config(self, hostname: str, technology: str,
                         params: Dict[str, Any], device_state: Dict[str, Any]) -> List[str]:
        tech_templates = TEMPLATES.get(technology.upper(), {})
        if hostname in tech_templates:
            base_config = list(tech_templates[hostname])
            return self._apply_params(base_config, params)
        return []

    def _apply_params(self, config: List[str], params: Dict[str, Any]) -> List[str]:
        if not params:
            return config
        processed = []
        for line in config:
            for key, value in params.items():
                placeholder = "{" + key + "}"
                if isinstance(value, str):
                    line = line.replace(placeholder, value)
                elif isinstance(value, (int, float)):
                    line = line.replace(placeholder, str(value))
            processed.append(line)
        return processed
