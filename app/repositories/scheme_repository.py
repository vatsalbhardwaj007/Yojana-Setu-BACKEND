"""Repository layer for querying government schemes and canonical relations."""

import json
from typing import Any, ClassVar

from app.db.session import get_db_connection, init_db
from app.schemas.scheme import (
    SchemeDetailResponse,
    SchemeDocumentResponse,
    SchemeProfileFieldResponse,
    SchemeRuleResponse,
    SchemeSummaryResponse,
    SchemeVerificationResponse,
    TutorialStepResponse,
)


class SchemeRepository:
    """Repository providing data access for the six canonical scheme tables."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path
        init_db(self.db_path, seed_if_empty=True)

    # -----------------------------------------------------------------------
    # Helper mappers
    # -----------------------------------------------------------------------
    @staticmethod
    def _parse_json(val: Any, default: Any = None) -> Any:
        if val is None:
            return default
        if isinstance(val, (list, dict)):
            return val
        try:
            return json.loads(val)
        except (ValueError, TypeError):
            return default

    @classmethod
    def _map_scheme_summary(cls, row: Any) -> SchemeSummaryResponse:
        return SchemeSummaryResponse(
            id=row["id"],
            scheme_code=row["scheme_code"],
            name=row["name"],
            description=row["description"],
            ministry=row["ministry"],
            department=row["department"],
            scheme_type=row["scheme_type"],
            status=row["status"],
            aliases=cls._parse_json(row["aliases"], []),
            target_groups=cls._parse_json(row["target_groups"], []),
            tags=cls._parse_json(row["tags"], []),
            benefits=cls._parse_json(row["benefits"], []),
            official_url=row["official_url"],
            effective_from=row["effective_from"],
            effective_to=row["effective_to"],
            last_verified_at=row["last_verified_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @classmethod
    def _map_rule(cls, row: Any) -> SchemeRuleResponse:
        return SchemeRuleResponse(
            id=row["id"],
            scheme_id=row["scheme_id"],
            rule_group=row["rule_group"],
            field=row["field"],
            operator=row["operator"],
            value=cls._parse_json(row["value"]),
            description=row["description"],
            rule_purpose=row["rule_purpose"],
            created_at=row["created_at"],
        )

    @classmethod
    def _map_document(cls, row: Any) -> SchemeDocumentResponse:
        return SchemeDocumentResponse(
            id=row["id"],
            scheme_id=row["scheme_id"],
            document_type=row["document_type"],
            document_name=row["document_name"],
            is_mandatory=bool(row["is_mandatory"]),
            description=row["description"],
            created_at=row["created_at"],
        )

    @classmethod
    def _map_tutorial_step(cls, row: Any) -> TutorialStepResponse:
        return TutorialStepResponse(
            id=row["id"],
            scheme_id=row["scheme_id"],
            step_number=row["step_number"],
            title=row["title"],
            description=row["description"],
            tips=row["tips"],
            created_at=row["created_at"],
        )

    @classmethod
    def _map_verification(cls, row: Any) -> SchemeVerificationResponse:
        return SchemeVerificationResponse(
            id=row["id"],
            scheme_id=row["scheme_id"],
            verification_method=row["verification_method"],
            verification_url=row["verification_url"],
            helpline_number=row["helpline_number"],
            last_verified_at=row["last_verified_at"],
            notes=row["notes"],
            created_at=row["created_at"],
        )

    @classmethod
    def _map_profile_field(cls, row: Any) -> SchemeProfileFieldResponse:
        return SchemeProfileFieldResponse(
            id=row["id"],
            scheme_id=row["scheme_id"],
            field_name=row["field_name"],
            field_type=row["field_type"],
            is_required=bool(row["is_required"]),
            allowed_values=cls._parse_json(row["allowed_values"]),
            description=row["description"],
            created_at=row["created_at"],
        )

    # -----------------------------------------------------------------------
    # Query methods
    # -----------------------------------------------------------------------
    def get_all(
        self,
        scheme_type: str | None = None,
        status: str | None = None,
        ministry: str | None = None,
    ) -> list[SchemeSummaryResponse]:
        """List schemes with optional filters."""
        query = "SELECT * FROM schemes WHERE 1=1"
        params: list[Any] = []

        if scheme_type:
            query += " AND scheme_type = ?"
            params.append(scheme_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        if ministry:
            query += " AND ministry = ?"
            params.append(ministry)

        query += " ORDER BY name ASC"

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._map_scheme_summary(row) for row in rows]

    def get_paged(
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
        where_clauses: list[str] = ["1=1"]
        params: list[Any] = []

        if scheme_type:
            st_pattern = f"%{scheme_type.strip().lower()}%"
            where_clauses.append("(LOWER(scheme_type) = ? OR LOWER(tags) LIKE ? OR LOWER(description) LIKE ?)")
            params.extend([scheme_type.strip().lower(), st_pattern, st_pattern])
        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if ministry:
            where_clauses.append("ministry = ?")
            params.append(ministry)
        if search:
            search_pattern = f"%{search.strip().lower()}%"
            where_clauses.append(
                "(LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(scheme_code) LIKE ? OR LOWER(tags) LIKE ?)"
            )
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        if target_group:
            tg_pattern = f"%{target_group.strip().lower()}%"
            where_clauses.append("(LOWER(target_groups) LIKE ? OR LOWER(tags) LIKE ?)")
            params.extend([tg_pattern, tg_pattern])
        if state:
            state_pattern = f"%{state.strip().lower()}%"
            where_clauses.append("(LOWER(tags) LIKE ? OR LOWER(description) LIKE ? OR LOWER(benefits) LIKE ?)")
            params.extend([state_pattern, state_pattern, state_pattern])

        where_sql = " AND ".join(where_clauses)

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            # Count total matching
            cursor.execute(f"SELECT COUNT(*) FROM schemes WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            # Fetch paged items
            query = f"SELECT * FROM schemes WHERE {where_sql} ORDER BY name ASC"
            query_params = list(params)
            if limit is not None:
                query += " LIMIT ?"
                query_params.append(limit)
            if offset is not None:
                query += " OFFSET ?"
                query_params.append(offset)

            cursor.execute(query, query_params)
            rows = cursor.fetchall()
            items = [self._map_scheme_summary(row) for row in rows]
            return items, total

    def get_by_code(self, scheme_code: str) -> SchemeDetailResponse | None:
        """Retrieve complete scheme details by its unique canonical code."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM schemes WHERE scheme_code = ?", (scheme_code,))
            row = cursor.fetchone()
            if not row:
                return None

            scheme_id = row["id"]
            return self._build_scheme_detail(conn, row, scheme_id)

    ALIAS_MAP: ClassVar[dict[str, str]] = {
        "pm_jay": "ayushman_bharat_pm_jay",
        "pmjay": "ayushman_bharat_pm_jay",
        "pm-jay": "ayushman_bharat_pm_jay",
        "pmay_u": "pmay_urban",
        "pmayu": "pmay_urban",
        "pmay-u": "pmay_urban",
        "pmay_g": "pmay_gramin",
        "pmayg": "pmay_gramin",
        "pmay-g": "pmay_gramin",
        "pmkisan": "pm_kisan",
        "pm-kisan": "pm_kisan",
    }

    def _resolve_scheme_id(self, conn: Any, identifier: str) -> str | None:
        """Find internal scheme UUID from scheme_code, UUID, or known alias."""
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM schemes WHERE scheme_code = ? OR id = ?", (identifier, identifier))
        row = cursor.fetchone()
        if row:
            return row["id"]
        normalized = identifier.strip().lower().replace("-", "_")
        canonical = self.ALIAS_MAP.get(normalized)
        if canonical:
            cursor.execute("SELECT id FROM schemes WHERE scheme_code = ?", (canonical,))
            row = cursor.fetchone()
            if row:
                return row["id"]
        return None

    def get_by_code_or_id(self, identifier: str) -> SchemeDetailResponse | None:
        """Retrieve scheme by scheme_code, UUID, or known alias."""
        detail = self.get_by_code(identifier)
        if detail:
            return detail
        detail = self.get_by_id(identifier)
        if detail:
            return detail
        normalized = identifier.strip().lower().replace("-", "_")
        canonical = self.ALIAS_MAP.get(normalized)
        if canonical:
            return self.get_by_code(canonical)
        return None

    def get_by_id(self, scheme_id: str) -> SchemeDetailResponse | None:
        """Retrieve complete scheme details by UUID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM schemes WHERE id = ?", (scheme_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return self._build_scheme_detail(conn, row, scheme_id)

    def _build_scheme_detail(
        self, conn: Any, scheme_row: Any, scheme_id: str
    ) -> SchemeDetailResponse:
        """Fetch all child datasets and assemble SchemeDetailResponse."""
        cursor = conn.cursor()

        # Rules (eligibility)
        cursor.execute(
            "SELECT * FROM scheme_rules WHERE scheme_id = ? AND rule_purpose = 'eligibility' ORDER BY rule_group, field",
            (scheme_id,),
        )
        rules = [self._map_rule(r) for r in cursor.fetchall()]

        # Exclusion Rules
        cursor.execute(
            "SELECT * FROM scheme_rules WHERE scheme_id = ? AND rule_purpose = 'exclusion' ORDER BY rule_group, field",
            (scheme_id,),
        )
        exclusion_rules = [self._map_rule(r) for r in cursor.fetchall()]

        # Documents
        cursor.execute(
            "SELECT * FROM scheme_documents WHERE scheme_id = ? ORDER BY is_mandatory DESC, document_name ASC",
            (scheme_id,),
        )
        documents = [self._map_document(r) for r in cursor.fetchall()]

        # Tutorial Steps
        cursor.execute(
            "SELECT * FROM tutorial_steps WHERE scheme_id = ? ORDER BY step_number ASC",
            (scheme_id,),
        )
        tutorials = [self._map_tutorial_step(r) for r in cursor.fetchall()]

        # Profile Fields
        cursor.execute(
            "SELECT * FROM scheme_profile_fields WHERE scheme_id = ? ORDER BY is_required DESC, field_name ASC",
            (scheme_id,),
        )
        profile_fields = [self._map_profile_field(r) for r in cursor.fetchall()]

        # Verification
        cursor.execute(
            "SELECT * FROM scheme_verification WHERE scheme_id = ? ORDER BY last_verified_at DESC",
            (scheme_id,),
        )
        verification = [self._map_verification(r) for r in cursor.fetchall()]

        summary = self._map_scheme_summary(scheme_row)

        return SchemeDetailResponse(
            **summary.model_dump(),
            rules=rules,
            exclusion_rules=exclusion_rules,
            documents=documents,
            tutorial_steps=tutorials,
            profile_fields=profile_fields,
            verification=verification,
        )

    def get_rules(
        self, scheme_code: str, rule_purpose: str | None = None
    ) -> list[SchemeRuleResponse]:
        """Retrieve rules for a scheme, optionally filtered by rule_purpose ('eligibility' or 'exclusion')."""
        with get_db_connection(self.db_path) as conn:
            scheme_id = self._resolve_scheme_id(conn, scheme_code)
            if not scheme_id:
                return []

            cursor = conn.cursor()
            if rule_purpose:
                cursor.execute(
                    "SELECT * FROM scheme_rules WHERE scheme_id = ? AND rule_purpose = ? ORDER BY rule_group, field",
                    (scheme_id, rule_purpose),
                )
            else:
                cursor.execute(
                    "SELECT * FROM scheme_rules WHERE scheme_id = ? ORDER BY rule_purpose, rule_group, field",
                    (scheme_id,),
                )
            return [self._map_rule(r) for r in cursor.fetchall()]

    def get_documents(
        self,
        scheme_code: str,
        document_type: str | None = None,
        is_mandatory: bool | None = None,
    ) -> list[SchemeDocumentResponse]:
        """Retrieve documents for a scheme with optional type and mandatory filters."""
        with get_db_connection(self.db_path) as conn:
            scheme_id = self._resolve_scheme_id(conn, scheme_code)
            if not scheme_id:
                return []

            cursor = conn.cursor()
            query = "SELECT * FROM scheme_documents WHERE scheme_id = ?"
            params: list[Any] = [scheme_id]

            if document_type:
                query += " AND document_type = ?"
                params.append(document_type)
            if is_mandatory is not None:
                query += " AND is_mandatory = ?"
                params.append(1 if is_mandatory else 0)

            query += " ORDER BY is_mandatory DESC, document_name ASC"
            cursor.execute(query, params)
            return [self._map_document(r) for r in cursor.fetchall()]

    def get_tutorial_steps(self, scheme_code: str) -> list[TutorialStepResponse]:
        """Retrieve ordered tutorial steps for a scheme."""
        with get_db_connection(self.db_path) as conn:
            scheme_id = self._resolve_scheme_id(conn, scheme_code)
            if not scheme_id:
                return []

            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tutorial_steps WHERE scheme_id = ? ORDER BY step_number ASC",
                (scheme_id,),
            )
            return [self._map_tutorial_step(r) for r in cursor.fetchall()]

    def get_profile_fields(
        self, scheme_code: str, is_required: bool | None = None
    ) -> list[SchemeProfileFieldResponse]:
        """Retrieve profile fields required/evaluated by a scheme."""
        with get_db_connection(self.db_path) as conn:
            scheme_id = self._resolve_scheme_id(conn, scheme_code)
            if not scheme_id:
                return []

            cursor = conn.cursor()
            query = "SELECT * FROM scheme_profile_fields WHERE scheme_id = ?"
            params: list[Any] = [scheme_id]

            if is_required is not None:
                query += " AND is_required = ?"
                params.append(1 if is_required else 0)

            query += " ORDER BY is_required DESC, field_name ASC"
            cursor.execute(query, params)
            return [self._map_profile_field(r) for r in cursor.fetchall()]

    def get_verification(self, scheme_code: str) -> list[SchemeVerificationResponse]:
        """Retrieve verification records and contact info for a scheme."""
        with get_db_connection(self.db_path) as conn:
            scheme_id = self._resolve_scheme_id(conn, scheme_code)
            if not scheme_id:
                return []

            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM scheme_verification WHERE scheme_id = ? ORDER BY last_verified_at DESC",
                (scheme_id,),
            )
            return [self._map_verification(r) for r in cursor.fetchall()]
