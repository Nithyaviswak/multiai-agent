import aiohttp
import asyncio
from typing import List, Dict, Any
from app.config import settings
from app.logging_config import logger
from asyncio_throttle import Throttler

class WebSearchTool:
    """Web search tool using Tavily API with rate limiting"""

    def __init__(self):
        self.base_url = "https://api.tavily.com/search"
        self.throttler = Throttler(rate_limit=10, period=60)

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not settings.TAVILY_API_KEY:
            return self._mock_search(query, max_results)
        async with self.throttler:
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "api_key": settings.TAVILY_API_KEY,
                        "query": query,
                        "max_results": max_results,
                    }
                    async with session.post(self.base_url, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            return self._process_results(data)
                        return []
            except Exception as e:
                logger.error("Search tool error", error=str(e))
                return []

    def _mock_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        return [{
            "title": f"Mock result for: {query[:30]}",
            "url": "https://example.com/mock",
            "content": f"Simulated search result for '{query}'. This is a mock response when no API key is configured.",
            "relevance_score": 0.9,
            "source": "mock",
        }]

    def _process_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        processed = []
        for result in data.get("results", []):
            processed.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "relevance_score": result.get("relevance_score", 0.8),
                "source": "tavily",
            })
        return processed


web_search_tool = WebSearchTool()
