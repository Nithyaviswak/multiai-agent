from __future__ import annotations

from typing import Any, Dict

from app.agents.base import BaseAgent
from app.logging_config import logger
from app.tools.geo.maps_client import GoogleMapsClientError, maps_client

FIELD_BY_MODE = {
    "car": "route_car",
    "bus": "route_bus",
    "train": "route_train",
    "bike": "route_bike",
}


class ModeRouteAgent(BaseAgent):
    """Computes the best route for a single transport mode via Directions API."""

    mode: str = "car"
    label: str = "Car"

    def __init__(self, model: str = None, mode: str = None, label: str = None):
        super().__init__(model)
        if mode:
            self.mode = mode
        if label:
            self.label = label

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        field = FIELD_BY_MODE[self.mode]
        step = f"route_{self.mode}"
        modes_selected = [m for m in (state.get("travel_modes") or []) if m in FIELD_BY_MODE]

        if self.mode not in modes_selected:
            return {
                f"{field}_complete": True,
                f"{field}_data": {"mode": self.mode, "skipped": True, "reason": "mode not requested"},
                "current_step": f"route_{self.mode}",
            }

        origin = state.get("origin")
        destination = state.get("destination")
        if not origin or not destination:
            return {
                f"{field}_complete": False,
                f"{field}_data": None,
                "errors": state.get("errors", []) + [
                    f"{self.label} route failed: origin/destination not set"
                ],
            }

        logger.info("Mode route agent started", mode=self.mode, origin=origin, destination=destination)
        try:
            route = await maps_client.directions(origin, destination, self.mode)
        except GoogleMapsClientError as e:
            return {
                f"{field}_complete": False,
                f"{field}_data": None,
                "errors": state.get("errors", []) + [
                    f"{self.label} route failed: {e}"
                ],
            }
        except Exception as e:
            logger.error("Mode route agent failed", mode=self.mode, error=str(e))
            return {
                f"{field}_complete": False,
                f"{field}_data": None,
                "errors": state.get("errors", []) + [
                    f"{self.label} route failed: {e}"
                ],
            }

        if route.get("status") != "OK":
            return {
                f"{field}_complete": False,
                f"{field}_data": None,
                "errors": state.get("errors", []) + [
                    f"{self.label} route failed: {route.get('error') or route.get('status')}"
                ],
            }

        route["label"] = self.label
        return {
            f"{field}_complete": True,
            f"{field}_data": route,
            "current_step": f"route_{self.mode}",
        }


class CarRouteAgent(ModeRouteAgent):
    mode = "car"
    label = "Car"


class BusRouteAgent(ModeRouteAgent):
    mode = "bus"
    label = "Bus"


class TrainRouteAgent(ModeRouteAgent):
    mode = "train"
    label = "Train"


class BikeRouteAgent(ModeRouteAgent):
    mode = "bike"
    label = "Bike"