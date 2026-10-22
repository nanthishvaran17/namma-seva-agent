import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

from backend.app.db.session import engine, Base

@pytest.fixture(autouse=True)
async def init_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_health_endpoint(client):
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["region"] == "Tamil Nadu, India"

@pytest.mark.asyncio
async def test_services_catalog_api(client):
    # List services
    res = await client.get("/api/v1/services")
    assert res.status_code == 200
    services = res.json()
    assert len(services) >= 5

    # Filter by Tamil query
    res_ta = await client.get("/api/v1/services?query=சாதி")
    assert res_ta.status_code == 200
    assert len(res_ta.json()) >= 1
    assert res_ta.json()[0]["service_id"] == "community_certificate"

    # Get specific service
    res_det = await client.get("/api/v1/services/income_certificate")
    assert res_det.status_code == 200
    data = res_det.json()
    assert data["service_id"] == "income_certificate"
    assert data["fee"]["amount_inr"] == 60.0

@pytest.mark.asyncio
async def test_action_plan_api(client):
    payload = {
        "target_service_id": "post_matric_scholarship",
        "user_completed_services": ["community_certificate"],
        "user_available_documents": ["photo", "income_proof"]
    }
    res = await client.post("/api/v1/services/action-plan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["target_service_id"] == "post_matric_scholarship"
    assert len(data["plan_steps"]) >= 2
    step_ids = [s["service_id"] for s in data["plan_steps"]]
    assert "income_certificate" in step_ids
    assert "post_matric_scholarship" in step_ids

@pytest.mark.asyncio
async def test_auth_and_user_task_flow(client):
    # 1. Register a new citizen
    email = "citizen.test@nammaseva.tn.gov.in"
    reg_payload = {
        "email": email,
        "password": "SecurePassword123!",
        "full_name": "Ravi Kumar",
        "phone_number": "9876543210",
        "preferred_language": "ta"
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    token = reg_data["access_token"]
    assert token

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get profile
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

    # 3. Create a task
    task_res = await client.post(
        "/api/v1/tasks",
        json={"service_id": "income_certificate"},
        headers=headers
    )
    assert task_res.status_code == 201
    task_data = task_res.json()
    task_id = task_data["id"]
    assert task_data["status"] == "COLLECTING_DOCUMENTS"

    # 4. Update task state
    update_res = await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={
            "status": "READY_FOR_USER_REVIEW",
            "reason": "All documents collected"
        },
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "READY_FOR_USER_REVIEW"

    # 5. Export data (DPDP compliance)
    export_res = await client.get("/api/v1/auth/me/export", headers=headers)
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert export_data["user_profile"]["email"] == email
    assert len(export_data["tasks"]) == 1

    # 6. Delete data
    del_res = await client.delete("/api/v1/auth/me/data", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"

@pytest.mark.asyncio
async def test_chat_api(client):
    # Chat with assistant anonymously
    chat_payload = {
        "message": "Enakku community certificate venum.",
        "language": "tanglish"
    }
    res = await client.post("/api/v1/chat", json=chat_payload)
    assert res.status_code == 200
    data = res.json()
    assert "சாதிச் சான்றிதழ்" in data["message"] or "Community Certificate" in data["message"]
    assert len(data["citations"]) > 0
    assert len(data["action_cards"]) > 0

@pytest.mark.asyncio
async def test_whatsapp_simulator(client):
    sim_payload = {
        "from_phone": "919876543210",
        "message_text": "வணக்கம், முதல் தலைமுறை பட்டதாரி சான்றிதழ் பெற என்ன செய்ய வேண்டும்?"
    }
    res = await client.post("/api/v1/whatsapp/simulate", json=sim_payload)
    assert res.status_code == 200
    data = res.json()
    assert "முதல் தலைமுறை பட்டதாரி" in data["reply_text"]
    assert data["channel"] == "WHATSAPP_SIMULATOR"
