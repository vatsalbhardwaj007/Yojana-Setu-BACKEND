"""Comprehensive tests for Phase 1 Data & Backend Integration.

Validates the 10 Phase 1 testing requirements:
1. Database/data layer initialization
2. Scheme retrieval (15 canonical schemes)
3. Scheme lookup by scheme_code
4. Scheme-not-found handling (404 and None)
5. Rule retrieval
6. Eligibility vs exclusion rule separation
7. Profile-field retrieval
8. Document retrieval
9. Tutorial retrieval
10. Related-data integrity across all 15 schemes
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.db.session import (
    get_db_connection,
    init_db,
)
from app.main import app
from app.repositories.scheme_repository import SchemeRepository
from app.schemas.scheme import (
    SchemeDetailResponse,
    SchemeSummaryResponse,
)
from app.services.scheme_service import SchemeNotFoundError, SchemeService


@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary SQLite database initialized with all 15 canonical schemes."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(db_path=path, seed_if_empty=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def repo(test_db_path):
    """Scheme repository pointing to test database."""
    return SchemeRepository(db_path=test_db_path)


@pytest.fixture
def service(repo):
    """Scheme service with test repository."""
    return SchemeService(repository=repo)


from app.api.v1.schemes import get_scheme_service


@pytest.fixture
def client(service):
    """TestClient for FastAPI app using test database dependency override."""
    app.dependency_overrides[get_scheme_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Database / Data Layer Initialization
# ---------------------------------------------------------------------------
def test_database_initialization(test_db_path):
    """Requirement 1: Database initializes the six canonical tables correctly."""
    with get_db_connection(test_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row["name"] for row in cursor.fetchall()}

    expected_tables = {
        "schemes",
        "scheme_rules",
        "scheme_documents",
        "tutorial_steps",
        "scheme_verification",
        "scheme_profile_fields",
    }
    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"


# ---------------------------------------------------------------------------
# 2. Scheme Retrieval (All 15 Canonical Schemes)
# ---------------------------------------------------------------------------
def test_scheme_retrieval(service):
    """Requirement 2: Backend retrieves all 15 canonical government schemes."""
    schemes = service.list_schemes()
    assert len(schemes) == 15
    for scheme in schemes:
        assert isinstance(scheme, SchemeSummaryResponse)
        assert scheme.scheme_code
        assert scheme.name
        assert scheme.ministry
        assert scheme.department
        assert scheme.scheme_type
        assert scheme.status in {"active", "inactive", "archived"}
        assert scheme.effective_from


def test_scheme_filtering(service):
    """Verify scheme listing with type and status filters."""
    pension_schemes = service.list_schemes(scheme_type="pension")
    assert len(pension_schemes) >= 1
    for s in pension_schemes:
        assert s.scheme_type == "pension"

    active_schemes = service.list_schemes(status="active")
    assert len(active_schemes) == 15


# ---------------------------------------------------------------------------
# 3. Scheme Lookup by scheme_code
# ---------------------------------------------------------------------------
def test_scheme_lookup_by_code(service):
    """Requirement 3: Fetch scheme detail by canonical snake_case scheme_code."""
    scheme = service.get_scheme_detail("pm_kisan")
    assert isinstance(scheme, SchemeDetailResponse)
    assert scheme.scheme_code == "pm_kisan"
    assert scheme.name == "Pradhan Mantri Kisan Samman Nidhi"
    assert scheme.ministry == "Ministry of Agriculture and Farmers Welfare"
    assert scheme.official_url == "https://pmkisan.gov.in/"
    assert len(scheme.benefits) > 0

    # Lookup by ID
    scheme_by_id = service.get_scheme_by_id(scheme.id)
    assert scheme_by_id.scheme_code == "pm_kisan"


# ---------------------------------------------------------------------------
# 4. Scheme-Not-Found Handling
# ---------------------------------------------------------------------------
def test_scheme_not_found_handling(service, repo, client):
    """Requirement 4: Non-existent scheme code raises SchemeNotFoundError and returns 404 via API."""
    with pytest.raises(SchemeNotFoundError):
        service.get_scheme_detail("non_existent_scheme_xyz")

    assert repo.get_by_code("non_existent_scheme_xyz") is None
    assert repo.get_by_id("00000000-0000-0000-0000-000000000000") is None

    # HTTP API test
    resp = client.get("/api/v1/schemes/non_existent_scheme_xyz")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. Rule Retrieval
# ---------------------------------------------------------------------------
def test_rule_retrieval(service):
    """Requirement 5: Retrieve rules for a scheme."""
    rules = service.get_scheme_rules("pm_kisan")
    assert len(rules) > 0
    for r in rules:
        assert r.rule_group
        assert r.field
        assert r.operator in {"=", "!=", ">=", "<=", ">", "<", "in", "not_in", "exists", "between"}
        assert r.description
        assert r.rule_purpose in {"eligibility", "exclusion"}


# ---------------------------------------------------------------------------
# 6. Eligibility vs Exclusion Rule Separation
# ---------------------------------------------------------------------------
def test_eligibility_vs_exclusion_rule_separation(service):
    """Requirement 6: Eligibility rules and exclusion criteria are strictly separated."""
    scheme = service.get_scheme_detail("pm_kisan")

    # In pm_kisan: 1 eligibility rule (cultivable land) and 8 exclusion rules
    assert len(scheme.rules) == 1
    assert scheme.rules[0].rule_purpose == "eligibility"
    assert scheme.rules[0].field == "has_cultivable_land_in_name"

    assert len(scheme.exclusion_rules) == 8
    for er in scheme.exclusion_rules:
        assert er.rule_purpose == "exclusion"

    # Query separately through service
    eligibility_only = service.get_scheme_rules("pm_kisan", rule_purpose="eligibility")
    assert len(eligibility_only) == 1
    assert all(r.rule_purpose == "eligibility" for r in eligibility_only)

    exclusion_only = service.get_scheme_rules("pm_kisan", rule_purpose="exclusion")
    assert len(exclusion_only) == 8
    assert all(r.rule_purpose == "exclusion" for r in exclusion_only)


# ---------------------------------------------------------------------------
# 7. Profile-Field Retrieval
# ---------------------------------------------------------------------------
def test_profile_field_retrieval(service):
    """Requirement 7: Retrieve user profile fields required to evaluate eligibility."""
    fields = service.get_profile_fields("pm_kisan")
    assert len(fields) == 9
    field_names = {f.field_name for f in fields}
    assert "has_cultivable_land_in_name" in field_names
    assert "is_institutional_land_holder" in field_names
    assert "monthly_pension" in field_names
    assert "paid_income_tax_last_assessment_year" in field_names

    for f in fields:
        assert f.field_type in {"text", "number", "date", "boolean", "select"}
        assert isinstance(f.is_required, bool)


# ---------------------------------------------------------------------------
# 8. Document Retrieval
# ---------------------------------------------------------------------------
def test_document_retrieval(service):
    """Requirement 8: Retrieve mandatory and optional documents."""
    docs = service.get_scheme_documents("pm_kisan")
    assert len(docs) == 3
    doc_types = {d.document_type for d in docs}
    assert "identity_proof" in doc_types
    assert "land_record" in doc_types
    assert "bank_details" in doc_types
    assert all(d.is_mandatory for d in docs)

    # Test schemes with optional documents (e.g. pm_svanidhi)
    svanidhi_docs = service.get_scheme_documents("pm_svanidhi")
    assert len(svanidhi_docs) > 0


# ---------------------------------------------------------------------------
# 9. Tutorial Retrieval
# ---------------------------------------------------------------------------
def test_tutorial_retrieval(service):
    """Requirement 9: Retrieve sequential tutorial application guidance steps."""
    steps = service.get_tutorial_steps("pm_kisan")
    assert len(steps) == 7
    step_numbers = [s.step_number for s in steps]
    assert step_numbers == [1, 2, 3, 4, 5, 6, 7]
    for s in steps:
        assert s.title
        assert s.description


# ---------------------------------------------------------------------------
# 10. Related-Data Integrity Across All 15 Schemes
# ---------------------------------------------------------------------------
def test_related_data_integrity(service):
    """Requirement 10: Validate data integrity across all 15 schemes."""
    schemes = service.list_schemes()
    assert len(schemes) == 15

    total_rules = 0
    total_exclusion_rules = 0
    total_docs = 0
    total_tutorials = 0
    total_profile_fields = 0
    total_verifications = 0

    for summary in schemes:
        detail = service.get_scheme_detail(summary.scheme_code)
        assert detail.id == summary.id
        assert detail.scheme_code == summary.scheme_code

        # Foreign key consistency
        for r in detail.rules:
            assert r.scheme_id == detail.id
            assert r.rule_purpose == "eligibility"
        for er in detail.exclusion_rules:
            assert er.scheme_id == detail.id
            assert er.rule_purpose == "exclusion"
        for d in detail.documents:
            assert d.scheme_id == detail.id
        for s in detail.tutorial_steps:
            assert s.scheme_id == detail.id
        for pf in detail.profile_fields:
            assert pf.scheme_id == detail.id
        for v in detail.verification:
            assert v.scheme_id == detail.id

        total_rules += len(detail.rules)
        total_exclusion_rules += len(detail.exclusion_rules)
        total_docs += len(detail.documents)
        total_tutorials += len(detail.tutorial_steps)
        total_profile_fields += len(detail.profile_fields)
        total_verifications += len(detail.verification)

    assert total_rules > 40
    assert total_exclusion_rules > 30
    assert total_docs > 70
    assert total_tutorials > 100
    assert total_profile_fields > 150
    assert total_verifications >= 15


# ---------------------------------------------------------------------------
# 11. REST API Integration Tests
# ---------------------------------------------------------------------------
def test_api_list_schemes(client):
    """Test GET /api/v1/schemes returns 200 and 15 schemes."""
    resp = client.get("/api/v1/schemes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 15


def test_api_get_scheme_detail(client):
    """Test GET /api/v1/schemes/atal_pension_yojana returns 200 with full details."""
    resp = client.get("/api/v1/schemes/atal_pension_yojana")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scheme_code"] == "atal_pension_yojana"
    assert "rules" in data
    assert "exclusion_rules" in data
    assert "documents" in data
    assert "tutorial_steps" in data
    assert "profile_fields" in data
    assert "verification" in data


def test_api_get_scheme_rules_filtered(client):
    """Test GET /api/v1/schemes/{code}/rules with purpose filter."""
    resp = client.get("/api/v1/schemes/pm_kisan/rules?rule_purpose=eligibility")
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) == 1
    assert rules[0]["rule_purpose"] == "eligibility"

    resp_excl = client.get("/api/v1/schemes/pm_kisan/rules?rule_purpose=exclusion")
    assert resp_excl.status_code == 200
    excl = resp_excl.json()
    assert len(excl) == 8
    assert all(r["rule_purpose"] == "exclusion" for r in excl)


def test_api_get_scheme_documents(client):
    """Test GET /api/v1/schemes/{code}/documents."""
    resp = client.get("/api/v1/schemes/pm_kisan/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert docs["scheme_code"] == "pm_kisan"
    assert len(docs["documents"]) == 3


def test_api_get_scheme_tutorials(client):
    """Test GET /api/v1/schemes/{code}/tutorials."""
    resp = client.get("/api/v1/schemes/pm_kisan/tutorials")
    assert resp.status_code == 200
    tutorials = resp.json()
    assert tutorials["scheme_code"] == "pm_kisan"
    assert len(tutorials["steps"]) == 7


def test_api_get_scheme_profile_fields(client):
    """Test GET /api/v1/schemes/{code}/profile-fields."""
    resp = client.get("/api/v1/schemes/pm_kisan/profile-fields")
    assert resp.status_code == 200
    fields = resp.json()
    assert len(fields) == 9
