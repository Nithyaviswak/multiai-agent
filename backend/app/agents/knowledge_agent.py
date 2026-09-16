from __future__ import annotations

from typing import Any, Dict, Optional, List

from app.agents.base import BaseAgent
from app.logging_config import logger


class KnowledgeAgent(BaseAgent):
    """Gathers lightweight travel context: route distance, meal stops, hours.

    Pure deterministic lookups + optional web search (Tavily) for travel tips
    when a key is configured. Never blocks the workflow on search failures.
    """

    def _distance_bin(self, distance_km: Optional[float]) -> str:
        if distance_km is None:
            return "unknown"
        if distance_km < 30:
            return "short"
        if distance_km < 150:
            return "medium"
        return "long"

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("intent", "")
        logger.info("Travel knowledge agent started")

        origin = state.get("origin") or ""
        destination = state.get("destination") or ""
        facts = [
            f"Cities/places: from {origin or 'origin'} to {destination or 'destination'}.",
            self._distance_tip(state.get("route_data") or {}),
            self._meal_tip(state.get("meal_types") or []),
        ]

        web_sources: List[Dict[str, Any]] = []
        try:
            from app.tools.calling.search_tool import search_tool
            search_query = f"travel tips {origin} to {destination} must see food route"
            results = await search_tool.execute(search_query, max_results=2)
            web_sources = results.get("results", []) or []
            web_sources = web_sources[:2]
        except Exception as e:
            logger.info("Travel web search skipped", error=str(e))

        return {
            "knowledge_data": {
                "facts": facts,
                "web_sources": web_sources,
                "total_sources": len(facts) + len(web_sources),
            },
            "knowledge_complete": True,
            "current_step": "knowledge",
        }

    def _distance_tip(self, route_data: Dict[str, Any]) -> str:
        dist = route_data.get("best_distance_km")
        dur = route_data.get("best_duration_min")
        if dist is None:
            return "Route distance not available yet."
        return (f"The best route is about {dist:.0f} km and takes roughly "
                f"{dur or 'unknown'} minutes by {route_data.get('best_label', route_data.get('best_mode', 'car'))}.")

    def _meal_tip(self, meal_types) -> str:
        if not meal_types:
            return "No meal stops requested; plan snack breaks on the move."
        return f"Planned meal stops: {', '.join(m.title() for m in meal_types)}."