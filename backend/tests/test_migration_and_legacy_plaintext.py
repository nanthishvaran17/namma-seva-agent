import uuid
import pytest
from sqlalchemy import text, select
from alembic.config import Config
from alembic import command

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.document import UserDocumentModel
from backend.app.db.migrations.encrypt_plaintext_rows import migrate_plaintext_rows_to_encryption
from backend.app.core.crypto import compute_phone_blind_index

@pytest.mark.asyncio
async def test_legacy_plaintext_read_without_crash():
    """
    Fix 3: When legacy plaintext rows exist in the database (e.g. before FLE migration),
    EncryptedString and EncryptedJSON must read them without error or crashing.
    """
    user_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    legacy_name = "Legacy Plaintext Citizen"
    legacy_phone = "9876543210"

    # Insert raw unencrypted strings bypassing TypeDecorator
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, full_name, phone_number, role, preferred_language, is_active, created_at, updated_at)
                VALUES (:uid, :email, 'dummy_hash', :name, :phone, 'CITIZEN', 'ta', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """),
            {"uid": user_id, "email": f"legacy_{uuid.uuid4().hex[:6]}@example.com", "name": legacy_name, "phone": legacy_phone}
        )
        await session.execute(
            text("""
                INSERT INTO user_documents (id, user_id, doc_code, original_filename, storage_path, mime_type, file_size_bytes, ocr_status, extracted_fields, user_corrections, is_verified_by_user, created_at, updated_at)
                VALUES (:did, :uid, 'income', 'test.pdf', '/tmp/fake.pdf', 'application/pdf', 500, 'PROCESSED', '{"annual_income": 45000, "status": "legacy"}', '{}', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """),
            {"did": doc_id, "uid": user_id}
        )
        await session.commit()

    # Load via ORM: must transparently return plaintext without crashing
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        assert user is not None
        assert user.full_name == legacy_name
        assert user.phone_number == legacy_phone

        doc = await session.get(UserDocumentModel, doc_id)
        assert doc is not None
        assert doc.extracted_fields["annual_income"] == 45000
        assert doc.extracted_fields["status"] == "legacy"

@pytest.mark.asyncio
async def test_batch_migration_encrypts_plaintext_rows():
    """
    Fix 3: migrate_plaintext_rows_to_encryption updates all legacy rows to AES-256-GCM
    and generates phone_blind_index.
    """
    user_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    legacy_name = "Kannan Murugesan"
    legacy_phone = "9778899001"

    async with AsyncSessionLocal() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, full_name, phone_number, phone_blind_index, role, preferred_language, is_active, created_at, updated_at)
                VALUES (:uid, :email, 'hash', :name, :phone, NULL, 'CITIZEN', 'ta', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """),
            {"uid": user_id, "email": f"migrate_{uuid.uuid4().hex[:6]}@example.com", "name": legacy_name, "phone": legacy_phone}
        )
        await session.execute(
            text("""
                INSERT INTO user_documents (id, user_id, doc_code, original_filename, storage_path, mime_type, file_size_bytes, ocr_status, extracted_fields, user_corrections, is_verified_by_user, created_at, updated_at)
                VALUES (:did, :uid, 'community', 'cert.pdf', '/tmp/fake.pdf', 'application/pdf', 500, 'PROCESSED', '{"caste": "BC", "name": "Kannan Murugesan"}', '{}', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """),
            {"did": doc_id, "uid": user_id}
        )
        await session.commit()

    # 1. Run batch migration
    async with AsyncSessionLocal() as session:
        stats = await migrate_plaintext_rows_to_encryption(session)
        assert stats["users_reencrypted"] >= 1
        assert stats["documents_reencrypted"] >= 1

    # 2. Assert raw DB table now stores FLE ciphertext and blind index
    async with AsyncSessionLocal() as session:
        raw_user = (await session.execute(
            text("SELECT full_name, phone_number, phone_blind_index FROM users WHERE id = :uid"),
            {"uid": user_id}
        )).fetchone()
        assert raw_user[0].startswith("FLE:1:")
        assert legacy_name not in raw_user[0]
        assert raw_user[1].startswith("FLE:1:")
        assert legacy_phone not in raw_user[1]
        assert raw_user[2] == compute_phone_blind_index(legacy_phone)

        raw_doc = (await session.execute(
            text("SELECT extracted_fields FROM user_documents WHERE id = :did"),
            {"did": doc_id}
        )).fetchone()
        assert raw_doc[0].startswith("FLE:1:")
        assert "Kannan Murugesan" not in raw_doc[0]

    # 3. Assert idempotency (second run re-encrypts 0 rows)
    async with AsyncSessionLocal() as session:
        stats2 = await migrate_plaintext_rows_to_encryption(session)
        assert stats2["users_reencrypted"] == 0
        assert stats2["documents_reencrypted"] == 0

def test_alembic_configuration_valid():
    """Fix 3: Verifies Alembic migration configuration and revision script exist and are valid."""
    cfg = Config("alembic.ini")
    script_loc = cfg.get_main_option("script_location")
    assert script_loc is not None
    assert "alembic" in script_loc
