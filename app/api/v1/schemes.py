from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.schemas.catalog import (
    RecommendationRequest,
    RecommendationResponse,
    SchemeDocumentsResponse,
    SchemeListResponse,
    SchemeTutorialResponse,
)
from app.schemas.scheme import (
    SchemeDetailResponse,
    SchemeDocumentResponse,
    SchemeProfileFieldResponse,
    SchemeRuleResponse,
    SchemeSummaryResponse,
    SchemeVerificationResponse,
    TutorialStepResponse,
)
from app.services.recommendation_service import RecommendationService
from app.services.scheme_service import SchemeNotFoundError, SchemeService

router = APIRouter(prefix="/schemes", tags=["Schemes"])


def get_scheme_service() -> SchemeService:
    """Dependency provider for SchemeService."""
    return SchemeService()


def get_recommendation_service() -> RecommendationService:
    """Dependency provider for RecommendationService."""
    return RecommendationService()


SchemeServiceDep = Annotated[SchemeService, Depends(get_scheme_service)]
RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]


@router.post("/recommend", response_model=RecommendationResponse)
def recommend_schemes(
    payload: RecommendationRequest,
    service: RecommendationServiceDep,
):
    """Provide deterministic metadata-based scheme recommendations for a citizen profile."""
    return service.recommend(profile=payload.profile, limit=payload.limit or 10)


@router.get("", response_model=SchemeListResponse | list[SchemeSummaryResponse])
def list_schemes(
    request: Request,
    service: SchemeServiceDep,
    scheme_type: Annotated[str | None, Query(description="Filter by scheme type")] = None,
    category: Annotated[str | None, Query(description="Alias for scheme type")] = None,
    status: Annotated[str | None, Query(description="Filter by status (active, inactive, archived)")] = "active",
    ministry: Annotated[str | None, Query(description="Filter by ministry name")] = None,
    search: Annotated[str | None, Query(description="Search text in name, description, tags")] = None,
    target_group: Annotated[str | None, Query(description="Filter by target group")] = None,
    state: Annotated[str | None, Query(description="Filter by state")] = None,
    limit: Annotated[int | None, Query(ge=1, le=100, description="Max items to return")] = 50,
    offset: Annotated[int | None, Query(ge=0, description="Offset for pagination")] = 0,
    format: Annotated[str | None, Query(description="Response format ('paged' or 'list')")] = None,
):
    """Retrieve catalog list of government schemes with optional filtering and pagination."""
    effective_type = scheme_type or category
    items, total = service.list_schemes_paged(
        scheme_type=effective_type,
        status=status,
        ministry=ministry,
        search=search,
        target_group=target_group,
        state=state,
        limit=limit,
        offset=offset,
    )

    # If hit on Phase 3 root path /schemes or explicitly requested paged format
    if format == "paged" or request.url.path == "/schemes":
        return SchemeListResponse(items=items, total=total)

    # Otherwise return list format for backward compatibility with Phase 1 /api/v1/schemes
    return items


@router.get("/{scheme_id}", response_model=SchemeDetailResponse)
def get_scheme_detail(
    scheme_id: str,
    service: SchemeServiceDep,
):
    """Retrieve full details of a scheme by its canonical snake_case code or UUID."""
    try:
        return service.get_scheme_by_code_or_id(scheme_id)
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme not found: '{scheme_id}'.",
        )


@router.get("/{scheme_id}/rules", response_model=list[SchemeRuleResponse])
def get_scheme_rules(
    scheme_id: str,
    service: SchemeServiceDep,
    rule_purpose: Annotated[
        str | None,
        Query(
            pattern="^(eligibility|exclusion)$",
            description="Filter by rule purpose: 'eligibility' or 'exclusion'",
        ),
    ] = None,
):
    """Retrieve eligibility or exclusion rules for a specific scheme."""
    try:
        scheme = service.get_scheme_by_code_or_id(scheme_id)
        return service.get_scheme_rules(scheme.scheme_code, rule_purpose=rule_purpose)
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme not found: '{scheme_id}'.",
        )


@router.get(
    "/{scheme_id}/documents",
    response_model=SchemeDocumentsResponse | list[SchemeDocumentResponse],
)
def get_scheme_documents(
    scheme_id: str,
    request: Request,
    service: SchemeServiceDep,
    document_type: Annotated[str | None, Query(description="Filter by document type")] = None,
    is_mandatory: Annotated[bool | None, Query(description="Filter by mandatory requirement")] = None,
):
    """Retrieve required and recommended documents for a scheme."""
    try:
        scheme = service.get_scheme_by_code_or_id(scheme_id)
        docs = service.get_scheme_documents(
            scheme.scheme_code, document_type=document_type, is_mandatory=is_mandatory
        )
        if request.url.path.startswith("/schemes/"):
            return SchemeDocumentsResponse(scheme_code=scheme.scheme_code, documents=docs)
        return docs
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme not found: '{scheme_id}'.",
        )


@router.get(
    "/{scheme_id}/tutorial",
    response_model=SchemeTutorialResponse,
)
def get_scheme_tutorial(
    scheme_id: str,
    service: SchemeServiceDep,
):
    """Retrieve sequential tutorial steps for a scheme application (Phase 3 singular path)."""
    try:
        scheme = service.get_scheme_by_code_or_id(scheme_id)
        steps = service.get_tutorial_steps(scheme.scheme_code)
        return SchemeTutorialResponse(scheme_code=scheme.scheme_code, steps=steps)
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme not found: '{scheme_id}'.",
        )


@router.get(
    "/{scheme_id}/tutorials",
    response_model=SchemeTutorialResponse | list[TutorialStepResponse],
)
def get_scheme_tutorials(
    scheme_id: str,
    request: Request,
    service: SchemeServiceDep,
):
    """Retrieve sequential tutorial steps (supporting both list and structured formats)."""
    try:
        scheme = service.get_scheme_by_code_or_id(scheme_id)
        steps = service.get_tutorial_steps(scheme.scheme_code)
        if request.url.path.startswith("/schemes/"):
            return SchemeTutorialResponse(scheme_code=scheme.scheme_code, steps=steps)
        return steps
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme not found: '{scheme_id}'.",
        )


@router.get("/{scheme_id}/profile-fields", response_model=list[SchemeProfileFieldResponse])
def get_scheme_profile_fields(
    scheme_id: str,
    service: SchemeServiceDep,
    is_required: Annotated[bool | None, Query(description="Filter by mandatory field")] = None,
):
    """Retrieve user profile fields needed to evaluate eligibility for a scheme."""
    try:
        scheme = service.get_scheme_by_code_or_id(scheme_id)
        return service.get_profile_fields(scheme.scheme_code, is_required=is_required)
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme not found: '{scheme_id}'.",
        )


@router.get("/{scheme_id}/verification", response_model=list[SchemeVerificationResponse])
def get_scheme_verification(
    scheme_id: str,
    service: SchemeServiceDep,
):
    """Retrieve official verification sources and helpline details for a scheme."""
    try:
        scheme = service.get_scheme_by_code_or_id(scheme_id)
        return service.get_verification(scheme.scheme_code)
    except SchemeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme not found: '{scheme_id}'.",
        )
