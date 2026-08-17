from typing import Dict, Any, List, Optional
from app.tools.web_search import web_search_tool
from app.logging_config import logger

class SearchTool:
    description = "Search the web or internal knowledge base for information"

    async def execute(self, query: str, max_results: int = 5, source: str = "web") -> Dict[str, Any]:
        results = await web_search_tool.search(query, max_results)
        return {"results": results, "total": len(results), "source": source}


search_tool = SearchTool()
