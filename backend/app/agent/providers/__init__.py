from typing import Dict, Any
from backend.app.core.config import settings
from backend.app.agent.providers.base import LLMProviderInterface, AgentResponse, ToolCall
from backend.app.agent.providers.mock_provider import MockLLMProvider

def get_provider_status() -> Dict[str, Any]:
    """
    Returns true operational status of the LLM provider.
    Never claims active capabilities that are not configured.
    """
    configured = (settings.LLM_PROVIDER or "mock").lower()
    has_gemini_key = bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 0)
    
    if settings.ENVIRONMENT == "test" or configured == "mock":
        return {
            "active_provider": "mock",
            "configured_provider": configured,
            "gemini_api_key_configured": has_gemini_key,
            "live_calls_made": False,
            "notice": "Deterministic mock provider active (offline / test mode)"
        }
    
    if configured == "gemini":
        if has_gemini_key:
            return {
                "active_provider": "gemini",
                "configured_provider": configured,
                "gemini_api_key_configured": True,
                "live_calls_made": True,
                "notice": "Gemini API key configured and adapter active"
            }
        else:
            return {
                "active_provider": "mock",
                "configured_provider": configured,
                "gemini_api_key_configured": False,
                "live_calls_made": False,
                "notice": "LLM_PROVIDER set to 'gemini' but GEMINI_API_KEY is missing; true active provider is mock"
            }
            
    return {
        "active_provider": "mock",
        "configured_provider": configured,
        "gemini_api_key_configured": has_gemini_key,
        "live_calls_made": False,
        "notice": f"Provider '{configured}' falling back to deterministic mock"
    }

def get_llm_provider() -> LLMProviderInterface:
    """
    Returns the configured LLM provider.
    Defaults to MockLLMProvider for deterministic tests and offline local dev.
    """
    if settings.ENVIRONMENT != "test" and settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        try:
            from backend.app.agent.providers.gemini_provider import GeminiLLMProvider
            return GeminiLLMProvider(api_key=settings.GEMINI_API_KEY)
        except Exception:
            return MockLLMProvider()
    return MockLLMProvider()

__all__ = [
    "LLMProviderInterface",
    "AgentResponse",
    "ToolCall",
    "MockLLMProvider",
    "get_llm_provider",
    "get_provider_status"
]
