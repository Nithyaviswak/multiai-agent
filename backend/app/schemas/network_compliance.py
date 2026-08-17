from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ComplianceCheck(BaseModel):
    check_id: str
    check_name: str
    category: str = Field(description="Category like security, routing, management, etc.")
    status: str = Field(description="pass, fail, or warning")
    severity: str = Field(description="critical, high, medium, low")
    device: str
    details: str
    recommendation: str

class ComplianceResponse(BaseModel):
    """Schema for compliance check results"""
    standard: str = Field(description="Compliance standard (CIS benchmarks, PCI-DSS, HIPAA, custom)")
    environment: str = Field(description="Environment checked")
    total_checks: int
    passed: int
    failed: int
    warnings: int
    overall_score: float = Field(description="Overall compliance score 0-100")
    checks: List[ComplianceCheck]
    remediation_plan: List[str]
