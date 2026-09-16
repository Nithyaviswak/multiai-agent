from typing import TypedDict, List, Optional, Dict, Any

class AgentState(TypedDict):
    """State representation for LangGraph travel planning workflow.

    Design notes:
    - The TravelPlannerAgent publishes `plan_complete` plus the structured
      fields (origin, destination, modes, meals, budget).
    - Each transport-mode route agent publishes its own `route_<mode>_complete`
      / `route_<mode>_data`. The comparator aggregates them into `route_data`
      once every selected mode has finished (the graph fans in automatically).
    - Failure handling relies on the `*_complete` flags: when a node reports
      incomplete or appends to `errors`, the workflow terminates early with a
      truthful `current_step`.
    - ``trace`` carries ordered per-step execution metadata (latency, tokens,
      retries) so a run is observable and reproducible by ``run_id``.
    """
    # User request (raw + structured)
    intent: str
    run_id: Optional[str]
    session_id: str
    user_id: str
    origin: Optional[str]
    destination: Optional[str]
    travel_modes: List[str]
    meal_types: List[str]
    time_budget_minutes: Optional[int]
    preferences: Optional[Dict[str, Any]]

    # Flow control
    current_step: str
    errors: List[str]
    retry_count: int
    should_retry: bool
    terminal_status: Optional[str]  # complete | error

    # Agent outputs
    plan_complete: bool
    plan_data: Optional[Dict[str, Any]]
    route_car_complete: bool
    route_car_data: Optional[Dict[str, Any]]
    route_bus_complete: bool
    route_bus_data: Optional[Dict[str, Any]]
    route_train_complete: bool
    route_train_data: Optional[Dict[str, Any]]
    route_bike_complete: bool
    route_bike_data: Optional[Dict[str, Any]]
    route_complete: bool
    route_data: Optional[Dict[str, Any]]
    knowledge_complete: bool
    knowledge_data: Optional[Dict[str, Any]]
    restaurants_complete: bool
    restaurants_data: Optional[Dict[str, Any]]
    places_complete: bool
    places_data: Optional[Dict[str, Any]]
    itinerary_complete: bool
    itinerary_data: Optional[Dict[str, Any]]

    # Final
    summary_data: Optional[Dict[str, Any]]
    summary_complete: bool

    # Observability
    trace: List[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]