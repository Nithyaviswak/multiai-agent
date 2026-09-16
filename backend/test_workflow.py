"""Smoke test for the compiled TravelWorkflow graph.

No live API calls in CI: the maps client is monkeypatched, so the graph runs
end-to-end with deterministic data. Requires a GOOGLE_MAPS_API_KEY only for the
optional `--live` mode (see conftest).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.graph.workflow import TravelWorkflow
from app.tools.geo import maps_client


def _fake_route(mode):
    return {
        "mode": mode,
        "status": "OK",
        "from": "Bengaluru",
        "to": "Mysuru",
        "distance_m": 120000,
        "distance_km": 120.0,
        "duration_sec": 6000,
        "duration_min": 100,
        "summary": f"{mode} route",
        "via_points": [[12.9, 77.6], [12.6, 77.4], [12.3, 77.2]],
    }


def _fake_place(name, place_id):
    return {
        "place_id": place_id,
        "name": name,
        "vicinity": "Near route",
        "rating": 4.5,
        "user_ratings_total": 100,
        "types": ["tourist_attraction"],
        "lat": 12.6,
        "lng": 77.4,
    }


def install_fakes():
    async def fake_directions(origin, destination, mode, depart_at=None):
        return _fake_route(mode)

    async def fake_place_search(**kwargs):
        return [_fake_place("Fort View", "p-fort"), _fake_place("Lake Park", "p-lake")]

    async def fake_search_tool(query, max_results=2):
        return {"results": [{"title": "Travel guide", "link": "https://example.com", "snippet": "tips"}]}

    maps_client.directions = fake_directions
    maps_client.place_search = fake_place_search
    maps_client.anchor_point = lambda route: {"lat": 12.6, "lng": 77.4}
    # Avoid live Tavily call in the knowledge agent.
    import app.tools.calling.search_tool as st
    st.search_tool.execute = fake_search_tool


async def main():
    install_fakes()
    wf = TravelWorkflow()
    result = await wf.run(
        "Plan a trip from Bengaluru to Mysuru by car with lunch and cover some places within 6 hours",
        origin="Bengaluru", destination="Mysuru",
        travel_modes=["car"], meal_types=["lunch"], time_budget_minutes=360,
    )
    print("current_step:", result.get("current_step"))
    print("terminal_status:", result.get("terminal_status"))
    assert result.get("current_step") == "complete", result.get("errors")
    assert result.get("summary_complete") is True
    assert result.get("itinerary_data", {}).get("stops")
    print("path_completed:", [t["step"] for t in result.get("trace", [])])
    print("SMOKE_OK")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())