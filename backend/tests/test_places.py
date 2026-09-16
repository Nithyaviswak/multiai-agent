import pytest

from app.agents.places_agent import PlacesAgent
from app.tools.geo import maps_client


def _place(place_id, name, lat, lng, rating=4.5, reviews=100, types=None):
    return {
        "place_id": place_id,
        "name": name,
        "vicinity": f"{name} road",
        "rating": rating,
        "user_ratings_total": reviews,
        "types": types or ["tourist_attraction", "point_of_interest"],
        "lat": lat,
        "lng": lng,
    }


class TestPlacesAgent:
    @pytest.mark.asyncio
    async def test_only_feasible_places_returned(self, monkeypatch):
        async def fake_place_search(**kwargs):
            return [
                _place("p1", "Bannerghatta Park", 12.80, 77.58, rating=4.8, reviews=5000,
                       types=["park", "zoo"]),          # visit 60 min, detour ~30 (far)
                _place("p2", "Lalbagh Garden", 12.95, 77.58, rating=4.7, reviews=8000,
                       types=["park", "garden"]),        # close
                _place("p3", "Mysore Palace", 12.30, 76.65, rating=4.9, reviews=40000,
                       types=["palace"]),                # very far
            ]

        monkeypatch.setattr(maps_client, "place_search", fake_place_search)
        monkeypatch.setattr(maps_client, "anchor_point", lambda route: {"lat": 12.9, "lng": 77.55})

        agent = PlacesAgent()
        state = {
            "route_data": {"best_duration_min": 90},
            "meal_types": ["lunch"],
            "time_budget_minutes": 240,
            "errors": [],
        }
        result = await agent.process(state)
        assert result["places_complete"] is True
        data = result["places_data"]
        # margin = 240 - 90 - 45 = 105
        assert data["margin_minutes"] == 105
        # Far places (cost likely > margin) must be filtered out
        for p in data["places"]:
            assert p["cost_minutes"] <= 105
        assert all(p["place_id"] in {"p1", "p2"} for p in data["places"])

    @pytest.mark.asyncio
    async def test_no_anchor_returns_error(self, monkeypatch):
        monkeypatch.setattr(maps_client, "anchor_point", lambda route: None)
        agent = PlacesAgent()
        state = {"route_data": {}, "meal_types": [], "errors": []}
        result = await agent.process(state)
        assert result["places_complete"] is False
        assert any("anchor" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_small_negative_margin_returns_empty(self, monkeypatch):
        async def fake_place_search(**kwargs):
            return [_place("p1", "Museum", 12.9, 77.55, rating=4.8, reviews=1000)]

        monkeypatch.setattr(maps_client, "place_search", fake_place_search)
        monkeypatch.setattr(maps_client, "anchor_point", lambda route: {"lat": 12.9, "lng": 77.55})
        agent = PlacesAgent()
        state = {
            "route_data": {"best_duration_min": 300},
            "meal_types": ["lunch", "dinner"],
            "time_budget_minutes": 360,
            "errors": [],
        }
        result = await agent.process(state)
        assert result["places_complete"] is True
        assert result["places_data"]["places"] == []