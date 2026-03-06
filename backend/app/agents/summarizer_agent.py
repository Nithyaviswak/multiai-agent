from typing import Dict, Any
from app.agents.base import BaseAgent
from app.tools.validation import validation_tool
from app.schemas.summary import SummaryResponse
from app.logging_config import logger

class SummarizerAgent(BaseAgent):
    """Summarizer Agent that condenses research into key insights"""

    @staticmethod
    def _normalize_summary_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize common LLM JSON variants to match SummaryResponse schema."""
        normalized = dict(data)

        summary_value = normalized.get("summary")
        if isinstance(summary_value, dict):
            list_summary = summary_value.get("bullet_points") or summary_value.get("main_points")
            if isinstance(list_summary, list):
                list_summary = [str(item).strip() for item in list_summary if str(item).strip()]
            normalized["summary"] = (
                summary_value.get("text")
                or summary_value.get("summary")
                or summary_value.get("content")
                or ("\n".join(list_summary) if list_summary else "")
                or str(summary_value)
            )
        elif isinstance(summary_value, list):
            normalized["summary"] = "\n".join(str(item).strip() for item in summary_value if item)
        elif not isinstance(summary_value, str):
            normalized["summary"] = str(summary_value or normalized.get("content", "")).strip()

        key_points_value = normalized.get("key_points")
        if isinstance(key_points_value, str):
            normalized["key_points"] = [line.strip("-* ").strip() for line in key_points_value.splitlines() if line.strip()]
        elif isinstance(key_points_value, list):
            normalized["key_points"] = [
                item.get("point", "").strip() if isinstance(item, dict) else str(item).strip()
                for item in key_points_value
                if (item.get("point", "").strip() if isinstance(item, dict) else str(item).strip())
            ]
        else:
            normalized["key_points"] = []

        if not normalized["key_points"] and normalized["summary"]:
            normalized["key_points"] = [
                line.strip("-* ").strip()
                for line in str(normalized["summary"]).splitlines()
                if line.strip()
            ][:5]

        word_count_value = normalized.get("word_count")
        if not isinstance(word_count_value, int) or word_count_value <= 0:
            normalized["word_count"] = len(str(normalized["summary"]).split())

        return normalized
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        research_data = state.get("research_data")
        topic = state.get("topic", "")
        
        if not research_data:
            return {
                "summary_complete": False,
                "summary_data": None,
                "summary_validation_errors": ["No research data available"],
                "errors": state.get("errors", []) + ["No research data for summary"]
            }
        
        logger.info("Summarizer agent started", topic=topic)
        
        try:
            # Prepare prompt for summarization
            research_text = "\n\n".join([
                f"Source: {result['title']}\nContent: {result['content'][:500]}..."
                for result in research_data.get("search_results", [])
            ])
            
            prompt = f"""
            Research Topic: {topic}
            
            Research Results:
            {research_text}
            
            Please create a comprehensive summary with clear bullet points.
            Focus on the most important insights and remove any noise or irrelevant information.
            
            Return a JSON object with:
            - summary: detailed bullet-point summary
            - key_points: list of main bullet points
            - word_count: approximate word count
            
            Make it professional and well-structured.
            """
            
            system_message = """You are an expert research summarizer. 
            Create clear, concise summaries with actionable insights.
            Always return valid JSON."""
            
            response = await self._call_llm(prompt, system_message)
            
            # Extract and validate JSON
            extracted_data = await validation_tool.extract_json_from_text(response)
            extracted_data = self._normalize_summary_payload(extracted_data)
            
            # Add topic to data
            extracted_data["topic"] = topic
            
            is_valid, validated_data, error_msg = await validation_tool.validate_output(
                extracted_data, SummaryResponse
            )
            
            if not is_valid:
                raise ValueError(f"Summary validation failed: {error_msg}")
            
            return {
                "summary_complete": True,
                "summary_data": validated_data.dict(),
                "summary_validation_errors": [],
                "current_step": "report"
            }
            
        except Exception as e:
            logger.error("Summarizer agent failed", error=str(e))
            return {
                "summary_complete": False,
                "summary_data": None,
                "summary_validation_errors": [str(e)],
                "errors": state.get("errors", []) + [f"Summary failed: {str(e)}"]
            }
