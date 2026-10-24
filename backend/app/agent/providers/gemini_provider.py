import logging
import httpx
from typing import List, Dict, Any, Optional
from backend.app.agent.providers.base import LLMProviderInterface, AgentResponse, ToolCall
from backend.app.agent.providers.mock_provider import MockLLMProvider
from backend.app.tools.registry import tool_registry

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Namma Seva Agent, Tamil Nadu's Unified AI Citizen Assistant for government welfare services and e-Sevai portals (TNeGA).
Your mission:
1. Guide citizens on applying for government certificates (Community, Income, Nativity, First Graduate, Legal Heir, OBC/EWS, etc.).
2. Explain state welfare schemes (Kalaignar Magalir Urimai Thogai, Pudhumai Penn, Tamil Pudhalvan, Moovalur Ramamirtham, Post-Matric Scholarships).
3. Specify required documents clearly, official fee structure (flat ₹60 at e-Sevai / tnesevai.tn.gov.in), processing time, and issuing authority (VAO, RI, Tahsildar).
4. Support Tamil, Tanglish, and English queries naturally. If the user writes in Tamil or Tanglish, reply in clear Tamil.
5. Provide official links (https://www.tnesevai.tn.gov.in, https://edistricts.tn.gov.in, https://tnsocialwelfare.tn.gov.in).
6. Always remain respectful, courteous, accessible, and grounded in official Tamil Nadu government policies.
7. CRITICAL: Never use any emojis, icons, or casual symbols in your output. Maintain a dignified, clean, and official Tamil Nadu Government communication style using clean markdown bullets and clear text only.
"""

class GeminiLLMProvider(LLMProviderInterface):
    """
    Live LLM provider backed by Google's Gemini API (gemini-2.5-flash / gemini-1.5-flash).
    Provides graceful fallback to deterministic mock rules if offline or rate-limited.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        self.fallback_provider = MockLLMProvider()

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_message = m.get("content", "").strip()
                break

        msg_lower = user_message.lower()

        # Check prompt injection or sensitive operations first
        injection_patterns = ["ignore previous instructions", "drop table", "leak database", "system prompt"]
        if any(pat in msg_lower for pat in injection_patterns):
            return await self.fallback_provider.generate_response(messages, tools_schema, context)

        # Check human escalation
        if any(kw in msg_lower for kw in ["human", "officer", "helpdesk", "complaint", "officer help", "மனித உதவி", "அதிகாரி", "escalate", "grievance", "புகார்"]):
            return await self.fallback_provider.generate_response(messages, tools_schema, context)

        # Check autonomous auto-apply (deterministic tool execution)
        if any(kw in msg_lower for kw in ["apply pannu", "apply panni", "auto apply", "automate", "அப்ளை பண்ணு", "விண்ணப்பிக்கவும்", "விண்ணப்பித்து", "நீயே அப்ளை", "apply for me", "apply panna", "auto-apply", "தானியங்கி விண்ணப்பம்"]):
            return await self.fallback_provider.generate_response(messages, tools_schema, context)

        # Format conversation for Gemini API
        contents = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            text = msg.get("content", "")
            if text:
                contents.append({
                    "role": role,
                    "parts": [{"text": text}]
                })

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(self.endpoint, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        reply_text = "".join(p.get("text", "") for p in parts if "text" in p).strip()
                        import re
                        reply_text = re.sub(r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\ufe0f]', '', reply_text).strip()
                        if reply_text:
                            is_tamil = any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in reply_text)
                            return AgentResponse(
                                content=reply_text,
                                language="ta" if is_tamil else "en",
                                tool_calls=[],
                                citations=[
                                    {"title": "Tamil Nadu e-Governance Agency (TNeGA)", "url": "https://www.tnesevai.tn.gov.in"},
                                    {"title": "TN e-District Portal", "url": "https://edistricts.tn.gov.in"}
                                ],
                                action_cards=[]
                            )
                else:
                    logger.warning(f"Gemini API returned status {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"Error calling Gemini API: {e}, falling back to rule provider.")

        # Graceful fallback to rich deterministic mock provider
        return await self.fallback_provider.generate_response(messages, tools_schema, context)
