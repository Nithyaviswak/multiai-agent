from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.config import settings
from app.logging_config import logger
from app.tools.geo.maps_client import haversine_km, maps_client
from app.tools.travel.itinerary_builder import estimate_detour_minutes, estimate_visit_minutes
from app.tools.travel.meal_matcher import meal_duration_minutes


class PlacesAgent(BaseAgent):
    """Finds places of interest near the route that fit the remaining time.

    A place is pre-filtered as feasible only when its estimated detour + visit
    time fits inside the slack left by travel time and the requested meal stops,
    so the itinerary builder never has to drop everything.
    """

    PLACE_QUERIES = ["tourist attractions", "monuments", "parks and gardens",
                     "museums", "historic sights", "viewpoints"]

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Places agent started")
        route_data = state.get("route_data") or {}
        anchor = maps_client.anchor_point(route_data)
        if not anchor:
            return {
                "places_complete": False,
                "places_data": None,
                "errors": state.get("errors", []) + ["No anchor point along the route."],
            }

        route_min = route_data.get("best_duration_min", 0)
        meal_min = sum(
            meal_duration_minutes(m, settings.MEAL_DURATION_MINUTES)
            for m in (state.get("meal_types") or [])
        )
        budget = state.get("time_budget_minutes") or settings.DEFAULT_TIME_BUDGET_MINUTES
        margin = budget - route_min - meal_min

        pool: Dict[str, Dict[str, Any]] = {}
        for query in self.PLACE_QUERIES:
            results = await maps_client.place_search(
                query=query, location=anchor,
                radius=settings.PLACES_RADIUS_METERS, max_results=maps_client.MAX_RESULTS,
            )
            for res in results:
                if res.get("error") or not res.get("place_id"):
                    continue
                if res["place_id"] in pool:
                    continue
                if res.get("lat") is not None:
                    res["distance_km"] = haversine_km(anchor["lat"], anchor["lng"],
                                                      res["lat"], res["lng"])
                else:
                    res["distance_km"] = None
                res["visit_minutes"] = estimate_visit_minutes(res.get("name", ""), res.get("types"))
                res["detour_minutes"] = estimate_detour_minutes(res.get("distance_km"))
                res["cost_minutes"] = res["visit_minutes"] + res["detour_minutes"]
                pool[res["place_id"]] = res

        candidates = sorted(
            pool.values(),
            key=lambda p: (p.get("rating") or 0.0, p.get("user_ratings_total") or 0),
            reverse=True,
        )

        # Feasibility pre-filter: detour + visit must fit the slack.
        feasible = [c for c in candidates if c["cost_minutes"] <= margin]
        feasible = feasible[: settings.MAX_PLACES_TO_COVER * 2]

        return {
            "places_complete": True,
            "places_data": {
                "places": feasible,
                "count": len(feasible),
                "margin_minutes": margin,
                "anchor": anchor,
                "total_candidates": len(candidates),
            },
            "current_step": "places",
        }