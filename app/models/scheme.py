"""Database entity models representing M4's six canonical scheme tables."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union


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
    created_at: Optional[str] = None


@dataclass
class SchemeDocumentModel:
    """Represents a row in the `scheme_documents` table."""

    id: str
    scheme_id: str
    document_type: str
    document_name: str
    is_mandatory: bool = True
    description: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class TutorialStepModel:
    """Represents a row in the `tutorial_steps` table."""

    id: str
    scheme_id: str
    step_number: int
    title: str
    description: str
    tips: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class SchemeVerificationModel:
    """Represents a row in the `scheme_verification` table."""

    id: str
    scheme_id: str
    verification_method: str
    verification_url: Optional[str] = None
    helpline_number: Optional[str] = None
    last_verified_at: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class SchemeProfileFieldModel:
    """Represents a row in the `scheme_profile_fields` table."""

    id: str
    scheme_id: str
    field_name: str
    field_type: str
    is_required: bool = True
    allowed_values: Optional[List[Any]] = None
    description: Optional[str] = None
    created_at: Optional[str] = None


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
    aliases: List[str] = field(default_factory=list)
    target_groups: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    official_url: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    last_verified_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Related entities (populated when joining)
    rules: List[SchemeRuleModel] = field(default_factory=list)
    exclusion_rules: List[SchemeRuleModel] = field(default_factory=list)
    documents: List[SchemeDocumentModel] = field(default_factory=list)
    tutorial_steps: List[TutorialStepModel] = field(default_factory=list)
    profile_fields: List[SchemeProfileFieldModel] = field(default_factory=list)
    verification: List[SchemeVerificationModel] = field(default_factory=list)
