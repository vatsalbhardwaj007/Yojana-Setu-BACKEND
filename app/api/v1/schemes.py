"""API routes for canonical government schemes catalog and details."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.scheme import (
    SchemeDetailResponse,
    SchemeDocumentResponse,
    SchemeProfileFieldResponse,
    SchemeRuleResponse,
    SchemeSummaryResponse,
    SchemeVerificationResponse,
    TutorialStepResponse,
)
from app.services.scheme_service import SchemeNotFoundError, SchemeService

router = APIRouter(prefix="/schemes", tags=["Schemes"])


def get_scheme_service() -> SchemeService:
    """Dependency provider for SchemeService."""
    return SchemeService()


@router.get("", response_model=List[SchemeSummaryResponse])
def list_schemes(
    scheme_type: Optional[str] = Query(None, description="Filter by scheme type"),
    status: Optional[str] = Query(None, description="Filter by status (active, inactive, archived)"),
    ministry: Optional[str] = Query(None, description="Filter by ministry name"),
    service: SchemeService = Depends(get_scheme_service),
):
    """Retrieve catalog list of government schemes with optional filtering."""
    return service.list_schemes(scheme_type=scheme_type, status=status, ministry=ministry)


@router.get("/{scheme_code}", response_model=SchemeDetailResponse)
def get_scheme_detail(
    scheme_code: str,
    service: SchemeService = Depends(get_scheme_service),
):
    """Retrieve full details of a scheme by its canonical snake_case code."""
    try:
        return service.get_scheme_detail(scheme_code)
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with code '{scheme_code}' not found.",
        )


@router.get("/{scheme_code}/rules", response_model=List[SchemeRuleResponse])
def get_scheme_rules(
    scheme_code: str,
    rule_purpose: Optional[str] = Query(
        None,
        pattern="^(eligibility|exclusion)$",
        description="Filter by rule purpose: 'eligibility' or 'exclusion'",
    ),
    service: SchemeService = Depends(get_scheme_service),
):
    """Retrieve eligibility or exclusion rules for a specific scheme."""
    try:
        return service.get_scheme_rules(scheme_code, rule_purpose=rule_purpose)
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with code '{scheme_code}' not found.",
        )


@router.get("/{scheme_code}/documents", response_model=List[SchemeDocumentResponse])
def get_scheme_documents(
    scheme_code: str,
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    is_mandatory: Optional[bool] = Query(None, description="Filter by mandatory requirement"),
    service: SchemeService = Depends(get_scheme_service),
):
    """Retrieve required and recommended documents for a scheme."""
    try:
        return service.get_scheme_documents(
            scheme_code, document_type=document_type, is_mandatory=is_mandatory
        )
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with code '{scheme_code}' not found.",
        )


@router.get("/{scheme_code}/tutorials", response_model=List[TutorialStepResponse])
def get_scheme_tutorials(
    scheme_code: str,
    service: SchemeService = Depends(get_scheme_service),
):
    """Retrieve sequential tutorial steps for a scheme application."""
    try:
        return service.get_tutorial_steps(scheme_code)
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with code '{scheme_code}' not found.",
        )


@router.get("/{scheme_code}/profile-fields", response_model=List[SchemeProfileFieldResponse])
def get_scheme_profile_fields(
    scheme_code: str,
    is_required: Optional[bool] = Query(None, description="Filter by mandatory field"),
    service: SchemeService = Depends(get_scheme_service),
):
    """Retrieve user profile fields needed to evaluate eligibility for a scheme."""
    try:
        return service.get_profile_fields(scheme_code, is_required=is_required)
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with code '{scheme_code}' not found.",
        )


@router.get("/{scheme_code}/verification", response_model=List[SchemeVerificationResponse])
def get_scheme_verification(
    scheme_code: str,
    service: SchemeService = Depends(get_scheme_service),
):
    """Retrieve official verification sources and helpline details for a scheme."""
    try:
        return service.get_verification(scheme_code)
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with code '{scheme_code}' not found.",
        )
