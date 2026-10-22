from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatMessage(BaseModel):
    role: str # "user", "assistant", "system"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    language: Optional[str] = "ta"
    context: Optional[Dict[str, Any]] = None

class Citation(BaseModel):
    title: str
    url: str

class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    language: str
    citations: List[Citation] = []
    action_cards: List[Dict[str, Any]] = []
    requires_user_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
