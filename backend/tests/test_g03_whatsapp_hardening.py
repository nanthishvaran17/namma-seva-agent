import hmac
import hashlib
import json
import logging
import httpx
import pytest
from httpx import AsyncClient, ASGITransport, Response as HttpxResponse, Request as HttpxRequest
from sqlalchemy import text, select

from backend.app.main import app
from backend.app.core.config import Settings, settings
from backend.app.db.session import engine, Base, AsyncSessionLocal
from backend.app.models.webhook import WebhookDeduplicationModel
from backend.app.api.v1.whatsapp import redact_phone, verify_meta_signature
from backend.app.automation.whatsapp_dispatcher import WhatsAppDispatcher

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

def test_whatsapp_app_secret_fail_closed_in_production():
    """Fix 1(a): In production, startup fails if WHATSAPP_APP_SECRET is missing or < 16 chars."""
    from pydantic import ValidationError
    with pytest.raises((ValueError, ValidationError), match="WHATSAPP_APP_SECRET is missing or insecure"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="a-very-secure-random-production-key-at-least-32-chars-long",
            DOC_ENCRYPTION_KEY="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            WHATSAPP_APP_SECRET="",
            DEMO_MODE=False
        )

def test_signature_verification_never_skipped_in_production(monkeypatch):
    """Fix 1(a): Signature verification can NEVER be skipped outside dev/test environments."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "prod_secret_key_12345")
    # Missing signature header must be rejected
    assert verify_meta_signature(b"sample raw payload", None) is False
    assert verify_meta_signature(b"sample raw payload", "") is False

@pytest.mark.asyncio
async def test_outbound_graph_api_dispatcher_retries_and_backoff(monkeypatch):
    """
    Fix 1(b): Outbound dispatcher retries on transient errors (5xx/429) using exponential backoff
    tested with a mocked HTTP client (no real network calls).
    """
    monkeypatch.setattr(settings, "WHATSAPP_TOKEN", "mock_wa_token_12345")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "1009988776655")

    dispatcher = WhatsAppDispatcher(max_retries=3, base_backoff_seconds=0.01)

    attempts = 0
    def mock_handler(request: HttpxRequest) -> HttpxResponse:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            # First attempt fails with 503 Service Unavailable
            return HttpxResponse(503, json={"error": "transient upstream outage"})
        # Second attempt succeeds with 200 OK
        return HttpxResponse(200, json={
            "messaging_product": "whatsapp",
            "messages": [{"id": "wamid.HBgLMTIzNDU2"}]
        })

    mock_client = AsyncClient(transport=httpx.MockTransport(mock_handler))

    result = await dispatcher.send_message(
        to_phone="9876543210",
        message="வணக்கம்! உங்கள் சேவை விவரங்கள்.",
        client=mock_client
    )

    assert attempts == 2
    assert result["delivery_status"] == "DELIVERED"
    assert result["retry_attempts"] == 2
    assert "wamid.HBgLMTIzNDU2" in str(result["cloud_api_response"])

@pytest.mark.asyncio
async def test_outbound_dispatcher_logs_never_contain_message_body_or_full_phone(caplog, monkeypatch):
    """
    Fix 1(b): Privacy requirement: logs must NEVER contain message bodies or unmasked phone numbers.
    """
    caplog.set_level(logging.INFO)
    dispatcher = WhatsAppDispatcher(max_retries=1, base_backoff_seconds=0.0)

    # In simulator mode
    monkeypatch.setattr(settings, "WHATSAPP_TOKEN", "")
    secret_body = "HIGHLY_CONFIDENTIAL_CITIZEN_AADHAAR_BODY_887766"
    raw_phone = "9876543210"

    await dispatcher.send_message(to_phone=raw_phone, message=secret_body)

    for record in caplog.records:
        # Message body MUST NOT appear anywhere in logs
        assert secret_body not in record.message
        # Full unmasked phone number MUST NOT appear in logs
        assert raw_phone not in record.message
        # Masked phone must be present
        if "Dispatched WhatsApp message" in record.message:
            assert "91********10" in record.message

@pytest.mark.asyncio
async def test_webhook_retry_safe_deduplication_failed_job_retryable(client, monkeypatch):
    """
    Fix 1(c): Dedupe is retry-safe:
    - Initial delivery creates 'received' record.
    - If background worker fails (status becomes 'failed'), Meta redelivery is allowed.
    - Status transitions back to 'received' and retry_count is incremented.
    """
    test_secret = "test-whatsapp-app-secret-key-32chars"
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", test_secret)

    msg_id = "wamid_retry_test_992211"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "entry_retry",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "id": msg_id,
                        "from": "919443322110",
                        "type": "text",
                        "text": {"body": "Check status"}
                    }]
                }
            }]
        }]
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = generate_signature(test_secret, raw_body)
    headers = {"Content-Type": "application/json", "X-Hub-Signature-256": sig}

    # 1. First delivery
    res1 = await client.post("/api/v1/whatsapp/webhook", content=raw_body, headers=headers)
    assert res1.status_code == 200

    # 2. Simulate worker failure: mark status as 'failed' in DB
    async with AsyncSessionLocal() as session:
        record = await session.get(WebhookDeduplicationModel, msg_id)
        assert record is not None
        assert record.status in ("received", "processing", "processed")
        record.status = "failed"
        record.error_message = "Upstream LLM timeout"
        await session.commit()

    # 3. Meta redelivery of the failed message: MUST BE ALLOWED
    res2 = await client.post("/api/v1/whatsapp/webhook", content=raw_body, headers=headers)
    assert res2.status_code == 200

    # Verify status transitioned back to 'received' and retry_count incremented
    async with AsyncSessionLocal() as session:
        reloaded = await session.get(WebhookDeduplicationModel, msg_id)
        assert reloaded is not None
        assert reloaded.retry_count == 1
        assert reloaded.status in ("received", "processing", "processed")

def test_phone_number_redaction():
    """G-03: Ensure phone numbers are masked for compliant privacy logging."""
    assert redact_phone("9876543210") == "98******10"
    assert redact_phone("+919876543210") == "+9*********10"
    assert redact_phone("") == "[EMPTY]"
    assert redact_phone("123") == "****"
