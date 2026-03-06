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
        self.throttler = Throttler(rate_limit=10, period=60)  # 10 requests per minute
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform web search with rate limiting and error handling
        """
        async with self.throttler:
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "api_key": settings.TAVILY_API_KEY,
                        "query": query,
                        "max_results": max_results,
                        "include_answer": False
                    }
                    
                    async with session.post(self.base_url, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            return self._process_results(data)
                        else:
                            error_text = await response.text()
                            logger.error("Search API error", status=response.status, error=error_text)
                            return []
                            
            except Exception as e:
                logger.error("Search tool error", error=str(e))
                return []
    
    def _process_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and enrich search results"""
        processed = []
        
        for result in data.get("results", []):
            processed.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "relevance_score": 0.8,  # Could be calculated based on query matching
                "published_date": result.get("published_date", ""),
                "source": "tavily"
            })
        
        return processed

# Singleton instance
web_search_tool = WebSearchTool()
