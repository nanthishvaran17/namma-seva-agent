from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Request, Response, status
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.agent.orchestrator import agent_orchestrator

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Cloud API & Simulator"])

class SimulateWhatsAppMessage(BaseModel):
    from_phone: str
    message_text: str

@router.get("/webhook")
async def verify_whatsapp_webhook(
    mode: Optional[str] = Query(None, alias="hub.mode"),
    token: Optional[str] = Query(None, alias="hub.verify_token"),
    challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """WhatsApp Cloud API Webhook handshake."""
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post("/webhook")
async def receive_whatsapp_webhook(request: Request):
    """Handles incoming production WhatsApp messages."""
    payload = await request.json()
    # Handle entry, changes, messages
    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                if msg.get("type") == "text":
                    body = msg.get("text", {}).get("body", "")
                    sender = msg.get("from")
                    # Process via agent
                    history = [{"role": "user", "content": body}]
                    res = await agent_orchestrator.process_user_message(history, user_context={"channel": "WHATSAPP", "phone": sender})
                    # Outgoing response logged / dispatched
    return {"status": "EVENT_RECEIVED"}

@router.post("/simulate")
async def simulate_whatsapp_interaction(data: SimulateWhatsAppMessage):
    """Interactive local simulator for testing WhatsApp Tamil/Tanglish/English flows without cloud credentials."""
    history = [{"role": "user", "content": data.message_text}]
    response = await agent_orchestrator.process_user_message(
        history,
        user_context={"channel": "WHATSAPP_SIMULATOR", "phone": data.from_phone}
    )
    return {
        "channel": "WHATSAPP_SIMULATOR",
        "sender": data.from_phone,
        "incoming_text": data.message_text,
        "reply_text": response.content,
        "language": response.language,
        "citations": response.citations,
        "action_cards": response.action_cards
    }

@router.post("/send")
async def send_whatsapp_message(data: SimulateWhatsAppMessage):
    """Dispatches an outgoing WhatsApp message to a phone number."""
    from backend.app.automation.whatsapp_dispatcher import whatsapp_dispatcher
    result = await whatsapp_dispatcher.send_custom_message(
        to_phone=data.from_phone,
        message_text=data.message_text
    )
    return result
