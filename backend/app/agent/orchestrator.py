import logging
from typing import List, Dict, Any, Optional
from backend.app.agent.providers import get_llm_provider, AgentResponse
from backend.app.tools.registry import tool_registry

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Coordinates citizen interactions, intent processing, tool execution,
    and verified source grounding.
    """

    def __init__(self, provider: Optional[Any] = None):
        self._provider = provider

    @property
    def provider(self):
        return self._provider or get_llm_provider()

    async def process_user_message(
        self,
        conversation_history: List[Dict[str, str]],
        user_context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Executes the AI agent conversation cycle:
        1. Query provider with conversation history and available tools
        2. Execute and validate any required tool calls
        3. Ensure source grounding before returning final response
        """
        tools_schema = tool_registry.get_tool_definitions()
        
        response = await self.provider.generate_response(
            messages=conversation_history,
            tools_schema=tools_schema,
            context=user_context
        )

        return response

agent_orchestrator = AgentOrchestrator()
