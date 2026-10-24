import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Request, Response, BackgroundTasks, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.db.session import get_db, AsyncSessionLocal
from backend.app.models.webhook import WebhookDeduplicationModel
from backend.app.agent.orchestrator import agent_orchestrator
from backend.app.automation.whatsapp_dispatcher import whatsapp_dispatcher
from backend.app.core.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Cloud API & Simulator"])

class SimulateWhatsAppMessage(BaseModel):
    from_phone: str
    message_text: str

def redact_phone(phone: Optional[str]) -> str:
    """Masks citizen telephone numbers for GDPR/DPDP compliant logging."""
    if not phone:
        return "[EMPTY]"
    clean = str(phone).strip()
    if len(clean) <= 4:
        return "****"
    return clean[:2] + "*" * (len(clean) - 4) + clean[-2:]

def verify_meta_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Cryptographically verifies the X-Hub-Signature-256 header using constant-time comparison.
    Signature verification can NEVER be skipped outside dev/test environments.
    """
    app_secret = settings.WHATSAPP_APP_SECRET
    env_clean = (settings.ENVIRONMENT or "production").strip().lower()
    is_dev = env_clean in {"development", "dev", "test", "testing"}

    if not is_dev:
        if not app_secret or not signature_header or not signature_header.startswith("sha256="):
            return False
    else:
        # In dev/test only: allow simulator handshake if secret and header are unset
        if not app_secret and not signature_header:
            return True
        if not signature_header or not signature_header.startswith("sha256="):
            return False

    expected_hash = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    expected_sig = f"sha256={expected_hash}"
    return hmac.compare_digest(expected_sig, signature_header)

async def process_incoming_whatsapp_task(message_id: str, sender_phone: str, message_body: str):
    """
    Asynchronous worker dispatching agent query and delivering reply via WhatsApp Cloud API.
    Updates persistent deduplication status across state lifecycle:
    received -> processing -> processed / failed.
    """
    masked_phone = redact_phone(sender_phone)
    logger.info("Starting background processing for message_id=%s from %s", message_id, masked_phone)

    async with AsyncSessionLocal() as session:
        dedupe_record = await session.get(WebhookDeduplicationModel, message_id)
        if dedupe_record:
            dedupe_record.status = "processing"
            await session.commit()

        try:
            history = [{"role": "user", "content": message_body}]
            response = await agent_orchestrator.process_user_message(
                history,
                user_context={"channel": "WHATSAPP", "phone": sender_phone}
            )

            # Dispatch reply back to citizen
            await whatsapp_dispatcher.send_message(
                to_phone=sender_phone,
                message=response.content
            )

            if dedupe_record:
                dedupe_record.status = "processed"
                dedupe_record.error_message = None
                await session.commit()

            logger.info("Successfully processed and delivered WhatsApp reply for message_id=%s to %s", message_id, masked_phone)

        except Exception as e:
            if dedupe_record:
                dedupe_record.status = "failed"
                dedupe_record.error_message = str(e)[:500]
                await session.commit()

            logger.error("Error processing background WhatsApp task for message_id=%s: %s", message_id, e)

@router.get("/webhook")
async def verify_whatsapp_webhook(
    mode: Optional[str] = Query(None, alias="hub.mode"),
    token: Optional[str] = Query(None, alias="hub.verify_token"),
    challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """WhatsApp Cloud API Webhook handshake verification."""
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge or "", media_type="text/plain")
    logger.warning("WhatsApp webhook handshake failed: verify token mismatch.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post(
    "/webhook",
    dependencies=[Depends(RateLimiter(key_prefix="whatsapp_webhook"))]
)
async def receive_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Handles incoming production WhatsApp messages:
    1. Reads raw bytes before parsing
    2. Enforces HMAC-SHA256 signature verification (never skipped outside dev/test)
    3. Retry-safe persistent database deduplication:
       - 'received' / 'processing' / 'processed': skipped to prevent duplicate runs
       - 'failed': allowed to retry on Meta redelivery
    4. Enqueues processing into background tasks
    5. Returns 200 OK immediately
    """
    raw_body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256")

    # 1. Enforce HMAC Signature verification
    if not verify_meta_signature(raw_body, sig_header):
        logger.warning("Rejected WhatsApp webhook: invalid or missing X-Hub-Signature-256 signature.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-Hub-Signature-256 webhook signature"
        )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.warning("Failed to decode webhook JSON: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON payload")

    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                message_id = msg.get("id")
                if not message_id:
                    continue

                # 2. Retry-Safe Persistent Database Deduplication
                existing = await db.get(WebhookDeduplicationModel, message_id)
                should_enqueue = False

                if existing:
                    if existing.status in ("processed", "processing"):
                        logger.info("Skipping duplicate webhook message_id=%s (status=%s)", message_id, existing.status)
                        continue
                    elif existing.status == "failed":
                        logger.info("Allowing retry for previously failed message_id=%s (retry_count=%d)", message_id, existing.retry_count)
                        existing.status = "received"
                        existing.retry_count += 1
                        db.add(existing)
                        await db.commit()
                        should_enqueue = True
                    else:
                        # Already received and queued
                        continue
                else:
                    sender = msg.get("from", "")
                    sender_hash = hashlib.sha256(sender.encode("utf-8")).hexdigest()
                    dedupe_entry = WebhookDeduplicationModel(
                        message_id=message_id,
                        sender_id_hash=sender_hash,
                        status="received",
                        channel="whatsapp"
                    )
                    db.add(dedupe_entry)
                    try:
                        await db.commit()
                        should_enqueue = True
                    except IntegrityError:
                        await db.rollback()
                        logger.info("Concurrent duplicate message_id=%s caught on insert; skipping", message_id)
                        continue

                # 3. Asynchronous Worker Execution
                if should_enqueue and msg.get("type") == "text":
                    body_text = msg.get("text", {}).get("body", "")
                    sender = msg.get("from", "")
                    background_tasks.add_task(
                        process_incoming_whatsapp_task,
                        message_id=message_id,
                        sender_phone=sender,
                        message_body=body_text
                    )

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
        "sender": redact_phone(data.from_phone),
        "incoming_text": data.message_text,
        "reply_text": response.content,
        "language": response.language,
        "citations": response.citations,
        "action_cards": response.action_cards
    }

@router.post("/send")
async def send_whatsapp_message(data: SimulateWhatsAppMessage):
    """Dispatches an outgoing WhatsApp message to a phone number."""
    result = await whatsapp_dispatcher.send_custom_message(
        to_phone=data.from_phone,
        message_text=data.message_text
    )
    return result
