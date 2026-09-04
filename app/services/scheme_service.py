"""Scheme service providing domain business operations for scheme catalog and details."""


from app.repositories.scheme_repository import SchemeRepository
from app.schemas.scheme import (
    SchemeDetailResponse,
    SchemeDocumentResponse,
    SchemeProfileFieldResponse,
    SchemeRuleResponse,
    SchemeSummaryResponse,
    SchemeVerificationResponse,
    TutorialStepResponse,
)


class SchemeNotFoundError(Exception):
    """Raised when a scheme cannot be found by its canonical code or ID."""

    def __init__(self, scheme_code_or_id: str):
        self.scheme_code_or_id = scheme_code_or_id
        super().__init__(f"Scheme not found: '{scheme_code_or_id}'")


class SchemeService:
    """Service layer managing scheme catalog and related data access."""

    def __init__(self, repository: SchemeRepository | None = None):
        self.repository = repository or SchemeRepository()

    def list_schemes(
        self,
        scheme_type: str | None = None,
        status: str | None = None,
        ministry: str | None = None,
    ) -> list[SchemeSummaryResponse]:
        """List all available schemes, optionally filtered."""
        return self.repository.get_all(scheme_type=scheme_type, status=status, ministry=ministry)

    def get_scheme_detail(self, scheme_code: str) -> SchemeDetailResponse:
        """Get full details of a scheme by scheme_code or raise SchemeNotFoundError."""
        detail = self.repository.get_by_code(scheme_code)
        if not detail:
            raise SchemeNotFoundError(scheme_code)
        return detail

    def get_scheme_by_id(self, scheme_id: str) -> SchemeDetailResponse:
        """Get full details of a scheme by UUID or raise SchemeNotFoundError."""
        detail = self.repository.get_by_id(scheme_id)
        if not detail:
            raise SchemeNotFoundError(scheme_id)
        return detail

    def get_scheme_by_code_or_id(self, identifier: str) -> SchemeDetailResponse:
        """Get full details of a scheme by scheme_code or by UUID, or raise SchemeNotFoundError."""
        detail = self.repository.get_by_code_or_id(identifier)
        if not detail:
            raise SchemeNotFoundError(identifier)
        return detail

    def list_schemes_paged(
        self,
        scheme_type: str | None = None,
        status: str | None = "active",
        ministry: str | None = None,
        search: str | None = None,
        target_group: str | None = None,
        state: str | None = None,
        limit: int | None = 50,
        offset: int | None = 0,
    ) -> tuple[list[SchemeSummaryResponse], int]:
        """List schemes with advanced filtering and total count."""
        return self.repository.get_paged(
            scheme_type=scheme_type,
            status=status,
            ministry=ministry,
            search=search,
            target_group=target_group,
            state=state,
            limit=limit,
            offset=offset,
        )

    def get_scheme_rules(
        self, scheme_code: str, rule_purpose: str | None = None
    ) -> list[SchemeRuleResponse]:
        """Get rules for a scheme. Verifies scheme existence first."""
        # Ensure scheme exists
        self.get_scheme_detail(scheme_code)
        return self.repository.get_rules(scheme_code, rule_purpose=rule_purpose)

    def get_scheme_documents(
        self,
        scheme_code: str,
        document_type: str | None = None,
        is_mandatory: bool | None = None,
    ) -> list[SchemeDocumentResponse]:
        """Get documents for a scheme. Verifies scheme existence first."""
        self.get_scheme_detail(scheme_code)
        return self.repository.get_documents(
            scheme_code, document_type=document_type, is_mandatory=is_mandatory
        )

    def get_tutorial_steps(self, scheme_code: str) -> list[TutorialStepResponse]:
        """Get ordered tutorial steps for a scheme. Verifies scheme existence first."""
        self.get_scheme_detail(scheme_code)
        return self.repository.get_tutorial_steps(scheme_code)

    def get_profile_fields(
        self, scheme_code: str, is_required: bool | None = None
    ) -> list[SchemeProfileFieldResponse]:
        """Get profile fields required by a scheme. Verifies scheme existence first."""
        self.get_scheme_detail(scheme_code)
        return self.repository.get_profile_fields(scheme_code, is_required=is_required)

    def get_verification(self, scheme_code: str) -> list[SchemeVerificationResponse]:
        """Get verification records for a scheme. Verifies scheme existence first."""
        self.get_scheme_detail(scheme_code)
        return self.repository.get_verification(scheme_code)
