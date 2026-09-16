import pytest

from app.agents.mode_route_agent import (
    CarRouteAgent, BusRouteAgent, TrainRouteAgent, BikeRouteAgent,
)
from app.tools.geo import maps_client

CAR_ROUTE = {
    "mode": "car",
    "status": "OK",
    "from": "Start Address",
    "to": "End Address",
    "distance_m": 120000,
    "distance_km": 120.0,
    "duration_sec": 5400,
    "duration_min": 90,
    "summary": "NH 44",
    "via_points": [[12.9, 77.0], [12.6, 77.1], [12.3, 77.2]],
}


class TestModeRouteAgents:
    @pytest.mark.asyncio
    async def test_car_route_ok(self, monkeypatch):
        async def fake_directions(origin, destination, mode, depart_at=None):
            return dict(CAR_ROUTE)

        monkeypatch.setattr(maps_client, "directions", fake_directions)
        agent = CarRouteAgent()
        state = {
            "origin": "A", "destination": "B", "travel_modes": ["car"],
            "errors": [],
        }
        result = await agent.process(state)
        assert result["route_car_complete"] is True
        assert result["route_car_data"]["mode"] == "car"
        assert result["route_car_data"]["duration_min"] == 90
        assert result["current_step"] == "route_car"

    @pytest.mark.asyncio
    async def test_mode_not_requested_skipped(self):
        agent = TrainRouteAgent()
        state = {"origin": "A", "destination": "B", "travel_modes": ["car"]}
        result = await agent.process(state)
        assert result["route_train_complete"] is True
        assert result["route_train_data"]["skipped"] is True

    @pytest.mark.asyncio
    async def test_directions_error_sets_complete_false(self, monkeypatch):
        async def failing_directions(origin, destination, mode, depart_at=None):
            return {"mode": "car", "status": "ZERO_RESULTS", "error": "no route found"}

        monkeypatch.setattr(maps_client, "directions", failing_directions)
        agent = CarRouteAgent()
        state = {"origin": "A", "destination": "B", "travel_modes": ["car"], "errors": []}
        result = await agent.process(state)
        assert result["route_car_complete"] is False
        assert result["route_car_data"] is None
        assert any("no route found" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_bus_and_bike_agents_use_own_fields(self, monkeypatch):
        async def fake_directions(origin, destination, mode, depart_at=None):
            return dict(CAR_ROUTE, mode=mode)

        monkeypatch.setattr(maps_client, "directions", fake_directions)
        state = {"origin": "A", "destination": "B", "travel_modes": ["bus", "bike"], "errors": []}
        bus = await BusRouteAgent().process(state)
        bike = await BikeRouteAgent().process(state)
        assert bus["route_bus_complete"] is True and bus["route_bus_data"]["mode"] == "bus"
        assert bike["route_bike_complete"] is True and bike["route_bike_data"]["mode"] == "bike"

    @pytest.mark.asyncio
    async def test_missing_origin_is_error(self):
        agent = CarRouteAgent()
        state = {"origin": None, "destination": "B", "travel_modes": ["car"], "errors": []}
        result = await agent.process(state)
        assert result["route_car_complete"] is False
        assert any("origin/destination" in e for e in result["errors"])