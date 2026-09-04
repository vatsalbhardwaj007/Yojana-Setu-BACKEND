from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.profile import (
    ProfileCreateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.services.profile_service import ProfileNotFoundError, ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])


def get_profile_service() -> ProfileService:
    """Dependency provider for ProfileService."""
    return ProfileService()


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
def create_profile(
    payload: ProfileCreateRequest,
    service: ProfileServiceDep,
):
    """Create or store a citizen profile without collecting sensitive credentials."""
    pid = payload.profile_id or payload.user_id or "default"
    profile_data = payload.profile or {}
    return service.create_profile(profile_data=profile_data, profile_id=pid)


@router.get("", response_model=ProfileResponse)
def get_profile(
    service: ProfileServiceDep,
    user_id: Annotated[str | None, Query(description="Citizen/user profile identifier")] = None,
    profile_id: Annotated[str | None, Query(description="Profile identifier")] = None,
):
    """Retrieve the stored citizen profile, or return 404 if not found."""
    target_id = profile_id or user_id or "default"
    try:
        return service.get_profile(profile_id=target_id)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found for ID: '{target_id}'. Please create a profile first.",
        )


@router.put("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    service: ProfileServiceDep,
    user_id: Annotated[str | None, Query(description="Citizen/user profile identifier")] = None,
    profile_id: Annotated[str | None, Query(description="Profile identifier")] = None,
):
    """Update citizen profile attributes without discarding existing stored fields."""
    target_id = payload.profile_id or payload.user_id or profile_id or user_id or "default"
    try:
        updates = payload.profile or {}
        return service.update_profile(updates=updates, profile_id=target_id)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found for ID: '{target_id}'. Please create a profile first.",
        )
