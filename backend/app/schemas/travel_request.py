from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


VALID_TRAVEL_MODES = ("car", "bus", "train", "bike")
VALID_MEAL_TYPES = ("tiffin", "lunch", "dinner")


class TravelRequest(BaseModel):
    """Natural language travel planning request with optional structured fields.

    When structured fields are omitted, the TravelPlannerAgent extracts them
    from ``intent`` (origin, destination, preferred transport modes, meal
    needs and the available time budget).
    """
    intent: str = Field(description="Natural language description of the trip")
    origin: Optional[str] = Field(default=None, description="Starting location (name or address)")
    destination: Optional[str] = Field(default=None, description="Final destination")
    travel_modes: Optional[List[str]] = Field(
        default=None,
        description=f"Transport modes to consider: {', '.join(VALID_TRAVEL_MODES)}",
    )
    meal_types: Optional[List[str]] = Field(
        default=None,
        description=f"Meal types to plan for: {', '.join(VALID_MEAL_TYPES)}",
    )
    time_budget_minutes: Optional[int] = Field(
        default=None, description="Total time available for the trip, in minutes"
    )
    preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extra preferences (budget, cuisine, avoid tolls, accessibility, etc.)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "I need to travel from Bengaluru to Mysuru by train. "
                          "I want lunch on the way and to cover some places within 6 hours.",
                "origin": "Bengaluru",
                "destination": "Mysuru",
                "travel_modes": ["train"],
                "meal_types": ["lunch"],
                "time_budget_minutes": 360,
            }
        }


class TravelResponse(BaseModel):
    """Response envelope for the travel workflow."""
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    workflow_id: Optional[str]