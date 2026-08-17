from typing import Dict, Any, List
from app.logging_config import logger

MOCK_DEVICES = {
    "core-router-01": {
        "hostname": "core-router-01",
        "vendor": "cisco",
        "platform": "ios-xe",
        "os_version": "17.9.1",
        "model": "C9300-48U",
        "serial": "CAT1234ABCD",
        "mgmt_ip": "192.168.1.1",
        "role": "core",
        "site": "devnet-sandbox",
        "interfaces": {
            "GigabitEthernet0/0": {"ip": "10.0.0.1", "mask": "255.255.255.0", "status": "up"},
            "GigabitEthernet0/1": {"ip": "10.0.1.1", "mask": "255.255.255.0", "status": "up"},
            "GigabitEthernet0/2": {"ip": "10.0.2.1", "mask": "255.255.255.0", "status": "up"},
        },
        "config": "hostname core-router-01\nip routing\ninterface GigabitEthernet0/0\n ip address 10.0.0.1 255.255.255.0\n no shutdown\n!",
        "vlans": [{"id": 10, "name": "Management"}, {"id": 20, "name": "Data"}, {"id": 30, "name": "Voice"}],
        "ospf": {"process_id": 1, "router_id": "10.0.0.1", "area": 0},
        "bgp": {"asn": 65001, "neighbors": ["10.0.2.2"]},
    },
    "edge-router-01": {
        "hostname": "edge-router-01",
        "vendor": "cisco",
        "platform": "ios-xe",
        "os_version": "17.6.3",
        "model": "C8200-1N-4T",
        "serial": "EDGE5678EFGH",
        "mgmt_ip": "192.168.1.2",
        "role": "edge",
        "site": "containerlab",
        "interfaces": {
            "GigabitEthernet0/0": {"ip": "203.0.113.1", "mask": "255.255.255.0", "status": "up"},
            "GigabitEthernet0/1": {"ip": "10.0.2.2", "mask": "255.255.255.0", "status": "up"},
            "GigabitEthernet0/2": {"ip": "10.10.0.1", "mask": "255.255.255.0", "status": "up"},
        },
        "config": "hostname edge-router-01\nip routing\ninterface GigabitEthernet0/0\n ip address 203.0.113.1 255.255.255.0\n no shutdown\n!",
        "vlans": [],
        "ospf": {"process_id": 1, "router_id": "203.0.113.1", "area": 0},
        "bgp": {"asn": 65001, "neighbors": ["10.0.2.1"]},
    },
    "distribution-sw-01": {
        "hostname": "distribution-sw-01",
        "vendor": "cisco",
        "platform": "ios-xe",
        "os_version": "17.3.6",
        "model": "C9300-24P",
        "serial": "DIST9012IJKL",
        "mgmt_ip": "192.168.1.3",
        "role": "distribution",
        "site": "gns3",
        "interfaces": {
            "GigabitEthernet0/1": {"ip": "10.0.1.2", "mask": "255.255.255.0", "status": "up"},
            "GigabitEthernet0/2": {"ip": "10.20.0.1", "mask": "255.255.255.0", "status": "up"},
            "Vlan10": {"ip": "192.168.10.1", "mask": "255.255.255.0", "status": "up"},
            "Vlan20": {"ip": "192.168.20.1", "mask": "255.255.255.0", "status": "up"},
        },
        "config": "hostname distribution-sw-01\nip routing\nvlan 10\n name Management\nvlan 20\n name Data\n!",
        "vlans": [{"id": 10, "name": "Management"}, {"id": 20, "name": "Data"}],
        "ospf": {"process_id": 1, "router_id": "10.0.1.2", "area": 0},
        "bgp": None,
    },
    "access-sw-01": {
        "hostname": "access-sw-01",
        "vendor": "cisco",
        "platform": "ios-xe",
        "os_version": "17.3.6",
        "model": "C9200-24P",
        "serial": "ACC3456MNOP",
        "mgmt_ip": "192.168.1.4",
        "role": "access",
        "site": "eve-ng",
        "interfaces": {
            "GigabitEthernet0/1": {"ip": "10.20.0.2", "mask": "255.255.255.0", "status": "up"},
            "GigabitEthernet0/2": {"ip": None, "mask": None, "status": "up"},
            "GigabitEthernet0/3": {"ip": None, "mask": None, "status": "up"},
            "Vlan10": {"ip": "192.168.10.2", "mask": "255.255.255.0", "status": "up"},
        },
        "config": "hostname access-sw-01\nvlan 10\n name Management\ninterface GigabitEthernet0/1\n switchport mode trunk\n!",
        "vlans": [{"id": 10, "name": "Management"}, {"id": 100, "name": "Users"}],
        "ospf": None,
        "bgp": None,
    },
}

ENVIRONMENTS = {
    "devnet-sandbox": {
        "name": "Cisco DevNet Sandbox",
        "type": "sandbox",
        "devices": ["core-router-01"],
        "description": "Cisco DevNet Always-On Sandbox with IOS-XE devices",
    },
    "containerlab": {
        "name": "ContainerLab",
        "type": "containerized",
        "devices": ["edge-router-01"],
        "description": "ContainerLab virtual network with containerized routers",
    },
    "gns3": {
        "name": "GNS3",
        "type": "simulator",
        "devices": ["distribution-sw-01"],
        "description": "GNS3 simulated network with virtual appliances",
    },
    "eve-ng": {
        "name": "EVE-NG",
        "type": "emulator",
        "devices": ["access-sw-01"],
        "description": "EVE-NG professional network emulation platform",
    },
}

class DeviceSimulator:
    """Simulates network devices across multiple environments"""

    def __init__(self):
        self.devices = MOCK_DEVICES
        self.environments = ENVIRONMENTS

    def get_device(self, hostname: str) -> Dict[str, Any]:
        if hostname in self.devices:
            return self.devices[hostname]
        raise ValueError(f"Device {hostname} not found")

    def get_all_devices(self) -> List[Dict[str, Any]]:
        return list(self.devices.values())

    def get_devices_by_role(self, role: str) -> List[Dict[str, Any]]:
        return [d for d in self.devices.values() if d["role"] == role]

    def get_devices_by_site(self, site: str) -> List[Dict[str, Any]]:
        return [d for d in self.devices.values() if d["site"] == site]

    def get_environments(self) -> Dict[str, Any]:
        return self.environments

    def get_topology(self) -> Dict[str, Any]:
        links = [
            {"source": "core-router-01", "target": "edge-router-01", "via": "GigabitEthernet0/2"},
            {"source": "core-router-01", "target": "distribution-sw-01", "via": "GigabitEthernet0/1"},
            {"source": "distribution-sw-01", "target": "access-sw-01", "via": "GigabitEthernet0/2"},
        ]
        return {
            "devices": self.get_all_devices(),
            "links": links,
            "environments": self.environments,
        }

    def update_interface_status(self, hostname: str, interface: str, status: str) -> bool:
        if hostname in self.devices and interface in self.devices[hostname]["interfaces"]:
            self.devices[hostname]["interfaces"][interface]["status"] = status
            return True
        return False

    def apply_config(self, hostname: str, config_lines: List[str]) -> Dict[str, Any]:
        if hostname not in self.devices:
            return {"success": False, "error": "Device not found"}
        device = self.devices[hostname]
        for line in config_lines:
            line = line.strip()
            if line.startswith("hostname"):
                device["hostname"] = line.split()[-1]
            elif line.startswith("interface"):
                iface_name = line.split()[-1]
                if iface_name not in device["interfaces"]:
                    device["interfaces"][iface_name] = {"ip": None, "mask": None, "status": "up"}
            elif "ip address" in line and "interface" not in line.split()[-1]:
                pass
        config_update = "\n".join(config_lines)
        device["config"] += f"\n{config_update}"
        return {"success": True, "device": hostname, "applied_lines": len(config_lines)}


device_simulator = DeviceSimulator()
