from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class IncidentEvent(BaseModel):
    event_type: str = Field(description="Type of event (interface_flap, link_down, routing_change, security, etc.)")
    device: str
    severity: str = Field(description="critical, high, medium, low")
    timestamp: str
    message: str
    source_interface: Optional[str] = None

class IncidentResponse(BaseModel):
    """Schema for incident analysis results"""
    incident_id: str
    title: str
    severity: str
    affected_devices: List[str]
    root_cause: str = Field(description="Identified root cause of the incident")
    impact_analysis: str = Field(description="Business/network impact assessment")
    recommended_actions: List[str] = Field(description="Recommended remediation steps")
    auto_remediation: bool = Field(description="Whether auto-remediation was attempted")
    auto_remediation_result: Optional[str] = None
    escalation_required: bool
