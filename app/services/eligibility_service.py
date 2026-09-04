"""Eligibility service orchestrating repository queries and rule engine evaluation."""

from typing import Any, Dict, Optional

from app.repositories.scheme_repository import SchemeRepository
from app.rules.engine import EligibilityEngine
from app.schemas.eligibility import EligibilityCheckResponse
from app.services.scheme_service import SchemeNotFoundError


class EligibilityService:
    """Service orchestrating scheme retrieval and deterministic rule evaluation."""

    def __init__(self, repository: Optional[SchemeRepository] = None):
        self.repository = repository or SchemeRepository()

    def check_eligibility(
        self, scheme_code: str, profile: Dict[str, Any]
    ) -> EligibilityCheckResponse:
        """Retrieve canonical scheme rules from database and evaluate eligibility."""
        scheme_detail = self.repository.get_by_code(scheme_code)
        if not scheme_detail:
            raise SchemeNotFoundError(scheme_code)

        return EligibilityEngine.evaluate(
            scheme_code=scheme_code,
            eligibility_rules=scheme_detail.rules,
            exclusion_rules=scheme_detail.exclusion_rules,
            profile=profile,
        )
