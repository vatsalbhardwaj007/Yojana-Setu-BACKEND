"""API routes for scheme eligibility evaluation."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.eligibility import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
)
from app.services.eligibility_service import EligibilityService
from app.services.scheme_service import SchemeNotFoundError

router = APIRouter(prefix="/eligibility", tags=["Eligibility"])


def get_eligibility_service() -> EligibilityService:
    """Dependency provider for EligibilityService."""
    return EligibilityService()


EligibilityServiceDep = Annotated[EligibilityService, Depends(get_eligibility_service)]


@router.post("/check", response_model=EligibilityCheckResponse)
def check_eligibility(
    payload: EligibilityCheckRequest,
    service: EligibilityServiceDep,
):
    """Evaluate citizen profile against a government scheme's canonical rules."""
    try:
        return service.check_eligibility(
            scheme_code=payload.scheme_code,
            profile=payload.profile,
        )
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with code '{payload.scheme_code}' not found.",
        )
