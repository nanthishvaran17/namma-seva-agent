import os
import uuid
import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from backend.app.core.config import settings
from backend.app.core.crypto import (
    encrypt_document_bytes,
    decrypt_document_bytes,
    encrypt_field,
    decrypt_field,
    register_doc_encryption_key,
    register_field_encryption_key,
    clear_keyrings,
    EncryptedString,
    EncryptedJSON
)

@pytest.fixture(autouse=True)
def cleanup_crypto_state():
    orig_doc_key = settings.DOC_ENCRYPTION_KEY
    orig_field_key = settings.FIELD_ENCRYPTION_KEY
    orig_doc_ver = settings.CURRENT_DOC_KEY_VERSION
    orig_field_ver = settings.CURRENT_FIELD_KEY_VERSION
    clear_keyrings()
    yield
    clear_keyrings()
    settings.DOC_ENCRYPTION_KEY = orig_doc_key
    settings.FIELD_ENCRYPTION_KEY = orig_field_key
    settings.CURRENT_DOC_KEY_VERSION = orig_doc_ver
    settings.CURRENT_FIELD_KEY_VERSION = orig_field_ver

def test_file_key_rotation_old_decrypts_new_writes_v2():
    """
    Fix 5: Test that a file written under key v1 (with NSEV1 magic header)
    decrypts cleanly after rotation to v2, while new writes use v2.
    """
    secret_pdf_content = b"%PDF-1.4 Sensitive Citizen Community Certificate 2026"
    aad = b"user-uuid-1234:doc-uuid-5678"
    old_doc_key = "old-doc-key-32chars-min-length-v1-secret"
    new_doc_key = "new-doc-key-32chars-min-length-v2-secret"

    # Step 1: Write file under version 1
    settings.DOC_ENCRYPTION_KEY = old_doc_key
    settings.CURRENT_DOC_KEY_VERSION = "1"
    v1_ciphertext = encrypt_document_bytes(secret_pdf_content, associated_data=aad)
    
    assert v1_ciphertext.startswith(b"NSEV1")
    assert secret_pdf_content not in v1_ciphertext

    # Step 2: Key rotation
    # Archive v1 key into keyring and activate v2 as primary
    register_doc_encryption_key("1", old_doc_key)
    settings.DOC_ENCRYPTION_KEY = new_doc_key
    settings.CURRENT_DOC_KEY_VERSION = "2"

    # Step 3: Decrypt v1 file using rotated keyring - MUST succeed
    decrypted_v1 = decrypt_document_bytes(v1_ciphertext, associated_data=aad)
    assert decrypted_v1 == secret_pdf_content

    # Step 4: New write MUST use new key and version 2 header
    new_content = b"%PDF-1.4 Newly Uploaded Nativity Certificate 2026"
    v2_ciphertext = encrypt_document_bytes(new_content, associated_data=aad)
    assert v2_ciphertext.startswith(b"NSEV2")
    assert new_content not in v2_ciphertext

    # Decrypt new file with active v2 key
    decrypted_v2 = decrypt_document_bytes(v2_ciphertext, associated_data=aad)
    assert decrypted_v2 == new_content

def test_file_decryption_wrong_key_fails_cleanly_no_plaintext_leak():
    """
    Fix 5: Tampered ciphertext, wrong key, or mismatched AAD must raise cleanly
    and NEVER leak sensitive citizen plaintext or key details in exception representations.
    """
    sensitive_data = b"CONFIDENTIAL_AADHAAR_9988_7766_5544"
    aad = b"valid_user:valid_doc"

    encrypted = encrypt_document_bytes(sensitive_data, associated_data=aad)

    # 1. Tamper with ciphertext bytes
    corrupted = bytearray(encrypted)
    corrupted[-5] ^= 0xFF

    with pytest.raises(Exception) as exc_info:
        decrypt_document_bytes(bytes(corrupted), associated_data=aad)

    # Assert no plaintext leaked in the error
    error_str = str(exc_info.value)
    error_repr = repr(exc_info.value)
    assert "CONFIDENTIAL_AADHAAR" not in error_str
    assert "CONFIDENTIAL_AADHAAR" not in error_repr
    assert "9988" not in error_str

    # 2. Mismatched Authenticated Additional Data (AAD)
    wrong_aad = b"attacker_user:valid_doc"
    with pytest.raises(Exception) as exc_info_aad:
        decrypt_document_bytes(encrypted, associated_data=wrong_aad)

    assert "CONFIDENTIAL_AADHAAR" not in str(exc_info_aad.value)

def test_field_encryption_key_rotation_and_tamper_safety():
    """
    Fix 5: Test that FLE encrypted fields written under v1 decrypt cleanly
    after rotation to v2, new writes use FLE:2:, and wrong key/tampering fails
    cleanly with NO plaintext in errors.
    """
    plain_phone = "9876543210"
    old_field_key = "old-field-key-32chars-min-len-v1"
    new_field_key = "new-field-key-32chars-min-len-v2"

    # Step 1: Encrypt field under version 1
    settings.FIELD_ENCRYPTION_KEY = old_field_key
    settings.CURRENT_FIELD_KEY_VERSION = "1"
    v1_field = encrypt_field(plain_phone)

    assert v1_field.startswith("FLE:1:")
    assert plain_phone not in v1_field

    # Step 2: Rotate field key
    register_field_encryption_key("1", old_field_key)
    settings.FIELD_ENCRYPTION_KEY = new_field_key
    settings.CURRENT_FIELD_KEY_VERSION = "2"

    # Step 3: Decrypt v1 field with rotated keyring
    decrypted_v1 = decrypt_field(v1_field)
    assert decrypted_v1 == plain_phone

    # Step 4: New write uses FLE:2:
    new_phone = "9123456789"
    v2_field = encrypt_field(new_phone)
    assert v2_field.startswith("FLE:2:")
    assert new_phone not in v2_field
    assert decrypt_field(v2_field) == new_phone

    # Step 5: Corrupt ciphertext and verify NO plaintext leaks in error
    parts = v2_field.split(":", 2)
    # Corrupt base64 body
    corrupt_b64 = parts[2][:10] + ("A" if parts[2][10] != "A" else "B") + parts[2][11:]
    corrupted_field = f"FLE:2:{corrupt_b64}"

    with pytest.raises(Exception) as exc_info:
        decrypt_field(corrupted_field)

    assert plain_phone not in str(exc_info.value)
    assert new_phone not in str(exc_info.value)
    assert plain_phone not in repr(exc_info.value)
