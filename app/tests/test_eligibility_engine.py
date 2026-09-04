"""Comprehensive unit tests for the generic deterministic EligibilityEngine."""

from app.repositories.scheme_repository import SchemeRepository
from app.rules.engine import EligibilityEngine
from app.schemas.scheme import SchemeRuleResponse
from app.services.eligibility_service import EligibilityService


# ---------------------------------------------------------------------------
# Synthetic Generic Engine Tests (STEP 21 Scenarios)
# ---------------------------------------------------------------------------
def test_all_rules_pass_eligible():
    """Scenario 1: All rules pass, no exclusions -> Eligible, eligible = true."""
    rules = [
        SchemeRuleResponse(
            rule_group="age",
            field="age",
            operator=">=",
            value=18,
            description="Applicant must be at least 18 years old",
            rule_purpose="eligibility",
        ),
        SchemeRuleResponse(
            rule_group="income",
            field="income",
            operator="<=",
            value=300000,
            description="Annual income must not exceed 300,000",
            rule_purpose="eligibility",
        ),
    ]
    exclusion_rules = [
        SchemeRuleResponse(
            rule_group="govt_employee",
            field="is_govt_employee",
            operator="=",
            value=True,
            description="Government employees are excluded",
            rule_purpose="exclusion",
        )
    ]
    profile = {"age": 25, "income": 200000, "is_govt_employee": False}

    result = EligibilityEngine.evaluate(
        scheme_code="test_scheme",
        eligibility_rules=rules,
        exclusion_rules=exclusion_rules,
        profile=profile,
    )

    assert result.status == "Eligible"
    assert result.eligible is True
    assert result.reason_codes == []
    assert result.reasons == []
    assert result.missing_fields == []
    assert len(result.evaluated_rules) == 3
    assert all(r.passed is True for r in result.evaluated_rules)


def test_one_rule_fails_not_eligible():
    """Scenario 2: One eligibility rule fails -> Not Eligible, eligible = false."""
    rules = [
        SchemeRuleResponse(
            rule_group="age",
            field="age",
            operator=">=",
            value=18,
            description="Applicant must be at least 18 years old",
            rule_purpose="eligibility",
        ),
        SchemeRuleResponse(
            rule_group="income",
            field="income",
            operator="<=",
            value=300000,
            description="Annual income must not exceed 300,000",
            rule_purpose="eligibility",
        ),
    ]
    profile = {"age": 16, "income": 200000}

    result = EligibilityEngine.evaluate(
        scheme_code="test_scheme",
        eligibility_rules=rules,
        exclusion_rules=[],
        profile=profile,
    )

    assert result.status == "Not Eligible"
    assert result.eligible is False
    assert "RULE_FAILED" in result.reason_codes
    assert "Applicant must be at least 18 years old" in result.reasons


def test_multiple_rules_fail_not_eligible():
    """Scenario 3: Multiple eligibility rules fail -> Not Eligible."""
    rules = [
        SchemeRuleResponse(
            rule_group="age",
            field="age",
            operator=">=",
            value=18,
            description="Applicant must be at least 18 years old",
            rule_purpose="eligibility",
        ),
        SchemeRuleResponse(
            rule_group="income",
            field="income",
            operator="<=",
            value=300000,
            description="Annual income must not exceed 300,000",
            rule_purpose="eligibility",
        ),
    ]
    profile = {"age": 16, "income": 400000}

    result = EligibilityEngine.evaluate(
        scheme_code="test_scheme",
        eligibility_rules=rules,
        exclusion_rules=[],
        profile=profile,
    )

    assert result.status == "Not Eligible"
    assert result.eligible is False
    assert "RULE_FAILED" in result.reason_codes
    assert len(result.reasons) == 2


def test_exclusion_triggers_not_eligible():
    """Scenario 4: Exclusion condition evaluates to True -> Not Eligible, EXCLUSION_TRIGGERED."""
    rules = [
        SchemeRuleResponse(
            rule_group="age",
            field="age",
            operator=">=",
            value=18,
            description="Applicant must be at least 18 years old",
            rule_purpose="eligibility",
        )
    ]
    exclusion_rules = [
        SchemeRuleResponse(
            rule_group="taxpayer",
            field="paid_income_tax",
            operator="=",
            value=True,
            description="Income taxpayers are excluded",
            rule_purpose="exclusion",
        )
    ]
    profile = {"age": 25, "paid_income_tax": True}

    result = EligibilityEngine.evaluate(
        scheme_code="test_scheme",
        eligibility_rules=rules,
        exclusion_rules=exclusion_rules,
        profile=profile,
    )

    assert result.status == "Not Eligible"
    assert result.eligible is False
    assert "EXCLUSION_TRIGGERED" in result.reason_codes
    assert "Income taxpayers are excluded" in result.reasons


def test_required_info_missing_potentially_eligible():
    """Scenario 5 & 6: Missing information without failures -> Potentially Eligible, eligible = null."""
    rules = [
        SchemeRuleResponse(
            rule_group="age",
            field="age",
            operator=">=",
            value=18,
            description="Applicant must be at least 18 years old",
            rule_purpose="eligibility",
        ),
        SchemeRuleResponse(
            rule_group="income",
            field="income",
            operator="<=",
            value=300000,
            description="Annual income must not exceed 300,000",
            rule_purpose="eligibility",
        ),
    ]
    profile = {"age": 25}  # income missing

    result = EligibilityEngine.evaluate(
        scheme_code="test_scheme",
        eligibility_rules=rules,
        exclusion_rules=[],
        profile=profile,
    )

    assert result.status == "Potentially Eligible"
    assert result.eligible is None
    assert result.reason_codes == ["MISSING_INFORMATION"]
    assert result.missing_fields == ["income"]
    assert result.reasons == []


def test_failed_rule_plus_missing_field_not_eligible():
    """Scenario 7: One rule failed + another field missing -> Definitively Not Eligible."""
    rules = [
        SchemeRuleResponse(
            rule_group="age",
            field="age",
            operator=">=",
            value=18,
            description="Applicant must be at least 18 years old",
            rule_purpose="eligibility",
        ),
        SchemeRuleResponse(
            rule_group="income",
            field="income",
            operator="<=",
            value=300000,
            description="Annual income must not exceed 300,000",
            rule_purpose="eligibility",
        ),
    ]
    profile = {"age": 16}  # age failed (<18), income missing

    result = EligibilityEngine.evaluate(
        scheme_code="test_scheme",
        eligibility_rules=rules,
        exclusion_rules=[],
        profile=profile,
    )

    assert result.status == "Not Eligible"
    assert result.eligible is False
    assert "RULE_FAILED" in result.reason_codes


def test_exclusion_triggered_plus_missing_field_not_eligible():
    """Scenario 8: Exclusion triggered + missing field -> Definitively Not Eligible."""
    rules = [
        SchemeRuleResponse(
            rule_group="age",
            field="age",
            operator=">=",
            value=18,
            description="Applicant must be at least 18 years old",
            rule_purpose="eligibility",
        )
    ]
    exclusion_rules = [
        SchemeRuleResponse(
            rule_group="taxpayer",
            field="paid_income_tax",
            operator="=",
            value=True,
            description="Income taxpayers are excluded",
            rule_purpose="exclusion",
        )
    ]
    profile = {"paid_income_tax": True}  # age missing, exclusion triggered

    result = EligibilityEngine.evaluate(
        scheme_code="test_scheme",
        eligibility_rules=rules,
        exclusion_rules=exclusion_rules,
        profile=profile,
    )

    assert result.status == "Not Eligible"
    assert result.eligible is False
    assert "EXCLUSION_TRIGGERED" in result.reason_codes


# ---------------------------------------------------------------------------
# PMAY-Urban Test Cases (STEP 19)
# ---------------------------------------------------------------------------
def test_pmay_urban_cases():
    repo = SchemeRepository()
    service = EligibilityService(repository=repo)

    # CASE 1 — Eligible: All rules pass, no exclusion triggered, no missing fields
    case1_profile = {
        "meets_pmay_u_income_category": True,
        "owns_pucca_house": False,
        "has_pmay_u_defined_family_composition": True,
        "resides_in_pmay_u_covered_town_or_city": True,
        "previously_availed_goi_housing_scheme": False,
    }
    res1 = service.check_eligibility("pmay_urban", case1_profile)
    assert res1.status == "Eligible"
    assert res1.eligible is True
    assert res1.reason_codes == []
    assert res1.missing_fields == []

    # CASE 2 — Failed eligibility: owns_pucca_house = true when rule requires false
    case2_profile = {
        "meets_pmay_u_income_category": True,
        "owns_pucca_house": True,
        "has_pmay_u_defined_family_composition": True,
        "resides_in_pmay_u_covered_town_or_city": True,
        "previously_availed_goi_housing_scheme": False,
    }
    res2 = service.check_eligibility("pmay_urban", case2_profile)
    assert res2.status == "Not Eligible"
    assert res2.eligible is False
    assert "RULE_FAILED" in res2.reason_codes
    assert any("pucca house" in r for r in res2.reasons)

    # CASE 3 — Missing information: Leave required field missing
    case3_profile = {
        "meets_pmay_u_income_category": True,
        "has_pmay_u_defined_family_composition": True,
        "resides_in_pmay_u_covered_town_or_city": True,
        "previously_availed_goi_housing_scheme": False,
        # "owns_pucca_house" is MISSING
    }
    res3 = service.check_eligibility("pmay_urban", case3_profile)
    assert res3.status == "Potentially Eligible"
    assert res3.eligible is None
    assert "MISSING_INFORMATION" in res3.reason_codes
    assert "owns_pucca_house" in res3.missing_fields

    # CASE 4 — Exclusion: previously_availed_goi_housing_scheme = true
    case4_profile = {
        "meets_pmay_u_income_category": True,
        "owns_pucca_house": False,
        "has_pmay_u_defined_family_composition": True,
        "resides_in_pmay_u_covered_town_or_city": True,
        "previously_availed_goi_housing_scheme": True,
    }
    res4 = service.check_eligibility("pmay_urban", case4_profile)
    assert res4.status == "Not Eligible"
    assert res4.eligible is False
    assert "EXCLUSION_TRIGGERED" in res4.reason_codes
    assert any("previously availed benefits" in r for r in res4.reasons)


# ---------------------------------------------------------------------------
# PM-KISAN Test Cases (STEP 17)
# ---------------------------------------------------------------------------
def test_pm_kisan_cases():
    repo = SchemeRepository()
    service = EligibilityService(repository=repo)

    # Fully eligible farmer
    eligible_profile = {
        "has_cultivable_land_in_name": True,
        "is_institutional_land_holder": False,
        "is_former_or_present_constitutional_post_holder": False,
        "is_former_or_present_specified_political_office_holder": False,
        "is_serving_or_retired_specified_government_employee": False,
        "monthly_pension": 5000,
        "paid_income_tax_last_assessment_year": False,
        "is_registered_practicing_specified_professional": False,
        "is_nri": False,
    }
    res = service.check_eligibility("pm_kisan", eligible_profile)
    assert res.status == "Eligible"
    assert res.eligible is True

    # Disqualified: pays income tax
    taxpayer_profile = dict(eligible_profile, paid_income_tax_last_assessment_year=True)
    res_tax = service.check_eligibility("pm_kisan", taxpayer_profile)
    assert res_tax.status == "Not Eligible"
    assert res_tax.eligible is False
    assert "EXCLUSION_TRIGGERED" in res_tax.reason_codes

    # Disqualified: no cultivable land
    no_land_profile = dict(eligible_profile, has_cultivable_land_in_name=False)
    res_no_land = service.check_eligibility("pm_kisan", no_land_profile)
    assert res_no_land.status == "Not Eligible"
    assert res_no_land.eligible is False
    assert "RULE_FAILED" in res_no_land.reason_codes


# ---------------------------------------------------------------------------
# PM-JAY Test Cases (STEP 18)
# ---------------------------------------------------------------------------
def test_pm_jay_cases():
    repo = SchemeRepository()
    service = EligibilityService(repository=repo)

    # Meets boolean entitlement criteria with all exclusion criteria evaluated to false
    entitled_profile = {
        "meets_pmjay_entitlement_criteria": True,
        "owns_two_three_or_four_wheeler_or_motorized_fishing_boat": False,
        "owns_mechanized_farming_equipment": False,
        "has_kisan_credit_card_limit_at_least_50000": False,
        "is_government_employee": False,
        "works_in_government_managed_non_agricultural_enterprise": False,
        "monthly_income": 5000,
        "owns_refrigerator_or_landline": False,
        "owns_decent_solidly_built_house": False,
        "owns_at_least_5_acres_agricultural_land": False,
    }
    res = service.check_eligibility("ayushman_bharat_pm_jay", entitled_profile)
    assert res.status == "Eligible"
    assert res.eligible is True

    # Entitlement condition false
    not_entitled_profile = dict(entitled_profile, meets_pmjay_entitlement_criteria=False)
    res_fail = service.check_eligibility("ayushman_bharat_pm_jay", not_entitled_profile)
    assert res_fail.status == "Not Eligible"
    assert res_fail.eligible is False
    assert "RULE_FAILED" in res_fail.reason_codes
