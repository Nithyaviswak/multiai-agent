from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.tools.web_search import web_search_tool
from app.tools.validation import validation_tool
from app.schemas.fact_check import FactCheckResponse
from app.logging_config import logger

class FactCheckerAgent(BaseAgent):
    """Fact Checker Agent that validates report claims"""
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        report_data = state.get("report_data")
        research_data = state.get("research_data", {})
        topic = state.get("topic", "")
        
        if not report_data:
            return {
                "fact_check_complete": False,
                "fact_check_data": None,
                "fact_check_confidence": 0.0,
                "errors": state.get("errors", []) + ["No report data for fact checking"]
            }
        
        logger.info("Fact checker agent started", topic=topic)
        
        try:
            # Extract key claims from report
            report_content = report_data.get("report_content", "")
            claims = self._extract_claims(report_content)
            
            checked_claims = []
            total_confidence = 0
            
            # Check each claim
            for claim in claims[:3]:  # Limit to first 3 claims for efficiency
                checked_claim = await self._check_single_claim(claim, topic)
                checked_claims.append(checked_claim)
                total_confidence += checked_claim.get("confidence", 0)
            
            overall_confidence = total_confidence / len(checked_claims) if checked_claims else 0
            
            fact_check_data = {
                "topic": topic,
                "overall_confidence": overall_confidence,
                "checked_claims": checked_claims,
                "recommendations": self._generate_recommendations(checked_claims)
            }
            
            # Validate output
            is_valid, validated_data, error_msg = await validation_tool.validate_output(
                fact_check_data, FactCheckResponse
            )
            
            if not is_valid:
                raise ValueError(f"Fact check validation failed: {error_msg}")
            
            # Check if we need to retry due to low confidence
            should_retry = overall_confidence < 0.7
            
            return {
                "fact_check_complete": True,
                "fact_check_data": validated_data.dict(),
                "fact_check_confidence": overall_confidence,
                "should_retry": should_retry,
                "current_step": "complete"
            }
            
        except Exception as e:
            logger.error("Fact checker agent failed", error=str(e))
            return {
                "fact_check_complete": False,
                "fact_check_data": None,
                "fact_check_confidence": 0.0,
                "should_retry": True,
                "errors": state.get("errors", []) + [f"Fact check failed: {str(e)}"]
            }
    
    def _extract_claims(self, report_content: str) -> List[str]:
        """Extract key claims from report content"""
        prompt = f"""
        Extract 3-5 key factual claims from this report:
        
        {report_content[:2000]}  # Limit length
        
        Return as a JSON list of strings.
        """
        
        # In production, this would use the LLM to extract claims
        # For now, return placeholder
        return [
            "Main claim from the report",
            "Secondary claim from the report"
        ]
    
    async def _check_single_claim(self, claim: str, topic: str) -> Dict[str, Any]:
        """Check a single claim against sources"""
        try:
            # Search for evidence
            search_results = await web_search_tool.search(f"{topic} {claim}", max_results=3)
            
            # Simple verification logic
            supporting_evidence = [result["content"][:200] for result in search_results[:2]]
            confidence = 0.8 if supporting_evidence else 0.3
            
            return {
                "claim": claim,
                "is_supported": bool(supporting_evidence),
                "confidence": confidence,
                "evidence": supporting_evidence,
                "explanation": f"Found {len(supporting_evidence)} supporting sources"
            }
        except Exception as e:
            logger.error("Claim check failed", claim=claim, error=str(e))
            return {
                "claim": claim,
                "is_supported": False,
                "confidence": 0.1,
                "evidence": [],
                "explanation": f"Error checking claim: {str(e)}"
            }
    
    def _generate_recommendations(self, claims: List[Dict]) -> List[str]:
        """Generate recommendations based on fact check results"""
        low_confidence_claims = [c for c in claims if c.get("confidence", 0) < 0.7]
        
        if not low_confidence_claims:
            return ["All claims appear well-supported. Good job!"]
        
        return [
            f"Consider adding more sources for claim: {claim['claim'][:50]}..."
            for claim in low_confidence_claims
        ]
