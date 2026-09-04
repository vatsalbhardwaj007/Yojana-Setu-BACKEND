"""Integration tests for Phase 3 API layer.

Covers all 19 scenarios specified in the Phase 3 specification:
1. POST /profile
2. GET /profile
3. PUT /profile
4. Missing profile (GET/PUT 404 when profile not found)
5. GET /schemes
6. GET /schemes with filters
7. GET /schemes/{id}
8. Invalid scheme (404)
9. POST /eligibility/check — Eligible
10. POST /eligibility/check — Potentially Eligible
11. POST /eligibility/check — Not Eligible
12. GET /schemes/{id}/documents for valid scheme
13. GET /schemes/{id}/documents for invalid scheme
14. GET /schemes/{id}/tutorial for valid scheme
15. GET /schemes/{id}/tutorial for invalid scheme
16. POST /schemes/recommend
17. Recommendation with minimal profile
18. Recommendation with richer profile
19. Verify recommendations do not claim legal eligibility
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.session import init_db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema and seed data are initialized before each test."""
    init_db()


# =====================================================================
# 1. PROFILE API TESTS (Scenarios 1 - 4)
# =====================================================================

def test_01_post_profile():
    """Test POST /profile creates a new profile and strips sensitive fields."""
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    payload = {
        "user_id": user_id,
        "age": 34,
        "state": "Uttar Pradesh",
        "gender": "male",
        "occupation": "farmer",
        "category": "General",
        "annual_income": 120000.0,
        "attributes": {
            "has_cultivable_land_in_name": True,
            "aadhaar_number": "1234-5678-9012",  # Should be stripped
            "password": "secret_password",        # Should be stripped
        }
    }
    response = client.post("/profile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    prof = data.get("profile", {})
    assert prof["age"] == 34
    assert prof["state"] == "Uttar Pradesh"
    assert prof["occupation"] == "farmer"
    # Verify sensitive data was stripped
    assert "aadhaar_number" not in prof.get("attributes", {})
    assert "password" not in prof.get("attributes", {})


def test_02_get_profile():
    """Test GET /profile retrieves stored profile."""
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    # Create profile first
    client.post("/profile", json={
        "user_id": user_id,
        "age": 28,
        "state": "Bihar",
        "category": "OBC"
    })

    # Retrieve profile
    response = client.get(f"/profile?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    prof = data.get("profile", {})
    assert prof["age"] == 28
    assert prof["state"] == "Bihar"
    assert prof["category"] == "OBC"


def test_03_put_profile():
    """Test PUT /profile updates an existing profile without wiping fields."""
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    # Create
    client.post("/profile", json={
        "user_id": user_id,
        "age": 40,
        "state": "Maharashtra",
        "occupation": "artisan",
        "attributes": {"initial_flag": True}
    })

    # Partial update
    update_payload = {
        "user_id": user_id,
        "annual_income": 95000.0,
        "attributes": {"new_flag": "yes"}
    }
    response = client.put("/profile", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    prof = data.get("profile", {})
    assert prof["age"] == 40  # Preserved
    assert prof["state"] == "Maharashtra"  # Preserved
    assert prof["occupation"] == "artisan"  # Preserved
    assert prof["annual_income"] == 95000.0
    # Attributes merged
    assert prof["attributes"].get("initial_flag") is True
    assert prof["attributes"].get("new_flag") == "yes"


def test_04_missing_profile_returns_404():
    """Test GET and PUT return 404 when profile does not exist."""
    non_existent = "non_existent_user_99999"
    get_res = client.get(f"/profile?user_id={non_existent}")
    assert get_res.status_code == 404
    assert "Profile not found" in get_res.json()["detail"]

    put_res = client.put("/profile", json={"user_id": non_existent, "age": 50})
    assert put_res.status_code == 404
    assert "Profile not found" in put_res.json()["detail"]


# =====================================================================
# 2. SCHEMES CATALOG API TESTS (Scenarios 5 - 8)
# =====================================================================

def test_05_get_schemes_paged():
    """Test GET /schemes returns list formatted with items and total."""
    response = client.get("/schemes")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 15
    assert len(data["items"]) >= 15

    # Check structure of items
    first_item = data["items"][0]
    assert "scheme_code" in first_item
    assert "name" in first_item
    assert "status" in first_item
    assert first_item["status"] == "active"


def test_06_get_schemes_with_filters():
    """Test GET /schemes with category, search, and status filters."""
    # Filter by category (Agriculture)
    res_cat = client.get("/schemes?category=Agriculture")
    assert res_cat.status_code == 200
    cat_data = res_cat.json()
    assert cat_data["total"] >= 1
    codes = [item["scheme_code"] for item in cat_data["items"]]
    assert "pm_kisan" in codes

    # Filter by search text
    res_search = client.get("/schemes?search=Ayushman")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total"] >= 1
    search_codes = [item["scheme_code"] for item in search_data["items"]]
    assert "ayushman_bharat_pm_jay" in search_codes or "pm_jay" in search_codes

    # Filter with non-matching search
    res_empty = client.get("/schemes?search=NonExistentSchemeXYZ")
    assert res_empty.status_code == 200
    empty_data = res_empty.json()
    assert empty_data["total"] == 0
    assert empty_data["items"] == []


def test_07_get_scheme_by_id_and_code():
    """Test GET /schemes/{scheme_id} resolves both by scheme_code and by UUID."""
    # By scheme_code
    res_code = client.get("/schemes/pm_kisan")
    assert res_code.status_code == 200
    data = res_code.json()
    assert data["scheme_code"] == "pm_kisan"
    assert "PM-KISAN" in data["name"] or "Pradhan Mantri" in data["name"]
    assert "benefits" in data
    assert "profile_fields" in data

    # By UUID
    uuid_str = data["id"]
    res_uuid = client.get(f"/schemes/{uuid_str}")
    assert res_uuid.status_code == 200
    data_uuid = res_uuid.json()
    assert data_uuid["scheme_code"] == "pm_kisan"
    assert data_uuid["id"] == uuid_str


def test_08_get_invalid_scheme_returns_404():
    """Test GET /schemes/{id} returns 404 for unknown scheme."""
    response = client.get("/schemes/invalid_unknown_scheme_123")
    assert response.status_code == 404
    assert "Scheme not found" in response.json()["detail"]


# =====================================================================
# 3. ELIGIBILITY API TESTS (Scenarios 9 - 11)
# =====================================================================

def test_09_post_eligibility_check_eligible():
    """Test POST /eligibility/check returns Eligible when all criteria are met."""
    payload = {
        "scheme_code": "pm_kisan",
        "profile": {
            "has_cultivable_land_in_name": True,
            "is_institutional_land_holder": False,
            "is_former_or_present_constitutional_post_holder": False,
            "is_former_or_present_specified_political_office_holder": False,
            "is_serving_or_retired_specified_government_employee": False,
            "monthly_pension": 0,
            "paid_income_tax_last_assessment_year": False,
            "is_registered_practicing_specified_professional": False,
            "is_nri": False,
        }
    }
    response = client.post("/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_code"] == "pm_kisan"
    assert data["status"] == "Eligible"
    assert data["eligible"] is True
    assert data["missing_fields"] == []


def test_10_post_eligibility_check_potentially_eligible():
    """Test POST /eligibility/check returns Potentially Eligible when required fields are missing."""
    payload = {
        "scheme_code": "pm_kisan",
        "profile": {
            # Missing cultivable land and exclusions
        }
    }
    response = client.post("/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_code"] == "pm_kisan"
    assert data["status"] == "Potentially Eligible"
    assert data["eligible"] is None
    assert "MISSING_INFORMATION" in data["reason_codes"]
    assert len(data["missing_fields"]) > 0


def test_11_post_eligibility_check_not_eligible():
    """Test POST /eligibility/check returns Not Eligible when disqualifying condition is present."""
    payload = {
        "scheme_code": "pm_kisan",
        "profile": {
            "has_cultivable_land_in_name": True,
            "paid_income_tax_last_assessment_year": True,  # Disqualifying exclusion
        }
    }
    response = client.post("/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_code"] == "pm_kisan"
    assert data["status"] == "Not Eligible"
    assert data["eligible"] is False
    assert len(data["reason_codes"]) > 0


# =====================================================================
# 4. DOCUMENTS API TESTS (Scenarios 12 - 13)
# =====================================================================

def test_12_get_documents_valid_scheme():
    """Test GET /schemes/{scheme_id}/documents returns document requirements from DB."""
    response = client.get("/schemes/pm_kisan/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_code"] == "pm_kisan"
    assert "documents" in data
    assert len(data["documents"]) > 0
    doc = data["documents"][0]
    assert "document_type" in doc
    assert "document_name" in doc
    assert "is_mandatory" in doc


def test_13_get_documents_invalid_scheme():
    """Test GET /schemes/{scheme_id}/documents returns 404 for invalid scheme."""
    response = client.get("/schemes/non_existent_scheme/documents")
    assert response.status_code == 404
    assert "Scheme not found" in response.json()["detail"]


# =====================================================================
# 5. TUTORIAL API TESTS (Scenarios 14 - 15)
# =====================================================================

def test_14_get_tutorial_valid_scheme():
    """Test GET /schemes/{scheme_id}/tutorial returns ordered steps."""
    response = client.get("/schemes/pm_kisan/tutorial")
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_code"] == "pm_kisan"
    assert "steps" in data
    assert len(data["steps"]) > 0
    step = data["steps"][0]
    assert "step_number" in step
    assert "title" in step
    assert "description" in step
    # Verify ordered ascending
    step_numbers = [s["step_number"] for s in data["steps"]]
    assert step_numbers == sorted(step_numbers)


def test_15_get_tutorial_invalid_scheme():
    """Test GET /schemes/{scheme_id}/tutorial returns 404 for unknown scheme."""
    response = client.get("/schemes/unknown_scheme_xyz/tutorial")
    assert response.status_code == 404
    assert "Scheme not found" in response.json()["detail"]


# =====================================================================
# 6. RECOMMENDATION API TESTS (Scenarios 16 - 19)
# =====================================================================

def test_16_post_schemes_recommend_basic():
    """Test POST /schemes/recommend returns ranked list of relevant schemes."""
    payload = {
        "profile": {
            "age": 35,
            "occupation": "farmer",
            "state": "Uttar Pradesh"
        }
    }
    response = client.post("/schemes/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) > 0
    first = data["items"][0]
    assert "scheme_code" in first
    assert "name" in first
    assert "score" in first
    assert "match_reasons" in first
    assert isinstance(first["match_reasons"], list)


def test_17_recommendation_with_minimal_profile():
    """Test POST /schemes/recommend handles minimal profile gracefully."""
    payload = {
        "profile": {}
    }
    response = client.post("/schemes/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] > 0
    # Every scheme gets a base score
    for item in data["items"]:
        assert item["score"] > 0.0


def test_18_recommendation_with_richer_profile():
    """Test POST /schemes/recommend ranks farmer schemes highest for a farmer profile."""
    farmer_payload = {
        "profile": {
            "occupation": "farmer",
            "annual_income": 80000.0,
            "category": "SC",
            "attributes": {
                "has_cultivable_land_in_name": True
            }
        }
    }
    response = client.post("/schemes/recommend", json=farmer_payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    top_scheme = data["items"][0]
    # For a farmer with land, pm_kisan or pm_fasal_bima should score highest
    top_codes = [item["scheme_code"] for item in data["items"][:3]]
    assert "pm_kisan" in top_codes or "pm_fasal_bima" in top_codes
    assert any("farmer" in r.lower() or "agriculture" in r.lower() for r in top_scheme["match_reasons"])


def test_19_recommendation_does_not_claim_legal_eligibility():
    """Test POST /schemes/recommend includes compliance disclaimer and does not decide eligibility."""
    payload = {
        "profile": {
            "age": 25,
            "occupation": "student"
        }
    }
    response = client.post("/schemes/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Compliance disclaimer must be present in response
    assert "disclaimer" in data
    assert "eligibility" in data["disclaimer"].lower()
    assert "/eligibility/check" in data["disclaimer"]

    # Items do NOT contain an 'eligible' field or claim legal approval
    for item in data["items"]:
        assert "eligible" not in item
        assert "status" not in item or item.get("status") == "active"  # Only scheme status, not eligibility status


# =====================================================================
# 7. REAL DATA VERIFICATION: PM-KISAN, PM-JAY, PMAY-U
# =====================================================================

def test_20_real_data_m4_verification():
    """Verify PM-KISAN, PM-JAY, and PMAY-U exist, resolve details, docs, and tutorials."""
    target_schemes = ["pm_kisan", "pm_jay", "pmay_u"]
    for code in target_schemes:
        # Details
        res = client.get(f"/schemes/{code}")
        assert res.status_code == 200, f"Failed retrieving {code}"
        scheme_data = res.json()
        assert scheme_data["scheme_code"] in (code, "ayushman_bharat_pm_jay", "pmay_urban")
        assert len(scheme_data.get("profile_fields", [])) > 0, f"No profile fields for {code}"

        # Documents
        doc_res = client.get(f"/schemes/{code}/documents")
        assert doc_res.status_code == 200
        assert len(doc_res.json().get("documents", [])) > 0, f"No documents for {code}"

        # Tutorials
        tut_res = client.get(f"/schemes/{code}/tutorial")
        assert tut_res.status_code == 200
        assert len(tut_res.json().get("steps", [])) > 0, f"No tutorial steps for {code}"
