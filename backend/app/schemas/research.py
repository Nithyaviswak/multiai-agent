from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ResearchResult(BaseModel):
    """Schema for individual research result"""
    title: str = Field(description="Title of the article/result")
    url: str = Field(description="Source URL")
    content: str = Field(description="Main content/description")
    relevance_score: float = Field(description="Relevance score 0-1")
    published_date: Optional[str] = Field(description="Publication date if available")

class ResearchResponse(BaseModel):
    """Schema for complete research response"""
    topic: str = Field(description="Research topic")
    search_results: List[ResearchResult] = Field(description="List of search results")
    total_results: int = Field(description="Total number of results")
    search_metadata: Dict[str, Any] = Field(description="Search metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Artificial Intelligence 2024",
                "total_results": 5,
                "search_results": [
                    {
                        "title": "AI Trends 2024",
                        "url": "https://example.com",
                        "content": "AI trends for 2024 include...",
                        "relevance_score": 0.95,
                        "published_date": "2024-01-15"
                    }
                ],
                "search_metadata": {"engine": "tavily", "search_time": "2.1s"}
            }
        }
