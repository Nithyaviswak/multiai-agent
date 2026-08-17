from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class LogEntry(BaseModel):
    timestamp: str
    device: str
    severity: str
    message: str
    log_source: str = Field(description="syslog, console, buffer, trap")

class LogAnalysisResponse(BaseModel):
    """Schema for log analysis results"""
    device: str
    total_logs_analyzed: int
    errors_found: int
    warnings_found: int
    critical_events: List[Dict[str, Any]]
    patterns_detected: List[str] = Field(description="Anomaly patterns found")
    recommendations: List[str]
    health_score: float = Field(description="Device health score 0-100")
