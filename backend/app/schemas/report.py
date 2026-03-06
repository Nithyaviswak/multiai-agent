from pydantic import BaseModel, Field

class ReportResponse(BaseModel):
    """Schema for professional report"""
    topic: str = Field(description="Report topic")
    report_content: str = Field(description="Full markdown report")
    title: str = Field(description="Report title")
    introduction: str = Field(description="Report introduction")
    sections: dict = Field(description="Report sections")
    conclusion: str = Field(description="Report conclusion")
    word_count: int = Field(description="Total word count")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "AI Trends 2024",
                "title": "Comprehensive Analysis of AI Trends in 2024",
                "introduction": "This report examines the key AI trends...",
                "sections": {
                    "section1": {"title": "Trend 1", "content": "Content..."}
                },
                "conclusion": "In conclusion, AI continues to evolve...",
                "report_content": "# AI Trends 2024\n\n## Introduction\n...",
                "word_count": 1500
            }
        }
