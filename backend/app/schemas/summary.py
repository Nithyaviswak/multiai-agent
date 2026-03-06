from pydantic import BaseModel, Field
from typing import List

class SummaryResponse(BaseModel):
    """Schema for summary response"""
    topic: str = Field(description="Original research topic")
    summary: str = Field(description="Detailed summary with bullet points")
    key_points: List[str] = Field(description="List of key bullet points")
    word_count: int = Field(description="Word count of summary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "AI Trends 2024",
                "summary": "• Trend 1: AI becomes more accessible...\n• Trend 2: Multimodal AI dominates...",
                "key_points": [
                    "AI accessibility increases",
                    "Multimodal models lead innovation"
                ],
                "word_count": 250
            }
        }
