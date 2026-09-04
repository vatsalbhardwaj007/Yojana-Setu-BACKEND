"""YojanaSetu FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_v1_router
from app.core.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event to initialize database schema and canonical schemes on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Government Scheme Discovery & Eligibility Engine API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.auth import router as auth_router
from app.api.v1.eligibility import router as eligibility_router
from app.api.v1.profile import router as profile_router
from app.api.v1.schemes import router as schemes_router

# Mount API routers (both at /api/v1 and root level for client flexibility)
app.include_router(api_v1_router)
app.include_router(auth_router)
app.include_router(schemes_router)
app.include_router(eligibility_router)
app.include_router(profile_router)



@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint to verify service availability."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
