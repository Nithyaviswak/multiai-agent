from typing import Dict, Any, List, Callable, Optional
from app.tools.network.device_simulator import device_simulator
from app.logging_config import logger

class NornirMock:
    """Mock Nornir automation operations - no real hardware required"""

    def __init__(self):
        self.inventory = self._build_inventory()

    def _build_inventory(self) -> Dict[str, Any]:
        hosts = {}
        for device in device_simulator.get_all_devices():
            hosts[device["hostname"]] = {
                "hostname": device["mgmt_ip"],
                "username": "admin",
                "password": "admin",
                "platform": device["platform"],
                "data": {
                    "role": device["role"],
                    "site": device["site"],
                    "model": device["model"],
                    "os_version": device["os_version"],
                    "serial": device["serial"],
                    "groups": [device["role"], device["site"]],
                },
            }
        return {
            "hosts": hosts,
            "groups": {
                "core": {"data": {"routing_protocol": "OSPF", "bgp": True}},
                "edge": {"data": {"routing_protocol": "BGP", "nat": True}},
                "distribution": {"data": {"routing_protocol": "OSPF", "stp": True}},
                "access": {"data": {"routing_protocol": "none", "stp": True}},
                "devnet-sandbox": {"data": {"environment": "sandbox"}},
                "containerlab": {"data": {"environment": "container"}},
                "gns3": {"data": {"environment": "simulation"}},
                "eve-ng": {"data": {"environment": "emulation"}},
            },
        }

    async def run(self, task: str, hosts: Optional[List[str]] = None,
                  **kwargs) -> Dict[str, Any]:
        targets = hosts if hosts else list(self.inventory["hosts"].keys())
        results = {}

        for hostname in targets:
            if hostname not in self.inventory["hosts"]:
                continue
            host_data = self.inventory["hosts"][hostname]
            device = device_simulator.get_device(hostname)

            if task == "napalm_get":
                getters = kwargs.get("getters", ["get_facts"])
                data = {}
                for getter in getters:
                    if getter == "get_facts":
                        data["facts"] = {
                            "hostname": device["hostname"],
                            "vendor": device["vendor"],
                            "model": device["model"],
                            "os_version": device["os_version"],
                            "serial_number": device["serial"],
                            "uptime": "2w3d",
                        }
                    elif getter == "get_interfaces":
                        data["interfaces"] = device["interfaces"]
                    elif getter == "get_config":
                        data["config"] = device["config"]
                results[hostname] = {"success": True, "result": data}

            elif task == "netmiko_send_command":
                command = kwargs.get("command", "show version")
                if command == "show version":
                    results[hostname] = {"success": True, "result": f"Cisco IOS XE {device['os_version']}"}
                else:
                    results[hostname] = {"success": True, "result": f"{command} executed on {hostname}"}

            elif task == "netmiko_send_config":
                commands = kwargs.get("commands", [])
                applied = device_simulator.apply_config(hostname, commands)
                results[hostname] = {"success": applied["success"], "result": applied}

            elif task == "ping":
                dest = kwargs.get("dest", "8.8.8.8")
                results[hostname] = {"success": True, "result": {"reachable": True, "rtt": 1.5}}

            else:
                results[hostname] = {"success": True, "result": f"Task '{task}' completed"}

        return {
            "task": task,
            "results": results,
            "failed_hosts": [],
            "total_hosts": len(targets),
        }

    async def filter(self, filter_func: Callable) -> List[str]:
        filtered = []
        for hostname, host_data in self.inventory["hosts"].items():
            if filter_func(host_data):
                filtered.append(hostname)
        return filtered

    async def get_inventory(self) -> Dict[str, Any]:
        return self.inventory

    async def backup_configs(self, hosts: Optional[List[str]] = None) -> Dict[str, Any]:
        targets = hosts if hosts else list(self.inventory["hosts"].keys())
        results = {}
        for hostname in targets:
            device = device_simulator.get_device(hostname)
            results[hostname] = {
                "hostname": hostname,
                "running_config": device["config"],
                "backup_time": "2026-07-24T12:00:00Z",
                "success": True,
            }
        return {"backup_results": results, "total": len(targets)}

    async def validate_configs(self, hosts: Optional[List[str]] = None) -> Dict[str, Any]:
        targets = hosts if hosts else list(self.inventory["hosts"].keys())
        results = {}
        for hostname in targets:
            device = device_simulator.get_device(hostname)
            results[hostname] = {
                "hostname": hostname,
                "valid": True,
                "warnings": [],
                "errors": [],
                "config_lines": len(device["config"].split("\n")),
            }
        return {"validation_results": results, "total": len(targets)}


nornir_mock = NornirMock()
