import pytest

from app.agents.travel_planner_agent import (
    TravelPlannerAgent, extract_travel_modes, extract_meal_types,
    extract_time_budget, extract_origin_destination, ALL_MODES, ALL_MEALS,
)


class TestTravelExtraction:
    def test_extract_modes(self):
        assert extract_travel_modes("travel by train from A to B") == ["train"]
        assert extract_travel_modes("drive by car to Goa") == ["car"]
        assert extract_travel_modes("take a bus") == ["bus"]
        assert extract_travel_modes("cycle to the beach") == ["bike"]
        assert extract_travel_modes("no mode mentioned") == []

    def test_extract_meals(self):
        assert extract_meal_types("I want lunch on the way") == ["lunch"]
        assert extract_meal_types("plan breakfast and dinner stops") == ["tiffin", "dinner"]
        assert extract_meal_types("no meals mentioned") == []

    def test_extract_time_budget(self):
        assert extract_time_budget("within 6 hours") == 360
        assert extract_time_budget("under 2 hours") == 120
        assert extract_time_budget("about 90 minutes") == 90
        assert extract_time_budget("half day trip") == 240
        assert extract_time_budget("no time mentioned") is None

    def test_extract_origin_destination(self):
        o, d = extract_origin_destination("from Bengaluru to Mysuru by train")
        assert o == "Bengaluru" and d == "Mysuru"
        o, d = extract_origin_destination("Start from Chennai and I need to reach Pondicherry")
        assert o == "Chennai" and d == "Pondicherry"


class TestTravelPlannerAgent:
    def _agent(self):
        agent = TravelPlannerAgent()

        async def no_llm(intent):
            return {}
        agent._llm_extract = no_llm
        return agent

    @pytest.mark.asyncio
    async def test_full_structured_state_no_llm(self):
        agent = self._agent()
        state = {
            "intent": "Travel from Bengaluru to Mysuru",
            "origin": "Bengaluru",
            "destination": "Mysuru",
            "travel_modes": ["train"],
            "meal_types": ["lunch"],
            "time_budget_minutes": 360,
            "preferences": {"budget": "medium"},
            "errors": [],
        }
        result = await agent.process(state)
        assert result["plan_complete"] is True
        plan = result["plan_data"]
        assert plan["origin"] == "Bengaluru"
        assert plan["destination"] == "Mysuru"
        assert plan["travel_modes"] == ["train"]
        assert plan["meal_types"] == ["lunch"]
        assert plan["time_budget_minutes"] == 360
        assert result["origin"] == "Bengaluru"
        assert result["current_step"] == "plan"

    @pytest.mark.asyncio
    async def test_extracts_from_intent_when_structured_missing(self):
        agent = self._agent()
        state = {
            "intent": "From Bengaluru to Mysuru by train, want lunch, 6 hours in total",
            "origin": None, "destination": None,
            "travel_modes": [], "meal_types": [],
            "time_budget_minutes": None,
            "errors": [],
        }
        result = await agent.process(state)
        assert result["plan_complete"] is True
        plan = result["plan_data"]
        assert plan["origin"] == "Bengaluru"
        assert plan["destination"] == "Mysuru"
        assert plan["travel_modes"] == ["train"]
        assert plan["meal_types"] == ["lunch"]
        assert plan["time_budget_minutes"] == 360

    @pytest.mark.asyncio
    async def test_falls_back_to_all_modes_and_meals(self):
        agent = self._agent()
        state = {
            "intent": "From Bengaluru to Mysuru",
            "origin": None, "destination": None,
            "travel_modes": [], "meal_types": [],
            "time_budget_minutes": None,
            "errors": [],
        }
        result = await agent.process(state)
        assert result["plan_complete"] is True
        plan = result["plan_data"]
        assert plan["travel_modes"] == ALL_MODES
        assert plan["meal_types"] == ALL_MEALS
        assert plan["time_budget_minutes"] == 360

    @pytest.mark.asyncio
    async def test_missing_destination_is_hard_error(self):
        agent = self._agent()
        state = {
            "intent": "Just explore a bit",
            "origin": "Bengaluru", "destination": None,
            "travel_modes": [], "meal_types": [],
            "time_budget_minutes": None,
            "errors": [],
        }
        result = await agent.process(state)
        assert result["plan_complete"] is False
        assert any("destination" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_invalid_modes_meals_dropped(self):
        agent = self._agent()
        state = {
            "intent": "From Bengaluru to Mysuru",
            "origin": "Bengaluru", "destination": "Mysuru",
            "travel_modes": ["car", "helicopter"], "meal_types": ["lunch", "snack"],
            "time_budget_minutes": 120,
            "errors": [],
        }
        result = await agent.process(state)
        assert result["plan_complete"] is True
        assert result["travel_modes"] == ["car"]
        assert result["meal_types"] == ["lunch"]