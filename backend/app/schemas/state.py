from typing import TypedDict, List, Optional, Dict, Any

class AgentState(TypedDict):
    """State representation for LangGraph network automation workflow.

    Design notes:
    - Every staged agent publishes a `*_complete` flag and a `*_data` payload.
    - Failure handling relies on these flags: when a node reports `*_complete=False`
      or appends to `errors`, the workflow terminates early with a truthful
      `current_step` (``error``) instead of continuing a doomed pipeline.
    - ``trace`` carries ordered per-step execution metadata (latency, tokens,
      retries) so a run is observable and reproducible by ``run_id``.
    """
    # User request
    intent: str
    run_id: Optional[str]
    session_id: str
    user_id: str

    # Flow control
    current_step: str
    errors: List[str]
    retry_count: int
    should_retry: bool
    terminal_status: Optional[str]  # complete | error | awaiting_approval | denied

    # Agent outputs
    intent_complete: bool
    intent_data: Optional[Dict[str, Any]]
    knowledge_complete: bool
    knowledge_data: Optional[Dict[str, Any]]
    topology_complete: bool
    topology_data: Optional[Dict[str, Any]]
    netconf_complete: bool
    netconf_data: Optional[Dict[str, Any]]
    config_complete: bool
    config_data: Optional[Dict[str, Any]]
    automation_complete: bool
    automation_data: Optional[Dict[str, Any]]
    verification_complete: bool
    verification_data: Optional[Dict[str, Any]]
    monitoring_complete: bool
    monitoring_data: Optional[Dict[str, Any]]
    compliance_complete: bool
    compliance_data: Optional[Dict[str, Any]]
    log_analysis_complete: bool
    log_analysis_data: Optional[Dict[str, Any]]
    incident_complete: bool
    incident_response_data: Optional[Dict[str, Any]]

    # Final
    summary_data: Optional[Dict[str, Any]]
    summary_complete: bool

    # Enterprise features
    requires_approval: bool
    approved: bool
    approval_id: Optional[str]

    # Observability
    trace: List[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]