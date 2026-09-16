from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.logging_config import logger
from app.tools.geo.maps_client import maps_client


class RouteComparatorAgent(BaseAgent):
    """Aggregates per-mode routes, ranks them and picks the best mode.

    Decision rules (deterministic):
      1. Modes that fit inside the time budget beat modes that do not.
      2. Among fitting modes, the fastest wins; ties broken by distance.
      3. If nothing fits, the fastest mode is recommended with a warning.
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Route comparator agent started")
        budget = state.get("time_budget_minutes") or 0
        from app.agents.mode_route_agent import FIELD_BY_MODE

        options: List[Dict[str, Any]] = []
        for mode, field in FIELD_BY_MODE.items():
            data = state.get(f"{field}_data") or {}
            if data.get("skipped") or data.get("status") != "OK":
                continue
            options.append({
                "mode": mode,
                "label": data.get("label", mode.title()),
                "duration_min": data.get("duration_min", 0),
                "distance_km": data.get("distance_km", 0.0),
                "summary": data.get("summary", ""),
                "duration_text": data.get("duration_text", ""),
                "fits_budget": budget > 0 and (data.get("duration_min", 0) <= budget),
            })

        if not options:
            return {
                "route_complete": False,
                "errors": state.get("errors", []) + ["No route could be computed for any selected mode."],
            }

        fitting = [o for o in options if o["fits_budget"]]
        pool = fitting or options
        pool = sorted(pool, key=lambda o: (o["duration_min"], o["distance_km"]))
        best = pool[0]
        best_data = state.get(f"{FIELD_BY_MODE[best['mode']]}_data") or {}

        route_data = {
            "origin": state.get("origin"),
            "destination": state.get("destination"),
            "best_mode": best["mode"],
            "best_label": best["label"],
            "best_duration_min": best["duration_min"],
            "best_distance_km": best["distance_km"],
            "best_summary": best_data.get("summary", ""),
            "budget_fits": bool(fitting),
            "time_budget_minutes": budget,
            "modes": options,
            "via_points": best_data.get("via_points", []),
        }

        return {
            "route_complete": True,
            "route_data": route_data,
            "current_step": "route_compare",
        }