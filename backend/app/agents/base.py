from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_groq import ChatGroq
from app.config import settings
from app.logging_config import logger

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL,
            temperature=0.7
        )
        self.max_retries = settings.MAX_RETRIES
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the state and return updated state"""
        pass
    
    async def _call_llm(self, prompt: str, system_message: str = "") -> str:
        """Make LLM call with error handling"""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        try:
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
            
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            raise e
