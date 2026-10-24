import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.main import app
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.core.security import create_access_token
from backend.app.cli import create_admin

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_registration_rejects_role_injection(client):
    """
    Fix 2 RBAC: Public registration must forbid extra fields like 'role'.
    Attempting to register with role='ADMIN' must trigger 422 Unprocessable Entity.
    """
    email = f"attacker_{uuid.uuid4().hex[:6]}@example.com"
    res = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Malicious User",
        "phone_number": "9123456789",
        "role": "ADMIN"  # Attempted privilege escalation
    })
    # Pydantic extra='forbid' must reject extra attributes
    assert res.status_code == 422

@pytest.mark.asyncio
async def test_registration_always_assigns_citizen_role(client):
    """
    Fix 2 RBAC: Public registration always assigns role='CITIZEN'.
    """
    email = f"citizen_{uuid.uuid4().hex[:6]}@example.com"
    res = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Normal Citizen",
        "phone_number": "9123456789"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["role"] == "CITIZEN"

    # Verify directly in SQLite DB
    async with AsyncSessionLocal() as session:
        user_res = await session.execute(select(User).where(User.email == email))
        user_db = user_res.scalar_one_or_none()
        assert user_db is not None
        assert user_db.role == "CITIZEN"

@pytest.mark.asyncio
async def test_profile_patch_rejects_role_escalation(client):
    """
    Fix 2 RBAC: Calling PATCH /api/v1/auth/me with role='ADMIN' is rejected with 422.
    """
    # 1. Register normal citizen
    email = f"citizen_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Citizen User",
        "phone_number": "9123456789"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Attempt role escalation via PATCH /me
    patch_res = await client.patch("/api/v1/auth/me", json={"role": "ADMIN"}, headers=headers)
    assert patch_res.status_code == 422

    # 3. Legitimate update succeeds without altering role
    legit_res = await client.patch("/api/v1/auth/me", json={"full_name": "Updated Citizen"}, headers=headers)
    assert legit_res.status_code == 200
    assert legit_res.json()["full_name"] == "Updated Citizen"
    assert legit_res.json()["role"] == "CITIZEN"

@pytest.mark.asyncio
async def test_first_admin_created_via_cli_only(client):
    """
    Fix 2 RBAC: The first administrator is created exclusively via CLI/seed.
    Once created, this admin account can successfully access admin endpoints.
    """
    admin_email = f"superadmin_{uuid.uuid4().hex[:6]}@tnega.gov.in"
    password = "SuperSecureAdminPass2026!"
    name = "First TNeGA Admin"

    # Run CLI creation function
    exit_code = await create_admin(email=admin_email, password=password, full_name=name)
    assert exit_code == 0

    # Verify DB record
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.email == admin_email))
        admin_db = res.scalar_one_or_none()
        assert admin_db is not None
        assert admin_db.role == "ADMIN"
        admin_id = admin_db.id

    # Admin JWT token can access /admin/playbooks
    token = create_access_token({"sub": admin_id, "email": admin_email, "role": "ADMIN"})
    admin_res = await client.get("/api/v1/admin/playbooks", headers={"Authorization": f"Bearer {token}"})
    assert admin_res.status_code == 200
    assert len(admin_res.json()) >= 5
