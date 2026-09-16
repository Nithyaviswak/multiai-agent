from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.config import settings
from app.logging_config import logger

ALL_MODES = ["car", "bus", "train", "bike"]
MODE_KEYWORDS = {
    "car": ["car", "cab", "taxi", "uber", "ola", "drive", "driving", "road trip"],
    "bus": ["bus", "volvo"],
    "train": ["train", "rail", "metro", "railway"],
    "bike": ["bike", "bicycle", "cycle", "cycling", "motorbike", "two-wheeler", "scooter"],
}
ALL_MEALS = ["tiffin", "lunch", "dinner"]
MEAL_KEYWORDS = {
    "tiffin": ["tiffin", "breakfast", "brunch", "morning meal"],
    "lunch": ["lunch", "noon meal", "afternoon meal"],
    "dinner": ["dinner", "evening meal", "supper"],
}
BUDGET_PATTERNS = [
    re.compile(r"(?P<v>\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\b", re.IGNORECASE),
    re.compile(r"(?P<v>\d+(?:\.\d+)?)\s*(?:minutes?|mins?)\b", re.IGNORECASE),
]


# ── Deterministic extraction helpers (pure & testable) ──────────
def extract_travel_modes(intent: str) -> List[str]:
    text = f" {intent.lower()} "
    found = [mode for mode in ALL_MODES if any(re.search(rf"\b{w}\b", text) for w in MODE_KEYWORDS[mode])]
    return found


def extract_meal_types(intent: str) -> List[str]:
    text = f" {intent.lower()} "
    return [meal for meal in ALL_MEALS if any(re.search(rf"\b{w}\b", text) for w in MEAL_KEYWORDS[meal])]


def extract_time_budget(intent: str) -> Optional[int]:
    text = intent.lower()
    for pattern in BUDGET_PATTERNS:
        m = pattern.search(text)
        if m:
            value = float(m.group("v"))
            if "min" in pattern.pattern:
                return max(15, int(value))
            return max(30, int(value * 60))
    if re.search(r"\bhalf\s+(?:a\s+)?day\b", text):
        return 240
    return None


def extract_origin_destination(intent: str) -> (Optional[str], Optional[str]):
    """Extract ``origin`` and ``destination`` with regex fallbacks (best-effort)."""
    text = intent.strip()
    if not text:
        return None, None

    stop = (r"\b(?:by|via|around|within|in|covering|cover|and|for|need|want|with|"
            r"take|spend|on|at|please|plan|have|stop|eat|lunch|dinner|tiffin|breakfast)\b")
    dest_verb = r"(?:reach|arrive\s+at|get\s+to|go\s+to|head\s+to)"

    def chunk(part: str) -> str:
        return re.split(stop, part, flags=re.IGNORECASE)[0].strip(" .,;")

    # 1) Canonical "from A to B ..." — the destination marker must not be part
    #    of a trailing travel verb (e.g. "need to reach X").
    m = re.search(
        r"\bfrom\s+(?P<origin>.+?)\s+to\s+(?:(?:" + dest_verb + r")\s+)?(?P<dest>.+?)(?=" + stop + r"|$)",
        text, re.IGNORECASE,
    )
    if m:
        origin = chunk(m.group("origin"))
        destination = chunk(m.group("dest"))
        if origin and destination:
            return origin, destination

    # 2) Verb-based destination + standalone "from".
    m = re.search(
        r"\b(?:" + dest_verb + r")\s+(?P<dest>.+?)(?=" + stop + r"|$)",
        text, re.IGNORECASE,
    )
    destination = chunk(m.group("dest")) if m else None
    m = re.search(r"\bfrom\s+(?P<origin>.+?)(?=" + stop + r"|$)", text, re.IGNORECASE)
    origin = chunk(m.group("origin")) if m else None
    return origin, destination


class TravelPlannerAgent(BaseAgent):
    """Planner that converts the raw request into a structured travel plan.

    Merge precedence: structured fields sent with the request > LLM extraction
    > deterministic regex extraction. Missing origin/destination is a hard error;
    modes/meals/budget fall back to sensible defaults.
    """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        intent = state.get("intent", "")
        logger.info("Travel planner agent started", intent=intent)

        origin, destination, modes, meals, budget = self._from_state(state)
        missing_origin = not origin
        missing_destination = not destination

        if missing_origin or missing_destination or not modes or not meals or budget is None:
            llm_fields = await self._llm_extract(intent)
        else:
            llm_fields = {}

        origin = origin or llm_fields.get("origin") or (extract_origin_destination(intent)[0])
        destination = (destination or llm_fields.get("destination")
                       or extract_origin_destination(intent)[1])
        modes = modes or llm_fields.get("travel_modes") or extract_travel_modes(intent)
        meals = meals or llm_fields.get("meal_types") or extract_meal_types(intent)
        if budget is None:
            budget = llm_fields.get("time_budget_minutes") or extract_time_budget(intent)

        modes = [m for m in modes if m in ALL_MODES] or list(ALL_MODES)
        meals = [m for m in meals if m in ALL_MEALS] or list(ALL_MEALS)
        budget = budget or settings.DEFAULT_TIME_BUDGET_MINUTES

        errors = []
        if not origin:
            errors.append("Could not determine the origin/starting point.")
        if not destination:
            errors.append("Could not determine the destination.")

        if errors:
            return {
                "plan_complete": False,
                "plan_data": None,
                "errors": state.get("errors", []) + errors,
            }

        plan = {
            "origin": origin,
            "destination": destination,
            "travel_modes": sorted(set(modes), key=ALL_MODES.index),
            "meal_types": meals,
            "time_budget_minutes": budget,
            "preferences": state.get("preferences") or {},
            "intent_summary": intent[:200],
        }
        logger.info("Travel plan parsed", origin=origin, destination=destination,
                    modes=plan["travel_modes"], budget=budget)
        return {
            "plan_complete": True,
            "plan_data": plan,
            "origin": origin,
            "destination": destination,
            "travel_modes": plan["travel_modes"],
            "meal_types": meals,
            "time_budget_minutes": budget,
            "current_step": "plan",
        }

    def _from_state(self, state: Dict[str, Any]):
        return (
            state.get("origin") or None,
            state.get("destination") or None,
            [m for m in (state.get("travel_modes") or []) if m in ALL_MODES],
            [m for m in (state.get("meal_types") or []) if m in ALL_MEALS],
            state.get("time_budget_minutes") or None,
        )

    async def _llm_extract(self, intent: str) -> Dict[str, Any]:
        prompt = f"""
Extract travel planning fields from this request. Return ONLY a JSON object.

Request: {intent}

JSON schema:
- origin: starting location name (string or null)
- destination: final destination name (string or null)
- travel_modes: array from ["car","bus","train","bike"] that the user mentioned or implied (may be empty)
- meal_types: array from ["tiffin","lunch","dinner"] for meals the user wants to plan (may be empty)
- time_budget_minutes: integer total minutes available for the trip, from phrases like "2 hours", "within 6 hours", "half day" (or null if absent)
- preferences: object of extra preferences (budget, cuisine, accessibility, avoid tolls)
"""
        try:
            result = await self._call_llm(prompt, system_message="Travel planning assistant. Return only JSON.")
            if result.get("error"):
                return {}
            from app.tools.validation import validation_tool
            parsed = await validation_tool.extract_json_from_text(result["content"])
            if not isinstance(parsed, dict) or "content" in parsed:
                return {}
            return {
                "origin": parsed.get("origin") or None,
                "destination": parsed.get("destination") or None,
                "travel_modes": parsed.get("travel_modes") or [],
                "meal_types": parsed.get("meal_types") or [],
                "time_budget_minutes": parsed.get("time_budget_minutes") or None,
                "preferences": parsed.get("preferences") or {},
            }
        except Exception as e:
            logger.info("LLM travel parse skipped", error=str(e))
            return {}