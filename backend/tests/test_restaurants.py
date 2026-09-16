import pytest

from app.agents.restaurant_agent import RestaurantAgent
from app.tools.geo import maps_client
from app.tools.geo.maps_client import haversine_km


def _restaurant(place_id, name, lat, lng, rating=4.5, reviews=100):
    return {
        "place_id": place_id,
        "name": name,
        "vicinity": f"{name} St",
        "rating": rating,
        "user_ratings_total": reviews,
        "price_level": 2,
        "types": ["restaurant", "food"],
        "lat": lat,
        "lng": lng,
    }


class TestRestaurantAgent:
    @pytest.mark.asyncio
    async def test_groups_results_by_meal(self, monkeypatch):
        calls = {}

        async def fake_place_search(**kwargs):
            query = kwargs.get("query")
            calls[query] = kwargs
            if "tiffin" in query:
                return [_restaurant("t1", "Idli Corner", 12.91, 77.01)]
            if "lunch" in query or "thali" in query:
                return [
                    _restaurant("l1", "Thali House", 12.90, 77.00),
                    _restaurant("l2", "Biryani Joint", 12.89, 77.02),
                ]
            return [(_restaurant("d1", "Dinner Co", 12.95, 77.05))]

        monkeypatch.setattr(maps_client, "place_search", fake_place_search)
        monkeypatch.setattr(maps_client, "anchor_point", lambda route: {"lat": 12.9, "lng": 77.0})

        agent = RestaurantAgent()
        state = {
            "meal_types": ["tiffin", "lunch"],
            "route_data": {"via_points": [[12.9, 77.0]]},
            "errors": [],
        }
        result = await agent.process(state)
        assert result["restaurants_complete"] is True
        data = result["restaurants_data"]
        assert set(data["meals"].keys()) == {"tiffin", "lunch"}
        assert len(data["meals"]["tiffin"]) == 1
        assert len(data["meals"]["lunch"]) == 2
        assert data["total"] >= 3
        assert data["meals"]["lunch"][0]["meal_type"] == "lunch"
        # Results ranked by rating then review count
        assert data["meals"]["lunch"][0]["name"] == "Thali House"
        # Distance computed from anchor
        assert data["meals"]["lunch"][0]["distance_km"] == pytest.approx(
            haversine_km(12.9, 77.0, 12.90, 77.00), rel=1e-6)

    @pytest.mark.asyncio
    async def test_no_meal_types_returns_empty(self, monkeypatch):
        calls = []

        async def fake_place_search(**kwargs):
            calls.append(kwargs)
            return []

        monkeypatch.setattr(maps_client, "place_search", fake_place_search)
        agent = RestaurantAgent()
        state = {"meal_types": [], "route_data": {"via_points": [[12.9, 77.0]]}}
        result = await agent.process(state)
        assert result["restaurants_complete"] is True
        assert result["restaurants_data"]["total"] == 0
        assert calls == []

    @pytest.mark.asyncio
    async def test_errors_from_places_ignored(self, monkeypatch):
        async def fake_place_search(**kwargs):
            return [{"error": "API down"}]

        monkeypatch.setattr(maps_client, "place_search", fake_place_search)
        monkeypatch.setattr(maps_client, "anchor_point", lambda route: {"lat": 12.9, "lng": 77.0})
        agent = RestaurantAgent()
        state = {"meal_types": ["lunch"], "route_data": {"via_points": [[12.9, 77.0]]}}
        result = await agent.process(state)
        assert result["restaurants_complete"] is True
        assert result["restaurants_data"]["total"] == 0

    def test_haversine_is_reasonable(self):
        d = haversine_km(12.9, 77.0, 13.0, 77.0)
        assert 10 < d < 13