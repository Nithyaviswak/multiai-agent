from __future__ import annotations

from typing import Any, Dict

from app.agents.base import BaseAgent
from app.config import settings
from app.logging_config import logger
from app.tools.travel.itinerary_builder import build_itinerary


class ItineraryAgent(BaseAgent):
    """Assembles the final timed plan within the user's time budget."""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Itinerary agent started")
        route_data = state.get("route_data") or {}
        places_data = state.get("places_data") or {}
        restaurants_data = state.get("restaurants_data") or {}

        if not route_data:
            return {
                "itinerary_complete": False,
                "itinerary_data": None,
                "errors": state.get("errors", []) + ["No route available to build an itinerary."],
            }

        best_route = {
            "mode": route_data.get("best_mode", "car"),
            "from": route_data.get("origin"),
            "to": route_data.get("destination"),
            "duration_min": route_data.get("best_duration_min", 0),
            "distance_km": route_data.get("best_distance_km", 0.0),
            "summary": route_data.get("best_summary", ""),
        }

        restaurants = restaurants_data.get("all") or []
        places = [p for p in (places_data.get("places") or []) if p.get("name")]

        itinerary = build_itinerary(
            route=best_route,
            meal_types=state.get("meal_types") or [],
            places=places,
            time_budget_minutes=state.get("time_budget_minutes")
            or settings.DEFAULT_TIME_BUDGET_MINUTES,
            restaurants=restaurants,
            default_meal_duration=settings.MEAL_DURATION_MINUTES,
            max_places=settings.MAX_PLACES_TO_COVER,
        )

        return {
            "itinerary_complete": True,
            "itinerary_data": itinerary,
            "current_step": "itinerary",
        }