from pydantic import BaseModel, Field
from typing import List, Dict

class FactCheckItem(BaseModel):
    """Schema for individual fact check"""
    claim: str = Field(description="The claim being verified")
    is_supported: bool = Field(description="Whether evidence supports the claim")
    confidence: float = Field(description="Confidence score 0-1")
    evidence: List[str] = Field(description="Supporting evidence")
    explanation: str = Field(description="Explanation of verification")

class FactCheckResponse(BaseModel):
    """Schema for complete fact check response"""
    topic: str = Field(description="Topic being fact-checked")
    overall_confidence: float = Field(description="Overall confidence score 0-1")
    checked_claims: List[FactCheckItem] = Field(description="List of checked claims")
    recommendations: List[str] = Field(description="Recommendations for improvement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "AI Trends 2024",
                "overall_confidence": 0.85,
                "checked_claims": [
                    {
                        "claim": "AI will transform healthcare in 2024",
                        "is_supported": True,
                        "confidence": 0.9,
                        "evidence": ["Source1", "Source2"],
                        "explanation": "Multiple sources confirm this trend"
                    }
                ],
                "recommendations": ["Add more recent sources", "Include counter-arguments"]
            }
        }
