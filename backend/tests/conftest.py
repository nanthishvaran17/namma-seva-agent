import os

os.environ.setdefault("ENVIRONMENT", "test")
# Disable SQLAlchemy Cython C-extensions on Windows/Python 3.14 to prevent Application Control DLL blocks
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

import pytest
from backend.app.core.config import settings, BACKEND_ROOT

# Enforce deterministic test environment and mock LLM during automated test suites
settings.ENVIRONMENT = "test"
settings.LLM_PROVIDER = "mock"
settings.DEMO_MODE = True
settings.DATABASE_URL = f"sqlite+aiosqlite:///{BACKEND_ROOT}/namma_seva_test.db"

# Remove any stale test database
test_db_path = BACKEND_ROOT / "namma_seva_test.db"
if test_db_path.exists():
    try:
        test_db_path.unlink()
    except Exception:
        pass

from backend.app.db.session import engine, Base, AsyncSessionLocal
from backend.app.playbooks.seeder import sync_playbooks_to_db
from backend.app.core.rate_limit import rate_limiter
import backend.app.models  # Register all models with Base

@pytest.fixture(autouse=True)
async def init_test_db():
    rate_limiter.reset()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await sync_playbooks_to_db(session)
    yield
    rate_limiter.reset()
