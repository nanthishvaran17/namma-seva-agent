import logging
import json
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.app.core.crypto import (
    encrypt_field,
    decrypt_field,
    compute_phone_blind_index,
    compute_field_aad
)

logger = logging.getLogger(__name__)

async def migrate_plaintext_rows_to_encryption(session: AsyncSession) -> Dict[str, Any]:
    """
    Scans existing database rows and migrates legacy unencrypted plaintext values
    and legacy un-bound FLE values to AES-256-GCM field-level encryption with AAD binding
    (table:column:row_id) and blind indexing.
    Safe and idempotent: rows already encrypted with AAD ('FLE:<version>:AAD:') are skipped.
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
        aad_name = compute_field_aad("users", "full_name", str(uid))
        if raw_name and ":AAD:" not in str(raw_name):
            try:
                plain_name = decrypt_field(raw_name, associated_data=aad_name)
                new_name = encrypt_field(plain_name, associated_data=aad_name)
                needs_update = True
            except Exception as e:
                logger.warning("Could not decrypt user %s full_name during migration: %s", uid, e)

        new_phone = raw_phone
        plain_phone_for_index = None
        aad_phone = compute_field_aad("users", "phone_number", str(uid))
        if raw_phone and ":AAD:" not in str(raw_phone):
            try:
                plain_phone_for_index = decrypt_field(raw_phone, associated_data=aad_phone)
                new_phone = encrypt_field(plain_phone_for_index, associated_data=aad_phone)
                needs_update = True
            except Exception as e:
                logger.warning("Could not decrypt user %s phone_number during migration: %s", uid, e)

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

        aad_extracted = compute_field_aad("user_documents", "extracted_fields", str(did))
        new_extracted = raw_extracted
        if raw_extracted and ":AAD:" not in str(raw_extracted):
            plain_str = decrypt_field(raw_extracted, associated_data=aad_extracted) if isinstance(raw_extracted, str) and raw_extracted.startswith("FLE:") else raw_extracted
            payload_str = plain_str if isinstance(plain_str, str) else json.dumps(plain_str)
            new_extracted = encrypt_field(payload_str, associated_data=aad_extracted)
            needs_update = True

        aad_corrections = compute_field_aad("user_documents", "user_corrections", str(did))
        new_corrections = raw_corrections
        if raw_corrections and ":AAD:" not in str(raw_corrections):
            plain_str = decrypt_field(raw_corrections, associated_data=aad_corrections) if isinstance(raw_corrections, str) and raw_corrections.startswith("FLE:") else raw_corrections
            payload_str = plain_str if isinstance(plain_str, str) else json.dumps(plain_str)
            new_corrections = encrypt_field(payload_str, associated_data=aad_corrections)
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
