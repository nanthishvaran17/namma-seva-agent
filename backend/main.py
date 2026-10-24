"""
Entrypoint alias delegating to backend.app.main:app
Allows running both:
  - uvicorn backend.app.main:app
  - uvicorn backend.main:app
"""

from backend.app.main import app

__all__ = ["app"]
