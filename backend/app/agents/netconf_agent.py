from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.tools.network.napalm_mock import napalm_mock
from app.tools.network.netmiko_mock import netmiko_mock
from app.logging_config import logger

class NETCONFAgent(BaseAgent):
    """NETCONF Agent that gathers device operational state via simulated NETCONF"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        topology_data = state.get("topology_data", {})
        devices = topology_data.get("devices", [])
        logger.info("NETCONF agent started", device_count=len(devices))

        try:
            device_states = []

            for device in devices:
                hostname = device["hostname"]
                await napalm_mock.open(hostname)

                facts = await napalm_mock.get_facts(hostname)
                interfaces = await napalm_mock.get_interfaces(hostname)
                config = await napalm_mock.get_config(hostname)
                vlans = await napalm_mock.get_vlans(hostname)
                alive = await napalm_mock.is_alive(hostname)

                device_state = {
                    "hostname": hostname,
                    "reachable": alive,
                    "facts": facts,
                    "interfaces": interfaces,
                    "running_config": config,
                    "vlans": vlans,
                    "operational_state": {
                        "ospf_neighbors": [],
                        "bgp_peers": [],
                        "routing_table": [],
                        "arp_table": [],
                    },
                }

                await netmiko_mock.connect(hostname)
                ospf_out = await netmiko_mock.send_command(hostname, "show ospf neighbor")
                bgp_out = await netmiko_mock.send_command(hostname, "show ip bgp summary")
                route_out = await netmiko_mock.send_command(hostname, "show ip route")
                device_state["operational_state"]["ospf_neighbors"] = ospf_out
                device_state["operational_state"]["bgp_peers"] = bgp_out
                device_state["operational_state"]["routing_table"] = route_out

                await napalm_mock.close(hostname)
                await netmiko_mock.disconnect(hostname)
                device_states.append(device_state)

            return {
                "netconf_complete": True,
                "netconf_data": {
                    "device_states": device_states,
                    "total_devices_queried": len(device_states),
                    "all_reachable": all(d["reachable"] for d in device_states),
                },
                "current_step": "netconf",
            }

        except Exception as e:
            logger.error("NETCONF agent failed", error=str(e))
            return {
                "netconf_complete": False,
                "netconf_data": None,
                "errors": state.get("errors", []) + [f"NETCONF collection failed: {str(e)}"],
            }
