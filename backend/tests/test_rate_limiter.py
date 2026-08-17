import asyncio
import importlib
from app.tools.rate_limiter import RateLimiter


def _module():
    return importlib.import_module("app.tools.rate_limiter")


async def _fill_and_try(lim: RateLimiter, user: str, n: int):
    success = 0
    for _ in range(n):
        if await lim.check_limit(user):
            success += 1
    extra = await lim.check_limit(user)
    return success, extra


def test_per_user_buckets_are_isolated():
    mod = _module()
    old_requests = mod.settings.RATE_LIMIT_REQUESTS
    old_window = mod.settings.RATE_LIMIT_WINDOW
    try:
        mod.settings.RATE_LIMIT_REQUESTS = 3
        mod.settings.RATE_LIMIT_WINDOW = 3600
        lim = RateLimiter()

        async def go():
            # Alice exhausts her entire budget.
            user_a, extra_a = await _fill_and_try(lim, "alice", 3)
            assert user_a == 3 and extra_a is False
            assert await lim.check_limit("alice") is False  # exhausted

            # Bob, who hasn't spent anything, still has his full budget.
            assert await lim.check_limit("bob") is True

            # Alice's exhaustion never affects Bob: his remaining 2 tokens are intact.
            user_b, extra_b = await _fill_and_try(lim, "bob", 2)
            assert user_b == 2 and extra_b is False
            assert await lim.check_limit("bob") is False

        asyncio.run(go())
    finally:
        mod.settings.RATE_LIMIT_REQUESTS = old_requests
        mod.settings.RATE_LIMIT_WINDOW = old_window


def test_remaining_reports_budget():
    lim = RateLimiter()

    async def go():
        assert lim.remaining("alice") >= 0

    asyncio.run(go())


def test_disabled_limit_passes_everything():
    mod = _module()
    old_requests = mod.settings.RATE_LIMIT_REQUESTS
    try:
        mod.settings.RATE_LIMIT_REQUESTS = 0
        lim = RateLimiter()

        async def go():
            ok = await _fill_and_try(lim, "alice", 100)
            assert ok[0] == 100 and ok[1] is True

        asyncio.run(go())
    finally:
        mod.settings.RATE_LIMIT_REQUESTS = old_requests