import uuid
import json
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.main import app
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.audit import AuditLogModel
from backend.app.models.deletion import DeletionReceiptModel

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_audit_hygiene_full_scan_finds_zero_user_pii_after_deletion(client):
    """
    Fix 2: Audit Hygiene
    After /me/data deletion:
    - Preserved admin audit rows must NOT contain any of the deleted user's PII
      (email, phone, full_name, extracted document fields).
    - A full database scan of preserved audit logs and deletion receipts confirms
      zero occurrences of the citizen's personal data.
    """
    test_email = f"hygiene_citizen_{uuid.uuid4().hex[:6]}@tnega.gov.in"
    test_name = "Karpagavalli Meenakshi"
    test_phone = "9442211009"

    # 1. Register citizen
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": test_email,
        "password": "SecurePassword123!",
        "full_name": test_name,
        "phone_number": test_phone
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    user_id = reg_res.json()["user"]["id"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. Add citizen personal activity log (should be completely deleted)
    async with AsyncSessionLocal() as session:
        citizen_login_log = AuditLogModel(
            user_id=user_id,
            action="USER_LOGIN",
            details={"ip": "192.168.1.50", "email": test_email, "phone": test_phone}
        )
        session.add(citizen_login_log)

        # 3. Add administrative audit logs (must be PRESERVED, but SANITIZED)
        admin_role_change = AuditLogModel(
            user_id=user_id,
            action="ADMIN_USER_ROLE_CHANGE",
            details={
                "target_email": test_email,
                "target_name": test_name,
                "target_phone": test_phone,
                "new_role": "REVIEWER",
                "approved_by": "zonal_director@tnega.gov.in",
                "reason": "Official appointment by state order"
            }
        )
        session.add(admin_role_change)

        admin_playbook_log = AuditLogModel(
            user_id=user_id,
            action="PLAYBOOK_VERIFICATION_STATUS_CHANGE",
            details={
                "who": "reviewer@tnega.gov.in",
                "note": "Verified against state gazette",
                "citizen_reference_email": test_email
            }
        )
        session.add(admin_playbook_log)
        await session.commit()

    # 4. Invoke DELETE /me/data
    del_res = await client.delete("/api/v1/auth/me/data", headers=auth_header)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"

    # 5. Full database scan across all preserved AuditLogModel and DeletionReceiptModel records
    async with AsyncSessionLocal() as session:
        all_audit_res = await session.execute(select(AuditLogModel))
        all_audits = all_audit_res.scalars().all()

        all_receipts_res = await session.execute(select(DeletionReceiptModel))
        all_receipts = all_receipts_res.scalars().all()

        # Serialize all preserved audit details and receipts to text for full-text search
        audit_dump = json.dumps([a.details for a in all_audits if a.details])
        receipt_dump = json.dumps([r.consent_withdrawal_evidence for r in all_receipts if r.consent_withdrawal_evidence])

        # Assert: NONE of the user's PII exists in any preserved audit row or receipt
        assert test_email not in audit_dump, f"Leak found: {test_email} present in preserved audit rows"
        assert test_name not in audit_dump, f"Leak found: {test_name} present in preserved audit rows"
        assert test_phone not in audit_dump, f"Leak found: {test_phone} present in preserved audit rows"

        assert test_email not in receipt_dump, f"Leak found: {test_email} present in deletion receipts"
        assert test_name not in receipt_dump, f"Leak found: {test_name} present in deletion receipts"
        assert test_phone not in receipt_dump, f"Leak found: {test_phone} present in deletion receipts"

        # Assert: The administrative action and non-PII accountability trail IS preserved
        matching_admin_rows = [a for a in all_audits if a.action == "ADMIN_USER_ROLE_CHANGE" and a.user_id == user_id]
        assert len(matching_admin_rows) == 1
        preserved_details = matching_admin_rows[0].details
        assert preserved_details["approved_by"] == "zonal_director@tnega.gov.in"
        assert preserved_details["new_role"] == "REVIEWER"
        assert preserved_details["target_email"] == "[REDACTED_PURGED_CITIZEN_PII]"
        assert preserved_details["target_name"] == "[REDACTED_PURGED_CITIZEN_PII]"
        assert preserved_details["target_phone"] == "[REDACTED_PURGED_CITIZEN_PII]"
