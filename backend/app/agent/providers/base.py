from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class AgentResponse(BaseModel):
    content: str
    language: str = "en"
    tool_calls: List[ToolCall] = []
    citations: List[Dict[str, str]] = []
    action_cards: List[Dict[str, Any]] = []
    requires_user_confirmation: bool = False
    confirmation_prompt: Optional[str] = None

class LLMProviderInterface(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Generates structured response from the LLM."""
        pass
