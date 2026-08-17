import asyncio
import time
from collections import defaultdict
from typing import Dict
from app.config import settings
from app.logging_config import logger


class RateLimiter:
    """Async token-bucket rate limiter, scoped per user.

    Each user gets ``RATE_LIMIT_REQUESTS`` requests per ``RATE_LIMIT_WINDOW``
    seconds. ``check_limit`` is a no-op when the limit is disabled (<=0).
    Buckets are evicted when inactive to keep memory bounded.
    """

    def __init__(self):
        self._buckets: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"tokens": float(settings.RATE_LIMIT_REQUESTS),
                     "last_refill": time.monotonic()}
        )
        self._lock = asyncio.Lock()
        self.max_users = 10_000  # eviction bound

    def _refill(self, key: str):
        bucket = self._buckets[key]
        now = time.monotonic()
        elapsed = now - bucket["last_refill"]
        rate = settings.RATE_LIMIT_REQUESTS / max(settings.RATE_LIMIT_WINDOW, 1)
        bucket["tokens"] = min(settings.RATE_LIMIT_REQUESTS,
                               bucket["tokens"] + elapsed * rate)
        bucket["last_refill"] = now

    async def check_limit(self, user_id: str = "anonymous") -> bool:
        if settings.RATE_LIMIT_REQUESTS <= 0:
            return True
        async with self._lock:
            key = user_id or "anonymous"
            self._refill(key)
            bucket = self._buckets[key]
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True
            # Evict inactive buckets to bound memory.
            if len(self._buckets) > self.max_users:
                now = time.monotonic()
                for k, b in list(self._buckets.items()):
                    if now - b["last_refill"] > 3600:
                        del self._buckets[k]
            logger.warning("Rate limit exceeded", user=key)
            return False

    def remaining(self, user_id: str = "anonymous") -> int:
        key = user_id or "anonymous"
        if settings.RATE_LIMIT_REQUESTS <= 0:
            return -1
        self._refill(key)
        return int(self._buckets[key]["tokens"])


rate_limiter = RateLimiter()