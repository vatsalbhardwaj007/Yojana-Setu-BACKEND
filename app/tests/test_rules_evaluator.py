"""Unit tests for low-level condition evaluator across all 10 canonical operators."""

import pytest
from app.rules.evaluator import evaluate_condition


# ---------------------------------------------------------------------------
# 1. Operator: '='
# ---------------------------------------------------------------------------
def test_operator_equals():
    # Numbers
    passed, err = evaluate_condition("=", 42, 42)
    assert passed is True and err is None

    passed, err = evaluate_condition("=", 42, 43)
    assert passed is False and err is None

    # Strings
    passed, err = evaluate_condition("=", "rural", "rural")
    assert passed is True and err is None

    passed, err = evaluate_condition("=", "rural", "urban")
    assert passed is False and err is None

    # Booleans
    passed, err = evaluate_condition("=", True, True)
    assert passed is True and err is None

    passed, err = evaluate_condition("=", False, False)
    assert passed is True and err is None

    passed, err = evaluate_condition("=", True, False)
    assert passed is False and err is None

    # Type safety: Strict boolean vs integer matching
    passed, err = evaluate_condition("=", True, 1)
    assert passed is False

    passed, err = evaluate_condition("=", False, 0)
    assert passed is False

    passed, err = evaluate_condition("=", "true", True)
    assert passed is False


# ---------------------------------------------------------------------------
# 2. Operator: '!='
# ---------------------------------------------------------------------------
def test_operator_not_equals():
    passed, err = evaluate_condition("!=", 10, 20)
    assert passed is True and err is None

    passed, err = evaluate_condition("!=", 10, 10)
    assert passed is False and err is None

    passed, err = evaluate_condition("!=", "student", "teacher")
    assert passed is True and err is None

    passed, err = evaluate_condition("!=", True, False)
    assert passed is True and err is None


# ---------------------------------------------------------------------------
# 3. Operator: '>='
# ---------------------------------------------------------------------------
def test_operator_gte():
    passed, _ = evaluate_condition(">=", 18, 18)
    assert passed is True

    passed, _ = evaluate_condition(">=", 25, 18)
    assert passed is True

    passed, _ = evaluate_condition(">=", 17, 18)
    assert passed is False

    # Dates
    passed, _ = evaluate_condition(">=", "2025-06-01", "2025-01-01")
    assert passed is True

    # Type safety
    passed, _ = evaluate_condition(">=", "not_a_number", 18)
    assert passed is False


# ---------------------------------------------------------------------------
# 4. Operator: '<='
# ---------------------------------------------------------------------------
def test_operator_lte():
    passed, _ = evaluate_condition("<=", 250000, 250000)
    assert passed is True

    passed, _ = evaluate_condition("<=", 200000, 250000)
    assert passed is True

    passed, _ = evaluate_condition("<=", 300000, 250000)
    assert passed is False

    # Type safety
    passed, _ = evaluate_condition("<=", True, 250000)
    assert passed is False


# ---------------------------------------------------------------------------
# 5. Operator: '>'
# ---------------------------------------------------------------------------
def test_operator_gt():
    passed, _ = evaluate_condition(">", 18, 17)
    assert passed is True

    passed, _ = evaluate_condition(">", 18, 18)
    assert passed is False

    passed, _ = evaluate_condition(">", 18, 19)
    assert passed is False


# ---------------------------------------------------------------------------
# 6. Operator: '<'
# ---------------------------------------------------------------------------
def test_operator_lt():
    passed, _ = evaluate_condition("<", 60, 65)
    assert passed is True

    passed, _ = evaluate_condition("<", 65, 65)
    assert passed is False

    passed, _ = evaluate_condition("<", 70, 65)
    assert passed is False


# ---------------------------------------------------------------------------
# 7. Operator: 'in'
# ---------------------------------------------------------------------------
def test_operator_in():
    allowed = ["SC", "ST", "OBC"]
    passed, _ = evaluate_condition("in", "SC", allowed)
    assert passed is True

    passed, _ = evaluate_condition("in", "GEN", allowed)
    assert passed is False

    # Strict type matching
    passed, _ = evaluate_condition("in", True, [1, 2, 3])
    assert passed is False

    # Malformed expected
    passed, _ = evaluate_condition("in", "SC", "not_a_list")
    assert passed is False


# ---------------------------------------------------------------------------
# 8. Operator: 'not_in'
# ---------------------------------------------------------------------------
def test_operator_not_in():
    excluded = ["institutional", "government"]
    passed, _ = evaluate_condition("not_in", "individual", excluded)
    assert passed is True

    passed, _ = evaluate_condition("not_in", "institutional", excluded)
    assert passed is False


# ---------------------------------------------------------------------------
# 9. Operator: 'between'
# ---------------------------------------------------------------------------
def test_operator_between():
    expected_range = {"min": 18, "max": 40}

    # Within range
    passed, _ = evaluate_condition("between", 25, expected_range)
    assert passed is True

    # Inclusive boundary
    passed, _ = evaluate_condition("between", 18, expected_range)
    assert passed is True

    passed, _ = evaluate_condition("between", 40, expected_range)
    assert passed is True

    # Out of range
    passed, _ = evaluate_condition("between", 17, expected_range)
    assert passed is False

    passed, _ = evaluate_condition("between", 41, expected_range)
    assert passed is False

    # Malformed expected values handled safely
    passed, _ = evaluate_condition("between", 25, {"min": 18})  # missing max
    assert passed is False

    passed, _ = evaluate_condition("between", 25, {"max": 40})  # missing min
    assert passed is False

    passed, _ = evaluate_condition("between", 25, "18-40")  # not a dict
    assert passed is False

    passed, _ = evaluate_condition("between", 25, None)
    assert passed is False

    passed, _ = evaluate_condition("between", "twenty", expected_range)  # non-number actual
    assert passed is False


# ---------------------------------------------------------------------------
# 10. Operator: 'exists'
# ---------------------------------------------------------------------------
def test_operator_exists():
    # exists = True: PASS when field is present and value is not None
    passed, _ = evaluate_condition("exists", "some_value", True, field_present=True)
    assert passed is True

    passed, _ = evaluate_condition("exists", 0, True, field_present=True)
    assert passed is True

    passed, _ = evaluate_condition("exists", False, True, field_present=True)
    assert passed is True

    passed, _ = evaluate_condition("exists", None, True, field_present=True)
    assert passed is False

    passed, _ = evaluate_condition("exists", None, True, field_present=False)
    assert passed is False

    # exists = False: PASS when field is absent or None
    passed, _ = evaluate_condition("exists", None, False, field_present=False)
    assert passed is True

    passed, _ = evaluate_condition("exists", None, False, field_present=True)
    assert passed is True

    passed, _ = evaluate_condition("exists", "some_value", False, field_present=True)
    assert passed is False


# ---------------------------------------------------------------------------
# 11. Unsupported Operator
# ---------------------------------------------------------------------------
def test_unsupported_operator():
    passed, err = evaluate_condition("regex", "abc", "a.*")
    assert passed is False
    assert "Unsupported operator" in err
