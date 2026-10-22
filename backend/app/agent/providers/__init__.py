from backend.app.core.config import settings
from backend.app.agent.providers.base import LLMProviderInterface, AgentResponse, ToolCall
from backend.app.agent.providers.mock_provider import MockLLMProvider

def get_llm_provider() -> LLMProviderInterface:
    """
    Returns the configured LLM provider.
    Defaults to MockLLMProvider for deterministic tests and offline local dev.
    """
    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        try:
            from backend.app.agent.providers.gemini_provider import GeminiLLMProvider
            return GeminiLLMProvider(api_key=settings.GEMINI_API_KEY)
        except Exception:
            return MockLLMProvider()
    return MockLLMProvider()

__all__ = ["LLMProviderInterface", "AgentResponse", "ToolCall", "MockLLMProvider", "get_llm_provider"]
