from typing import Dict, Any, List, Optional
from app.tools.network.device_simulator import device_simulator
from app.logging_config import logger

class NAPALMMock:
    """Mock NAPALM operations - no real hardware required"""

    def __init__(self):
        self.connections = {}

    async def open(self, hostname: str, username: str = "admin", password: str = "admin") -> bool:
        try:
            device = device_simulator.get_device(hostname)
            self.connections[hostname] = {"device": device, "username": username}
            logger.info("NAPALM connection opened", hostname=hostname)
            return True
        except ValueError:
            logger.error("NAPALM connection failed", hostname=hostname)
            return False

    async def close(self, hostname: str):
        self.connections.pop(hostname, None)

    async def get_facts(self, hostname: str) -> Dict[str, Any]:
        device = device_simulator.get_device(hostname)
        return {
            "hostname": device["hostname"],
            "vendor": device["vendor"],
            "model": device["model"],
            "os_version": device["os_version"],
            "serial_number": device["serial"],
            "uptime": "2 weeks, 3 days, 14 hours",
            "interface_list": list(device["interfaces"].keys()),
        }

    async def get_interfaces(self, hostname: str) -> Dict[str, Any]:
        device = device_simulator.get_device(hostname)
        return device["interfaces"]

    async def get_interfaces_ip(self, hostname: str) -> Dict[str, Any]:
        device = device_simulator.get_device(hostname)
        result = {}
        for name, iface in device["interfaces"].items():
            if iface["ip"]:
                result[name] = {"ipv4": {iface["ip"]: {"prefix_length": int(iface["mask"].split(".")[-1])}}}
        return result

    async def get_config(self, hostname: str, retrieve: str = "running") -> str:
        device = device_simulator.get_device(hostname)
        return device["config"]

    async def get_vlans(self, hostname: str) -> List[Dict[str, Any]]:
        device = device_simulator.get_device(hostname)
        return device.get("vlans", [])

    async def get_arp_table(self, hostname: str) -> List[Dict[str, Any]]:
        return [
            {"ip": "192.168.1.1", "mac": "00:11:22:33:44:01", "interface": "GigabitEthernet0/0", "age": 120},
            {"ip": "192.168.1.2", "mac": "00:11:22:33:44:02", "interface": "GigabitEthernet0/0", "age": 95},
        ]

    async def get_ntp_servers(self, hostname: str) -> Dict[str, Any]:
        return {"208.67.222.222": {}, "208.67.220.220": {}}

    async def get_ntp_stats(self, hostname: str) -> List[Dict[str, Any]]:
        return [
            {"remote": "208.67.222.222", "reference": ".GPS.", "stratum": 2, "offset": 1.234, "delay": 45.6},
        ]

    async def ping(self, hostname: str, destination: str) -> Dict[str, Any]:
        return {
            "success": True,
            "source": hostname,
            "destination": destination,
            "min_rtt": 1.234,
            "avg_rtt": 1.567,
            "max_rtt": 2.001,
            "packet_loss": 0,
            "packets_sent": 5,
            "packets_received": 5,
        }

    async def traceroute(self, hostname: str, destination: str) -> Dict[str, Any]:
        return {
            "success": True,
            "source": hostname,
            "destination": destination,
            "hops": [
                {"hop": 1, "probes": [{"ip": "10.0.0.1", "rtt": 1.1}]},
                {"hop": 2, "probes": [{"ip": "10.0.2.2", "rtt": 2.2}]},
                {"hop": 3, "probes": [{"ip": destination, "rtt": 3.3}]},
            ],
        }

    async def is_alive(self, hostname: str) -> bool:
        return hostname in device_simulator.devices


napalm_mock = NAPALMMock()
