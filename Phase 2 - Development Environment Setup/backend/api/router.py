"""Version-1 API router (all endpoints live under /api/v1, spec 14.13)."""

from fastapi import APIRouter

from backend.api.prefix import API_PREFIX
from backend.api.v1 import health, system

api_router = APIRouter(prefix=API_PREFIX)
api_router.include_router(health.router)
api_router.include_router(system.router)
