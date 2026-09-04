from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUserDep
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
    current_user: CurrentUserDep,
):
    """Create or store a citizen profile strictly for the authenticated user."""
    pid = current_user.id
    profile_data = payload.profile or {}
    return service.create_profile(profile_data=profile_data, profile_id=pid)


@router.get("", response_model=ProfileResponse)
def get_profile(
    service: ProfileServiceDep,
    current_user: CurrentUserDep,
):
    """Retrieve the stored citizen profile for the authenticated user, or return 404."""
    target_id = current_user.id
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
    current_user: CurrentUserDep,
):
    """Update citizen profile attributes for the authenticated user without discarding existing stored fields."""
    target_id = current_user.id
    try:
        updates = payload.profile or {}
        return service.update_profile(updates=updates, profile_id=target_id)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found for ID: '{target_id}'. Please create a profile first.",
        )

