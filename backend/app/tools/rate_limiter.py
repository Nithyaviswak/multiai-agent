from ratelimit import limits, sleep_and_retry
from app.config import settings
from app.logging_config import logger

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self):
        self.call_count = 0
    
    @sleep_and_retry
    @limits(calls=settings.RATE_LIMIT_REQUESTS, period=settings.RATE_LIMIT_WINDOW)
    async def check_limit(self):
        """Check and enforce rate limit"""
        self.call_count += 1
        logger.info("Rate limit check", call_count=self.call_count)
        return True

rate_limiter = RateLimiter()
