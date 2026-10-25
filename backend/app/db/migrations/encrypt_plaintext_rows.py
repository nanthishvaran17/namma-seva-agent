import logging
import json
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.app.core.crypto import (
    encrypt_field,
    decrypt_field,
    compute_phone_blind_index
)

logger = logging.getLogger(__name__)

async def migrate_plaintext_rows_to_encryption(session: AsyncSession) -> Dict[str, Any]:
    """
    Scans existing database rows and migrates legacy unencrypted plaintext values
    to AES-256-GCM field-level encryption (FLE) with blind indexing.
    Safe and idempotent: rows already encrypted (prefixed with 'FLE:') are skipped.
    """
    stats = {
        "users_scanned": 0,
        "users_reencrypted": 0,
        "documents_scanned": 0,
        "documents_reencrypted": 0
    }

    # 1. Migrate Users Table
    user_rows = (await session.execute(
        text("SELECT id, full_name, phone_number, phone_blind_index FROM users")
    )).fetchall()

    for row in user_rows:
        uid, raw_name, raw_phone, blind_idx = row[0], row[1], row[2], row[3]
        stats["users_scanned"] += 1
        needs_update = False

        new_name = raw_name
        if raw_name and not str(raw_name).startswith("FLE:"):
            new_name = encrypt_field(raw_name)
            needs_update = True

        new_phone = raw_phone
        plain_phone_for_index = raw_phone
        if raw_phone:
            if not str(raw_phone).startswith("FLE:"):
                new_phone = encrypt_field(raw_phone)
                needs_update = True
            else:
                plain_phone_for_index = decrypt_field(raw_phone)

        new_blind_idx = blind_idx
        if (not blind_idx) and plain_phone_for_index:
            new_blind_idx = compute_phone_blind_index(plain_phone_for_index)
            needs_update = True

        if needs_update:
            await session.execute(
                text("UPDATE users SET full_name = :fn, phone_number = :pn, phone_blind_index = :bi WHERE id = :uid"),
                {"fn": new_name, "pn": new_phone, "bi": new_blind_idx, "uid": uid}
            )
            stats["users_reencrypted"] += 1

    # 2. Migrate User Documents Table (extracted_fields and user_corrections)
    doc_rows = (await session.execute(
        text("SELECT id, extracted_fields, user_corrections FROM user_documents")
    )).fetchall()

    for row in doc_rows:
        did, raw_extracted, raw_corrections = row[0], row[1], row[2]
        stats["documents_scanned"] += 1
        needs_update = False

        new_extracted = raw_extracted
        if raw_extracted and not str(raw_extracted).startswith("FLE:"):
            payload_str = raw_extracted if isinstance(raw_extracted, str) else json.dumps(raw_extracted)
            new_extracted = encrypt_field(payload_str)
            needs_update = True

        new_corrections = raw_corrections
        if raw_corrections and not str(raw_corrections).startswith("FLE:"):
            payload_str = raw_corrections if isinstance(raw_corrections, str) else json.dumps(raw_corrections)
            new_corrections = encrypt_field(payload_str)
            needs_update = True

        if needs_update:
            await session.execute(
                text("UPDATE user_documents SET extracted_fields = :ef, user_corrections = :uc WHERE id = :did"),
                {"ef": new_extracted, "uc": new_corrections, "did": did}
            )
            stats["documents_reencrypted"] += 1

    await session.commit()
    logger.info("Field-level encryption migration complete: %s", stats)
    return stats
