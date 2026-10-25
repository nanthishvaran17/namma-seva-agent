import uuid
import pytest
from sqlalchemy import text, select
from cryptography.exceptions import InvalidTag

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.document import UserDocumentModel
from backend.app.core.crypto import (
    encrypt_field,
    decrypt_field,
    compute_field_aad
)
from backend.app.db.migrations.encrypt_plaintext_rows import migrate_plaintext_rows_to_encryption

@pytest.mark.asyncio
async def test_fle_aad_row_swap_prevention():
    """
    Fix 3: Bind AAD (table:column:row_id). Swapping an encrypted field from
    Row A into Row B causes AES-GCM tag verification to fail cleanly.
    """
    user_a_id = str(uuid.uuid4())
    user_b_id = str(uuid.uuid4())

    async with AsyncSessionLocal() as session:
        user_a = User(
            id=user_a_id,
            email=f"user_a_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="hash",
            full_name="Alice Muthu",
            phone_number="9876543210",
            role="CITIZEN",
            is_active=True
        )
        user_b = User(
            id=user_b_id,
            email=f"user_b_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="hash",
            full_name="Bob Selvam",
            phone_number="9123456789",
            role="CITIZEN",
            is_active=True
        )
        session.add_all([user_a, user_b])
        await session.commit()

    # Raw SQL swap: Copy User A's encrypted full_name into User B's row
    async with AsyncSessionLocal() as session:
        user_a_raw = (await session.execute(
            text("SELECT full_name FROM users WHERE id = :uid"), {"uid": user_a_id}
        )).scalar()
        assert ":AAD:" in user_a_raw

        await session.execute(
            text("UPDATE users SET full_name = :fn WHERE id = :uid"),
            {"fn": user_a_raw, "uid": user_b_id}
        )
        await session.commit()

    # Accessing User B's full_name MUST fail because AAD mismatch (user_a_id != user_b_id)
    async with AsyncSessionLocal() as session:
        user_b = await session.get(User, user_b_id)
        assert user_b is not None
        with pytest.raises(Exception):
            _ = user_b.full_name

@pytest.mark.asyncio
async def test_fle_aad_column_swap_prevention():
    """
    Fix 3: Swapping an encrypted full_name into phone_number in the same row
    causes AES-GCM tag verification to fail due to column mismatch in AAD.
    """
    user_id = str(uuid.uuid4())

    async with AsyncSessionLocal() as session:
        user = User(
            id=user_id,
            email=f"col_swap_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="hash",
            full_name="Kavitha Raman",
            phone_number="9840112233",
            role="CITIZEN",
            is_active=True
        )
        session.add(user)
        await session.commit()

    # Copy full_name ciphertext into phone_number column
    async with AsyncSessionLocal() as session:
        raw_name = (await session.execute(
            text("SELECT full_name FROM users WHERE id = :uid"), {"uid": user_id}
        )).scalar()

        await session.execute(
            text("UPDATE users SET phone_number = :fn WHERE id = :uid"),
            {"fn": raw_name, "uid": user_id}
        )
        await session.commit()

    # Reading phone_number MUST fail because AAD was bound to column "full_name"
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        assert user is not None
        with pytest.raises(Exception):
            _ = user.phone_number

@pytest.mark.asyncio
async def test_legacy_fle_without_aad_handled_without_crash(monkeypatch):
    """
    Legacy FLE values (FLE:1:<b64>, no AAD) are rejected by default (ALLOW_LEGACY_FLE=False).
    During the migration window (ALLOW_LEGACY_FLE=True), the ORM can read them and the batch
    migration re-encrypts them to AAD-bound format.
    After migration, legacy rows read cleanly without the flag.
    """
    from backend.app.core import config as cfg_module

    user_id = str(uuid.uuid4())
    legacy_name = "Perumal Swamy"
    legacy_phone = "9776655443"

    # Encrypt without AAD (legacy format FLE:1:<b64>)
    legacy_encrypted_name = encrypt_field(legacy_name, associated_data=None)
    legacy_encrypted_phone = encrypt_field(legacy_phone, associated_data=None)
    assert ":AAD:" not in legacy_encrypted_name
    assert legacy_encrypted_name.startswith("FLE:1:")

    async with AsyncSessionLocal() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, full_name, phone_number, role, preferred_language, is_active, created_at, updated_at)
                VALUES (:uid, :email, 'hash', :name, :phone, 'CITIZEN', 'ta', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """),
            {"uid": user_id, "email": f"legacy_fle_{uuid.uuid4().hex[:6]}@example.com", "name": legacy_encrypted_name, "phone": legacy_encrypted_phone}
        )
        await session.commit()

    # 1. Without the flag, ORM must raise (fail-closed / default behaviour)
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        assert user is not None
        with pytest.raises(ValueError, match="Legacy FLE ciphertext"):
            _ = user.full_name

    # 2. With ALLOW_LEGACY_FLE=True (migration window), ORM reads cleanly
    monkeypatch.setattr(cfg_module.settings, "ALLOW_LEGACY_FLE", True)
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        assert user is not None
        assert user.full_name == legacy_name
        assert user.phone_number == legacy_phone

    # 3. Batch migration re-encrypts legacy rows to AAD-bound format
    async with AsyncSessionLocal() as session:
        stats = await migrate_plaintext_rows_to_encryption(session)
        assert stats["users_reencrypted"] >= 1

    # 4. After migration, raw DB row carries :AAD: tag
    async with AsyncSessionLocal() as session:
        raw_name = (await session.execute(
            text("SELECT full_name FROM users WHERE id = :uid"), {"uid": user_id}
        )).scalar()
        assert ":AAD:" in raw_name

    # 5. After migration, ORM reads cleanly WITHOUT the flag (flag restored to False by monkeypatch)
    monkeypatch.setattr(cfg_module.settings, "ALLOW_LEGACY_FLE", False)
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        assert user is not None
        assert user.full_name == legacy_name

