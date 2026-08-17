from typing import Dict, Any, List, Optional
from app.tools.network.device_simulator import device_simulator
from app.logging_config import logger

class pyATSMock:
    """Mock pyATS test and parsing operations - no real hardware required"""

    def __init__(self):
        self.test_results = {}

    async def parse(self, hostname: str, command: str, output: Optional[str] = None) -> Dict[str, Any]:
        device = device_simulator.get_device(hostname)
        if command == "show version":
            return {
                "version": {
                    "operating_system": "IOS-XE",
                    "software_version": device["os_version"],
                    "system_image": f"flash:{device['platform']}.bin",
                    "uptime": "2 weeks, 3 days, 14 hours",
                    "hostname": device["hostname"],
                    "chassis": device["model"],
                    "serial_number": device["serial"],
                }
            }
        elif command == "show ip interface brief":
            interfaces = {}
            for name, iface in device["interfaces"].items():
                interfaces[name] = {
                    "ip_address": iface["ip"] or "unassigned",
                    "status": iface["status"],
                    "protocol": iface["status"],
                }
            return {"interface": interfaces}
        elif command == "show running-config":
            return {"running_config": device["config"]}
        elif command == "show interfaces":
            interfaces = {}
            for name, iface in device["interfaces"].items():
                interfaces[name] = {
                    "interface": name,
                    "oper_status": iface["status"],
                    "admin_status": iface["status"],
                    "ip_address": iface["ip"] or "",
                    "mtu": 1500,
                    "bandwidth": 1000000,
                }
            return {"interfaces": interfaces}
        elif command == "show vlan":
            vlans = {}
            for vlan in device.get("vlans", []):
                vlans[str(vlan["id"])] = {"vlan_id": vlan["id"], "name": vlan["name"], "status": "active"}
            return {"vlan": vlans}
        elif "show ip route" in command:
            return {
                "vrf": {
                    "default": {
                        "routing_table": {
                            "10.0.0.0/24": {"network": "10.0.0.0", "netmask": "255.255.255.0", "nexthop": "directly connected"},
                            "0.0.0.0/0": {"network": "0.0.0.0", "netmask": "0.0.0.0", "nexthop": "203.0.113.1"},
                        }
                    }
                }
            }
        elif "show ospf" in command and "neighbor" not in command:
            ospf = device.get("ospf", {})
            return {
                "process": {
                    str(ospf.get("process_id", "1")): {
                        "router_id": ospf.get("router_id", "0.0.0.0"),
                        "area": str(ospf.get("area", 0)),
                    }
                }
            }
        else:
            return {"raw_output": f"Parsed {command} on {hostname}"}

    async def learn(self, hostname: str, feature: str) -> Dict[str, Any]:
        device = device_simulator.get_device(hostname)
        feature_map = {
            "interface": self._learn_interfaces(device),
            "vlan": self._learn_vlans(device),
            "ospf": self._learn_ospf(device),
            "bgp": self._learn_bgp(device),
            "routing": self._learn_routing(device),
            "platform": self._learn_platform(device),
            "acl": self._learn_acl(device),
        }
        return feature_map.get(feature, {"info": {f"{feature}": {"learned": True}}})

    async def _learn_interfaces(self, device: Dict[str, Any]) -> Dict[str, Any]:
        interfaces = {}
        for name, iface in device["interfaces"].items():
            interfaces[name] = {
                "oper_status": iface["status"],
                "enabled": iface["status"] == "up",
                "ipv4": iface["ip"] or "",
                "description": "",
            }
        return {"info": {"interfaces": interfaces}}

    async def _learn_vlans(self, device: Dict[str, Any]) -> Dict[str, Any]:
        vlans = {}
        for vlan in device.get("vlans", []):
            vlans[str(vlan["id"])] = {"vlan_id": vlan["id"], "name": vlan["name"], "status": "active"}
        return {"info": {"vlans": vlans}}

    async def _learn_ospf(self, device: Dict[str, Any]) -> Dict[str, Any]:
        ospf = device.get("ospf", {})
        if not ospf:
            return {"info": {}}
        return {"info": {"ospf": ospf}}

    async def _learn_bgp(self, device: Dict[str, Any]) -> Dict[str, Any]:
        bgp = device.get("bgp", {})
        if not bgp:
            return {"info": {}}
        return {"info": {"bgp": bgp}}

    async def _learn_routing(self, device: Dict[str, Any]) -> Dict[str, Any]:
        return {"info": {"vrf": {"default": {"routes": {}}}}}

    async def _learn_platform(self, device: Dict[str, Any]) -> Dict[str, Any]:
        return {"info": {
            "chassis": device["model"],
            "os": device["os_version"],
            "serial": device["serial"],
            "memory": {"total": 4096, "free": 2048},
        }}

    async def _learn_acl(self, device: Dict[str, Any]) -> Dict[str, Any]:
        return {"info": {"acl": {
            "ACL_IN": {"type": "extended", "entries": 5},
            "ACL_OUT": {"type": "extended", "entries": 3},
        }}}

    async def run_test(self, hostname: str, test_name: str, **kwargs) -> Dict[str, Any]:
        test_map = {
            "verify_interfaces": {"passed": True, "message": "All interfaces are up"},
            "verify_ospf_neighbors": {"passed": True, "message": "OSPF neighbors are FULL"},
            "verify_bgp_peers": {"passed": True, "message": "BGP peers are established"},
            "verify_vlans": {"passed": True, "message": "VLAN configuration is consistent"},
            "verify_connectivity": {"passed": True, "message": "End-to-end connectivity verified"},
            "verify_config": {"passed": True, "message": "Running config matches expected"},
            "verify_backup": {"passed": True, "message": "Backup completed successfully"},
        }
        result = test_map.get(test_name, {"passed": False, "message": f"Unknown test {test_name}"})
        result["device"] = hostname
        self.test_results.setdefault(hostname, []).append(result)
        return result

    async def get_test_summary(self, hostname: Optional[str] = None) -> Dict[str, Any]:
        if hostname:
            results = self.test_results.get(hostname, [])
            passed = sum(1 for r in results if r["passed"])
            return {"hostname": hostname, "total": len(results), "passed": passed, "failed": len(results) - passed}
        all_results = []
        for h, tests in self.test_results.items():
            for t in tests:
                all_results.append({**t, "device": h})
        passed = sum(1 for r in all_results if r["passed"])
        return {"total": len(all_results), "passed": passed, "failed": len(all_results) - passed}

    async def diff_config(self, hostname: str, config_a: str, config_b: str) -> List[str]:
        lines_a = config_a.split("\n")
        lines_b = config_b.split("\n")
        diff = []
        for i, (a, b) in enumerate(zip(lines_a, lines_b)):
            if a != b:
                diff.append(f"! Line {i+1}: {a} -> {b}")
        if len(lines_a) < len(lines_b):
            for i in range(len(lines_a), len(lines_b)):
                diff.append(f"+{lines_b[i]}")
        elif len(lines_b) < len(lines_a):
            for i in range(len(lines_b), len(lines_a)):
                diff.append(f"-{lines_a[i]}")
        return diff


pyats_mock = pyATSMock()
