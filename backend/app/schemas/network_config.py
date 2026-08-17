from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DeviceConfig(BaseModel):
    hostname: str
    config_lines: List[str]
    config_text: str
    config_type: str = Field(description="running, startup, or candidate")

class ConfigGenerationRequest(BaseModel):
    technology: str = Field(description="Technology for config (OSPF, BGP, VLAN, ACL, etc.)")
    parameters: Dict[str, Any] = Field(description="Config parameters")
    target_devices: List[str] = Field(description="Target device hostnames")

class ConfigGenerationResponse(BaseModel):
    """Schema for generated configurations"""
    technology: str = Field(description="Technology configured")
    configurations: List[DeviceConfig] = Field(description="Generated device configurations")
    total_devices: int = Field(description="Number of devices configured")
    generation_status: str = Field(description="Success, partial, or failed")
    warnings: List[str] = Field(description="Configuration warnings")

class ConfigVerificationResponse(BaseModel):
    """Schema for configuration verification results"""
    device: str
    config_applied: bool
    verification_checks: List[Dict[str, Any]]
    overall_status: str = Field(description="pass, fail, or warning")
    rollback_required: bool
