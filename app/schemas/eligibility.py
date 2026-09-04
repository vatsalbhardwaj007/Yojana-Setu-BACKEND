"""Pydantic schemas for eligibility evaluation request and explainable response."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

EligibilityStatus = Literal["Eligible", "Potentially Eligible", "Not Eligible"]

ReasonCode = Literal["RULE_FAILED", "EXCLUSION_TRIGGERED", "MISSING_INFORMATION"]


class EvaluatedRuleResponse(BaseModel):
    """Explainable result of an evaluated eligibility or exclusion rule."""

    model_config = ConfigDict(from_attributes=True)

    field: str = Field(..., description="Profile field evaluated")
    operator: str = Field(..., description="Canonical operator used for evaluation")
    expected: Any = Field(..., description="Expected value from scheme rule definition")
    actual: Any = Field(None, description="Actual profile value, or None if missing")
    passed: bool | None = Field(
        None,
        description="True if rule passed, False if failed, None if missing information",
    )
    rule_type: Literal["eligibility", "exclusion"] = Field(
        ...,
        description="'eligibility' condition or disqualifying 'exclusion' condition",
    )
    description: str = Field(..., description="Human-readable rule explanation from database")


class EligibilityCheckRequest(BaseModel):
    """Payload for checking citizen eligibility against a government scheme."""

    scheme_code: str = Field(
        ...,
        min_length=1,
        description="Canonical snake_case scheme identifier, e.g. pm_kisan",
    )
    profile: dict[str, Any] = Field(
        default_factory=dict,
        description="Citizen profile attributes as key-value pairs",
    )


class EligibilityCheckResponse(BaseModel):
    """Explainable eligibility evaluation response matching Phase 2 contract."""

    scheme_code: str = Field(..., description="Scheme evaluated")
    status: EligibilityStatus = Field(
        ...,
        description="'Eligible', 'Potentially Eligible', or 'Not Eligible'",
    )
    eligible: bool | None = Field(
        None,
        description="True for Eligible, False for Not Eligible, None (null) for Potentially Eligible",
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Deterministic machine-readable reason codes",
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Human-readable explanation reasons derived from failed/triggered rules",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Required profile fields that were missing or not provided",
    )
    evaluated_rules: list[EvaluatedRuleResponse] = Field(
        default_factory=list,
        description="List of all rules evaluated with individual outcomes",
    )
