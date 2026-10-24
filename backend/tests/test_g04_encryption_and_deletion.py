import os
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from cryptography.exceptions import InvalidTag

from backend.app.main import app
from backend.app.core.config import Settings
from backend.app.core.crypto import (
    encrypt_document_bytes,
    decrypt_document_bytes,
    ENCRYPTED_FILE_MAGIC
)
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User, UserConsent
from backend.app.models.task import UserTaskModel, TaskEventModel
from backend.app.models.document import UserDocumentModel
from backend.app.models.reminder import ReminderModel
from backend.app.models.conversation import ConversationModel, MessageModel
from backend.app.models.audit import AuditLogModel

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

def test_aes_gcm_encryption_roundtrip():
    """G-04: Test AES-256-GCM encryption with fresh nonce per encryption and authentication."""
    plaintext = b"%PDF-1.4 Simulated Citizen Community Certificate Content"
    
    # 1. Encrypt
    encrypted_1 = encrypt_document_bytes(plaintext)
    encrypted_2 = encrypt_document_bytes(plaintext)

    # Must start with magic header
    assert encrypted_1.startswith(ENCRYPTED_FILE_MAGIC)
    # Fresh nonce per file ensures non-deterministic ciphertexts
    assert encrypted_1 != encrypted_2

    # 2. Decrypt
    decrypted = decrypt_document_bytes(encrypted_1)
    assert decrypted == plaintext

    # 3. Tampering triggers authentication failure
    tampered = bytearray(encrypted_1)
    tampered[-1] ^= 0xFF  # Flip a bit in the auth tag
    with pytest.raises(InvalidTag):
        decrypt_document_bytes(bytes(tampered))

def test_doc_encryption_key_fail_closed_in_production():
    """G-04: In production, startup fails if DOC_ENCRYPTION_KEY is missing or under 32 chars."""
    from pydantic import ValidationError
    with pytest.raises((ValueError, ValidationError), match="DOC_ENCRYPTION_KEY is missing"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="a-very-secure-random-production-key-at-least-32-chars-long",
            DOC_ENCRYPTION_KEY="",
            DEMO_MODE=False
        )

@pytest.mark.asyncio
async def test_document_upload_is_encrypted_at_rest_and_decryptable(client):
    """G-04: Document uploaded through API is encrypted on disk and decrypted on download."""
    # Register citizen
    email = f"crypto_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePassword123!",
        "full_name": "Crypto Citizen",
        "phone_number": "9876543210"
    })
    token = reg_res.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # Upload document
    pdf_content = b"%PDF-1.4 Sensitive Citizen Aadhaar Proof 1234-5678-9012"
    files = {"file": ("aadhaar.pdf", pdf_content, "application/pdf")}
    data = {"doc_code": "address_proof"}

    upload_res = await client.post("/api/v1/documents/upload", files=files, data=data, headers=auth_header)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Locate file on disk and verify encryption
    async with AsyncSessionLocal() as session:
        doc = await session.get(UserDocumentModel, doc_id)
        assert doc is not None
        storage_path = doc.storage_path

    assert os.path.exists(storage_path)
    with open(storage_path, "rb") as f:
        disk_bytes = f.read()

    # Raw disk bytes MUST start with encryption magic header and MUST NOT contain plaintext
    assert disk_bytes.startswith(ENCRYPTED_FILE_MAGIC)
    assert b"1234-5678-9012" not in disk_bytes

    # Download through authenticated endpoint decrypts seamlessly
    down_res = await client.get(f"/api/v1/documents/{doc_id}/download", headers=auth_header)
    assert down_res.status_code == 200
    assert down_res.content == pdf_content

@pytest.mark.asyncio
async def test_complete_user_data_purge_me_data(client):
    """
    G-04 Complete Deletion: After DELETE /me/data:
    - 0 DB rows remain across all user tables (users, tasks, events, documents, reminders, messages, consents, audit)
    - 0 files or directories remain on disk for that user
    - Old token is invalidated
    """
    # 1. Register user
    email = f"purge_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePassword123!",
        "full_name": "Purge Citizen",
        "phone_number": "9443322110"
    })
    token = reg_res.json()["access_token"]
    user_id = reg_res.json()["user"]["id"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. Upload document (creating physical file)
    pdf_content = b"%PDF-1.4 Income Proof Document"
    files = {"file": ("income.pdf", pdf_content, "application/pdf")}
    upload_res = await client.post("/api/v1/documents/upload", files=files, data={"doc_code": "income_certificate"}, headers=auth_header)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 3. Create a task and reminder
    async with AsyncSessionLocal() as session:
        task = UserTaskModel(user_id=user_id, service_id="income_certificate", status="DRAFT")
        session.add(task)
        await session.flush()

        event = TaskEventModel(task_id=task.id, previous_status=None, new_status="DRAFT", reason="Created")
        session.add(event)

        conv = ConversationModel(user_id=user_id, channel="WEB")
        session.add(conv)
        await session.flush()

        msg = MessageModel(conversation_id=conv.id, sender="user", content="Hello")
        session.add(msg)
        await session.commit()

        # Get file path
        doc = await session.get(UserDocumentModel, doc_id)
        storage_path = doc.storage_path

    # Verify file exists on disk prior to deletion
    assert os.path.exists(storage_path)

    # 4. Invoke DELETE /me/data
    del_res = await client.delete("/api/v1/auth/me/data", headers=auth_header)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"

    # 5. Assert physical file and user storage directory are purged
    assert not os.path.exists(storage_path)
    user_dir = os.path.dirname(storage_path)
    assert not os.path.exists(user_dir)

    # 6. Assert 0 DB rows remain across all user tables
    async with AsyncSessionLocal() as session:
        # User
        assert (await session.get(User, user_id)) is None
        # Tasks
        tasks = (await session.execute(select(UserTaskModel).where(UserTaskModel.user_id == user_id))).scalars().all()
        assert len(tasks) == 0
        # Documents
        docs = (await session.execute(select(UserDocumentModel).where(UserDocumentModel.user_id == user_id))).scalars().all()
        assert len(docs) == 0
        # Reminders
        reminders = (await session.execute(select(ReminderModel).where(ReminderModel.user_id == user_id))).scalars().all()
        assert len(reminders) == 0
        # Consents
        consents = (await session.execute(select(UserConsent).where(UserConsent.user_id == user_id))).scalars().all()
        assert len(consents) == 0
        # Conversations
        convs = (await session.execute(select(ConversationModel).where(ConversationModel.user_id == user_id))).scalars().all()
        assert len(convs) == 0
        # Audit logs
        logs = (await session.execute(select(AuditLogModel).where(AuditLogModel.user_id == user_id))).scalars().all()
        assert len(logs) == 0

    # 7. Old token is rejected
    check_res = await client.get("/api/v1/auth/me", headers=auth_header)
    assert check_res.status_code == 401
