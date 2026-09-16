from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.config import settings
from app.logging_config import logger
from app.tools.geo.maps_client import haversine_km, maps_client
from app.tools.travel.meal_matcher import MEAL_PROFILES, normalize_meal_type


class RestaurantAgent(BaseAgent):
    """Finds restaurants near the route, grouped by meal type.

    For every requested meal (tiffin/lunch/dinner) it runs a Places text search
    using that meal's keywords biased to the route's midpoint. Results are
    tagged with the meal they were found for, rated by (rating, review count)
    and deduplicated by place_id.
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Restaurant agent started")
        route_data = state.get("route_data") or {}
        anchor = maps_client.anchor_point(route_data)
        meal_types = [m for m in (state.get("meal_types") or []) if normalize_meal_type(m)]
        radius = settings.RESTAURANT_RADIUS_METERS

        if not anchor or not meal_types:
            return {
                "restaurants_complete": True,
                "restaurants_data": {
                    "meals": {},
                    "all": [],
                    "total": 0,
                    "anchor": anchor,
                    "message": "No anchor point or meal types available.",
                },
                "current_step": "restaurants",
            }

        meals: Dict[str, List[Dict[str, Any]]] = {m: [] for m in meal_types}
        now_hour = datetime.now().hour
        for meal in meal_types:
            profile = MEAL_PROFILES.get(meal, {})
            query = " ".join(profile.get("search_keywords", ["restaurant"]))
            open_now = profile.get("start_hour", 0) <= now_hour < profile.get("end_hour", 24)
            results = await maps_client.place_search(
                query=query, location=anchor, radius=radius, open_now=open_now,
                max_results=4,
            )
            for res in results:
                if res.get("error"):
                    continue
                res["meal_type"] = meal
                if res.get("lat") is not None and anchor:
                    res["distance_km"] = haversine_km(anchor["lat"], anchor["lng"],
                                                      res["lat"], res["lng"])
                else:
                    res["distance_km"] = None
                meals[meal].append(res)

        all_results: List[Dict[str, Any]] = []
        seen: set = set()
        for meal, items in meals.items():
            ranked = sorted(
                items,
                key=lambda r: (r.get("rating") or 0.0, r.get("user_ratings_total") or 0),
                reverse=True,
            )
            meals[meal] = ranked[:3]
            for r in ranked[:3]:
                if r["place_id"] in seen:
                    continue
                seen.add(r["place_id"])
                all_results.append({**r, "meal_match": meal})

        return {
            "restaurants_complete": True,
            "restaurants_data": {
                "meals": {m: items for m, items in meals.items()},
                "all": all_results,
                "total": len(all_results),
                "anchor": anchor,
            },
            "current_step": "restaurants",
        }