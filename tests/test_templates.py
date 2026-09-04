"""Tests for eligibility result templates."""

from whatsapp import templates


class TestEligibilityEligible:
    def test_eligible_message_contains_scheme_name(self):
        result = {
            "scheme_code": "pm_kisan",
            "m2_status": "Eligible",
            "eligible": True,
            "reasons": [],
            "missing_fields": [],
        }
        msg = templates.eligibility_eligible(result)
        assert "eligible" in msg.lower()
        assert "pm_kisan" in msg.lower() or "PM-KISAN" in msg or "Kisan" in msg

    def test_eligible_message_with_reasons(self):
        result = {
            "scheme_code": "pm_kisan",
            "m2_status": "Eligible",
            "eligible": True,
            "reasons": ["Meets all criteria"],
            "missing_fields": [],
        }
        msg = templates.eligibility_eligible(result)
        assert "Meets all criteria" in msg
        assert "Details" in msg

    def test_eligible_message_without_reasons(self):
        result = {
            "scheme_code": "pm_kisan",
            "m2_status": "Eligible",
            "eligible": True,
            "reasons": [],
            "missing_fields": [],
        }
        msg = templates.eligibility_eligible(result)
        assert "eligible" in msg.lower()
        assert "0 for main menu" in msg

    def test_eligible_message_unknown_scheme_code(self):
        result = {
            "scheme_code": "unknown_scheme",
            "m2_status": "Eligible",
            "eligible": True,
            "reasons": [],
            "missing_fields": [],
        }
        msg = templates.eligibility_eligible(result)
        assert "eligible" in msg.lower()


class TestEligibilityNotEligible:
    def test_not_eligible_message(self):
        result = {
            "scheme_code": "pm_kisan",
            "m2_status": "Not Eligible",
            "eligible": False,
            "reasons": ["Income tax exclusion triggered."],
            "reason_codes": ["EXCLUSION_TRIGGERED"],
            "missing_fields": [],
        }
        msg = templates.eligibility_not_eligible(result)
        assert "not eligible" in msg.lower()
        assert "Income tax" in msg
        assert "Reasons" in msg

    def test_not_eligible_with_multiple_reasons(self):
        result = {
            "scheme_code": "pm_kisan",
            "m2_status": "Not Eligible",
            "eligible": False,
            "reasons": ["Reason one", "Reason two", "Reason three"],
            "reason_codes": ["EXCLUSION_TRIGGERED", "RULE_FAILED"],
            "missing_fields": [],
        }
        msg = templates.eligibility_not_eligible(result)
        assert "Reason one" in msg
        assert "Reason two" in msg
        assert "Reason three" in msg

    def test_not_eligible_no_reasons(self):
        result = {
            "scheme_code": "pm_kisan",
            "m2_status": "Not Eligible",
            "eligible": False,
            "reasons": [],
            "missing_fields": [],
        }
        msg = templates.eligibility_not_eligible(result)
        assert "not eligible" in msg.lower()
        assert "0 for main menu" in msg


class TestEligibilityPotentiallyEligible:
    def test_potentially_eligible_message(self):
        result = {
            "scheme_code": "pm_kisan",
            "m2_status": "Potentially Eligible",
            "eligible": None,
            "reasons": [],
            "missing_fields": ["has_cultivable_land_in_name"],
        }
        msg = templates.eligibility_potentially_eligible(result)
        assert "potentially eligible" in msg.lower()
        assert "has cultivable land in name" in msg.lower()

    def test_potentially_eligible_with_multiple_fields(self):
        result = {
            "scheme_code": "pm_kisan",
            "m2_status": "Potentially Eligible",
            "eligible": None,
            "reasons": [],
            "missing_fields": ["field_one", "field_two", "field_three"],
        }
        msg = templates.eligibility_potentially_eligible(result)
        assert "field one" in msg.lower()
        assert "field two" in msg.lower()
        assert "field three" in msg.lower()

    def test_potentially_eligible_no_fields(self):
        result = {
            "scheme_code": "pm_kisan",
            "m2_status": "Potentially Eligible",
            "eligible": None,
            "reasons": [],
            "missing_fields": [],
        }
        msg = templates.eligibility_potentially_eligible(result)
        assert "potentially eligible" in msg.lower()
        assert "0 for main menu" in msg

    def test_potentially_eligible_shows_profile_hint(self):
        result = {
            "scheme_code": "pm_kisan",
            "m2_status": "Potentially Eligible",
            "eligible": None,
            "missing_fields": ["age"],
        }
        msg = templates.eligibility_potentially_eligible(result)
        assert "key:value" in msg.lower() or "age:30" in msg.lower()


class TestEligibilityError:
    def test_error_message(self):
        msg = templates.eligibility_error("Service unavailable")
        assert "couldn't check" in msg.lower()
        assert "Service unavailable" in msg
        assert "0 for main menu" in msg

    def test_error_message_with_timeout(self):
        msg = templates.eligibility_error("Request timed out")
        assert "timed out" in msg.lower()
        assert "try again" in msg.lower()
