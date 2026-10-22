from fastapi import APIRouter
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.services import router as services_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.tasks import router as tasks_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.reminders import router as reminders_router
from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.whatsapp import router as whatsapp_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(services_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(reminders_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(whatsapp_router)
