"""Authentication and user identity endpoints."""

from fastapi import APIRouter

from app.api.deps import CurrentUserDep
from app.schemas.auth import UserMeResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=UserMeResponse)
def get_current_user_identity(current_user: CurrentUserDep) -> UserMeResponse:
    """Retrieve the authenticated citizen's identity derived exclusively from the verified JWT."""
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
    )
