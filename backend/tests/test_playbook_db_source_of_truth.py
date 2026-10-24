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
from backend.app.playbooks.loader import playbook_loader
from backend.app.playbooks.seeder import (
    sync_playbooks_to_db,
    detect_playbook_divergence,
    export_db_playbooks_to_disk
)

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture(autouse=True)
def preserve_playbook_disk():
    """Preserves disk JSON files so test modifications are cleanly reverted."""
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
        playbook_loader.reload()

@pytest.mark.asyncio
async def test_playbook_status_survives_restart():
    """
    Fix 3: DB is the source of truth.
    When a playbook is updated to VERIFIED in DB, subsequent restarts
    (sync_playbooks_to_db) MUST NOT overwrite DB verification status from disk.
    """
    service_id = "community_certificate"
    async with AsyncSessionLocal() as session:
        db_model = await session.get(ServicePlaybookModel, service_id)
        assert db_model is not None
        # Mark as VERIFIED in DB
        db_model.verification_status = "VERIFIED"
        db_model.verified_by = "officer@tnega.gov.in"
        db_model.last_verified = "2026-10-24"
        await session.commit()

    # Simulate server restart / seeder execution
    async with AsyncSessionLocal() as session:
        await sync_playbooks_to_db(session)

    # Verify DB status is preserved
    async with AsyncSessionLocal() as session:
        reloaded = await session.get(ServicePlaybookModel, service_id)
        assert reloaded.verification_status == "VERIFIED"
        assert reloaded.verified_by == "officer@tnega.gov.in"
        assert reloaded.last_verified == "2026-10-24"

    # Verify in-memory catalog took DB ground truth
    cat_item = playbook_loader.get_service(service_id)
    assert cat_item["verification_status"] == "VERIFIED"
    assert cat_item["verified_by"] == "officer@tnega.gov.in"

@pytest.mark.asyncio
async def test_disk_json_never_written_on_production_request_path(client, monkeypatch):
    """
    Fix 3: In production environments, updating playbook verification status
    never touches disk JSON files in the request path.
    """
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    service_id = "community_certificate"
    playbook_file = Path(settings.PLAYBOOKS_DIR) / f"{service_id}.json"
    mtime_before = os.path.getmtime(playbook_file)

    # Create admin
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

    # Patch status
    res = await client.patch(
        f"/api/v1/admin/playbooks/{service_id}/status",
        json={"verification_status": "VERIFIED"},
        headers=headers
    )
    assert res.status_code == 200

    # Verify disk JSON was NOT modified
    mtime_after = os.path.getmtime(playbook_file)
    assert mtime_before == mtime_after

@pytest.mark.asyncio
async def test_divergence_detection_and_explicit_export(client):
    """
    Fix 3: Disk and DB cannot diverge silently:
    - detect_playbook_divergence detects differences between DB and disk.
    - Explicit export writes DB playbooks to disk resolving divergence.
    """
    service_id = "community_certificate"

    # Set DB to VERIFIED while disk has NEEDS_VERIFICATION
    async with AsyncSessionLocal() as session:
        db_model = await session.get(ServicePlaybookModel, service_id)
        db_model.verification_status = "VERIFIED"
        db_model.verified_by = "lead@tnega.gov.in"
        db_model.last_verified = "2026-10-24"
        await session.commit()

        divergences = await detect_playbook_divergence(session)
        # Must detect that DB is VERIFIED while disk is NEEDS_VERIFICATION
        assert len(divergences) >= 1
        found = any(d["service_id"] == service_id for d in divergences)
        assert found is True

        # Now trigger explicit export
        count = await export_db_playbooks_to_disk(session)
        assert count >= 5

        # Divergence resolved
        div_after = await detect_playbook_divergence(session)
        assert len(div_after) == 0
