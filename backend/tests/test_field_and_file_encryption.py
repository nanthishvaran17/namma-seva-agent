import os
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, text
from cryptography.exceptions import InvalidTag

from backend.app.main import app
from backend.app.core.config import Settings, settings
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.document import UserDocumentModel
from backend.app.core.crypto import (
    encrypt_document_bytes,
    decrypt_document_bytes,
    encrypt_field,
    decrypt_field,
    compute_phone_blind_index,
    register_doc_encryption_key,
    register_field_encryption_key,
    clear_keyrings,
    FILE_MAGIC_PREFIX
)

@pytest.fixture(autouse=True)
def cleanup_keyrings():
    """Ensure dynamic keyrings are reset after every test."""
    yield
    clear_keyrings()

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

# ---------------------------------------------------------------------------
# 1. File Encryption Hardening: Key Versioning & Zero-Downtime Rotation
# ---------------------------------------------------------------------------

def test_file_encryption_versioning_and_rotation():
    plaintext = b"Sensitive Aadhaar and Income Proof Record for Citizen"
    
    # 1. Encrypt with v1
    payload_v1 = encrypt_document_bytes(plaintext, associated_data=b"u1:d1", key_version="1")
    assert payload_v1.startswith(FILE_MAGIC_PREFIX + b"1")

    # 2. Encrypt with v2 (simulate rotated key)
    v2_key = "a9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcb"
    register_doc_encryption_key("2", v2_key)
    payload_v2 = encrypt_document_bytes(plaintext, associated_data=b"u1:d2", key_version="2")
    assert payload_v2.startswith(FILE_MAGIC_PREFIX + b"2")

    # 3. Decrypt both payloads correctly using key version embedded in header
    decrypted_v1 = decrypt_document_bytes(payload_v1, associated_data=b"u1:d1")
    decrypted_v2 = decrypt_document_bytes(payload_v2, associated_data=b"u1:d2")
    assert decrypted_v1 == plaintext
    assert decrypted_v2 == plaintext

    # 4. Unknown key version fails gracefully
    with pytest.raises(ValueError, match="no key found in keyring"):
        bad_payload = FILE_MAGIC_PREFIX + b"9" + os.urandom(12) + os.urandom(32)
        decrypt_document_bytes(bad_payload)

# ---------------------------------------------------------------------------
# 2. File Encryption: AAD Binding and Tampering Detection
# ---------------------------------------------------------------------------

def test_file_aad_binding_and_tampering_detection():
    plaintext = b"Tamil Nadu e-District Community Certificate Signed"
    correct_aad = b"citizen_user_42:document_uuid_100"
    
    payload = encrypt_document_bytes(plaintext, associated_data=correct_aad, key_version="1")

    # Successful decryption with exact AAD
    assert decrypt_document_bytes(payload, associated_data=correct_aad) == plaintext

    # Tampered user_id in AAD (attacker swapped document ownership)
    tampered_user_aad = b"attacker_user_99:document_uuid_100"
    with pytest.raises(InvalidTag):
        decrypt_document_bytes(payload, associated_data=tampered_user_aad)

    # Tampered doc_id in AAD
    tampered_doc_aad = b"citizen_user_42:document_uuid_999"
    with pytest.raises(InvalidTag):
        decrypt_document_bytes(payload, associated_data=tampered_doc_aad)

    # Corrupted ciphertext
    corrupted_payload = payload[:-4] + b"XXXX"
    with pytest.raises(InvalidTag):
        decrypt_document_bytes(corrupted_payload, associated_data=correct_aad)

# ---------------------------------------------------------------------------
# 3. Field-Level Encryption (FLE) for User PII at Rest
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_field_level_encryption_user_pii_at_rest():
    test_name = "Thirunavukkarasu Sundaram"
    test_phone = "9876543210"
    test_email = f"fle_{uuid.uuid4().hex[:6]}@example.com"

    async with AsyncSessionLocal() as session:
        user = User(
            email=test_email,
            hashed_password="dummy_hash_not_used",
            full_name=test_name,
            phone_number=test_phone,
            role="CITIZEN"
        )
        session.add(user)
        await session.commit()
        user_id = user.id

    # 1. Direct raw SQL inspection: verify database stores ONLY ciphertext
    async with AsyncSessionLocal() as session:
        raw_res = await session.execute(
            text("SELECT full_name, phone_number FROM users WHERE id = :uid"),
            {"uid": user_id}
        )
        raw_row = raw_res.fetchone()
        assert raw_row is not None
        raw_name, raw_phone = raw_row[0], raw_row[1]

        # Plaintext MUST NOT exist in DB table
        assert test_name not in raw_name
        assert test_phone not in raw_phone

        # Must have FLE header
        assert raw_name.startswith("FLE:1:")
        assert raw_phone.startswith("FLE:1:")

    # 2. ORM transparent decryption
    async with AsyncSessionLocal() as session:
        loaded = await session.get(User, user_id)
        assert loaded is not None
        assert loaded.full_name == test_name
        assert loaded.phone_number == test_phone

# ---------------------------------------------------------------------------
# 4. Blind Index for Deterministic Phone Lookups without Plaintext Storage
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_phone_blind_index_and_lookups():
    phone_raw = "9887766554"
    phone_formatted = "+91 98877-66554"
    phone_canonical = "919887766554"

    # All variations map to identical deterministic blind index
    idx1 = compute_phone_blind_index(phone_raw)
    idx2 = compute_phone_blind_index(phone_formatted)
    idx3 = compute_phone_blind_index(phone_canonical)

    assert idx1 is not None
    assert len(idx1) == 64  # SHA-256 HMAC hex digest length
    assert idx1 == idx2 == idx3

    # Insert user and query by blind index
    email = f"blind_{uuid.uuid4().hex[:6]}@example.com"
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            hashed_password="hash",
            full_name="Kavitha Citizen",
            phone_number=phone_formatted
        )
        session.add(user)
        await session.commit()
        user_id = user.id

    async with AsyncSessionLocal() as session:
        # Verify raw DB stores index, not plaintext
        raw_res = await session.execute(
            text("SELECT phone_blind_index FROM users WHERE id = :uid"),
            {"uid": user_id}
        )
        db_blind_index = raw_res.scalar_one()
        assert db_blind_index == idx1

        # Look up user by blind index matching citizen input
        search_idx = compute_phone_blind_index("9887766554")
        res = await session.execute(select(User).where(User.phone_blind_index == search_idx))
        found_user = res.scalar_one_or_none()
        assert found_user is not None
        assert found_user.id == user_id
        assert found_user.full_name == "Kavitha Citizen"

# ---------------------------------------------------------------------------
# 5. Document Extracted OCR Fields Encryption at Rest
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_document_extracted_fields_encrypted_at_rest():
    user_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    secret_ocr_data = {
        "applicant_name": "Meenakshi Sundaram",
        "aadhaar_last4": "8877",
        "caste": "Most Backward Class",
        "annual_income_inr": 72000
    }

    async with AsyncSessionLocal() as session:
        # Create parent user to satisfy foreign key constraint
        user = User(
            id=user_id,
            email=f"doc_user_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="hash",
            full_name="Meenakshi Sundaram"
        )
        session.add(user)
        await session.commit()

    async with AsyncSessionLocal() as session:
        doc = UserDocumentModel(
            id=doc_id,
            user_id=user_id,
            doc_code="community_certificate",
            original_filename="community_cert.pdf",
            storage_path="/tmp/fake_path.pdf",
            mime_type="application/pdf",
            file_size_bytes=1024,
            extracted_fields=secret_ocr_data
        )
        session.add(doc)
        await session.commit()

    # Verify raw database table does NOT store plaintext OCR values
    async with AsyncSessionLocal() as session:
        raw_res = await session.execute(
            text("SELECT extracted_fields FROM user_documents WHERE id = :did"),
            {"did": doc_id}
        )
        raw_extracted = raw_res.scalar_one()
        assert raw_extracted.startswith("FLE:1:")
        assert "Meenakshi Sundaram" not in raw_extracted
        assert "8877" not in raw_extracted
        assert "72000" not in raw_extracted

    # Verify ORM loads and decrypts JSON correctly
    async with AsyncSessionLocal() as session:
        loaded_doc = await session.get(UserDocumentModel, doc_id)
        assert loaded_doc is not None
        assert loaded_doc.extracted_fields["applicant_name"] == "Meenakshi Sundaram"
        assert loaded_doc.extracted_fields["annual_income_inr"] == 72000

# ---------------------------------------------------------------------------
# 6. Key Separation Validation
# ---------------------------------------------------------------------------

def test_key_separation_enforced_in_production():
    shared_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"
    valid_key_2 = "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1"
    valid_key_3 = "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"

    # Fails if FIELD_ENCRYPTION_KEY == SECRET_KEY
    with pytest.raises(ValueError, match="FIELD_ENCRYPTION_KEY must be strictly distinct from SECRET_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=shared_key,
            DOC_ENCRYPTION_KEY=valid_key_2,
            FIELD_ENCRYPTION_KEY=shared_key,
            WHATSAPP_APP_SECRET="min16charsappsecret!",
            WHATSAPP_VERIFY_TOKEN="custom_prod_token_123"
        )

    # Fails if FIELD_ENCRYPTION_KEY == DOC_ENCRYPTION_KEY
    with pytest.raises(ValueError, match="FIELD_ENCRYPTION_KEY must be strictly distinct"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=valid_key_2,
            DOC_ENCRYPTION_KEY=shared_key,
            FIELD_ENCRYPTION_KEY=shared_key,
            WHATSAPP_APP_SECRET="min16charsappsecret!",
            WHATSAPP_VERIFY_TOKEN="custom_prod_token_123"
        )

    # Succeeds with strictly separate keys
    s = Settings(
        ENVIRONMENT="production",
        SECRET_KEY=shared_key,
        DOC_ENCRYPTION_KEY=valid_key_2,
        FIELD_ENCRYPTION_KEY=valid_key_3,
        WHATSAPP_APP_SECRET="min16charsappsecret!",
        WHATSAPP_VERIFY_TOKEN="custom_prod_token_123"
    )
    assert s.FIELD_ENCRYPTION_KEY != s.SECRET_KEY
    assert s.FIELD_ENCRYPTION_KEY != s.DOC_ENCRYPTION_KEY
