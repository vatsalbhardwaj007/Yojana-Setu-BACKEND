"""Version 1 API routes package."""

from fastapi import APIRouter
from app.api.v1.schemes import router as schemes_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(schemes_router)

__all__ = ["api_v1_router"]
