"""Pydantic schemas for authentication and verified user identity."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedUser(BaseModel):
    """Authenticated citizen identity extracted from verified Supabase JWT claims."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="User unique identifier (UUID from JWT 'sub' claim)")
    email: str | None = Field(None, description="User email address if present in claims")
    phone: str | None = Field(None, description="User phone number if present in claims")
    role: str | None = Field(None, description="User role (e.g. 'authenticated')")
    app_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Supabase application metadata"
    )
    user_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Supabase user profile metadata"
    )


class UserMeResponse(BaseModel):
    """Response schema for GET /api/v1/auth/me representing verified caller identity."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Authenticated user unique identifier (UUID)")
    email: str | None = Field(None, description="User email address if available")
    phone: str | None = Field(None, description="User phone number if available")
    role: str | None = Field(None, description="User authentication role")
