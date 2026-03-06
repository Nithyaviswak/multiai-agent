from typing import Dict, Any
from app.agents.base import BaseAgent
from app.tools.validation import validation_tool
from app.schemas.report import ReportResponse
from app.logging_config import logger

class ReportWriterAgent(BaseAgent):
    """Report Writer Agent that creates professional reports"""
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        summary_data = state.get("summary_data")
        topic = state.get("topic", "")
        
        if not summary_data:
            return {
                "report_complete": False,
                "report_data": None,
                "report_validation_errors": ["No summary data available"],
                "errors": state.get("errors", []) + ["No summary data for report"]
            }
        
        logger.info("Report writer agent started", topic=topic)
        
        try:
            prompt = f"""
            Research Topic: {topic}
            
            Summary Data:
            {summary_data.get('summary', '')}
            
            Create a professional report in markdown format with:
            - Engaging title
            - Introduction
            - 3-5 main sections with subheadings
            - Conclusion
            - Proper formatting (headings, bullet points, etc.)
            
            Return a JSON object with:
            - title: report title
            - introduction: introductory paragraph
            - sections: object with section titles and content
            - conclusion: concluding paragraph
            - report_content: full markdown content
            - word_count: approximate word count
            
            Make it suitable for business or academic use.
            """
            
            system_message = """You are a professional report writer. 
            Create well-structured, engaging reports with proper markdown formatting.
            Always return valid JSON."""
            
            response = await self._call_llm(prompt, system_message)
            
            # Extract and validate JSON
            extracted_data = await validation_tool.extract_json_from_text(response)
            
            # Add topic to data
            extracted_data["topic"] = topic
            
            is_valid, validated_data, error_msg = await validation_tool.validate_output(
                extracted_data, ReportResponse
            )
            
            if not is_valid:
                raise ValueError(f"Report validation failed: {error_msg}")
            
            return {
                "report_complete": True,
                "report_data": validated_data.dict(),
                "report_validation_errors": [],
                "current_step": "fact_check"
            }
            
        except Exception as e:
            logger.error("Report writer agent failed", error=str(e))
            return {
                "report_complete": False,
                "report_data": None,
                "report_validation_errors": [str(e)],
                "errors": state.get("errors", []) + [f"Report failed: {str(e)}"]
            }
