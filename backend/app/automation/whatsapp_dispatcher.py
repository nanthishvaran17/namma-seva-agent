"""
WhatsApp Delivery Dispatcher
Handles real-time automated outbound dispatch of messages and status updates
to citizens via Meta WhatsApp Cloud API with exponential backoff retries.

PRIVACY & LOGGING INVARIANTS:
1. Citizen telephone numbers are ALWAYS masked before logging (e.g. 98****10).
2. Outbound message bodies are NEVER logged to disk or console.
3. Live network calls are only made when WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID
   are configured; in test/dev/mock mode, dispatch records are captured in memory.
"""

import asyncio
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def utcnow():
    return datetime.now(timezone.utc)

def redact_phone(phone: Optional[str]) -> str:
    """Masks citizen telephone numbers for GDPR/DPDP compliant logging."""
    if not phone:
        return "[EMPTY]"
    clean = str(phone).strip()
    if len(clean) <= 4:
        return "****"
    return clean[:2] + "*" * (len(clean) - 4) + clean[-2:]

class WhatsAppDispatcher:
    """
    Automated WhatsApp notification and document delivery service with
    exponential backoff retries and privacy-preserving logging.
    """

    def __init__(self, max_retries: int = 3, base_backoff_seconds: float = 0.5):
        self.dispatched_messages = []
        self.max_retries = max_retries
        self.base_backoff_seconds = base_backoff_seconds

    async def send_message(
        self,
        to_phone: str,
        message: str,
        client: Optional[httpx.AsyncClient] = None,
        backoff_factor: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Sends an outbound text message via WhatsApp Cloud API (Graph API) with retry logic.
        """
        now = utcnow()
        clean_phone = to_phone.replace("+", "").replace(" ", "").replace("-", "")
        if len(clean_phone) == 10:
            clean_phone = f"91{clean_phone}"

        masked_phone = redact_phone(clean_phone)
        backoff = self.base_backoff_seconds if backoff_factor is None else backoff_factor

        dispatch_record = {
            "to_phone": clean_phone,
            "message_length": len(message),
            "dispatched_at": now.isoformat(),
            "channel": "WHATSAPP_CLOUD_API" if settings.WHATSAPP_TOKEN else "WHATSAPP_SIMULATOR",
            "delivery_status": "PENDING",
            "retry_attempts": 0
        }

        # 1. Simulator / Unconfigured mode: do not make real network calls
        if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            dispatch_record["delivery_status"] = "DELIVERED"
            logger.info("Dispatched WhatsApp message via simulator to %s (len=%d chars)", masked_phone, len(message))
            self.dispatched_messages.append(dispatch_record)
            return dispatch_record

        # 2. Production Graph API Dispatch with Exponential Backoff
        url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {"preview_url": True, "body": message}
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            dispatch_record["retry_attempts"] = attempt
            try:
                # Use caller-provided client or create a dedicated client
                if client is not None:
                    resp = await client.post(url, json=payload, headers=headers)
                else:
                    async with httpx.AsyncClient(timeout=10.0) as http_client:
                        resp = await http_client.post(url, json=payload, headers=headers)

                if resp.status_code in (200, 201):
                    dispatch_record["cloud_api_response"] = resp.json()
                    dispatch_record["delivery_status"] = "DELIVERED"
                    logger.info("Successfully delivered WhatsApp message to %s (attempt=%d)", masked_phone, attempt)
                    self.dispatched_messages.append(dispatch_record)
                    return dispatch_record

                # Non-retryable 4xx client errors (except 429 rate limit)
                if 400 <= resp.status_code < 500 and resp.status_code != 429:
                    error_detail = f"HTTP {resp.status_code} client error"
                    logger.warning("WhatsApp Cloud API non-retryable error for %s: %s", masked_phone, error_detail)
                    dispatch_record["delivery_status"] = "FAILED"
                    dispatch_record["error"] = error_detail
                    self.dispatched_messages.append(dispatch_record)
                    return dispatch_record

                # Retryable error (429 rate limit or 5xx server error)
                last_error = f"HTTP {resp.status_code}"
                logger.warning("Transient WhatsApp Cloud API error for %s: %s (attempt %d/%d)", masked_phone, last_error, attempt, self.max_retries)

            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_error = f"Network/Timeout exception: {type(exc).__name__}"
                logger.warning("Network failure dispatching WhatsApp message to %s: %s (attempt %d/%d)", masked_phone, last_error, attempt, self.max_retries)
            except Exception as exc:
                last_error = f"Unexpected error: {type(exc).__name__}"
                logger.error("Unexpected error dispatching WhatsApp message to %s: %s", masked_phone, last_error)
                break

            # Sleep with exponential backoff before retrying
            if attempt < self.max_retries and backoff > 0:
                await asyncio.sleep(backoff * (2 ** (attempt - 1)))

        dispatch_record["delivery_status"] = "FAILED"
        dispatch_record["error"] = last_error
        logger.error("Exhausted all %d retries for WhatsApp message to %s. Final status: FAILED", self.max_retries, masked_phone)
        self.dispatched_messages.append(dispatch_record)
        return dispatch_record

    async def send_custom_message(self, to_phone: str, message_text: str) -> Dict[str, Any]:
        """Convenience method delegating to send_message."""
        return await self.send_message(to_phone=to_phone, message=message_text)

    async def send_certificate_notification(
        self,
        to_phone: str,
        citizen_name: str,
        service_name: str,
        arn: str,
        cert_number: str,
        download_url: str,
        issuing_officer: str = "மண்டல துணை வட்டாட்சியர் (Zonal Deputy Tahsildar)"
    ) -> Dict[str, Any]:
        """
        Sends application completion notification with download instructions.
        Note: The message explicitly states this is an application guidance receipt.
        """
        message_text = (
            f"வணக்கம் {citizen_name}!\n\n"
            f"உங்கள் {service_name} விண்ணப்பப் படிவம் மற்றும் சரிபார்ப்பு பட்டியல் தயாராக உள்ளது.\n\n"
            f"விண்ணப்பக் குறிப்பு எண் (ARN): {arn}\n"
            f"வழங்கிய அதிகாரி: {issuing_officer}\n\n"
            f"உங்கள் விண்ணப்ப விவரங்களை பதிவிறக்கம் செய்ய:\n"
            f"http://localhost:8000{download_url}\n\n"
            f"நன்றி,\n"
            f"நம்ம சேவை AI ஏஜென்ட் - தமிழ்நாடு அரசு இ-சேவை வழிகாட்டி"
        )
        return await self.send_message(to_phone=to_phone, message=message_text)

    def get_latest_dispatches(self, limit: int = 10):
        return list(reversed(self.dispatched_messages[-limit:]))

whatsapp_dispatcher = WhatsAppDispatcher()
