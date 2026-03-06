from typing import Dict, Any
from app.agents.base import BaseAgent
from app.tools.web_search import web_search_tool
from app.tools.validation import validation_tool
from app.schemas.research import ResearchResponse
from app.logging_config import logger

class ResearchAgent(BaseAgent):
    """Research Agent that performs web search and structures results"""
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state.get("topic", "")
        logger.info("Research agent started", topic=topic)
        
        try:
            # Perform web search
            search_results = await web_search_tool.search(topic, max_results=5)
            
            if not search_results:
                raise ValueError("No search results found")
            
            # Generate structured response
            research_data = {
                "topic": topic,
                "search_results": search_results,
                "total_results": len(search_results),
                "search_metadata": {"engine": "tavily", "search_time": "completed"}
            }
            
            # Validate output
            is_valid, validated_data, error_msg = await validation_tool.validate_output(
                research_data, ResearchResponse
            )
            
            if not is_valid:
                raise ValueError(f"Research validation failed: {error_msg}")
            
            return {
                "research_complete": True,
                "research_data": validated_data.dict(),
                "research_validation_errors": [],
                "current_step": "summary"
            }
            
        except Exception as e:
            logger.error("Research agent failed", error=str(e))
            return {
                "research_complete": False,
                "research_data": None,
                "research_validation_errors": [str(e)],
                "errors": state.get("errors", []) + [f"Research failed: {str(e)}"]
            }
