import os
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.document import UserDocumentModel
from backend.app.core.file_validation import (
    detect_file_type_from_magic_bytes,
    sanitize_filename,
    validate_uploaded_file
)

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
async def auth_headers(client):
    email = f"file_val_{uuid.uuid4().hex[:6]}@example.com"
    reg = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePassword123!",
        "full_name": "File Val Citizen",
        "phone_number": "9876543210"
    })
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Valid binary samples with authentic magic bytes
VALID_PDF = b"%PDF-1.4\n%Valid authentic PDF binary document sample for testing."
VALID_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
VALID_WEBP = b"RIFF\x1a\x00\x00\x00WEBPVP8 \x0e\x00\x00\x00"

def test_magic_byte_detection_unit():
    """G-08 Unit: Magic byte parser correctly detects format from binary headers."""
    assert detect_file_type_from_magic_bytes(VALID_PDF) == "pdf"
    assert detect_file_type_from_magic_bytes(VALID_PNG) == "png"
    assert detect_file_type_from_magic_bytes(VALID_JPEG) == "jpeg"
    assert detect_file_type_from_magic_bytes(VALID_WEBP) == "webp"
    # Invalid magic bytes
    assert detect_file_type_from_magic_bytes(b"<html>hello</html>") is None
    assert detect_file_type_from_magic_bytes(b"MZ\x90\x00\x03\x00\x00\x00") is None  # EXE
    assert detect_file_type_from_magic_bytes(b"") is None

def test_path_traversal_sanitization_unit():
    """G-08 Unit: Filename sanitization strips traversal sequences and directory paths."""
    assert sanitize_filename("../../../../etc/passwd.pdf") == "passwd.pdf"
    assert sanitize_filename("..\\..\\windows\\system32\\calc.exe.pdf") == "calc.exe.pdf"
    assert sanitize_filename("normal_doc.pdf") == "normal_doc.pdf"
    assert sanitize_filename("../../../secret.png") == "secret.png"

@pytest.mark.asyncio
async def test_valid_pdf_upload_accepted(client, auth_headers):
    """G-08: Authentic PDF upload succeeds with 201 Created."""
    files = {"file": ("citizen_ration_card.pdf", VALID_PDF, "application/pdf")}
    res = await client.post("/api/v1/documents/upload", files=files, data={"doc_code": "address_proof"}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["original_filename"] == "citizen_ration_card.pdf"

@pytest.mark.asyncio
async def test_valid_png_upload_accepted(client, auth_headers):
    """G-08: Authentic PNG photo upload succeeds with 201 Created."""
    files = {"file": ("applicant_photo.png", VALID_PNG, "image/png")}
    res = await client.post("/api/v1/documents/upload", files=files, data={"doc_code": "photo"}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["original_filename"] == "applicant_photo.png"

@pytest.mark.asyncio
async def test_valid_jpeg_upload_accepted(client, auth_headers):
    """G-08: Authentic JPEG upload succeeds with 201 Created."""
    files = {"file": ("community_cert.jpg", VALID_JPEG, "image/jpeg")}
    res = await client.post("/api/v1/documents/upload", files=files, data={"doc_code": "community_certificate"}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["original_filename"] == "community_cert.jpg"

@pytest.mark.asyncio
async def test_spoofed_content_magic_bytes_rejected(client, auth_headers):
    """G-08: Text/HTML disguised as a PDF is rejected via magic byte inspection with 400."""
    fake_pdf = b"<html><script>alert('xss')</script></html>"
    files = {"file": ("malicious.pdf", fake_pdf, "application/pdf")}
    res = await client.post("/api/v1/documents/upload", files=files, data={"doc_code": "address_proof"}, headers=auth_headers)
    assert res.status_code == 400
    assert "magic bytes do not match" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_extension_mismatch_rejected(client, auth_headers):
    """G-08: Valid PNG file disguised with .pdf extension is rejected with 400."""
    files = {"file": ("fake_extension.pdf", VALID_PNG, "image/png")}
    res = await client.post("/api/v1/documents/upload", files=files, data={"doc_code": "photo"}, headers=auth_headers)
    assert res.status_code == 400
    assert "does not match detected format" in res.json()["detail"]

@pytest.mark.asyncio
async def test_content_type_spoofing_rejected(client, auth_headers):
    """G-08: Valid PDF sent with declared MIME type image/png is rejected with 400."""
    files = {"file": ("document.pdf", VALID_PDF, "image/png")}
    res = await client.post("/api/v1/documents/upload", files=files, data={"doc_code": "address_proof"}, headers=auth_headers)
    assert res.status_code == 400
    assert "content-type spoofing detected" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_path_traversal_upload_sanitized_and_contained(client, auth_headers):
    """G-08: Path traversal attempts in filename are strictly sanitized and contained inside user directory."""
    traversal_filename = "../../../../etc/passwd.pdf"
    files = {"file": (traversal_filename, VALID_PDF, "application/pdf")}
    res = await client.post("/api/v1/documents/upload", files=files, data={"doc_code": "address_proof"}, headers=auth_headers)
    assert res.status_code == 201
    doc_id = res.json()["id"]

    # Verify storage path is contained and filename sanitized
    async with AsyncSessionLocal() as session:
        doc = await session.get(UserDocumentModel, doc_id)
        assert doc is not None
        assert ".." not in doc.storage_path
        assert doc.original_filename == "passwd.pdf"
        assert os.path.isabs(doc.storage_path)
        # Verify file is strictly inside UPLOAD_DIR
        assert str(doc.storage_path).startswith(settings.UPLOAD_DIR)

@pytest.mark.asyncio
async def test_oversized_file_rejected(client, auth_headers):
    """G-08: Files exceeding MAX_UPLOAD_SIZE_BYTES (5MB) are rejected with 400."""
    oversized_content = b"%PDF-1.4\n" + b"0" * (settings.MAX_UPLOAD_SIZE_BYTES + 1024)
    files = {"file": ("huge_file.pdf", oversized_content, "application/pdf")}
    res = await client.post("/api/v1/documents/upload", files=files, data={"doc_code": "address_proof"}, headers=auth_headers)
    assert res.status_code == 400
    assert "exceeds maximum allowed size" in res.json()["detail"].lower()
