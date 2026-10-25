import io
import logging
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from backend.app.main import app
from backend.app.db.session import engine, AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.document import UserDocumentModel
from backend.app.automation.whatsapp_dispatcher import WhatsAppDispatcher
from backend.app.core.crypto import decrypt_field

class LogCaptureHandler(logging.Handler):
    """Custom log handler that captures all log record formatted strings."""
    def __init__(self):
        super().__init__()
        self.records = []
        self.formatted_logs = []

    def emit(self, record):
        self.records.append(record)
        self.formatted_logs.append(self.format(record))

@pytest.fixture
def log_capturer():
    handler = LogCaptureHandler()
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    sqla_logger = logging.getLogger("sqlalchemy.engine")
    
    orig_root_level = root_logger.level
    orig_sqla_level = sqla_logger.level
    orig_echo = engine.echo

    # Set to DEBUG to capture everything including SQL echo statements
    root_logger.setLevel(logging.DEBUG)
    sqla_logger.setLevel(logging.DEBUG)
    engine.echo = True
    
    root_logger.addHandler(handler)
    sqla_logger.addHandler(handler)

    yield handler

    root_logger.removeHandler(handler)
    sqla_logger.removeHandler(handler)
    root_logger.setLevel(orig_root_level)
    sqla_logger.setLevel(orig_sqla_level)
    engine.echo = orig_echo

@pytest.mark.asyncio
async def test_no_fle_fields_leak_in_logs_sql_echo_or_exceptions(log_capturer):
    """
    Fix 6: Prove with a test that no FLE field (full_name, phone_number,
    extracted fields) appears in logs, exception messages, or SQL echo output.
    """
    citizen_name = "Muthukumar Arumugam"
    citizen_phone = "9840123456"
    extracted_data = {
        "ration_card_no": "05/G/0123456",
        "annual_income": 75000,
        "community_name": "Most Backward Class"
    }

    # 1. API Flow: Registration & User operations
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_email = f"muthu_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": unique_email,
            "password": "SecurePassword123!",
            "full_name": citizen_name,
            "phone_number": citizen_phone,
            "preferred_language": "ta"
        })
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Query /me
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200

    # 2. Database Insert with FLE fields & Extracted Document fields
    user_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        user = User(
            id=user_id,
            email=f"docuser_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="hash",
            full_name=citizen_name,
            phone_number=citizen_phone,
            role="CITIZEN",
            is_active=True
        )
        session.add(user)
        
        doc = UserDocumentModel(
            id=doc_id,
            user_id=user_id,
            doc_code="community_certificate",
            original_filename="community.pdf",
            storage_path="/tmp/test_comm.pdf",
            mime_type="application/pdf",
            file_size_bytes=1024,
            ocr_status="PROCESSED",
            extracted_fields=extracted_data,
            user_corrections={},
            is_verified_by_user=False
        )
        session.add(doc)
        await session.commit()

    # 3. Trigger simulated WhatsApp dispatch to verify phone masking
    dispatcher = WhatsAppDispatcher()
    await dispatcher.send_message(
        to_phone=citizen_phone,
        message=f"Vanakkam {citizen_name}, your certificate is ready."
    )

    # 4. Trigger decryption exception on tampered FLE ciphertext
    corrupted_fle = "FLE:1:invalid_base64_payload_corrupted_tag_12345"
    with pytest.raises(Exception) as exc_info:
        decrypt_field(corrupted_fle)
    # Check exception representation
    exc_repr = f"{exc_info.value!r} {str(exc_info.value)}"
    assert citizen_name not in exc_repr
    assert citizen_phone not in exc_repr
    assert "05/G/0123456" not in exc_repr

    # 5. Full audit of all captured log lines (including SQL statements & parameters)
    all_logs_combined = "\n".join(log_capturer.formatted_logs)

    # Citizen full name must never appear in logs or SQL parameters
    assert citizen_name not in all_logs_combined, (
        f"PII Leak: Citizen name '{citizen_name}' was found in logs/SQL echo!"
    )

    # Raw 10-digit citizen phone must never appear in logs or SQL parameters
    assert citizen_phone not in all_logs_combined, (
        f"PII Leak: Raw phone number '{citizen_phone}' was found in logs/SQL echo!"
    )

    # Extracted sensitive fields must never appear in logs or SQL parameters
    assert "05/G/0123456" not in all_logs_combined, (
        "PII Leak: Ration card number was found in logs/SQL echo!"
    )
    assert "Most Backward Class" not in all_logs_combined, (
        "PII Leak: Community caste details found in logs/SQL echo!"
    )
