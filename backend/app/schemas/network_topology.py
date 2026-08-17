from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class TopologyDevice(BaseModel):
    hostname: str
    vendor: str
    platform: str
    model: str
    os_version: str
    role: str
    site: str
    mgmt_ip: str
    interfaces: Dict[str, Any]

class TopologyLink(BaseModel):
    source: str
    target: str
    via: str

class TopologyResponse(BaseModel):
    """Schema for network topology data"""
    environment: str = Field(description="Network environment name")
    environment_type: str = Field(description="Environment type (sandbox, containerized, simulator, emulator)")
    devices: List[TopologyDevice] = Field(description="Discovered network devices")
    links: List[TopologyLink] = Field(description="Network links between devices")
    device_count: int = Field(description="Number of devices discovered")
    health_summary: str = Field(description="Overall network health assessment")
