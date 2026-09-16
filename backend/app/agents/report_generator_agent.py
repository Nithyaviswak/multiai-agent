from __future__ import annotations

from typing import Any, Dict

from app.agents.base import BaseAgent
from app.logging_config import logger
from app.tools.calling.report_generator_tool import report_generator_tool


class ReportGeneratorAgent(BaseAgent):
    """Creates the final structured travel plan report."""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Travel report generator started")
        plan = state.get("plan_data") or {}
        route_data = state.get("route_data") or {}
        restaurants = state.get("restaurants_data") or {}
        places = state.get("places_data") or {}
        itinerary = state.get("itinerary_data") or {}
        knowledge = state.get("knowledge_data") or {}

        mode_options = route_data.get("modes") or []
        modes_line = "; ".join(
            f"{m['label']} ~{m['duration_min']}min ({m.get('distance_km', 0):.0f} km)"
            + (" ✓" if m.get("fits_budget") else " ✗")
            for m in mode_options
        ) or "Not available."

        restaurant_line = ", ".join(
            r.get("name", "") for r in (restaurants.get("all") or [])[:4]
        ) or "No restaurants found near the route."

        best_route = next(
            (m for m in mode_options if m.get("mode") == route_data.get("best_mode")), None)

        sections = {
            "Trip Summary": (
                f"Route: {plan.get('origin')} → {plan.get('destination')}. "
                f"Time budget: {plan.get('time_budget_minutes')} minutes. "
                f"Recommended mode: {route_data.get('best_label')} "
                f"~{route_data.get('best_duration_min')} min "
                f"{route_data.get('best_distance_km', 0):.0f} km."
            ),
            "Transport Comparison": modes_line,
            "Best Route": (
                f"{route_data.get('best_label')} in ~{route_data.get('best_duration_min')} min "
                f"({route_data.get('best_distance_km', 0):.0f} km). "
                f"Within budget: {'Yes' if route_data.get('budget_fits') else 'No'}."
            ),
            "Restaurants": restaurant_line,
            "Places to Cover": (
                f"{itinerary.get('feasibility')}: {', '.join(itinerary.get('places_covered') or []) or 'None fit the time budget.'}"
            ),
            "Timeline": "\n".join(
                f"{s['time']} {s['label']} ({s.get('duration_minutes', 0)} min)"
                for s in (itinerary.get("stops") or [])
            ) or "No itinerary generated.",
            "Travel Notes": "\n".join(knowledge.get("facts", [])) or "No notes.",
        }

        metrics = {
            "origin": plan.get("origin", ""),
            "destination": plan.get("destination", ""),
            "recommended_mode": route_data.get("best_mode", "car"),
            "duration_minutes": best_route.get("duration_min", 0) if best_route else 0,
            "distance_km": route_data.get("best_distance_km", 0.0),
            "restaurants_found": restaurants.get("total", 0),
            "places_covered": len(itinerary.get("places_covered") or []),
            "budget_fits": itinerary.get("feasibility") == "fits",
            "time_budget_minutes": itinerary.get("time_budget_minutes"),
        }

        title = f"Travel Plan: {plan.get('origin', 'Origin')} to {plan.get('destination', 'Destination')}"

        report = await report_generator_tool.execute(
            title=title[:90],
            sections=sections,
            metrics=metrics,
        )

        return {
            "summary_complete": True,
            "summary_data": report,
            "current_step": "complete",
        }