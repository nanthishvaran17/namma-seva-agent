import uuid
import pytest
from sqlalchemy import select

from backend.app.core.config import Settings
from backend.app.core.crypto import (
    compute_phone_blind_index,
    register_blind_index_key,
    clear_keyrings
)
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.db.migrations.reindex_blind_index import reindex_all_phone_blind_indexes

@pytest.fixture(autouse=True)
def clean_crypto():
    clear_keyrings()
    yield
    clear_keyrings()

def test_blind_index_key_separation_enforced():
    """
    Fix 4: Confirm BLIND_INDEX_KEY must be distinct from SECRET_KEY,
    DOC_ENCRYPTION_KEY, FIELD_ENCRYPTION_KEY, and DELETION_PEPPER in production.
    """
    valid_key = "a" * 32
    # Attempting to share BLIND_INDEX_KEY with any other key raises ValueError
    with pytest.raises(ValueError, match="Key separation violation"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=valid_key,
            DOC_ENCRYPTION_KEY="b" * 32,
            FIELD_ENCRYPTION_KEY="c" * 32,
            BLIND_INDEX_KEY=valid_key,  # duplicate of SECRET_KEY
            DELETION_PEPPER="d" * 32,
            WHATSAPP_APP_SECRET="e" * 32
        )

@pytest.mark.asyncio
async def test_blind_index_rotation_and_reindexing():
    """
    Fix 4: When BLIND_INDEX_KEY is rotated, reindex_all_phone_blind_indexes
    re-hashes all phone numbers from FLE decrypted User.phone_number and
    enables queries to find users using the new key version.
    """
    test_phone = "9876543210"
    user_id = str(uuid.uuid4())
    email = f"reindex_user_{uuid.uuid4().hex[:6]}@example.com"

    # 1. Create a user under initial key version "1"
    async with AsyncSessionLocal() as session:
        user = User(
            id=user_id,
            email=email,
            hashed_password="dummy_hash_for_test",
            full_name="Rotation Test Citizen",
            phone_number=test_phone,
            phone_blind_index=compute_phone_blind_index(test_phone, key_version="1"),
            role="CITIZEN",
            is_active=True
        )
        session.add(user)
        await session.commit()

    # 2. Verify lookup under version "1" works
    async with AsyncSessionLocal() as session:
        idx_v1 = compute_phone_blind_index(test_phone, key_version="1")
        res = await session.execute(select(User).where(User.phone_blind_index == idx_v1))
        found = res.scalar_one_or_none()
        assert found is not None
        assert found.id == user_id

    # 3. Rotate key: register new key version "2"
    new_rotated_key = "brand-new-rotated-blind-index-key-2026-v2"
    register_blind_index_key("2", new_rotated_key)

    # Prior to reindexing, lookup using version "2" finds NOTHING
    async with AsyncSessionLocal() as session:
        idx_v2 = compute_phone_blind_index(test_phone, key_version="2")
        assert idx_v2 != idx_v1
        res = await session.execute(select(User).where(User.phone_blind_index == idx_v2))
        assert res.scalar_one_or_none() is None

    # 4. Run the reindexing migration
    async with AsyncSessionLocal() as session:
        stats = await reindex_all_phone_blind_indexes(session, key_version="2")
        assert stats["reindexed_count"] >= 1
        assert stats["key_version"] == "2"

    # 5. After reindexing, lookup using version "2" SUCCEEDS!
    async with AsyncSessionLocal() as session:
        idx_v2 = compute_phone_blind_index(test_phone, key_version="2")
        res = await session.execute(select(User).where(User.phone_blind_index == idx_v2))
        found = res.scalar_one_or_none()
        assert found is not None
        assert found.id == user_id
        assert found.phone_number == test_phone
