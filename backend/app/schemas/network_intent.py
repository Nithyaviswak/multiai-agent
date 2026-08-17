from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class IntentResponse(BaseModel):
    """Schema for parsed network intent"""
    action: str = Field(description="Network action requested (configure, verify, troubleshoot, backup, audit)")
    target_devices: List[str] = Field(description="Target device hostnames or roles")
    technology: str = Field(description="Network technology (OSPF, BGP, VLAN, ACL, etc.)")
    parameters: Dict[str, Any] = Field(description="Configuration parameters extracted from intent")
    environment: str = Field(description="Target environment (devnet-sandbox, containerlab, gns3, eve-ng)")
    priority: str = Field(description="Priority level (high, medium, low)")
    intent_summary: str = Field(description="Human-readable summary of the parsed intent")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "configure",
                "target_devices": ["core-router-01", "distribution-sw-01"],
                "technology": "OSPF",
                "parameters": {"process_id": 1, "area": 0, "network": ["10.0.0.0/24"]},
                "environment": "devnet-sandbox",
                "priority": "high",
                "intent_summary": "Configure OSPF process 1 on core and distribution switches"
            }
        }


class NetworkIntentRequest(BaseModel):
    """Natural language intent request"""
    intent: str = Field(description="Natural language description of the network task")
    environment: Optional[str] = Field(default="devnet-sandbox", description="Target environment")
