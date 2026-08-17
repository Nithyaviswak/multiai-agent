from typing import Dict, Any, List, Optional
from app.tools.network.device_simulator import device_simulator
from app.logging_config import logger

class NetmikoMock:
    """Mock Netmiko SSH operations - no real hardware required"""

    def __init__(self):
        self.connections = {}

    async def connect(self, hostname: str, username: str = "admin", password: str = "admin",
                      device_type: str = "cisco_ios") -> bool:
        try:
            device = device_simulator.get_device(hostname)
            self.connections[hostname] = {"device": device, "device_type": device_type}
            logger.info("Netmiko connection opened", hostname=hostname)
            return True
        except ValueError:
            logger.error("Netmiko connection failed", hostname=hostname)
            return False

    async def disconnect(self, hostname: str):
        self.connections.pop(hostname, None)

    async def send_command(self, hostname: str, command: str) -> str:
        device = device_simulator.get_device(hostname)
        cmd_map = {
            "show version": f"Cisco IOS XE Software, Version {device['os_version']}\n"
                           f"ROM: Bootstrap program\n"
                           f"{device['hostname']} uptime is 2 weeks, 3 days\n"
                           f"System image file is: flash:{device['platform']}.bin\n"
                           f"Hardware: {device['model']}, {device['serial']}",
            "show running-config": device["config"],
            "show ip interface brief": self._format_interfaces_brief(device),
            "show interfaces": self._format_interfaces_detail(device),
            "show vlan brief": self._format_vlans(device),
            "show ip route": self._format_routing_table(device),
            "show cdp neighbors": self._format_cdp_neighbors(device),
            "show ospf neighbor": self._format_ospf_neighbors(device),
            "show inventory": f"NAME: Chassis, DESCR: {device['model']}\nPID: {device['model']}, SN: {device['serial']}",
            "show clock": "*14:30:00.123 UTC Mon Jul 24 2026",
            "show logging": self._format_logs(device),
        }
        for pattern, result in cmd_map.items():
            if command.startswith(pattern):
                return result
        if "show ip ospf" in command:
            return f"Routing Process \"ospf 1\" with ID {device.get('ospf', {}).get('router_id', '0.0.0.0')}"
        if "show bgp" in command:
            return f"BGP with ASN {device.get('bgp', {}).get('asn', 'Unknown')}"
        return f"Command '{command}' executed successfully on {hostname}"

    async def send_config_set(self, hostname: str, config_commands: List[str]) -> str:
        result = device_simulator.apply_config(hostname, config_commands)
        if result["success"]:
            return f"Applied {result['applied_lines']} config lines to {hostname}"
        return f"Failed to apply config: {result['error']}"

    async def save_config(self, hostname: str) -> str:
        return f"Configuration saved to startup-config on {hostname}"

    def _format_interfaces_brief(self, device: Dict[str, Any]) -> str:
        lines = ["Interface              IP-Address      Status     Protocol"]
        for name, iface in device["interfaces"].items():
            ip = iface["ip"] or "unassigned"
            status = iface["status"]
            protocol = "up" if status == "up" else "down"
            lines.append(f"{name:20} {ip:15} {status:10} {protocol}")
        return "\n".join(lines)

    def _format_interfaces_detail(self, device: Dict[str, Any]) -> str:
        lines = []
        for name, iface in device["interfaces"].items():
            lines.append(f"{name} is {iface['status']}, line protocol is {iface['status']}")
            lines.append(f"  Internet address is {iface['ip'] or 'not set'}/{iface['mask'] or 'N/A'}")
            lines.append(f"  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec")
            lines.append(f"  Reliability 255/255, txload 1/255, rxload 1/255")
            lines.append("")
        return "\n".join(lines)

    def _format_vlans(self, device: Dict[str, Any]) -> str:
        lines = ["VLAN Name                             Status    Ports"]
        for vlan in device.get("vlans", []):
            lines.append(f"{vlan['id']:4} {vlan['name']:30} active")
        return "\n".join(lines)

    def _format_routing_table(self, device: Dict[str, Any]) -> str:
        return ("Codes: L - local, C - connected, S - static, O - OSPF, B - BGP\n"
                "Gateway of last resort is 203.0.113.1 to network 0.0.0.0\n\n"
                "S*    0.0.0.0/0 [1/0] via 203.0.113.1\n"
                "C     10.0.0.0/24 is directly connected, GigabitEthernet0/0\n"
                "C     10.0.1.0/24 is directly connected, GigabitEthernet0/1\n"
                "O     10.20.0.0/24 [110/2] via 10.0.1.2, 00:12:34, GigabitEthernet0/1")

    def _format_cdp_neighbors(self, device: Dict[str, Any]) -> str:
        hosts = device_simulator.get_all_devices()
        neighbors = [h["hostname"] for h in hosts if h["hostname"] != device["hostname"]]
        if not neighbors:
            return "No CDP neighbors found"
        lines = ["Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID"]
        for i, n in enumerate(neighbors[:2]):
            lines.append(f"{n:16} Gig 0/{i}           172         R S I      C9300     Gig 0/{i}")
        return "\n".join(lines)

    def _format_ospf_neighbors(self, device: Dict[str, Any]) -> str:
        ospf = device.get("ospf")
        if not ospf:
            return "No OSPF neighbors found"
        return (f"Neighbor ID     Pri   State           Dead Time   Address         Interface\n"
                f"10.0.1.2        1   FULL/DR         00:00:33    10.0.1.2        GigabitEthernet0/1\n"
                f"10.0.2.2        1   FULL/BDR        00:00:37    10.0.2.2        GigabitEthernet0/2")

    def _format_logs(self, device: Dict[str, Any]) -> str:
        return ("Syslog logging: enabled\n"
                "Console logging: level debugging, 47 messages logged\n"
                "Monitor logging: level debugging, 0 messages logged\n"
                "Buffer logging: level informational, 127 messages logged\n"
                "Trap logging: level informational, 189 message lines logged\n\n"
                f"Jul 24 12:00:00: %LINEPROTO-5-UPDOWN: Line protocol on Interface {device['hostname']}, changed state to up\n"
                f"Jul 24 12:00:05: %LINK-3-UPDOWN: Interface GigabitEthernet0/0, changed state to up\n"
                "Jul 24 11:45:12: %SEC-6-IPACCESSLOGP: list ACL_IN permitted tcp 10.0.0.5(54321) -> 10.0.1.10(80)")


netmiko_mock = NetmikoMock()
