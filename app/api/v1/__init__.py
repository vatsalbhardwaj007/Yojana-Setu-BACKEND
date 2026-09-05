from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.eligibility import router as eligibility_router
from app.api.v1.profile import router as profile_router
from app.api.v1.schemes import router as schemes_router
from app.api.v1.search import router as search_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(schemes_router)
api_v1_router.include_router(eligibility_router)
api_v1_router.include_router(profile_router)
api_v1_router.include_router(search_router)

__all__ = [
    "api_v1_router",
    "auth_router",
    "eligibility_router",
    "profile_router",
    "schemes_router",
    "search_router",
]

