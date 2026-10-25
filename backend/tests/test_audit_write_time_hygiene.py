import json
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.main import app
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.audit import AuditLogModel
from backend.app.core.security import get_password_hash

@pytest.mark.asyncio
async def test_audit_logs_zero_pii_at_write_time():
    """
    Fix 4: Verify that audit entries across user registration, user login,
    and admin actions NEVER store citizen or admin PII (email, full name, phone)
    in the details JSON dictionary at write time. Only opaque identifiers are written.
    """
    citizen_email = f"audit_clean_{uuid.uuid4().hex[:6]}@example.com"
    citizen_name = "Thirunavukkarasu Muthu"
    citizen_phone = "9840998877"
    citizen_pass = "SecurePass123!"

    admin_email = f"admin_{uuid.uuid4().hex[:6]}@tnega.gov.in"
    admin_id = str(uuid.uuid4())

    # Pre-seed an admin user
    async with AsyncSessionLocal() as session:
        admin_user = User(
            id=admin_id,
            email=admin_email,
            hashed_password=get_password_hash("AdminPass123!"),
            full_name="TNeGA Officer",
            role="ADMIN",
            is_active=True
        )
        session.add(admin_user)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Citizen Registration Action Path
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": citizen_email,
            "password": citizen_pass,
            "full_name": citizen_name,
            "phone_number": citizen_phone,
            "preferred_language": "ta"
        })
        assert reg_res.status_code == 201
        citizen_uid = reg_res.json()["user"]["id"]

        # 2. Citizen Login Action Path
        login_res = await client.post("/api/v1/auth/login", json={
            "email": citizen_email,
            "password": citizen_pass
        })
        assert login_res.status_code == 200

        # Admin Login to get token
        admin_login = await client.post("/api/v1/auth/login", json={
            "email": admin_email,
            "password": "AdminPass123!"
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]

        # 3. Admin Playbook Action Path
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        pb_res = await client.patch(
            "/api/v1/admin/playbooks/community_certificate/status",
            json={
                "verification_status": "NEEDS_VERIFICATION",
                "verified_by": "PENDING_OFFICIAL_VERIFICATION",
                "review_notes": "Routine check"
            },
            headers=admin_headers
        )
        assert pb_res.status_code == 200

    # 4. Database Scan: Inspect audit rows created by these action paths
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(AuditLogModel).where(
                AuditLogModel.user_id.in_([citizen_uid, admin_id])
            )
        )
        audit_rows = res.scalars().all()
        assert len(audit_rows) >= 3

        for row in audit_rows:
            details_str = json.dumps(row.details)
            # PII Checks: email, name, phone must appear 0 times
            assert citizen_email not in details_str, f"Citizen email found in audit details: {details_str}"
            assert admin_email not in details_str, f"Admin email found in audit details: {details_str}"
            assert citizen_name not in details_str, f"Citizen name found in audit details: {details_str}"
            assert citizen_phone not in details_str, f"Citizen phone found in audit details: {details_str}"
            assert "9840998877" not in details_str

            # Opaque ID check: must only use opaque IDs
            if row.action in ("USER_REGISTRATION", "USER_LOGIN"):
                assert row.details.get("opaque_user_id") == row.user_id
            elif row.action == "PLAYBOOK_VERIFICATION_STATUS_CHANGE":
                assert row.details.get("admin_user_id") == admin_id
