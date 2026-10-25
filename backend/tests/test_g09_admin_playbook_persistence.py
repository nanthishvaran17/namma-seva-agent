import os
import json
import uuid
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.playbook import ServicePlaybookModel
from backend.app.models.audit import AuditLogModel
from backend.app.playbooks.loader import playbook_loader

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture(autouse=True)
async def preserve_playbook_file():
    """Restores the original playbook file content and DB state after test completes."""
    service_id = "community_certificate"
    playbook_file = Path(settings.PLAYBOOKS_DIR) / f"{service_id}.json"
    original_content = None
    if playbook_file.exists():
        with open(playbook_file, "r", encoding="utf-8") as f:
            original_content = f.read()
    try:
        yield
    finally:
        if original_content and playbook_file.exists():
            with open(playbook_file, "w", encoding="utf-8") as f:
                f.write(original_content)
        async with AsyncSessionLocal() as session:
            db_model = await session.get(ServicePlaybookModel, service_id)
            if db_model:
                db_model.verification_status = "NEEDS_VERIFICATION"
                db_model.verified_by = "PENDING_OFFICIAL_VERIFICATION"
                db_model.last_verified = None
                await session.commit()
        playbook_loader.reload()

@pytest.mark.asyncio
async def test_citizen_cannot_update_playbook_status(client):
    """G-09 RBAC: Citizen user receives 403 Forbidden attempting to update playbook verification."""
    # Register normal citizen
    email = f"citizen_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Normal Citizen",
        "phone_number": "9123456789"
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {token}"}

    # Attempt to update status
    res = await client.patch(
        "/api/v1/admin/playbooks/community_certificate/status",
        json={"verification_status": "VERIFIED"},
        headers=citizen_headers
    )
    assert res.status_code == 403
    assert "Insufficient administrative privileges" in res.json()["detail"]

@pytest.mark.asyncio
async def test_unauthenticated_cannot_update_playbook_status(client):
    """G-09 RBAC: Unauthenticated caller receives 401 Unauthorized."""
    res = await client.patch(
        "/api/v1/admin/playbooks/community_certificate/status",
        json={"verification_status": "VERIFIED"}
    )
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_admin_updates_status_to_verified_with_audit_trail(client):
    """
    G-09 Persistence & Audit:
    Admin user updates playbook to VERIFIED.
    - Sets verified_by = admin_user.email and last_verified = today
    - Persists in-memory loader, SQLite database, and disk JSON file
    - Records comprehensive audit log with who, when, old_status, new_status
    """
    # 1. Create admin user
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@tnega.gov.in"
    async with AsyncSessionLocal() as session:
        admin_user = User(
            email=admin_email,
            hashed_password=get_password_hash("AdminSecret123!"),
            full_name="TNeGA Official Reviewer",
            role="ADMIN",
            is_active=True
        )
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        admin_id = admin_user.id

    admin_token = create_access_token({"sub": admin_id, "email": admin_email, "role": "ADMIN"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Patch status to VERIFIED
    notes = "Verified against Tamil Nadu G.O. Ms No. 235, Revenue Dept."
    patch_res = await client.patch(
        "/api/v1/admin/playbooks/community_certificate/status",
        json={
            "verification_status": "VERIFIED",
            "review_notes": notes
        },
        headers=admin_headers
    )
    assert patch_res.status_code == 200
    res_data = patch_res.json()
    assert res_data["verification_status"] == "VERIFIED"
    assert res_data["verified_by"] == admin_email
    assert res_data["last_verified"] is not None

    # 3. Verify in-memory loader
    in_memory = playbook_loader.get_service("community_certificate")
    assert in_memory["verification_status"] == "VERIFIED"
    assert in_memory["verified_by"] == admin_email
    assert in_memory["last_verified"] == res_data["last_verified"]
    assert in_memory["review_notes"] == notes

    # 4. Verify SQLite database persistence
    async with AsyncSessionLocal() as session:
        db_playbook = await session.get(ServicePlaybookModel, "community_certificate")
        assert db_playbook is not None
        assert db_playbook.verification_status == "VERIFIED"
        assert db_playbook.verified_by == admin_email
        assert db_playbook.last_verified == res_data["last_verified"]
        assert db_playbook.review_notes == notes

        # Verify audit log row
        audit_query = select(AuditLogModel).where(
            AuditLogModel.action == "PLAYBOOK_VERIFICATION_STATUS_CHANGE",
            AuditLogModel.resource_id == "community_certificate"
        ).order_by(AuditLogModel.created_at.desc())
        audit_res = await session.execute(audit_query)
        audit_row = audit_res.scalar_one_or_none()
        assert audit_row is not None
        assert audit_row.user_id == admin_id
        assert audit_row.details["who"] == admin_email
        assert audit_row.details["new_status"] == "VERIFIED"
        assert audit_row.details["review_notes"] == notes

    # 5. Export DB to disk via explicit export (Fix 3)
    from backend.app.playbooks.seeder import export_db_playbooks_to_disk
    async with AsyncSessionLocal() as session:
        await export_db_playbooks_to_disk(session)

    # Verify JSON file on disk
    playbook_file = Path(settings.PLAYBOOKS_DIR) / "community_certificate.json"
    assert playbook_file.exists()
    with open(playbook_file, "r", encoding="utf-8") as f:
        disk_data = json.load(f)
    assert disk_data["verification_status"] == "VERIFIED"
    assert disk_data["verified_by"] == admin_email
    assert disk_data["last_verified"] == res_data["last_verified"]

    # 6. Now revert back to NEEDS_VERIFICATION and verify invariant: last_verified must become null
    revert_res = await client.patch(
        "/api/v1/admin/playbooks/community_certificate/status",
        json={"verification_status": "NEEDS_VERIFICATION"},
        headers=admin_headers
    )
    assert revert_res.status_code == 200
    revert_data = revert_res.json()
    assert revert_data["verification_status"] == "NEEDS_VERIFICATION"
    assert revert_data["verified_by"] == "PENDING_OFFICIAL_VERIFICATION"
    assert revert_data["last_verified"] is None

    # Export reverted DB state to disk
    async with AsyncSessionLocal() as session:
        await export_db_playbooks_to_disk(session)

    # Disk file check after revert
    with open(playbook_file, "r", encoding="utf-8") as f:
        disk_reverted = json.load(f)
    assert disk_reverted["verification_status"] == "NEEDS_VERIFICATION"
    assert disk_reverted["verified_by"] == "PENDING_OFFICIAL_VERIFICATION"
    assert disk_reverted["last_verified"] is None

@pytest.mark.asyncio
async def test_invalid_status_rejected(client):
    """G-09 Validation: Invalid verification statuses return 400 Bad Request."""
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@tnega.gov.in"
    async with AsyncSessionLocal() as session:
        admin_user = User(
            email=admin_email,
            hashed_password=get_password_hash("AdminPass123!"),
            full_name="Admin",
            role="ADMIN",
            is_active=True
        )
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        admin_id = admin_user.id

    token = create_access_token({"sub": admin_id, "email": admin_email, "role": "ADMIN"})
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.patch(
        "/api/v1/admin/playbooks/community_certificate/status",
        json={"verification_status": "SUPER_VERIFIED"},
        headers=headers
    )
    assert res.status_code == 400
    assert "Invalid status" in res.json()["detail"]
