"""Pydantic schemas for Citizen Profile management."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProfileResponse(BaseModel):
    """Citizen profile storage and API response representation."""

    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: str = Field(default="default", description="Profile identifier")
    user_id: str | None = Field(None, description="Citizen/user identifier")
    profile: dict[str, Any] = Field(
        default_factory=dict,
        description="Citizen demographic and eligibility attributes",
    )
    created_at: str | None = Field(None, description="ISO timestamp of profile creation")
    updated_at: str | None = Field(None, description="ISO timestamp of last profile update")

    @model_validator(mode="after")
    def populate_fields(self) -> "ProfileResponse":
        if not self.user_id:
            self.user_id = self.id
        # Also surface profile fields at top-level for direct access
        for k, v in self.profile.items():
            if not hasattr(self, k):
                object.__setattr__(self, k, v)
        return self


class ProfileCreateRequest(BaseModel):
    """Request payload for creating or replacing citizen profile."""

    model_config = ConfigDict(extra="allow")

    profile_id: str | None = Field(None, description="Optional custom profile identifier")
    user_id: str | None = Field(None, description="Alias for profile identifier")
    profile: dict[str, Any] | None = Field(
        None,
        description="Nested profile attributes, or passed at root level",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_profile(cls, data: Any) -> Any:
        """Allow profile attributes either inside 'profile' key or at top-level."""
        if isinstance(data, dict):
            pid = data.get("profile_id") or data.get("user_id")
            if "profile" in data and isinstance(data["profile"], dict):
                clean_p = dict(data["profile"])
                return {"profile_id": pid, "user_id": pid, "profile": clean_p}
            # If attributes are at top-level
            clean_p = {k: v for k, v in data.items() if k not in ("profile", "profile_id", "user_id")}
            return {"profile_id": pid, "user_id": pid, "profile": clean_p}
        return data


class ProfileUpdateRequest(BaseModel):
    """Request payload for updating an existing citizen profile (partial or full)."""

    model_config = ConfigDict(extra="allow")

    profile_id: str | None = Field(None, description="Profile or user identifier to update")
    user_id: str | None = Field(None, description="Alias for profile identifier")
    profile: dict[str, Any] | None = Field(
        None,
        description="Attributes to update",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_profile(cls, data: Any) -> Any:
        """Allow update attributes either inside 'profile' key or at top-level."""
        if isinstance(data, dict):
            pid = data.get("profile_id") or data.get("user_id")
            if "profile" in data and isinstance(data["profile"], dict):
                clean_p = dict(data["profile"])
                return {"profile_id": pid, "user_id": pid, "profile": clean_p}
            clean_p = {k: v for k, v in data.items() if k not in ("profile", "profile_id", "user_id")}
            return {"profile_id": pid, "user_id": pid, "profile": clean_p}
        return data
