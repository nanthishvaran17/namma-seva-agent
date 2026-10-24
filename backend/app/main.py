from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.db.session import engine, Base, AsyncSessionLocal
from backend.app.playbooks.seeder import sync_playbooks_to_db
from backend.app.api.v1 import api_v1_router
import backend.app.models  # Ensure all models are registered with Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Enforce foreign-key referential integrity by seeding service playbooks
    async with AsyncSessionLocal() as session:
        await sync_playbooks_to_db(session)

    yield
    # Cleanup on shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Tamil Nadu's Unified AI Agent for Government Services — Official API Gateway",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount API V1
app.include_router(api_v1_router)

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

from backend.app.agent.providers import get_provider_status

@app.get("/health", tags=["System Health"])
async def health_check():
    provider_info = get_provider_status()
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "region": "Tamil Nadu, India",
        "environment": settings.ENVIRONMENT,
        "llm_provider": provider_info["active_provider"],
        "provider_details": provider_info
    }

@app.get("/{full_path:path}", tags=["Frontend Single Page App"])
async def serve_frontend(full_path: str):
    if FRONTEND_DIST.exists():
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    return {
        "message": "Namma Seva Agent AI Gateway is running.",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
