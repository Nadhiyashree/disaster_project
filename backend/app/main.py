"""
backend/app/main.py
===================
Module alias for backend.main as referenced in project architecture documentation.
Re-exports the FastAPI app instance and route definitions.
"""
from backend.main import app, get_enriched_reports

__all__ = ["app", "get_enriched_reports"]
