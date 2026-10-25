"""
Tests for ALLOW_LEGACY_FLE fail-closed enforcement.

Item 1 of final Wave-1 hardening commits.
"""
import os
import pytest
from unittest.mock import patch
from backend.app.core.crypto import encrypt_field, decrypt_field, compute_field_aad


def _make_legacy_ciphertext(plaintext: str) -> str:
    """Produce a real FLE ciphertext WITHOUT AAD (legacy format: FLE:<ver>:<b64>)."""
    return encrypt_field(plaintext, associated_data=None)


def _make_aad_ciphertext(plaintext: str, aad: bytes) -> str:
    """Produce a real FLE ciphertext WITH AAD binding (FLE:<ver>:AAD:<b64>)."""
    return encrypt_field(plaintext, associated_data=aad)


# ---------------------------------------------------------------------------
# 1. Default (ALLOW_LEGACY_FLE=False) must reject legacy ciphertext placed
#    into a bound column (caller supplies associated_data).
# ---------------------------------------------------------------------------

def test_legacy_ciphertext_rejected_when_aad_expected():
    """
    Legacy FLE value in a now-AAD-bound column must raise ValueError when
    ALLOW_LEGACY_FLE is False (the default / production default).
    """
    legacy = _make_legacy_ciphertext("sensitive-value")
    assert legacy.startswith("FLE:"), "Precondition: legacy ciphertext must be FLE-prefixed"
    assert ":AAD:" not in legacy, "Precondition: legacy ciphertext must NOT carry AAD marker"

    aad = compute_field_aad("users", "full_name", "some-row-uuid")
    # settings.ALLOW_LEGACY_FLE defaults to False
    with pytest.raises(ValueError, match="Legacy FLE ciphertext"):
        decrypt_field(legacy, associated_data=aad)


def test_legacy_ciphertext_without_aad_still_decrypts_normally():
    """
    Legacy FLE value read without associated_data (unbound column or old path)
    must still decrypt successfully; the flag only blocks the downgrade path.
    """
    plaintext = "hello-legacy"
    legacy = _make_legacy_ciphertext(plaintext)
    result = decrypt_field(legacy, associated_data=None)
    assert result == plaintext


def test_aad_bound_ciphertext_decrypts_normally():
    """AAD-bound ciphertext must decrypt with correct AAD under any flag state."""
    aad = compute_field_aad("users", "full_name", "row-123")
    ct = _make_aad_ciphertext("my-name", aad)
    assert ":AAD:" in ct, "Precondition: must carry AAD marker"
    result = decrypt_field(ct, associated_data=aad)
    assert result == "my-name"


# ---------------------------------------------------------------------------
# 2. With ALLOW_LEGACY_FLE=True (migration window), legacy ciphertext in a
#    bound column must decrypt (GCM called with aad=None for legacy format).
# ---------------------------------------------------------------------------

def test_legacy_ciphertext_decrypts_with_flag_set(monkeypatch):
    """
    When ALLOW_LEGACY_FLE=True (dev/test migration window only), a legacy FLE
    ciphertext must decrypt even when the caller supplies associated_data.
    """
    plaintext = "legacy-field-value"
    legacy = _make_legacy_ciphertext(plaintext)

    from backend.app.core import config as cfg_module
    monkeypatch.setattr(cfg_module.settings, "ALLOW_LEGACY_FLE", True)

    aad = compute_field_aad("users", "full_name", "row-abc")
    result = decrypt_field(legacy, associated_data=aad)
    assert result == plaintext


# ---------------------------------------------------------------------------
# 3. Production config must not allow ALLOW_LEGACY_FLE=True.
# ---------------------------------------------------------------------------

def test_production_config_rejects_allow_legacy_fle_true():
    """
    ENVIRONMENT=production with ALLOW_LEGACY_FLE=true must raise at Settings
    validation time.
    """
    from pydantic import ValidationError
    from backend.app.core.config import Settings

    env_vars = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "DOC_ENCRYPTION_KEY": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "FIELD_ENCRYPTION_KEY": "ccccccccccccccccccccccccccccccccc",
        "BLIND_INDEX_KEY": "ddddddddddddddddddddddddddddddddd",
        "DELETION_PEPPER": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "WHATSAPP_APP_SECRET": "sixteen_chars_ok",
        "ALLOW_LEGACY_FLE": "true",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        with pytest.raises((ValueError, ValidationError), match="ALLOW_LEGACY_FLE"):
            Settings(_env_file=None)
