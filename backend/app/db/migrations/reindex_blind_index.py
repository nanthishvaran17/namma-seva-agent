"""
Reindex utility for Phone Blind Indexes during BLIND_INDEX_KEY rotation.

When rotating BLIND_INDEX_KEY:
1. Register the new key version (e.g., version "2") in the keyring or update BLIND_INDEX_KEY in .env.
2. Run this utility: it iterates over all users, decrypts phone_number using FLE,
   recomputes phone_blind_index using the new key, and updates the database.
3. Once completed, queries looking up users by phone will use the rotated key.
"""

import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.core.crypto import compute_phone_blind_index

logger = logging.getLogger(__name__)

async def reindex_all_phone_blind_indexes(session: AsyncSession, key_version: str = "1") -> dict:
    """
    Recomputes and updates phone_blind_index for all users using the specified blind index key version.
    """
    result = await session.execute(select(User))
    users = result.scalars().all()
    
    reindexed_count = 0
    skipped_count = 0

    for user in users:
        # user.phone_number is transparently decrypted by EncryptedString
        plain_phone = user.phone_number
        if plain_phone:
            new_blind_index = compute_phone_blind_index(plain_phone, key_version=key_version)
            user.phone_blind_index = new_blind_index
            reindexed_count += 1
        else:
            skipped_count += 1

    await session.commit()
    logger.info(
        "Blind index reindexing complete: %d users updated, %d skipped using key version '%s'",
        reindexed_count, skipped_count, key_version
    )
    return {
        "reindexed_count": reindexed_count,
        "skipped_count": skipped_count,
        "key_version": key_version
    }
