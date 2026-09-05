"""Pydantic schemas for scheme listing, documents, tutorials, and recommendations."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.scheme import (
    SchemeDocumentResponse,
    SchemeSummaryResponse,
    TutorialStepResponse,
)


class SchemeListResponse(BaseModel):
    """Paged/structured scheme catalog listing."""

    model_config = ConfigDict(from_attributes=True)

    items: list[SchemeSummaryResponse] = Field(
        default_factory=list,
        description="List of available schemes",
    )
    total: int = Field(..., description="Total count of schemes matching criteria")


class SchemeDocumentsResponse(BaseModel):
    """Documents requirement response for a scheme."""

    model_config = ConfigDict(from_attributes=True)

    scheme_code: str = Field(..., description="Canonical snake_case scheme identifier")
    documents: list[SchemeDocumentResponse] = Field(
        default_factory=list,
        description="Required and recommended documents",
    )


class SchemeTutorialResponse(BaseModel):
    """Sequential tutorial guidance steps for a scheme."""

    model_config = ConfigDict(from_attributes=True)

    scheme_code: str = Field(..., description="Canonical snake_case scheme identifier")
    steps: list[TutorialStepResponse] = Field(
        default_factory=list,
        description="Ordered application tutorial steps",
    )


class RecommendationRequest(BaseModel):
    """Payload for requesting deterministic scheme recommendations."""

    profile: dict[str, Any] = Field(
        default_factory=dict,
        description="Citizen profile attributes",
    )
    limit: int | None = Field(default=10, ge=1, le=50, description="Max schemes to return")


class RecommendedSchemeItem(BaseModel):
    """Recommended scheme item with match reasons and relevance score."""

    model_config = ConfigDict(from_attributes=True)

    scheme_code: str = Field(..., description="Canonical scheme code")
    name: str = Field(..., description="Official scheme name")
    match_reasons: list[str] = Field(
        default_factory=list,
        description="Non-legal relevance reasons matching profile metadata",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (0.0 to 1.0; does not indicate legal eligibility)",
    )


class RecommendationResponse(BaseModel):
    """Scheme recommendation response."""

    model_config = ConfigDict(from_attributes=True)

    items: list[RecommendedSchemeItem] = Field(
        default_factory=list,
        description="Recommended schemes ordered by relevance",
    )
    total: int = Field(..., description="Number of recommended schemes")
    disclaimer: str = Field(
        default="Recommendations are based on profile relevance and do not guarantee eligibility. Please check formal eligibility via /eligibility/check.",
        description="Legal and compliance notice",
    )


class SchemeSearchResultItem(BaseModel):
    """A single ranked result for a semantic scheme search."""

    model_config = ConfigDict(from_attributes=True)

    scheme: SchemeSummaryResponse = Field(..., description="Canonical scheme summary")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance confidence (0.0 to 1.0; does not indicate legal eligibility)",
    )
    match_reason: str = Field(
        ...,
        description="Human-readable explanation of why the scheme was matched",
    )


class SchemeSearchResponse(BaseModel):
    """Semantic search results with an optional clarifying question."""

    model_config = ConfigDict(from_attributes=True)

    results: list[SchemeSearchResultItem] = Field(
        default_factory=list,
        description="Ranked scheme matches, best first",
    )
    clarifying_question: str | None = Field(
        default=None,
        description="Follow-up prompt shown when no result is strong enough",
    )


class TranscriptionConfigResponse(BaseModel):
    """Capability flags for speech-to-text."""

    model_config = ConfigDict(from_attributes=True)

    server_stt_configured: bool = Field(
        default=False,
        description="True when the backend has a Gemini API key for server-side STT",
    )


class TranscriptionResponse(BaseModel):
    """Recognised speech text returned by the transcription service."""

    model_config = ConfigDict(from_attributes=True)

    text: str = Field(..., description="Recognised speech text")
