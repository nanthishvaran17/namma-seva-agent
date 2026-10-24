import hmac
import hashlib
import json
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, select

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.db.session import engine, Base, AsyncSessionLocal
from backend.app.models.webhook import WebhookDeduplicationModel
from backend.app.api.v1.whatsapp import redact_phone

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

def generate_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"

@pytest.mark.asyncio
async def test_whatsapp_webhook_valid_signature(client, monkeypatch):
    """G-03: Webhook accepts request with cryptographically valid HMAC-SHA256 signature."""
    test_secret = "test-whatsapp-app-secret-key-32chars"
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", test_secret)

    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "entry_1",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "id": "wamid_valid_001",
                        "from": "919876543210",
                        "type": "text",
                        "text": {"body": "Vanakkam"}
                    }]
                }
            }]
        }]
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = generate_signature(test_secret, raw_body)

    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sig
    }

    res = await client.post("/api/v1/whatsapp/webhook", content=raw_body, headers=headers)
    assert res.status_code == 200
    assert res.json() == {"status": "EVENT_RECEIVED"}

@pytest.mark.asyncio
async def test_whatsapp_webhook_invalid_signature_rejected(client, monkeypatch):
    """G-03: Webhook rejects request with fraudulent or incorrect HMAC signature with 403."""
    test_secret = "test-whatsapp-app-secret-key-32chars"
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", test_secret)

    raw_body = b'{"test": "payload"}'
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "sha256=0000000000000000000000000000000000000000000000000000000000000000"
    }

    res = await client.post("/api/v1/whatsapp/webhook", content=raw_body, headers=headers)
    assert res.status_code == 403
    assert "Invalid or missing X-Hub-Signature-256" in res.json()["detail"]

@pytest.mark.asyncio
async def test_whatsapp_webhook_missing_signature_rejected(client, monkeypatch):
    """G-03: Webhook rejects request lacking X-Hub-Signature-256 header when secret is configured."""
    test_secret = "test-whatsapp-app-secret-key-32chars"
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", test_secret)

    raw_body = b'{"test": "payload"}'
    headers = {"Content-Type": "application/json"}

    res = await client.post("/api/v1/whatsapp/webhook", content=raw_body, headers=headers)
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_whatsapp_webhook_tampered_payload_rejected(client, monkeypatch):
    """G-03: Altering even one byte of payload invalidates signature and triggers 403."""
    test_secret = "test-whatsapp-app-secret-key-32chars"
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", test_secret)

    original_body = b'{"amount": 60}'
    sig = generate_signature(test_secret, original_body)

    tampered_body = b'{"amount": 600}'  # Tampered
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sig
    }

    res = await client.post("/api/v1/whatsapp/webhook", content=tampered_body, headers=headers)
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_whatsapp_persistent_database_deduplication(client, monkeypatch):
    """
    G-03: Webhook deduplication must use persistent database store.
    Identical message ID delivered multiple times is processed only once.
    """
    test_secret = "test-whatsapp-app-secret-key-32chars"
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", test_secret)

    unique_msg_id = "wamid_dedupe_test_unique_9981"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "entry_dedupe",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "id": unique_msg_id,
                        "from": "919443322110",
                        "type": "text",
                        "text": {"body": "First graduate status"}
                    }]
                }
            }]
        }]
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = generate_signature(test_secret, raw_body)
    headers = {"Content-Type": "application/json", "X-Hub-Signature-256": sig}

    # First delivery
    res1 = await client.post("/api/v1/whatsapp/webhook", content=raw_body, headers=headers)
    assert res1.status_code == 200

    # Verify message recorded in DB
    async with AsyncSessionLocal() as session:
        record = await session.get(WebhookDeduplicationModel, unique_msg_id)
        assert record is not None
        assert record.message_id == unique_msg_id
        assert record.channel == "whatsapp"

    # Second delivery (duplicate retry from Meta)
    res2 = await client.post("/api/v1/whatsapp/webhook", content=raw_body, headers=headers)
    assert res2.status_code == 200

    # Ensure still exactly one row exists
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(WebhookDeduplicationModel).where(WebhookDeduplicationModel.message_id == unique_msg_id)
        )
        rows = res.scalars().all()
        assert len(rows) == 1

def test_phone_number_redaction():
    """G-03: Ensure phone numbers are masked for compliant privacy logging."""
    assert redact_phone("9876543210") == "98******10"
    assert redact_phone("+919876543210") == "+9*********10"
    assert redact_phone("") == "[EMPTY]"
    assert redact_phone("123") == "****"
