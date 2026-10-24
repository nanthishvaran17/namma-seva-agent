import os
import base64
import hashlib
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from backend.app.core.config import settings

# 5-byte file header to identify encrypted files and prevent double-encryption
ENCRYPTED_FILE_MAGIC = b"NSEV1"
NONCE_SIZE_BYTES = 12

def _derive_aes_key() -> bytes:
    """
    Derives a deterministic 256-bit (32-byte) binary key from settings.DOC_ENCRYPTION_KEY.
    Uses SHA-256 to ensure exactly 32 bytes regardless of whether string is raw passphrase, hex, or base64.
    """
    key_str = settings.DOC_ENCRYPTION_KEY
    if not key_str:
        # Fallback for testing/dev
        key_str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    return hashlib.sha256(key_str.encode("utf-8")).digest()

def encrypt_document_bytes(plaintext: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """
    Encrypts arbitrary document bytes using AES-256-GCM with a fresh random 12-byte nonce per file.
    Output binary format: [5-byte magic 'NSEV1'] + [12-byte nonce] + [ciphertext + 16-byte auth tag].
    """
    if not plaintext:
        return b""

    key = _derive_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_SIZE_BYTES)
    
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return ENCRYPTED_FILE_MAGIC + nonce + ciphertext

def decrypt_document_bytes(payload: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """
    Decrypts document bytes previously encrypted with encrypt_document_bytes.
    Verifies authentication tag and magic header.
    If the payload is not encrypted (e.g. legacy plain file), returns original payload.
    """
    if not payload:
        return b""

    if not payload.startswith(ENCRYPTED_FILE_MAGIC):
        # Unencrypted legacy file fallback
        return payload

    prefix_len = len(ENCRYPTED_FILE_MAGIC)
    nonce = payload[prefix_len : prefix_len + NONCE_SIZE_BYTES]
    ciphertext = payload[prefix_len + NONCE_SIZE_BYTES :]

    key = _derive_aes_key()
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, associated_data)

def is_payload_encrypted(payload: bytes) -> bool:
    """Checks whether binary data begins with the Namma Seva encryption magic header."""
    return payload.startswith(ENCRYPTED_FILE_MAGIC)

def encrypt_string(plaintext: str) -> str:
    """Encrypts a string and returns a URL-safe Base64 encoded string."""
    if not plaintext:
        return ""
    encrypted = encrypt_document_bytes(plaintext.encode("utf-8"))
    return base64.urlsafe_b64encode(encrypted).decode("utf-8")

def decrypt_string(ciphertext_b64: str) -> str:
    """Decrypts a URL-safe Base64 encoded string back to plaintext."""
    if not ciphertext_b64:
        return ""
    try:
        raw_encrypted = base64.urlsafe_b64decode(ciphertext_b64.encode("utf-8"))
        decrypted_bytes = decrypt_document_bytes(raw_encrypted)
        return decrypted_bytes.decode("utf-8")
    except Exception:
        # If unencrypted legacy string
        return ciphertext_b64
