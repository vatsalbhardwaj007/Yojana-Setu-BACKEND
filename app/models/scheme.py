"""Database entity models representing M4's six canonical scheme tables."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SchemeRuleModel:
    """Represents a row in the `scheme_rules` table."""

    id: str
    scheme_id: str
    rule_group: str
    field: str
    operator: str
    value: Any
    description: str
    rule_purpose: str = "eligibility"  # 'eligibility' or 'exclusion'
    created_at: str | None = None


@dataclass
class SchemeDocumentModel:
    """Represents a row in the `scheme_documents` table."""

    id: str
    scheme_id: str
    document_type: str
    document_name: str
    is_mandatory: bool = True
    description: str | None = None
    created_at: str | None = None


@dataclass
class TutorialStepModel:
    """Represents a row in the `tutorial_steps` table."""

    id: str
    scheme_id: str
    step_number: int
    title: str
    description: str
    tips: str | None = None
    created_at: str | None = None


@dataclass
class SchemeVerificationModel:
    """Represents a row in the `scheme_verification` table."""

    id: str
    scheme_id: str
    verification_method: str
    verification_url: str | None = None
    helpline_number: str | None = None
    last_verified_at: str | None = None
    notes: str | None = None
    created_at: str | None = None


@dataclass
class SchemeProfileFieldModel:
    """Represents a row in the `scheme_profile_fields` table."""

    id: str
    scheme_id: str
    field_name: str
    field_type: str
    is_required: bool = True
    allowed_values: list[Any] | None = None
    description: str | None = None
    created_at: str | None = None


@dataclass
class SchemeModel:
    """Represents a row in the `schemes` table."""

    id: str
    scheme_code: str
    name: str
    description: str
    ministry: str
    department: str
    scheme_type: str
    status: str = "active"
    aliases: list[str] = field(default_factory=list)
    target_groups: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    official_url: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    last_verified_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    # Related entities (populated when joining)
    rules: list[SchemeRuleModel] = field(default_factory=list)
    exclusion_rules: list[SchemeRuleModel] = field(default_factory=list)
    documents: list[SchemeDocumentModel] = field(default_factory=list)
    tutorial_steps: list[TutorialStepModel] = field(default_factory=list)
    profile_fields: list[SchemeProfileFieldModel] = field(default_factory=list)
    verification: list[SchemeVerificationModel] = field(default_factory=list)
