"""
WhatsApp Delivery Dispatcher
Handles real-time automated dispatch of official certificates, status updates,
and acknowledgment receipts to citizens via WhatsApp Cloud API & local simulator.
"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def utcnow():
    return datetime.now(timezone.utc)

class WhatsAppDispatcher:
    """
    Automated WhatsApp notification and document delivery service.
    """

    def __init__(self):
        self.dispatched_messages = []

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
        Sends the final approved certificate message with download link.
        """
        now = utcnow()
        clean_phone = to_phone.replace("+", "").replace(" ", "").replace("-", "")

        message_text = (
            f"வணக்கம் {citizen_name}!\n\n"
            f"உங்கள் {service_name} வட்டாட்சியரால் அங்கீகரிக்கப்பட்டு தயாராக உள்ளது.\n\n"
            f"விண்ணப்ப எண் (ARN): {arn}\n"
            f"சான்றிதழ் எண்: {cert_number}\n"
            f"வழங்கிய அதிகாரி: {issuing_officer}\n\n"
            f"உங்கள் ஒரிஜினல் டிஜிட்டல் சான்றிதழை பதிவிறக்கம் செய்ய கீழ்கண்ட இணைப்பை பயன்படுத்தவும்:\n"
            f"http://localhost:8000{download_url}\n\n"
            f"நன்றி,\n"
            f"நம்ம சேவை AI ஏஜென்ட் - தமிழ்நாடு அரசு இ-சேவை மையம்"
        )

        dispatch_record = {
            "to_phone": clean_phone,
            "citizen_name": citizen_name,
            "message_text": message_text,
            "arn": arn,
            "cert_number": cert_number,
            "download_url": download_url,
            "dispatched_at": now.isoformat(),
            "channel": "WHATSAPP_CLOUD_API" if settings.WHATSAPP_TOKEN else "WHATSAPP_SIMULATOR",
            "delivery_status": "DELIVERED"
        }

        # 1. If Meta Cloud API token is configured, fire live request
        if settings.WHATSAPP_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
            try:
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
                    "text": {"preview_url": True, "body": message_text}
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code in (200, 201):
                        dispatch_record["cloud_api_response"] = resp.json()
                        logger.info(f"WhatsApp Cloud API successfully dispatched to {clean_phone}")
                    else:
                        logger.warning(f"WhatsApp Cloud API error {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Error calling WhatsApp Cloud API: {e}")

        elif settings.CALLMEBOT_APIKEY:
            try:
                import urllib.parse
                encoded = urllib.parse.quote(message_text)
                callmebot_url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={encoded}&apikey={settings.CALLMEBOT_APIKEY}"
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(callmebot_url)
                    if resp.status_code == 200:
                        dispatch_record["channel"] = "CALLMEBOT_API"
                        dispatch_record["delivery_status"] = "DELIVERED"
                        logger.info(f"Certificate dispatched via CallMeBot to {clean_phone}")
            except Exception as e:
                logger.error(f"Error sending certificate via CallMeBot: {e}")

        self.dispatched_messages.append(dispatch_record)
        return dispatch_record

    async def send_custom_message(
        self,
        to_phone: str,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Sends a general text message to any citizen WhatsApp number.
        """
        now = utcnow()
        clean_phone = to_phone.replace("+", "").replace(" ", "").replace("-", "")
        if len(clean_phone) == 10:
            clean_phone = f"91{clean_phone}"

        import urllib.parse
        encoded_text = urllib.parse.quote(message_text)
        direct_whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_text}"

        dispatch_record = {
            "to_phone": clean_phone,
            "message_text": message_text,
            "direct_whatsapp_url": direct_whatsapp_url,
            "dispatched_at": now.isoformat(),
            "channel": "WHATSAPP_CLOUD_API" if settings.WHATSAPP_TOKEN else "WHATSAPP_DIRECT_LINK",
            "delivery_status": "SENT"
        }

        if settings.WHATSAPP_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
            try:
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
                    "text": {"preview_url": True, "body": message_text}
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code in (200, 201):
                        dispatch_record["cloud_api_response"] = resp.json()
                        dispatch_record["delivery_status"] = "DELIVERED"
                        logger.info(f"Custom WhatsApp message dispatched to {clean_phone}")
                    else:
                        logger.warning(f"WhatsApp Cloud API response {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Error sending WhatsApp message: {e}")

        # CallMeBot Direct API Integration
        elif settings.CALLMEBOT_APIKEY:
            try:
                callmebot_url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={encoded_text}&apikey={settings.CALLMEBOT_APIKEY}"
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(callmebot_url)
                    if resp.status_code == 200:
                        dispatch_record["channel"] = "CALLMEBOT_API"
                        dispatch_record["delivery_status"] = "DELIVERED"
                        logger.info(f"CallMeBot WhatsApp message delivered to {clean_phone}")
                    else:
                        logger.warning(f"CallMeBot response: {resp.status_code} - {resp.text}")
            except Exception as e:
                logger.error(f"Error calling CallMeBot API: {e}")

        self.dispatched_messages.append(dispatch_record)
        return dispatch_record

    def get_latest_dispatches(self, limit: int = 10):
        return list(reversed(self.dispatched_messages[-limit:]))

whatsapp_dispatcher = WhatsAppDispatcher()
