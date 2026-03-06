from typing import TypedDict, List, Optional, Dict, Any
from pydantic import BaseModel

class AgentState(TypedDict):
    """State representation for LangGraph workflow"""
    topic: str
    research_complete: bool
    research_data: Optional[List[Dict[str, Any]]]
    research_validation_errors: List[str]
    summary_complete: bool
    summary_data: Optional[str]
    summary_validation_errors: List[str]
    report_complete: bool
    report_data: Optional[str]
    report_validation_errors: List[str]
    fact_check_complete: bool
    fact_check_data: Optional[Dict[str, Any]]
    fact_check_confidence: Optional[float]
    errors: List[str]
    current_step: str
    retry_count: int
    should_retry: bool
