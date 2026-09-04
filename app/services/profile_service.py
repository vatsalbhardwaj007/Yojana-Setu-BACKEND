"""Citizen profile service managing profile lifecycle and security sanitization."""

from typing import Any

from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileResponse

DISALLOWED_FIELDS = {
    "aadhaar",
    "aadhaar_number",
    "password",
    "otp",
    "bank_pin",
    "cvv",
    "card_number",
}


class ProfileNotFoundError(Exception):
    """Raised when the citizen profile is requested but does not exist."""

    def __init__(self, profile_id: str = "default"):
        self.profile_id = profile_id
        super().__init__(f"Profile '{profile_id}' not found.")


class ProfileService:
    """Service managing citizen profile persistence and updates."""

    def __init__(self, repository: ProfileRepository | None = None):
        self.repository = repository or ProfileRepository()

    @classmethod
    def _sanitize_profile(cls, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Recursively strip sensitive fields like passwords, OTPs, or Aadhaar numbers."""
        clean: dict[str, Any] = {}
        for k, v in profile_data.items():
            if k.lower() in DISALLOWED_FIELDS:
                continue
            if isinstance(v, dict):
                clean[k] = cls._sanitize_profile(v)
            else:
                clean[k] = v
        return clean

    def create_profile(
        self, profile_data: dict[str, Any], profile_id: str = "default"
    ) -> ProfileResponse:
        """Store or replace citizen profile."""
        clean_data = self._sanitize_profile(profile_data)
        saved = self.repository.save_profile(clean_data, profile_id=profile_id)
        return ProfileResponse(**saved)

    def get_profile(self, profile_id: str = "default") -> ProfileResponse:
        """Retrieve stored citizen profile, or raise ProfileNotFoundError."""
        found = self.repository.get_profile(profile_id=profile_id)
        if not found:
            raise ProfileNotFoundError(profile_id)
        return ProfileResponse(**found)

    def update_profile(
        self, updates: dict[str, Any], profile_id: str = "default"
    ) -> ProfileResponse:
        """Update existing profile attributes without discarding previously stored ones."""
        clean_updates = self._sanitize_profile(updates)
        updated = self.repository.update_profile(clean_updates, profile_id=profile_id)
        if not updated:
            raise ProfileNotFoundError(profile_id)
        return ProfileResponse(**updated)
