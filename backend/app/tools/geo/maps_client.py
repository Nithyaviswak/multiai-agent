from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import settings
from app.logging_config import logger

# Maps API travel_mode / transit_mode mapping per our named transport modes.
MODE_PARAMS: Dict[str, Dict[str, str]] = {
    "car": {"travel_mode": "driving"},
    "bus": {"travel_mode": "transit", "transit_mode": "bus"},
    "train": {"travel_mode": "transit", "transit_mode": "rail"},
    "bike": {"travel_mode": "bicycling"},
}


class GoogleMapsClientError(RuntimeError):
    """Recoverable Google Maps API failure (treated as agent error)."""


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Great-circle distance (km) between two lat/lng points."""
    import math
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(a)), 2)


class GoogleMapsClient:
    """Minimal async wrapper around Google Maps Directions / Geocoding / Places.

    Real HTTP calls with live data. A per-process cache (24h TTL) keyed on the
    full request keeps repeated queries from burning quota. Failing/erroring
    responses are never cached so transient failures get retried.
    """

    BASE = "https://maps.googleapis.com/maps/api"
    CACHE_TTL_SECONDS = 60 * 60 * 24
    MAX_RESULTS = 8

    def __init__(self, api_key: Optional[str] = None, timeout: float = 15.0):
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        self.timeout = timeout
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._sem = asyncio.Semaphore(6)

    # ── Caching helpers ──────────────────────────────────────────
    def _cache_key(self, kind: str, params: Dict[str, Any]) -> str:
        blob = json.dumps(params, sort_keys=True, default=str)
        return f"{kind}:{hashlib.md5(blob.encode('utf-8')).hexdigest()}"

    def _cache_get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry and entry[0] > time.time():
            return entry[1]
        self._cache.pop(key, None)
        return None

    def _cache_set(self, key: str, value: Any) -> None:
        self._cache[key] = (time.time() + self.CACHE_TTL_SECONDS, value)
        if len(self._cache) > 2048:
            for k in list(self._cache)[:512]:
                self._cache.pop(k, None)

    # ── Core request helper ──────────────────────────────────────
    async def _get_json(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        cache_key = self._cache_key(path, params)
        hit = self._cache_get(cache_key)
        if hit is not None:
            return hit

        params = {**params, "key": self.api_key}
        url = f"{self.BASE}/{path}/json"
        async with self._sem:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)

        if resp.status_code != 200:
            raise GoogleMapsClientError(
                f"Maps API HTTP {resp.status_code} for {path}"
            )
        data = resp.json()
        status = data.get("status", "UNKNOWN")
        if status == "OK" or status == "ZERO_RESULTS":
            self._cache_set(cache_key, data)
        return data

    # ── Directions ───────────────────────────────────────────────
    async def directions(self, origin: str, destination: str,
                         mode: str, depart_at: Optional[str] = None) -> Dict[str, Any]:
        """Return a normalized route for the named mode (car/bus/train/bike).

        Never raises for ZERO_RESULTS / REQUEST_DENIED: those are returned as
        dicts carrying an ``error`` key so agents can handle them truthfully.
        """
        mode = (mode or "car").lower()
        params: Dict[str, Any] = {"origin": origin, "destination": destination}
        params.update(MODE_PARAMS.get(mode, MODE_PARAMS["car"]))
        if depart_at:
            params["departure_time"] = depart_at

        try:
            data = await self._get_json("directions", params)
        except GoogleMapsClientError as e:
            return {"error": str(e), "status": "ERROR", "mode": mode}

        if data.get("status") != "OK":
            return {
                "error": f"Directions {data.get('status')}: {data.get('error_message', '')}",
                "status": data.get("status", "ERROR"),
                "mode": mode,
            }
        return self._normalize_route(data, mode)

    def _normalize_route(self, data: Dict[str, Any], mode: str) -> Dict[str, Any]:
        route = data["routes"][0]
        legs = route.get("legs", [])
        distance_m = sum(int(l.get("distance", {}).get("value", 0)) for l in legs)
        duration_sec = sum(int(l.get("duration", {}).get("value", 0)) for l in legs)
        via_points: List[List[float]] = []
        for leg in legs:
            for step in leg.get("steps", []):
                loc = step.get("start_location")
                if loc:
                    via_points.append([loc["lat"], loc["lng"]])
            loc = leg.get("end_location")
            if loc:
                via_points.append([loc["lat"], loc["lng"]])
        return {
            "mode": mode,
            "status": "OK",
            "from": legs[0].get("start_address", "") if legs else "",
            "to": legs[-1].get("end_address", "") if legs else "",
            "distance_m": distance_m,
            "distance_km": round(distance_m / 1000.0, 2),
            "duration_sec": duration_sec,
            "duration_min": round(duration_sec / 60.0),
            "duration_text": route.get("summary", "") or "route",
            "summary": route.get("summary", ""),
            "via_points": via_points[:200],
        }

    def anchor_point(self, route_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Pick a representative point along the route (middle of via_points)."""
        points = route_data.get("via_points") or []
        if not points:
            return None
        return {"lat": points[len(points) // 2][0], "lng": points[len(points) // 2][1]}

    # ── Geocoding ────────────────────────────────────────────────
    async def geocode(self, address: str) -> Dict[str, Any]:
        try:
            data = await self._get_json("geocode", {"address": address})
        except GoogleMapsClientError as e:
            return {"error": str(e), "status": "ERROR"}
        results = data.get("results", [])
        if data.get("status") != "OK" or not results:
            return {"error": f"Geocode {data.get('status')}", "status": data.get("status", "ERROR")}
        loc = results[0]["geometry"]["location"]
        return {
            "status": "OK",
            "lat": loc["lat"],
            "lng": loc["lng"],
            "formatted_address": results[0].get("formatted_address", address),
        }

    # ── Places ───────────────────────────────────────────────────
    async def place_search(self, *, query: str = "", location: Optional[Dict[str, float]] = None,
                           radius: Optional[int] = None, open_now: bool = False,
                           nearby_keyword: str = "point of interest",
                           max_results: int = MAX_RESULTS) -> List[Dict[str, Any]]:
        """Text or nearby place search; returns normalized place dicts."""
        params: Dict[str, Any] = {}
        if query:
            params["query"] = query
        else:
            params["keyword"] = nearby_keyword
        if location:
            params["location"] = f"{location['lat']},{location['lng']}"
        if radius:
            params["radius"] = radius
        if open_now:
            params["opennow"] = "true"
        if not query and location is None:
            return []

        try:
            path = "place/textsearch" if query else "place/nearbysearch"
            data = await self._get_json(path, params)
        except GoogleMapsClientError as e:
            return [{"error": str(e)}]
        if data.get("status") != "OK":
            return []

        out = []
        for p in data.get("results", [])[:max_results]:
            loc = (p.get("geometry") or {}).get("location") or {}
            out.append({
                "place_id": p.get("place_id"),
                "name": p.get("name", ""),
                "vicinity": p.get("formatted_address") or p.get("vicinity", ""),
                "rating": p.get("rating"),
                "user_ratings_total": p.get("user_ratings_total", 0),
                "price_level": p.get("price_level"),
                "types": p.get("types", []),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
            })
        return out

    async def place_details(self, place_id: str) -> Dict[str, Any]:
        try:
            data = await self._get_json(
                "place/details",
                {"place_id": place_id,
                 "fields": "opening_hours,website,formatted_address,rating"},
            )
        except GoogleMapsClientError as e:
            return {"error": str(e)}
        if data.get("status") != "OK" or not data.get("result"):
            return {}
        detail = data["result"]
        return {
            "place_id": place_id,
            "opening_hours": (detail.get("opening_hours") or {}).get("weekday_text", []),
            "website": detail.get("website"),
            "address": detail.get("formatted_address", ""),
            "rating": detail.get("rating"),
            "open_now": (detail.get("opening_hours") or {}).get("open_now"),
        }

    def has_credentials(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))


maps_client = GoogleMapsClient()