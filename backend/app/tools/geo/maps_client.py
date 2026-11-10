from __future__ import annotations

import asyncio
import hashlib
import json
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import settings
from app.logging_config import logger

# ---------------------------------------------------------------------------
# Free geodata stack (no API keys):
#   - Geocoding : Nominatim (OpenStreetMap)   — 1 req/s, custom User-Agent
#   - Routing   : OSRM public server          — driving / cycling profiles
#   - POI       : Overpass (OpenStreetMap)    — tag/radius queries
#   - Fallback  : Photon (komoot)             — free-form text place search
# ---------------------------------------------------------------------------

# Per-mode routing strategy.
#   osrm           → real OSRM route for the given profile
#   osrm_estimate  → real OSRM road route, travel time scaled for slower transit
#   rail_estimate  → great-circle corridor estimate (no free transit routing)
MODE_PROFILES: Dict[str, Dict[str, Any]] = {
    "car":   {"kind": "osrm", "profile": "driving", "factor": 1.0},
    "bike":  {"kind": "osrm", "profile": "cycling", "factor": 1.0},
    "bus":   {"kind": "osrm_estimate", "profile": "driving", "factor": 1.45},
    "train": {"kind": "rail_estimate", "speed_kmh": 62.0, "detour_factor": 1.15},
}

# Overpass tag filters for common place queries (keyword → (key, value) pairs).
KEYWORD_TAGS: Dict[str, List[Tuple[str, str]]] = {
    "tourist attractions": [("tourism", "attraction")],
    "attraction": [("tourism", "attraction")],
    "monuments": [("historic", "monument"), ("historic", "memorial")],
    "monument": [("historic", "monument")],
    "parks and gardens": [("leisure", "park"), ("leisure", "garden")],
    "gardens": [("leisure", "garden")],
    "parks": [("leisure", "park")],
    "museums": [("tourism", "museum")],
    "museum": [("tourism", "museum")],
    "historic sights": [("historic", "yes"), ("tourism", "attraction")],
    "historic": [("historic", "yes")],
    "viewpoints": [("tourism", "viewpoint")],
    "viewpoint": [("tourism", "viewpoint")],
    "temples": [("historic", "temple"), ("amenity", "place_of_worship")],
    "beaches": [("natural", "beach")],
    "lakes": [("natural", "water"), ("leisure", "nature_reserve")],
    # Meal search keywords → restaurant amenities.
    "tiffin": [("amenity", "restaurant"), ("amenity", "cafe"),
               ("amenity", "fast_food"), ("amenity", "bar")],
    "breakfast": [("amenity", "restaurant"), ("amenity", "cafe"),
                  ("amenity", "fast_food"), ("amenity", "bar")],
    "lunch": [("amenity", "restaurant"), ("amenity", "cafe")],
    "thali": [("amenity", "restaurant"), ("amenity", "cafe")],
    "dinner": [("amenity", "restaurant"), ("amenity", "cafe")],
    "restaurant": [("amenity", "restaurant"), ("amenity", "cafe"),
                   ("amenity", "fast_food"), ("amenity", "bar")],
    "restaurants": [("amenity", "restaurant"), ("amenity", "cafe"),
                    ("amenity", "fast_food"), ("amenity", "bar")],
}

# OSM amenity tags used when searching restaurants by meal.
RESTAURANT_OSM_TAGS: List[Tuple[str, str]] = [
    ("amenity", "restaurant"),
    ("amenity", "cafe"),
    ("amenity", "fast_food"),
    ("amenity", "bar"),
]


class MapsClientError(RuntimeError):
    """Recoverable maps-provider failure (treated as agent error)."""


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Great-circle distance (km) between two lat/lng points."""
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(a)), 2)


def decode_polyline(polyline: str, precision: int = 5) -> List[List[float]]:
    """Decode an (OSRM/Google-style) encoded polyline into [lat, lng] pairs.

    OSRM's public server returns geometry either as GeoJSON coordinates (when
    it honours ``geometries=geojson``) or as an encoded polyline string (older
    backends ignore the param). Decoding both keeps the client robust.
    """
    factor = float(10 ** precision)
    coords: List[List[float]] = []
    index, lat, lng = 0, 0, 0
    n = len(polyline)
    while index < n:
        for is_lat in (True, False):
            result, shift = 0, 0
            while True:
                b = ord(polyline[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if is_lat:
                lat += delta
            else:
                lng += delta
        coords.append([lat / factor, lng / factor])
    return coords


class FreeMapsClient:
    """Async wrapper for the free OpenStreetMap data stack.

    Nominatim for geocoding, OSRM for car/bike/bus routes, Overpass for
    nearby places/restaurants and Photon as a free-text fallback. No API keys
    required. A per-process cache (24h TTL) keeps repeated queries cheap.
    """

    CACHE_TTL_SECONDS = 60 * 60 * 24
    MAX_RESULTS = 8
    NOMINATIM_MIN_INTERVAL = 1.05  # seconds between Nominatim calls (usage policy)

    def __init__(self, timeout: float = 20.0):
        self.nominatim_url = settings.NOMINATIM_URL.rstrip("/")
        self.osrm_url = settings.OSRM_URL.rstrip("/")
        self.overpass_url = settings.OVERPASS_URL.rstrip("/")
        self.photon_url = settings.PHOTON_URL.rstrip("/")
        self.timeout = timeout
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._sem = asyncio.Semaphore(4)
        self._nominatim_lock = asyncio.Lock()
        self._nominatim_last: float = 0.0
        self._user_agent = (
            "multiai-agent/1.0 (multi-agent travel planner demo; "
            "http://openfreemap.org for map tiles)"
        )

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

    # ── Core request helpers ──────────────────────────────────────
    async def _get_json(self, url: str, params: Optional[Dict[str, Any]] = None,
                        headers: Optional[Dict[str, str]] = None,
                        pool: str = "default") -> Dict[str, Any]:
        cache_key = self._cache_key(f"{pool}:{url}", params or {})
        hit = self._cache_get(cache_key)
        if hit is not None:
            return hit

        async with self._sem:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params or {}, headers=headers or {})

        if resp.status_code != 200:
            raise MapsClientError(f"Maps HTTP {resp.status_code} for {url}")
        data = resp.json()
        self._cache_set(cache_key, data)
        return data

    async def _nominatim(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Nominatim call, throttled to its usage policy (1 req/s)."""
        async with self._nominatim_lock:
            now = time.monotonic()
            wait = self.NOMINATIM_MIN_INTERVAL - (now - self._nominatim_last)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                return await self._get_json(
                    f"{self.nominatim_url}/search",
                    {**params, "format": "jsonv2", "limit": 1, "accept-language": "en"},
                    headers={"User-Agent": self._user_agent},
                    pool="nominatim",
                )
            finally:
                self._nominatim_last = time.monotonic()

    # ── Geocoding (Nominatim) ─────────────────────────────────────
    async def geocode(self, address: str) -> Dict[str, Any]:
        if not address or not address.strip():
            return {"error": "Empty address", "status": "ZERO_RESULTS"}
        try:
            data = await self._nominatim({"q": address})
        except MapsClientError as e:
            return {"error": str(e), "status": "ERROR"}

        if not isinstance(data, list) or not data:
            return {
                "error": f"Geocode ZERO_RESULTS for {address!r}",
                "status": "ZERO_RESULTS",
            }
        first = data[0]
        return {
            "status": "OK",
            "lat": float(first.get("lat")),
            "lng": float(first.get("lon")),
            "formatted_address": first.get("display_name") or address,
            "osm_id": first.get("osm_id"),
            "osm_type": first.get("osm_type"),
            "place_class": first.get("class"),
            "place_type": first.get("type"),
        }

    # ── Directions (OSRM + rail/bus estimates) ────────────────────
    async def directions(self, origin: str, destination: str,
                         mode: str, depart_at: Optional[str] = None) -> Dict[str, Any]:
        """Return a normalized route for the named mode (car/bus/train/bike).

        Never raises for provider-level failures: those are returned as dicts
        carrying an ``error`` key so agents can handle them truthfully.
        Departure time is ignored (routing is static; no live transit feeds).
        """
        mode = (mode or "car").lower()
        profile = MODE_PROFILES.get(mode, MODE_PROFILES["car"])

        start = await self.geocode(origin)
        end = await self.geocode(destination)
        if start.get("status") != "OK" or end.get("status") != "OK":
            return {
                "error": f"Geocoding failed: {start.get('error') or end.get('error') or 'no result'}",
                "status": "ZERO_RESULTS",
                "mode": mode,
            }

        try:
            if profile["kind"] == "rail_estimate":
                route = self._rail_estimate(mode, start, end, profile)
            else:
                route = await self._osrm_route(mode, start, end, profile)
        except MapsClientError as e:
            return {"error": str(e), "status": "ERROR", "mode": mode}
        except Exception as e:  # network etc.
            logger.error("Route provider failed", mode=mode, error=str(e))
            return {"error": f"{mode} route unavailable: {e}", "status": "ERROR", "mode": mode}

        return route

    async def _osrm_route(self, mode: str, start: Dict[str, Any],
                          end: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        coords = f"{start['lng']},{start['lat']};{end['lng']},{end['lat']}"
        url = (f"{self.osrm_url}/route/v1/{profile['profile']}/{coords}"
               f"?overview=full&geometries=geojson&continue_straight=false")
        data = await self._get_json(url, pool="osrm")

        if data.get("code") != "Ok" or not data.get("routes"):
            return {
                "error": f"OSRM {data.get('code', 'ERROR')}",
                "status": "ZERO_RESULTS",
                "mode": mode,
            }
        route = data["routes"][0]
        distance_m = int(route.get("distance", 0))
        duration_sec = float(route.get("duration", 0))
        factor = float(profile.get("factor", 1.0))
        estimate = factor != 1.0

        # Geometry arrives as GeoJSON coordinates (dict) on modern OSRM
        # backends, or as an encoded polyline (str) on older ones. Handle both.
        geometry = route.get("geometry")
        if isinstance(geometry, dict):
            coords = (geometry.get("coordinates") or [])
        elif isinstance(geometry, str) and geometry:
            coords = [list(p) for p in decode_polyline(geometry)]
        else:
            coords = []
        via_points = [[p[1], p[0]] for p in coords]  # [lng, lat] → [lat, lng]
        via_points = via_points[:250]
        if estimate and via_points:
            # Keep the road shape but rescale the travel time for bus travel.
            duration_sec *= factor
            summary = f"{self._route_summary(route) or 'road route'}, bus time estimated"
        else:
            summary = self._route_summary(route)

        return self._normalize_route(
            mode=mode, status="OK", start=start, end=end,
            distance_m=distance_m, duration_sec=int(duration_sec),
            via_points=via_points, summary=summary, estimate=estimate,
        )

    @staticmethod
    def _route_summary(route: Dict[str, Any]) -> str:
        """Best-effort road summary from an OSRM route (handles odd shapes)."""
        legs = route.get("legs")
        if isinstance(legs, list) and legs and isinstance(legs[0], dict):
            summary = legs[0].get("summary")
            if isinstance(summary, str) and summary:
                return summary
        summary = route.get("summary")
        return summary if isinstance(summary, str) else ""

    def _rail_estimate(self, mode: str, start: Dict[str, Any],
                       end: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic rail-corridor estimate (no free transit data)."""
        crow_km = haversine_km(start["lat"], start["lng"], end["lat"], end["lng"])
        distance_km = round(crow_km * float(profile["detour_factor"]), 2)
        distance_m = int(distance_km * 1000)
        speed_kmh = float(profile["speed_kmh"])
        duration_sec = int((distance_km / speed_kmh) * 3600)

        # Interpolate a simple great-circle corridor so the map can draw a line.
        n = 7
        via_points = [
            [
                round(start["lat"] + (end["lat"] - start["lat"]) * t / (n - 1), 6),
                round(start["lng"] + (end["lng"] - start["lng"]) * t / (n - 1), 6),
            ]
            for t in range(n)
        ]
        return self._normalize_route(
            mode=mode, status="OK", start=start, end=end,
            distance_m=distance_m, duration_sec=duration_sec,
            via_points=via_points,
            summary="estimated rail corridor", estimate=True,
        )

    def _normalize_route(self, *, mode: str, status: str, start: Dict[str, Any],
                         end: Dict[str, Any], distance_m: int, duration_sec: int,
                         via_points: List[List[float]], summary: str,
                         estimate: bool = False) -> Dict[str, Any]:
        return {
            "mode": mode,
            "status": status,
            "from": start.get("formatted_address", ""),
            "to": end.get("formatted_address", ""),
            "distance_m": distance_m,
            "distance_km": round(distance_m / 1000.0, 2),
            "duration_sec": duration_sec,
            "duration_min": round(duration_sec / 60.0),
            "duration_text": summary or "route",
            "summary": summary,
            "via_points": via_points,
            "estimate": estimate,
        }

    def anchor_point(self, route_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Pick a representative point along the route (middle of via_points)."""
        points = route_data.get("via_points") or []
        if not points:
            return None
        return {"lat": points[len(points) // 2][0], "lng": points[len(points) // 2][1]}

    # ── Places (Overpass + Photon fallback) ───────────────────────
    async def place_search(self, *, query: str = "", location: Optional[Dict[str, float]] = None,
                           radius: Optional[int] = None, open_now: bool = False,
                           nearby_keyword: str = "point of interest",
                           max_results: int = MAX_RESULTS,
                           osm_tags: Optional[List[Tuple[str, str]]] = None) -> List[Dict[str, Any]]:
        """Nearby places / restaurant search returning normalized place dicts.

        ``osm_tags`` (list of (key, value)) gives exact OpenStreetMap tag
        filters — the reliable path. Otherwise the query string is mapped to
        common OSM tags; unknown queries fall back to Photon full-text search.
        ``radius`` is honoured for Overpass (meters). ``open_now`` is accepted
        for API compatibility but ignored (no live opening-hours source).
        """
        if max_results <= 0:
            return []

        tags: List[Tuple[str, str]] = []
        if osm_tags:
            tags = list(osm_tags)
        else:
            tags = self._tags_for_query(query or nearby_keyword)

        if tags and location:
            return await self._overpass_search(
                tags=tags, lat=location["lat"], lng=location["lng"],
                radius=radius or settings.PLACES_RADIUS_METERS,
                max_results=max_results,
            )
        if not location:
            return []
        return await self._photon_search(
            query=query or nearby_keyword, lat=location["lat"], lng=location["lng"],
            max_results=max_results,
        )

    @staticmethod
    def _tags_for_query(query: str) -> List[Tuple[str, str]]:
        lowered = (query or "").lower()
        for keyword, tags in KEYWORD_TAGS.items():
            if lowered and keyword in lowered:
                return list(tags)
        return []

    async def _overpass_search(self, *, tags: List[Tuple[str, str]], lat: float,
                               lng: float, radius: int, max_results: int) -> List[Dict[str, Any]]:
        selector = "".join(
            f'["{k}"="{v}"]' for k, v in tags
        )
        # One query for all tag variants: nodes and ways (with center points).
        parts: List[str] = []
        for k, v in tags:
            parts.append(f'node["{k}"="{v}"](around:{radius},{lat},{lng});')
            parts.append(f'way["{k}"="{v}"](around:{radius},{lat},{lng});')
        query = (
            "[out:json][timeout:25];(\n"
            + "\n".join(parts)
            + "\n);\nout center " + str(min(max_results * 2, 60)) + ";"
        )
        try:
            data = await self._get_json(
                f"{self.overpass_url}",
                {"data": query},
                headers={"User-Agent": self._user_agent},
                pool="overpass",
            )
        except MapsClientError as e:
            return [{"error": str(e)}]

        results: List[Dict[str, Any]] = []
        for el in data.get("elements", []):
            tags_dict = el.get("tags") or {}
            name = tags_dict.get("name")
            if not name:
                continue  # unnamed POIs are useless for an itinerary
            node_lat = el.get("lat")
            node_lng = el.get("lon")
            center = el.get("center") or {}
            lat_v = node_lat if node_lat is not None else center.get("lat")
            lng_v = node_lng if node_lng is not None else center.get("lon")
            if lat_v is None or lng_v is None:
                continue

            types: List[str] = []
            for k, v in tags:
                if tags_dict.get(k) == v:
                    types.append(v)
            rating = None
            try:
                stars = tags_dict.get("stars")
                if stars:
                    rating = float(stars)
            except (TypeError, ValueError):
                rating = None

            results.append({
                "place_id": f"osm:{el.get('type', 'node')}:{el.get('id')}",
                "name": name,
                "vicinity": " ".join(
                    x for x in (tags_dict.get("addr:city"),
                                tags_dict.get("addr:street"),
                                tags_dict.get("cuisine", "")) if x
                ) or (tags_dict.get("amenity") or tags_dict.get("tourism") or ""),
                "rating": rating,
                "user_ratings_total": 0,
                "price_level": None,
                "types": types,
                "lat": round(float(lat_v), 6),
                "lng": round(float(lng_v), 6),
                "source": "overpass",
            })
            if len(results) >= max_results:
                break
        return results

    async def _photon_search(self, *, query: str, lat: float, lng: float,
                             max_results: int) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "q": query, "limit": max_results, "lang": "en",
            "lat": lat, "lon": lng,
        }
        try:
            data = await self._get_json(f"{self.photon_url}/api", params, pool="photon")
        except MapsClientError as e:
            return [{"error": str(e)}]

        results: List[Dict[str, Any]] = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            name = props.get("name")
            if not name:
                continue
            coords = (feature.get("geometry") or {}).get("coordinates") or []
            if len(coords) < 2:
                continue
            osm_id = props.get("osm_id")
            osm_type = props.get("osm_type")
            if osm_id and osm_type:
                place_id = f"photon:{osm_type}:{osm_id}"
            else:
                place_id = "photon:" + hashlib.md5(
                    f"{name}:{coords}".encode("utf-8")).hexdigest()[:12]

            place_type = props.get("type") or ""
            place_class = props.get("class") or ""
            city = props.get("city") or props.get("state") or props.get("country") or ""
            results.append({
                "place_id": place_id,
                "name": name,
                "vicinity": city or place_type or place_class,
                "rating": None,
                "user_ratings_total": 0,
                "price_level": None,
                "types": [t for t in (place_class, place_type) if t],
                "lat": round(float(coords[1]), 6),
                "lng": round(float(coords[0]), 6),
                "source": "photon",
            })
        return results

    # ── Availability ──────────────────────────────────────────────
    def has_credentials(self) -> bool:
        """Free public services — always available, no credentials needed."""
        return True

    def provider(self) -> Dict[str, str]:
        return {
            "name": "OpenFreeMap / OpenStreetMap",
            "geocoding": self.nominatim_url,
            "routing": self.osrm_url,
            "places": self.overpass_url,
            "fallback_search": self.photon_url,
            "tiles": "https://tiles.openfreemap.org/styles",
        }


maps_client = FreeMapsClient()