from __future__ import annotations

from typing import Dict, List

# Meal windows (hour-of-day, 24h) and restaurant-discovery keywords per meal.
MEAL_PROFILES: Dict[str, Dict] = {
    "tiffin": {
        "label": "Tiffin / Breakfast",
        "start_hour": 6,
        "end_hour": 11,
        "search_keywords": ["tiffin", "breakfast", "idli", "dosa", "poha", "morning foods"],
        "place_types": [],
    },
    "lunch": {
        "label": "Lunch",
        "start_hour": 11,
        "end_hour": 16,
        "search_keywords": ["lunch", "thali", "buffet", "veg meals", "biryani"],
        "place_types": [],
    },
    "dinner": {
        "label": "Dinner",
        "start_hour": 16,
        "end_hour": 23,
        "search_keywords": ["dinner", "restaurant", "evening meal", "dhaba"],
        "place_types": [],
    },
}


def normalize_meal_type(value: str) -> str:
    v = (value or "").strip().lower()
    for meal in MEAL_PROFILES:
        if v == meal:
            return meal
        if v in ("breakfast", "brunch", "morning"):
            return "tiffin"
        if v in ("noon", "afternoon"):
            return "lunch"
        if v in ("night", "supper"):
            return "dinner"
    return v if v in MEAL_PROFILES else ""


def meal_start_hour(meal_type: str) -> int:
    profile = MEAL_PROFILES.get(normalize_meal_type(meal_type), {})
    return profile.get("start_hour", 12)


def meal_duration_minutes(meal_type: str, default: int) -> int:
    """Heuristic dwell times so tests stay deterministic."""
    base = {
        "tiffin": 30,
        "lunch": 45,
        "dinner": 60,
    }.get(normalize_meal_type(meal_type), default)
    return max(15, base)


def recommend_start_hour(meal_types: List[str], default: int = 7) -> int:
    """Pick a departure hour near the beginning of the earliest requested meal."""
    cleansed = [m for m in (normalize_meal_type(x) for x in meal_types) if m]
    if not cleansed:
        return default
    earliest = min(meal_start_hour(m) for m in cleansed) - 2
    return max(6, min(default, earliest))


def search_keywords_for(meal_types: List[str]) -> List[str]:
    keywords: List[str] = []
    for meal in meal_types:
        profile = MEAL_PROFILES.get(normalize_meal_type(meal))
        if profile:
            keywords.extend(profile["search_keywords"])
    return keywords or ["restaurant"]