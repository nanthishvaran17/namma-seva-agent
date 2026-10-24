import os
import pytest
import uuid
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from backend.app.core.config import Settings, INSECURE_DEFAULT_SECRETS
from backend.app.documents.processor import document_processor
from backend.app.playbooks.loader import playbook_loader
from backend.app.tools.registry import tool_registry
from backend.app.models.user import User
from backend.app.models.task import UserTaskModel
from backend.app.db.session import engine, Base, AsyncSessionLocal
from backend.app.playbooks.seeder import sync_playbooks_to_db

@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await sync_playbooks_to_db(session)
        yield session

@pytest.mark.asyncio
async def test_demo_mode_fail_closed_ocr(monkeypatch):
    """
    Follow-up 1: With DEMO_MODE unset or False, simulated OCR must return DISABLED_IN_PRODUCTION.
    """
    from backend.app.core.config import settings
    monkeypatch.setattr(settings, "DEMO_MODE", False)

    result = await document_processor.process_document(
        file_path="/dummy/path/doc.pdf",
        mime_type="application/pdf",
        doc_code="community_certificate",
        original_filename="sample_doc.pdf"
    )

    assert result["is_demo"] is False
    assert result["status"] == "DISABLED_IN_PRODUCTION"
    assert "Simulated OCR is disabled in non-demo mode" in result["notice"]


def test_environment_fail_closed_production():
    """
    Follow-up 2: ENVIRONMENT must be fail-closed.
    If unset or 'production' without a valid 32+ char secret, settings validation must raise ValueError.
    """
    # 1. Production with empty SECRET_KEY
    with pytest.raises((ValueError, ValidationError)):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="",
            DEMO_MODE=False
        )

    # 2. Production with insecure default secret
    with pytest.raises((ValueError, ValidationError)):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="namma-seva-super-secret-key-change-in-production-2026",
            DEMO_MODE=False
        )

    # 3. Production with DEMO_MODE enabled must be blocked
    with pytest.raises((ValueError, ValidationError)):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="a-very-secure-random-production-key-at-least-32-chars-long",
            DEMO_MODE=True
        )

    # 4. Dev/test mode explicitly opting in succeeds even with default fallback
    dev_settings = Settings(
        _env_file=None,
        ENVIRONMENT="development",
        SECRET_KEY="",
        DEMO_MODE=True
    )
    assert dev_settings.ENVIRONMENT == "development"
    assert dev_settings.DEMO_MODE is True


@pytest.mark.asyncio
async def test_sqlite_foreign_keys_enforced(db_session):
    """
    Follow-up 3: PRAGMA foreign_keys must be active (= 1) on SQLite dialect,
    and attempting to insert an invalid foreign key into user_tasks must raise IntegrityError.
    """
    # Verify PRAGMA is 1
    res = await db_session.execute(text("PRAGMA foreign_keys"))
    fk_status = res.scalar()
    assert fk_status == 1, f"Expected PRAGMA foreign_keys=1, got {fk_status}"

    # Create a valid user
    user = User(
        email=f"fk_test_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="dummy_hash_for_test",
        full_name="FK Test Citizen",
        phone_number="9876543210"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Attempt to insert user_task with non-existent service_id
    invalid_task = UserTaskModel(
        user_id=user.id,
        service_id="non_existent_unregistered_service_id_9999",
        status="DRAFT"
    )
    db_session.add(invalid_task)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


def test_playbooks_marked_needs_verification():
    """
    Follow-up 5 & Small Fix 2: All playbooks in knowledge base must be marked NEEDS_VERIFICATION,
    have verified_by = 'PENDING_OFFICIAL_VERIFICATION', and last_verified MUST be null.
    """
    assert len(playbook_loader.catalog) >= 5, "Expected at least 5 seeded playbooks"
    for s_id, s_data in playbook_loader.catalog.items():
        assert s_data["verification_status"] == "NEEDS_VERIFICATION", (
            f"Playbook '{s_id}' has verification_status '{s_data['verification_status']}', "
            f"must be 'NEEDS_VERIFICATION'"
        )
        assert s_data.get("verified_by") == "PENDING_OFFICIAL_VERIFICATION", (
            f"Playbook '{s_id}' missing or invalid verified_by field"
        )
        assert s_data.get("last_verified") is None, (
            f"Playbook '{s_id}' has last_verified='{s_data.get('last_verified')}'; must be null while pending verification"
        )


def test_playbook_cannot_carry_last_verified_while_pending():
    """
    Small Fix 2 Invariant: A playbook with verified_by=PENDING cannot carry a last_verified date.
    Attempting to validate such a playbook must raise ValueError.
    """
    sample_data = dict(next(iter(playbook_loader.catalog.values())))
    # Inject last_verified into a pending verification playbook
    sample_data["verified_by"] = "PENDING_OFFICIAL_VERIFICATION"
    sample_data["last_verified"] = "2026-10-24"
    sample_data["verification_status"] = "NEEDS_VERIFICATION"

    with pytest.raises(ValueError, match="cannot carry a last_verified date"):
        playbook_loader._validate_playbook_structure(sample_data, "test_invalid.json")


def test_health_reports_true_provider_status():
    """
    Small Fix 1: /health must report true provider status, key presence, and live call status.
    """
    from backend.app.agent.providers import get_provider_status
    status = get_provider_status()
    # In test environment, active provider must be mock and live calls must be False
    assert status["active_provider"] == "mock"
    assert status["live_calls_made"] is False
    assert "mock" in status["notice"].lower()


def test_no_autonomous_submission_tools():
    """
    Follow-up 6: Tool registry must NOT expose auto_apply_service.
    """
    tool_defs = tool_registry.get_tool_definitions()
    tool_names = [t["name"] for t in tool_defs]
    assert "auto_apply_service" not in tool_names, "Autonomous submission tool 'auto_apply_service' must be purged"
