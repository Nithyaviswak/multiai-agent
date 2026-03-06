from langgraph.graph import StateGraph, END
from typing import Dict, Any
from app.agents.research_agent import ResearchAgent
from app.agents.summarizer_agent import SummarizerAgent
from app.agents.report_writer_agent import ReportWriterAgent
from app.agents.fact_checker_agent import FactCheckerAgent
from app.schemas.state import AgentState
from app.logging_config import logger

class ResearchWorkflow:
    """LangGraph workflow for the multi-agent system"""
    
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.summarizer_agent = SummarizerAgent()
        self.report_writer_agent = ReportWriterAgent()
        self.fact_checker_agent = FactCheckerAgent()
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("research", self._research_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("write_report", self._write_report_node)
        workflow.add_node("fact_check", self._fact_check_node)
        workflow.add_node("decide_retry", self._decide_retry_node)
        
        # Add edges
        workflow.set_entry_point("research")
        workflow.add_edge("research", "summarize")
        workflow.add_edge("summarize", "write_report")
        workflow.add_edge("write_report", "fact_check")
        workflow.add_edge("fact_check", "decide_retry")
        
        # Conditional edge for retry
        workflow.add_conditional_edges(
            "decide_retry",
            self._should_retry,
            {
                "retry": "research",
                "continue": END
            }
        )
        
        return workflow.compile()
    
    async def _research_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research agent"""
        return await self.research_agent.process(state)
    
    async def _summarize_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute summarizer agent"""
        return await self.summarizer_agent.process(state)
    
    async def _write_report_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report writer agent"""
        return await self.report_writer_agent.process(state)
    
    async def _fact_check_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fact checker agent"""
        return await self.fact_checker_agent.process(state)
    
    async def _decide_retry_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Decide whether to retry the workflow"""
        retry_count = state.get("retry_count", 0)
        should_retry = state.get("should_retry", False)
        
        if should_retry and retry_count < 2:  # Max 2 retries
            logger.info("Workflow retry triggered", retry_count=retry_count)
            return {
                "retry_count": retry_count + 1,
                "should_retry": False,
                "current_step": "retry"
            }
        else:
            return {
                "current_step": "complete",
                "should_retry": False
            }
    
    def _should_retry(self, state: Dict[str, Any]) -> str:
        """Determine if workflow should retry"""
        if state.get("should_retry", False) and state.get("retry_count", 0) < 2:
            return "retry"
        return "continue"
    
    async def run(self, topic: str) -> Dict[str, Any]:
        """Execute the complete workflow"""
        initial_state = {
            "topic": topic,
            "research_complete": False,
            "summary_complete": False,
            "report_complete": False,
            "fact_check_complete": False,
            "errors": [],
            "retry_count": 0,
            "should_retry": False,
            "current_step": "research"
        }
        
        try:
            result = await self.graph.ainvoke(initial_state)
            return result
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            return {
                **initial_state,
                "errors": [f"Workflow failed: {str(e)}"],
                "current_step": "error"
            }

# Singleton instance
research_workflow = ResearchWorkflow()
