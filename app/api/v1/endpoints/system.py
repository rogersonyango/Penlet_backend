# app/api/v1/endpoints/system.py
"""
System API endpoints for health, version, and status monitoring.
"""

from fastapi import APIRouter
from datetime import datetime
import platform

# Define your app's version (you can also load this from a config or __version__ file)
API_VERSION = "1.0.0"
APP_NAME = "3D Educational Resource API"

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/health/", summary="Health Check")
def get_health() -> dict:
    """
    Return a simple health check response.
    Indicates the API is running and reachable.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/version/", summary="API Version")
def get_version() -> dict:
    """
    Return API version and metadata.
    """
    return {
        "app_name": APP_NAME,
        "version": API_VERSION,
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/status/", summary="System Status")
def get_status() -> dict:
    """
    Return extended system status (can be expanded with DB, cache, etc. later).
    """
    return {
        "status": "operational",
        "uptime": "since server start",  # In production, you could track actual uptime
        "services": {
            "database": "unknown",        # Later: test DB connection
            "storage": "ok",              # Assuming local file storage works
            "cache": "not configured"     # Optional
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }