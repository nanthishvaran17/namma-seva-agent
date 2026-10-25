import os
import re
import json
import base64
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.types import TypeDecorator, Text
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# 5-byte file header prefix to identify encrypted files and prevent double-encryption
ENCRYPTED_FILE_MAGIC = b"NSEV1"  # Default v1 magic header for backwards compatibility
FILE_MAGIC_PREFIX = b"NSEV"
NONCE_SIZE_BYTES = 12

# In-memory keyring registries for graceful zero-downtime key rotation
_DOC_KEY_RING: Dict[str, bytes] = {}
_FIELD_KEY_RING: Dict[str, bytes] = {}
_BLIND_INDEX_KEY_RING: Dict[str, bytes] = {}

def register_doc_encryption_key(version: str, key_str: str) -> None:
    """Registers an older or rotated document encryption key in the keyring."""
    v_clean = version.replace("v", "")
    _DOC_KEY_RING[v_clean] = hashlib.sha256(key_str.encode("utf-8")).digest()

def register_field_encryption_key(version: str, key_str: str) -> None:
    """Registers an older or rotated field encryption key in the keyring."""
    v_clean = version.replace("v", "")
    _FIELD_KEY_RING[v_clean] = hashlib.sha256(key_str.encode("utf-8")).digest()

def register_blind_index_key(version: str, key_str: str) -> None:
    """Registers an older or rotated blind index key in the keyring."""
    v_clean = version.replace("v", "")
    _BLIND_INDEX_KEY_RING[v_clean] = hashlib.sha256(key_str.encode("utf-8")).digest()

def clear_keyrings() -> None:
    """Clears all dynamically registered rotation keys (useful for test isolation)."""
    _DOC_KEY_RING.clear()
    _FIELD_KEY_RING.clear()
    _BLIND_INDEX_KEY_RING.clear()

def _derive_doc_key() -> bytes:
    """Derives a deterministic 256-bit (32-byte) binary key from settings.DOC_ENCRYPTION_KEY."""
    key_str = settings.DOC_ENCRYPTION_KEY or "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    return hashlib.sha256(key_str.encode("utf-8")).digest()

def _derive_field_key() -> bytes:
    """Derives a deterministic 256-bit (32-byte) binary key from settings.FIELD_ENCRYPTION_KEY."""
    key_str = settings.FIELD_ENCRYPTION_KEY or "field-sec-0123456789abcdef0123456789abcdef0123456789abcdef"
    return hashlib.sha256(key_str.encode("utf-8")).digest()

def get_current_doc_key_version() -> str:
    return getattr(settings, "CURRENT_DOC_KEY_VERSION", "1")

def get_current_field_key_version() -> str:
    return getattr(settings, "CURRENT_FIELD_KEY_VERSION", "1")

def get_current_blind_index_key_version() -> str:
    return getattr(settings, "CURRENT_BLIND_INDEX_KEY_VERSION", "1")

def get_doc_key(version: str = "1") -> bytes:
    """Retrieves document key by version tag ('1', '2', etc.), consulting keyring for rotation."""
    v_clean = version.replace("v", "")
    if v_clean in _DOC_KEY_RING:
        return _DOC_KEY_RING[v_clean]
    if v_clean == get_current_doc_key_version().replace("v", "") or v_clean == "1":
        return _derive_doc_key()
    raise ValueError(f"Unknown document encryption key version '{version}' - no key found in keyring for rotation")

def get_field_key(version: str = "1") -> bytes:
    """Retrieves field key by version tag ('1', '2', etc.), consulting keyring for rotation."""
    v_clean = version.replace("v", "")
    if v_clean in _FIELD_KEY_RING:
        return _FIELD_KEY_RING[v_clean]
    if v_clean == get_current_field_key_version().replace("v", "") or v_clean == "1":
        return _derive_field_key()
    raise ValueError(f"Unknown field encryption key version '{version}' - no key found in keyring for rotation")

def get_blind_index_key(version: str = "1") -> bytes:
    """Retrieves blind index key by version tag ('1', '2', etc.), consulting keyring for rotation."""
    v_clean = version.replace("v", "")
    if v_clean in _BLIND_INDEX_KEY_RING:
        return _BLIND_INDEX_KEY_RING[v_clean]
    if v_clean == get_current_blind_index_key_version().replace("v", "") or v_clean == "1":
        key_str = settings.BLIND_INDEX_KEY or "blind-sec-0123456789abcdef0123456789abcdef0123456789abcdef"
        return hashlib.sha256(key_str.encode("utf-8")).digest()
    raise ValueError(f"Unknown blind index key version '{version}' - no key found in keyring for rotation")

# ---------------------------------------------------------------------------
# File-Level Encryption (AES-256-GCM + AAD Binding + Key Rotation Header)
# ---------------------------------------------------------------------------

def encrypt_document_bytes(
    plaintext: bytes,
    associated_data: Optional[bytes] = None,
    key_version: Optional[str] = None
) -> bytes:
    """
    Encrypts arbitrary document bytes using AES-256-GCM with a fresh random 12-byte nonce per file.
    Binds Authenticated Additional Data (AAD) e.g. f"{user_id}:{document_id}".
    Output binary format: [4-byte 'NSEV' + 1-byte version] + [12-byte nonce] + [ciphertext + 16-byte auth tag].
    """
    if not plaintext:
        return b""

    ver = key_version or get_current_doc_key_version()
    v_clean = ver.replace("v", "")
    key = get_doc_key(v_clean)
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_SIZE_BYTES)
    
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    header = FILE_MAGIC_PREFIX + v_clean[:1].encode("ascii")
    return header + nonce + ciphertext

def decrypt_document_bytes(
    payload: bytes,
    associated_data: Optional[bytes] = None
) -> bytes:
    """
    Decrypts document bytes previously encrypted with encrypt_document_bytes.
    Extracts key version from header and supports older keys during rotation.
    Verifies authentication tag and bound associated data (AAD).
    If payload is not encrypted (e.g. legacy plain file), returns original payload.
    """
    if not payload:
        return b""

    if not is_payload_encrypted(payload):
        # Unencrypted legacy file fallback
        return payload

    # Header is 5 bytes: b"NSEV" + 1-byte version
    version_char = chr(payload[4])
    key = get_doc_key(version_char)
    
    prefix_len = len(FILE_MAGIC_PREFIX) + 1
    nonce = payload[prefix_len : prefix_len + NONCE_SIZE_BYTES]
    ciphertext = payload[prefix_len + NONCE_SIZE_BYTES :]

    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, associated_data)

def is_payload_encrypted(payload: bytes) -> bool:
    """Checks whether binary data begins with the Namma Seva encryption magic header prefix."""
    return bool(payload and payload.startswith(FILE_MAGIC_PREFIX) and len(payload) >= (len(FILE_MAGIC_PREFIX) + 1 + NONCE_SIZE_BYTES + 16))

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

# ---------------------------------------------------------------------------
# Field-Level Encryption (AES-256-GCM + Blind Index)
# ---------------------------------------------------------------------------

def encrypt_field(plaintext: str, key_version: Optional[str] = None) -> str:
    """
    Encrypts a field string using AES-256-GCM with a fresh random nonce.
    Format: FLE:<version>:<urlsafe_base64(nonce + ciphertext + tag)>
    """
    if plaintext is None:
        return None
    if not plaintext:
        return ""

    ver = key_version or get_current_field_key_version()
    v_clean = ver.replace("v", "")
    key = get_field_key(v_clean)
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_SIZE_BYTES)
    ciphertext = aesgcm.encrypt(nonce, str(plaintext).encode("utf-8"), None)
    encoded = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return f"FLE:{v_clean}:{encoded}"

def decrypt_field(ciphertext_str: str) -> str:
    """
    Decrypts an FLE encrypted field string.
    If the string does not have the 'FLE:' prefix, returns it as-is for backwards compatibility.
    """
    if ciphertext_str is None:
        return None
    if not isinstance(ciphertext_str, str) or not ciphertext_str.startswith("FLE:"):
        return ciphertext_str

    parts = ciphertext_str.split(":", 2)
    if len(parts) != 3:
        return ciphertext_str

    version_tag = parts[1]
    b64_payload = parts[2]
    try:
        raw = base64.urlsafe_b64decode(b64_payload.encode("ascii"))
        nonce = raw[:NONCE_SIZE_BYTES]
        ciphertext = raw[NONCE_SIZE_BYTES:]
        key = get_field_key(version_tag)
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode("utf-8")
    except Exception as e:
        logger.error("Failed to decrypt field with version %s: %s", version_tag, e)
        raise

def compute_phone_blind_index(
    phone: Optional[str],
    key_version: str = "1",
    key_override: Optional[bytes] = None
) -> Optional[str]:
    """
    Generates a deterministic HMAC-SHA256 blind index for exact phone lookups using BLIND_INDEX_KEY.
    Normalizes input by stripping formatting and canonicalizing to 91XXXXXXXXXX.
    Database queries can search on phone_blind_index without storing plaintext phone numbers.
    """
    if not phone:
        return None
    clean = re.sub(r"\D", "", str(phone).strip())
    if not clean:
        return None
    # Canonicalize Indian 10-digit mobile number with 91 prefix
    if len(clean) == 10:
        clean = "91" + clean

    v_clean = key_version.replace("v", "")
    key = key_override if key_override is not None else get_blind_index_key(v_clean)
    return hmac.new(key, f"phone_blind_index:{clean}".encode("utf-8"), hashlib.sha256).hexdigest()

def compute_deletion_user_hash(user_id: str, pepper_override: Optional[str] = None) -> str:
    """
    Computes an HMAC-SHA256 digest of user_id with settings.DELETION_PEPPER.
    A plain SHA-256 allows brute-force recovery if user IDs are short or sequential.
    The pepper makes unauthorized reversal or guessing infeasible without the pepper secret.
    """
    pepper = pepper_override or settings.DELETION_PEPPER or "pepper-sec-0123456789abcdef0123456789abcdef0123456789abcdef"
    return hmac.new(
        key=pepper.encode("utf-8"),
        msg=f"deletion_receipt:{user_id}".encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

def compute_deletion_receipt_signature(
    receipt_id: str,
    user_id_hash: str,
    timestamp_iso: str,
    pepper_override: Optional[str] = None
) -> str:
    """Computes an HMAC-SHA256 signature validating the authenticity of a deletion receipt."""
    pepper = pepper_override or settings.DELETION_PEPPER or "pepper-sec-0123456789abcdef0123456789abcdef0123456789abcdef"
    msg = f"{receipt_id}:{user_id_hash}:{timestamp_iso}".encode("utf-8")
    return hmac.new(key=pepper.encode("utf-8"), msg=msg, digestmod=hashlib.sha256).hexdigest()

# ---------------------------------------------------------------------------
# SQLAlchemy Custom TypeDecorators for Seamless Model Encryption
# ---------------------------------------------------------------------------

class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that encrypts strings with AES-256-GCM before writing to DB,
    and decrypts them transparently on load.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_field(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_field(value)

class EncryptedJSON(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that serializes dictionaries/lists to JSON, encrypts with AES-256-GCM,
    and deserializes on load.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        serialized = json.dumps(value)
        return encrypt_field(serialized)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        plain_str = decrypt_field(value)
        if not plain_str:
            return {}
        try:
            return json.loads(plain_str)
        except Exception:
            return {}
