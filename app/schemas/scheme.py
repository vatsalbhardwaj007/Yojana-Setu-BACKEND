"""Pydantic schemas reflecting M4 canonical scheme data models."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Canonical enumerations matching canonical_values.json
SchemeType = Literal[
    "subsidy",
    "insurance",
    "pension",
    "benefit",
    "loan_guarantee",
    "scholarship",
    "employment",
    "healthcare",
    "housing",
    "other",
]

SchemeStatus = Literal["active", "inactive", "archived"]

RuleOperator = Literal[
    "=",
    "!=",
    ">=",
    "<=",
    ">",
    "<",
    "in",
    "not_in",
    "exists",
    "between",
]

RulePurpose = Literal["eligibility", "exclusion"]

DocumentType = Literal[
    "identity_proof",
    "address_proof",
    "income_proof",
    "category_certificate",
    "age_proof",
    "land_record",
    "bank_details",
    "photograph",
    "declaration",
    "other",
]

ProfileFieldType = Literal["text", "number", "date", "boolean", "select"]

VerificationMethod = Literal["online", "offline", "both"]


# ---------------------------------------------------------------------------
# 1. Scheme Rule Schema
# ---------------------------------------------------------------------------
class SchemeRuleBase(BaseModel):
    """Canonical representation of an eligibility or exclusion rule."""

    model_config = ConfigDict(from_attributes=True)

    rule_group: str = Field(..., description="Logical grouping, e.g. age, income, category")
    field: str = Field(..., description="Profile field key evaluated by this rule")
    operator: RuleOperator = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Scalar, list, or range object {min, max}")
    description: str = Field(..., description="Human-readable rule explanation")
    rule_purpose: RulePurpose = Field(
        default="eligibility",
        description="'eligibility' criteria or disqualifying 'exclusion' criteria",
    )


class SchemeRuleResponse(SchemeRuleBase):
    """Rule response schema including persistent database identifiers."""

    id: str | None = None
    scheme_id: str | None = None
    created_at: datetime | str | None = None


# ---------------------------------------------------------------------------
# 2. Scheme Document Schema
# ---------------------------------------------------------------------------
class SchemeDocumentBase(BaseModel):
    """Document requirement definition for scheme application."""

    model_config = ConfigDict(from_attributes=True)

    document_type: DocumentType = Field(..., description="Standard classification of document")
    document_name: str = Field(..., description="Human-readable name of document")
    is_mandatory: bool = Field(default=True, description="Whether the document is strictly required")
    description: str | None = Field(default=None, description="Guidance or details about the document")


class SchemeDocumentResponse(SchemeDocumentBase):
    """Document response schema including persistent database identifiers."""

    id: str | None = None
    scheme_id: str | None = None
    created_at: datetime | str | None = None


# ---------------------------------------------------------------------------
# 3. Tutorial Step Schema
# ---------------------------------------------------------------------------
class TutorialStepBase(BaseModel):
    """Step-by-step application guidance step."""

    model_config = ConfigDict(from_attributes=True)

    step_number: int = Field(..., ge=1, description="Sequential step index starting at 1")
    title: str = Field(..., description="Title of the guidance step")
    description: str = Field(..., description="Detailed instructions for this step")
    tips: str | None = Field(default=None, description="Helpful tips or best practices")


class TutorialStepResponse(TutorialStepBase):
    """Tutorial step response schema including persistent database identifiers."""

    id: str | None = None
    scheme_id: str | None = None
    created_at: datetime | str | None = None


# ---------------------------------------------------------------------------
# 4. Scheme Verification Schema
# ---------------------------------------------------------------------------
class SchemeVerificationBase(BaseModel):
    """Verification and support channel details for a scheme."""

    model_config = ConfigDict(from_attributes=True)

    verification_method: VerificationMethod = Field(..., description="online, offline, or both")
    verification_url: str | None = Field(default=None, description="Official portal verification URL")
    helpline_number: str | None = Field(default=None, description="Helpline phone contact")
    last_verified_at: datetime | str = Field(..., description="Timestamp of data verification")
    notes: str | None = Field(default=None, description="Verification notes or source citations")


class SchemeVerificationResponse(SchemeVerificationBase):
    """Verification response schema including persistent database identifiers."""

    id: str | None = None
    scheme_id: str | None = None
    created_at: datetime | str | None = None


# ---------------------------------------------------------------------------
# 5. Scheme Profile Field Schema
# ---------------------------------------------------------------------------
class SchemeProfileFieldBase(BaseModel):
    """User profile field requirement for checking scheme eligibility."""

    model_config = ConfigDict(from_attributes=True)

    field_name: str = Field(..., description="Canonical profile attribute name")
    field_type: ProfileFieldType = Field(..., description="Data type: text, number, date, boolean, select")
    is_required: bool = Field(default=True, description="Whether field is required for checking eligibility")
    allowed_values: list[Any] | None = Field(default=None, description="Permitted values for select field")
    description: str | None = Field(default=None, description="Description of the requested user attribute")


class SchemeProfileFieldResponse(SchemeProfileFieldBase):
    """Profile field response schema including persistent database identifiers."""

    id: str | None = None
    scheme_id: str | None = None
    created_at: datetime | str | None = None


# ---------------------------------------------------------------------------
# 6. Scheme Top-Level Schemas
# ---------------------------------------------------------------------------
class SchemeBase(BaseModel):
    """Core government scheme metadata."""

    model_config = ConfigDict(from_attributes=True)

    scheme_code: str = Field(..., description="Stable snake_case canonical identifier, e.g. pm_kisan")
    name: str = Field(..., description="Official scheme name")
    description: str = Field(..., description="Scheme summary and description")
    ministry: str = Field(..., description="Parent ministry")
    department: str = Field(..., description="Implementing department or body")
    scheme_type: SchemeType = Field(..., description="Broad scheme category")
    status: SchemeStatus = Field(default="active", description="Operational status")
    aliases: list[str] = Field(default_factory=list, description="Alternative names or abbreviations")
    target_groups: list[str] = Field(default_factory=list, description="Target beneficiary categories")
    tags: list[str] = Field(default_factory=list, description="Search and categorization tags")
    benefits: list[str] = Field(default_factory=list, description="Key scheme entitlements / benefits")
    official_url: str | None = Field(default=None, description="Official government portal URL")
    effective_from: date | str = Field(..., description="Scheme effective start date")
    effective_to: date | str | None = Field(default=None, description="Scheme end date if archived")
    last_verified_at: datetime | str = Field(..., description="ISO 8601 verification timestamp")


class SchemeSummaryResponse(SchemeBase):
    """Compact summary of a scheme for catalog listing."""

    id: str | None = None
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None


class SchemeDetailResponse(SchemeSummaryResponse):
    """Comprehensive scheme model including all 6 canonical relational child datasets."""

    rules: list[SchemeRuleResponse] = Field(
        default_factory=list,
        description="Eligibility rules (rule_purpose = 'eligibility')",
    )
    exclusion_rules: list[SchemeRuleResponse] = Field(
        default_factory=list,
        description="Exclusion criteria rules (rule_purpose = 'exclusion')",
    )
    documents: list[SchemeDocumentResponse] = Field(
        default_factory=list,
        description="Required and recommended documents",
    )
    tutorial_steps: list[TutorialStepResponse] = Field(
        default_factory=list,
        description="Sequential application tutorial guidance",
    )
    profile_fields: list[SchemeProfileFieldResponse] = Field(
        default_factory=list,
        description="Profile fields evaluated for eligibility",
    )
    verification: list[SchemeVerificationResponse] = Field(
        default_factory=list,
        description="Verification history and helpline contacts",
    )
