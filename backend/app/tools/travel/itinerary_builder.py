from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from app.tools.travel.meal_matcher import (
    meal_duration_minutes,
    recommend_start_hour,
    normalize_meal_type,
)

MEAL_LABELS = {
    "tiffin": "Tiffin / Breakfast",
    "lunch": "Lunch",
    "dinner": "Dinner",
}


def estimate_visit_minutes(name: str, types: List[str] = None, fallback: int = 45) -> int:
    """Heuristic visitor dwell time from place metadata (deterministic)."""
    types = types or []
    joined = " ".join([name.lower(), " ".join(types)])

    def has(*words: str) -> bool:
        return any(w in joined for w in words)

    if has("museum", "palace", "fort", "gallery", "temple"):
        return 90
    if has("park", "garden", "lake", "zoo", "botanical"):
        return 60
    if has("beach", "viewpoint", "view point", "scenic"):
        return 45
    if has("mall", "market", "bazaar"):
        return 75
    return max(30, fallback)


def estimate_detour_minutes(distance_km: float) -> int:
    """Extra travel time to leave the main route and visit a nearby place."""
    if distance_km is None:
        return 15
    if distance_km <= 2:
        return 5
    if distance_km <= 6:
        return 10
    if distance_km <= 12:
        return 20
    return 30


def _min_for_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        sec = value.get("value", value.get("seconds", 0))
    elif isinstance(value, (str,)):
        try:
            return max(1, round(float(value)))
        except (TypeError, ValueError):
            return default
    else:
        sec = value or 0
    minutes = round(int(sec) / 60)
    return minutes if minutes > 0 else default


def route_duration_minutes(route_data: Dict[str, Any]) -> int:
    if not route_data:
        return 0
    return _min_for_int(route_data.get("duration_min", route_data.get("duration", 0)), 0)


def build_itinerary(
    *,
    route: Dict[str, Any],
    meal_types: List[str],
    places: List[Dict[str, Any]],
    time_budget_minutes: int,
    restaurants: List[Dict[str, Any]] = None,
    default_meal_duration: int = 45,
    max_places: int = 5,
    start_hour: Optional[int] = None,
) -> Dict[str, Any]:
    """Build a timed travel itinerary that fits the time budget.

    Deterministic scheduling rules:
      1. Route travel time, the requested meal stop(s) and the chosen places
         must all fit inside ``time_budget_minutes``.
      2. Places are selected greedily by rating (highest first) subject to the
         detour + visit cost still fitting in the remaining margin.
      3. Stops are emitted in a sensible chronological order: departure, places
         before the meal, the meal slot, remaining places, final arrival.
    """
    restaurants = restaurants or []
    meals = [m for m in (normalize_meal_type(x) for x in meal_types) if m]
    budget = max(60, int(time_budget_minutes or 0))

    route_min = route_duration_minutes(route)
    meal_min = sum(meal_duration_minutes(m, default_meal_duration) for m in meals)
    margin = budget - route_min - meal_min
    feasible = margin > 0

    ranked = sorted(
        places,
        key=lambda p: (p.get("rating", 0.0) or 0.0, p.get("user_ratings_total", 0) or 0),
        reverse=True,
    )

    chosen: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    remaining = margin
    for place in ranked:
        if len(chosen) >= max_places:
            skipped.append({**place, "reason": "place limit reached"})
            continue
        visit = estimate_visit_minutes(place.get("name", ""), place.get("types"))
        detour = estimate_detour_minutes(place.get("distance_km"))
        cost = detour + visit
        if remaining >= cost:
            chosen.append({**place, "visit_minutes": visit, "detour_minutes": detour})
            remaining -= cost
        else:
            skipped.append({**place, "reason": "does not fit remaining time"})

    clock_start = start_hour if start_hour is not None else (
        recommend_start_hour(meals) if meals else 7
    )
    cursor = datetime(2000, 1, 1, clock_start, 0)
    stops: List[Dict[str, Any]] = []

    def add_stop(kind: str, label: str, desc: str, duration_min: int = 0,
                 extra: Optional[Dict[str, Any]] = None) -> None:
        nonlocal cursor
        stops.append({
            "id": len(stops) + 1,
            "kind": kind,
            "label": label,
            "description": desc,
            "time": cursor.strftime("%H:%M"),
            "duration_minutes": duration_min,
            **(extra or {}),
        })
        cursor += timedelta(minutes=duration_min)

    add_stop("departure", "Depart", f"Start from origin", 0,
             {"place": route.get("from", "")})

    places_before = chosen[: max(1, len(chosen) // 2)] or chosen
    places_after = chosen[len(places_before):]

    for p in places_before:
        add_stop(
            "place", p.get("display_name") or p.get("name"), p.get("name", ""),
            p["visit_minutes"] + p["detour_minutes"],
            {"place_id": p.get("place_id"), "rating": p.get("rating"),
             "distance_km": p.get("distance_km")},
        )

    for idx, meal in enumerate(meals):
        restaurant = None
        if restaurants:
            restaurant = restaurants[0]
        add_stop(
            "meal", MEAL_LABELS.get(meal, meal.title()), f"Meal break ({meal})",
            meal_duration_minutes(meal, default_meal_duration),
            {"meal_type": meal,
             "restaurant_name": restaurant.get("name") if restaurant else None,
             "restaurant_address": restaurant.get("vicinity", "") if restaurant else ""},
        )
        if len(restaurants) > 1:
            restaurants = restaurants[1:]

    for p in places_after:
        add_stop(
            "place", p.get("display_name") or p.get("name"), p.get("name", ""),
            p["visit_minutes"] + p["detour_minutes"],
            {"place_id": p.get("place_id"), "rating": p.get("rating"),
             "distance_km": p.get("distance_km")},
        )

    add_stop("arrival", "Arrive", f"Reach destination", 0,
             {"place": route.get("to", ""), "mode": route.get("mode")})

    total_planned = route_min + meal_min + sum(
        p["visit_minutes"] + p["detour_minutes"] for p in chosen
    )

    return {
        "mode": route.get("mode", "car"),
        "origin": route.get("from", ""),
        "destination": route.get("to", ""),
        "time_budget_minutes": budget,
        "route_minutes": route_min,
        "meal_minutes": meal_min,
        "places_minutes": sum(p["visit_minutes"] + p["detour_minutes"] for p in chosen),
        "total_planned_minutes": total_planned,
        "feasibility": "fits" if feasible and total_planned <= budget else "over_budget",
        "places_covered": [p["name"] for p in chosen],
        "places_skipped": [
            {"name": p.get("name", ""), "reason": p.get("reason", "")} for p in skipped
        ],
        "starts_at": f"{clock_start:02d}:00",
        "stops": stops,
    }