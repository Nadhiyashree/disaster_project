"""
backend/app package wrapper for FastAPI routes and schemas.
Re-exports backend.main and backend.schemas for compatibility.
"""
from backend.main import app
from backend import schemas

__all__ = ["app", "schemas"]
