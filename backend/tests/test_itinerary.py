import pytest

from app.tools.travel.itinerary_builder import (
    build_itinerary, estimate_visit_minutes, estimate_detour_minutes,
    route_duration_minutes,
)


ROUTE = {
    "mode": "car",
    "from": "Bengaluru",
    "to": "Mysuru",
    "duration_min": 90,
    "distance_km": 120.0,
    "summary": "NH 275",
}


def _place(place_id, name, rating=4.6, reviews=100, distance_km=3.0, types=None):
    return {
        "place_id": place_id,
        "name": name,
        "rating": rating,
        "user_ratings_total": reviews,
        "distance_km": distance_km,
        "types": types or ["tourist_attraction"],
    }


def _restaurant(name, address="Near route"):
    return {"name": name, "vicinity": address}


class TestEstimators:
    def test_visit_minutes_by_type(self):
        assert estimate_visit_minutes("Mysore Palace", ["tourist_attraction"]) == 90
        assert estimate_visit_minutes("Cubbon Park", ["park"]) == 60
        assert estimate_visit_minutes("Sunset Point", ["view_point"]) == 45
        assert estimate_visit_minutes("Random Store", ["store"]) == 45

    def test_detour_by_distance(self):
        assert estimate_detour_minutes(1.0) == 5
        assert estimate_detour_minutes(4.0) == 10
        assert estimate_detour_minutes(9.0) == 20
        assert estimate_detour_minutes(30.0) == 30
        assert estimate_detour_minutes(None) == 15

    def test_route_duration(self):
        assert route_duration_minutes({"duration_min": 90}) == 90
        assert route_duration_minutes({"duration": {"value": 2100}}) == 35
        assert route_duration_minutes(None) == 0


class TestBuildItinerary:
    def test_places_ranked_and_within_budget(self):
        places = [
            _place("p1", "Top Palace", rating=4.9, reviews=1000, distance_km=2.0,
                   types=["palace"]),        # visit 90 + detour 5 = 95
            _place("p2", "Big Park", rating=4.5, reviews=900, distance_km=1.0,
                   types=["park"]),          # visit 60 + detour 5 = 65
            _place("p3", "Mediocre View", rating=3.5, reviews=50, distance_km=30.0),
        ]
        itinerary = build_itinerary(
            route=ROUTE, meal_types=["lunch"], places=places,
            time_budget_minutes=360, restaurants=[_restaurant("Thali House")],
            default_meal_duration=45, max_places=5,
        )
        assert itinerary["feasibility"] == "fits"
        assert itinerary["places_covered"] == ["Top Palace", "Big Park"]
        # Skipped because total would not fit OR low rating lost the ranking
        assert any(s["name"] == "Mediocre View" for s in itinerary["places_skipped"])
        kinds = [s["kind"] for s in itinerary["stops"]]
        assert kinds[0] == "departure"
        assert "meal" in kinds
        assert kinds[-1] == "arrival"
        meal_stop = next(s for s in itinerary["stops"] if s["kind"] == "meal")
        assert meal_stop["restaurant_name"] == "Thali House"
        assert meal_stop["meal_type"] == "lunch"
        assert meal_stop["duration_minutes"] == 45
        assert itinerary["total_planned_minutes"] <= 360

    def test_over_budget_flag(self):
        places = [
            _place("p1", "Far Palace", rating=4.9, reviews=1000, distance_km=100.0,
                   types=["palace"]),   # visit 90 + detour 30 = 120
            _place("p2", "Reflected Museum", rating=4.8, reviews=500, distance_km=100.0,
                   types=["museum"]),
        ]
        itinerary = build_itinerary(
            route={"**": "x", **ROUTE, "duration_min": 300}, meal_types=["lunch"],
            places=places, time_budget_minutes=80, restaurants=[],
            default_meal_duration=45, max_places=3,
        )
        # route 300 > budget 80 -> no room at all
        assert itinerary["total_planned_minutes"] > itinerary["time_budget_minutes"]

    def test_no_places_no_meals(self):
        itinerary = build_itinerary(
            route=ROUTE, meal_types=[], places=[],
            time_budget_minutes=120, restaurants=[],
        )
        assert itinerary["feasibility"] == "fits"
        assert itinerary["places_covered"] == []
        kinds = [s["kind"] for s in itinerary["stops"]]
        assert kinds == ["departure", "arrival"]
        assert itinerary["starts_at"] == "07:00"

    def test_meal_restaurants_rotated(self):
        itinerary = build_itinerary(
            route=ROUTE, meal_types=["tiffin", "lunch"], places=[],
            time_budget_minutes=240,
            restaurants=[_restaurant("Breakfast Co"), _restaurant("Lunch Co")],
        )
        meals = [s for s in itinerary["stops"] if s["kind"] == "meal"]
        assert [m["restaurant_name"] for m in meals] == ["Breakfast Co", "Lunch Co"]
        assert [m["duration_minutes"] for m in meals] == [30, 45]

    def test_deterministic_output(self):
        places = [
            _place("p1", "A Museum", rating=4.8, reviews=10, types=["museum"]),
            _place("p2", "B Park", rating=4.7, reviews=8, types=["park"]),
        ]
        a = build_itinerary(route=ROUTE, meal_types=["lunch"], places=places,
                            time_budget_minutes=200, max_places=2)
        b = build_itinerary(route=ROUTE, meal_types=["lunch"], places=places,
                            time_budget_minutes=200, max_places=2)
        assert a == b