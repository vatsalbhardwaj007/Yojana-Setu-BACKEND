"""Integration tests for the /eligibility/check API endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_check_eligibility_pmay_u_eligible():
    """Test POST /eligibility/check for an eligible PMAY-U applicant."""
    payload = {
        "scheme_code": "pmay_urban",
        "profile": {
            "meets_pmay_u_income_category": True,
            "owns_pucca_house": False,
            "has_pmay_u_defined_family_composition": True,
            "resides_in_pmay_u_covered_town_or_city": True,
            "previously_availed_goi_housing_scheme": False,
        },
    }
    response = client.post("/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_code"] == "pmay_urban"
    assert data["status"] == "Eligible"
    assert data["eligible"] is True
    assert data["reason_codes"] == []
    assert data["reasons"] == []
    assert data["missing_fields"] == []
    assert len(data["evaluated_rules"]) == 5


def test_api_check_eligibility_v1_path():
    """Test POST /api/v1/eligibility/check alias path."""
    payload = {
        "scheme_code": "pmay_urban",
        "profile": {
            "meets_pmay_u_income_category": True,
            "owns_pucca_house": False,
            "has_pmay_u_defined_family_composition": True,
            "resides_in_pmay_u_covered_town_or_city": True,
            "previously_availed_goi_housing_scheme": False,
        },
    }
    response = client.post("/api/v1/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Eligible"
    assert data["eligible"] is True


def test_api_check_eligibility_potentially_eligible():
    """Test POST /eligibility/check with missing information."""
    payload = {
        "scheme_code": "pm_kisan",
        "profile": {
            # Cultivable land information missing
        },
    }
    response = client.post("/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Potentially Eligible"
    assert data["eligible"] is None
    assert "MISSING_INFORMATION" in data["reason_codes"]
    assert "has_cultivable_land_in_name" in data["missing_fields"]


def test_api_check_eligibility_not_eligible_exclusion():
    """Test POST /eligibility/check when an exclusion triggers."""
    payload = {
        "scheme_code": "pm_kisan",
        "profile": {
            "has_cultivable_land_in_name": True,
            "paid_income_tax_last_assessment_year": True,
        },
    }
    response = client.post("/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Not Eligible"
    assert data["eligible"] is False
    assert "EXCLUSION_TRIGGERED" in data["reason_codes"]
    assert len(data["reasons"]) > 0


def test_api_check_eligibility_scheme_not_found():
    """Test POST /eligibility/check with non-existent scheme_code -> 404."""
    payload = {
        "scheme_code": "invalid_unknown_scheme_123",
        "profile": {"age": 30},
    }
    response = client.post("/eligibility/check", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_api_check_eligibility_missing_scheme_code():
    """Test POST /eligibility/check with invalid schema (missing scheme_code) -> 422."""
    payload = {"profile": {"age": 30}}
    response = client.post("/eligibility/check", json=payload)
    assert response.status_code == 422
