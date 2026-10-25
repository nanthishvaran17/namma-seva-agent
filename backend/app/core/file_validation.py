import os
import re
from typing import Optional, Tuple

ALLOWED_EXTENSIONS_BY_TYPE = {
    "pdf": {".pdf"},
    "jpeg": {".jpg", ".jpeg"},
    "png": {".png"},
    "webp": {".webp"}
}

ALLOWED_MIME_BY_TYPE = {
    "pdf": "application/pdf",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp"
}

def detect_file_type_from_magic_bytes(data: bytes) -> Optional[str]:
    """
    Inspects leading binary bytes to determine true file type.
    Rejects spoofed extensions and corrupt files.
    """
    if not data or len(data) < 12:
        return None
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    return None

def sanitize_filename(filename: str) -> str:
    """
    Guards against path traversal attacks (../../etc/passwd, absolute paths, null bytes).
    Extracts base filename and removes dangerous filesystem characters.
    """
    if not filename:
        return "document"
    # Normalize backslashes so path traversal stripping works consistently across Windows and Linux
    normalized = filename.replace("\\", "/")
    base = os.path.basename(normalized)
    # Remove traversal sequences and forbidden characters
    cleaned = re.sub(r'[\x00/\\:\*\?"<>\|]', '_', base)
    cleaned = cleaned.replace("..", "_")
    cleaned = cleaned.strip(" ._")
    return cleaned or "document"

def validate_uploaded_file(content: bytes, raw_filename: str, declared_mime: str) -> Tuple[str, str, str]:
    """
    Validates uploaded document content against rigorous security rules:
    1. Detects true format from binary magic bytes
    2. Enforces that declared MIME type matches detected format
    3. Enforces that filename extension strictly matches detected magic bytes
    4. Sanitizes filename against path traversal
    
    Returns:
        (detected_type, canonical_extension, sanitized_filename)
        
    Raises:
        ValueError with descriptive error message if validation fails.
    """
    # 1. Inspect magic bytes
    detected_type = detect_file_type_from_magic_bytes(content)
    if not detected_type:
        raise ValueError(
            "Security validation error: File magic bytes do not match any permitted document format. "
            "Only authentic PDF, PNG, JPEG, and WebP files are accepted."
        )

    # 2. Check declared MIME vs detected magic bytes
    expected_mime = ALLOWED_MIME_BY_TYPE[detected_type]
    if detected_type == "jpeg" and declared_mime in {"image/jpeg", "image/jpg"}:
        pass
    elif declared_mime != expected_mime:
        raise ValueError(
            f"Security validation error: Declared MIME type '{declared_mime}' does not match "
            f"binary file content '{expected_mime}' (content-type spoofing detected)."
        )

    # 3. Check filename extension vs detected magic bytes
    sanitized = sanitize_filename(raw_filename)
    ext = os.path.splitext(sanitized)[1].lower()
    allowed_exts = ALLOWED_EXTENSIONS_BY_TYPE[detected_type]
    if ext not in allowed_exts:
        raise ValueError(
            f"Security validation error: File extension '{ext}' does not match detected format '{detected_type}'. "
            f"Allowed extensions for {detected_type.upper()}: {', '.join(sorted(allowed_exts))}."
        )

    canonical_ext = ".jpg" if ext == ".jpg" else f".{detected_type}"
    return detected_type, canonical_ext, sanitized
