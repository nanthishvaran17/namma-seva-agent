import hashlib
import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings
from backend.app.core.crypto import (
    compute_deletion_user_hash,
    compute_deletion_receipt_signature,
    compute_phone_blind_index
)

def test_deletion_user_hash_requires_pepper():
    """
    Fix 1: Deletion receipt user_id_hash must be HMAC-SHA256 with a dedicated pepper.
    Plain SHA-256 allows dictionary attacks/rainbow tables on sequential or short IDs.
    """
    user_id = "citizen-user-uuid-12345"
    pepper_1 = "pepper_key_one_32chars_minimum_length_prod!"
    pepper_2 = "pepper_key_two_32chars_minimum_length_prod!"

    hash_with_pepper_1 = compute_deletion_user_hash(user_id, pepper_override=pepper_1)
    hash_with_pepper_2 = compute_deletion_user_hash(user_id, pepper_override=pepper_2)
    plain_sha256 = hashlib.sha256(user_id.encode("utf-8")).hexdigest()

    # Peppered hash must NOT match plain SHA-256
    assert hash_with_pepper_1 != plain_sha256
    assert hash_with_pepper_2 != plain_sha256
    
    # Different peppers must produce completely different hashes
    assert hash_with_pepper_1 != hash_with_pepper_2

    # Receipt signature requires pepper as well
    sig_1 = compute_deletion_receipt_signature("rcpt-1", hash_with_pepper_1, "2026-10-25T10:00:00Z", pepper_override=pepper_1)
    sig_2 = compute_deletion_receipt_signature("rcpt-1", hash_with_pepper_1, "2026-10-25T10:00:00Z", pepper_override=pepper_2)
    assert sig_1 != sig_2

def test_production_startup_fails_if_pepper_missing_or_short():
    """Fix 1: Production startup fails if DELETION_PEPPER is missing or under 32 chars."""
    with pytest.raises((ValueError, ValidationError), match="DELETION_PEPPER is missing, insecure, or under 32 characters"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="min32chars_secure_secret_key_prod_test!",
            DOC_ENCRYPTION_KEY="min32chars_secure_doc_key_prod_test!",
            FIELD_ENCRYPTION_KEY="min32chars_field_encryption_key_prod!",
            BLIND_INDEX_KEY="min32chars_blind_index_key_prod_test!",
            DELETION_PEPPER="",  # Missing
            WHATSAPP_VERIFY_TOKEN="custom_prod_verify_token_12345",
            WHATSAPP_APP_SECRET="min16charsappsecret!"
        )

def test_production_startup_fails_if_blind_index_key_missing_or_short():
    """Fix 4: Production startup fails if BLIND_INDEX_KEY is missing or under 32 chars."""
    with pytest.raises((ValueError, ValidationError), match="BLIND_INDEX_KEY is missing, insecure, or under 32 characters"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="min32chars_secure_secret_key_prod_test!",
            DOC_ENCRYPTION_KEY="min32chars_secure_doc_key_prod_test!",
            FIELD_ENCRYPTION_KEY="min32chars_field_encryption_key_prod!",
            BLIND_INDEX_KEY="too_short",  # < 32 chars
            DELETION_PEPPER="min32chars_deletion_pepper_prod_test!",
            WHATSAPP_VERIFY_TOKEN="custom_prod_verify_token_12345",
            WHATSAPP_APP_SECRET="min16charsappsecret!"
        )

def test_production_startup_fails_if_any_keys_shared_pairwise():
    """Fix 1 & 4: Strict 5-way pairwise key separation enforced at startup in production."""
    base_keys = {
        "SECRET_KEY": "key_one_32chars_minimum_length_prod_alpha!",
        "DOC_ENCRYPTION_KEY": "key_two_32chars_minimum_length_prod_beta!!",
        "FIELD_ENCRYPTION_KEY": "key_three_32chars_minimum_length_prod_gamma",
        "BLIND_INDEX_KEY": "key_four_32chars_minimum_length_prod_delta",
        "DELETION_PEPPER": "key_five_32chars_minimum_length_prod_epsilon"
    }

    # Test collision: DELETION_PEPPER == SECRET_KEY
    collision_1 = dict(base_keys)
    collision_1["DELETION_PEPPER"] = collision_1["SECRET_KEY"]
    with pytest.raises(ValueError, match="Key separation violation"):
        Settings(_env_file=None, ENVIRONMENT="production", WHATSAPP_VERIFY_TOKEN="tok123", WHATSAPP_APP_SECRET="sec1234567890123", **collision_1)

    # Test collision: BLIND_INDEX_KEY == FIELD_ENCRYPTION_KEY
    collision_2 = dict(base_keys)
    collision_2["BLIND_INDEX_KEY"] = collision_2["FIELD_ENCRYPTION_KEY"]
    with pytest.raises(ValueError, match="Key separation violation"):
        Settings(_env_file=None, ENVIRONMENT="production", WHATSAPP_VERIFY_TOKEN="tok123", WHATSAPP_APP_SECRET="sec1234567890123", **collision_2)

    # Test collision: BLIND_INDEX_KEY == DELETION_PEPPER
    collision_3 = dict(base_keys)
    collision_3["BLIND_INDEX_KEY"] = collision_3["DELETION_PEPPER"]
    with pytest.raises(ValueError, match="Key separation violation"):
        Settings(_env_file=None, ENVIRONMENT="production", WHATSAPP_VERIFY_TOKEN="tok123", WHATSAPP_APP_SECRET="sec1234567890123", **collision_3)

    # Test collision: DOC_ENCRYPTION_KEY == BLIND_INDEX_KEY
    collision_4 = dict(base_keys)
    collision_4["DOC_ENCRYPTION_KEY"] = collision_4["BLIND_INDEX_KEY"]
    with pytest.raises(ValueError, match="Key separation violation"):
        Settings(_env_file=None, ENVIRONMENT="production", WHATSAPP_VERIFY_TOKEN="tok123", WHATSAPP_APP_SECRET="sec1234567890123", **collision_4)

    # All 5 strictly distinct keys succeed
    valid_settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        WHATSAPP_VERIFY_TOKEN="tok123",
        WHATSAPP_APP_SECRET="sec1234567890123",
        **base_keys
    )
    assert valid_settings.DELETION_PEPPER != valid_settings.SECRET_KEY
    assert valid_settings.BLIND_INDEX_KEY != valid_settings.FIELD_ENCRYPTION_KEY
