"""Low-level deterministic condition evaluator for government scheme rules.

Supported canonical operators:
- '='
- '!='
- '>='
- '<='
- '>'
- '<'
- 'in'
- 'not_in'
- 'exists'
- 'between'

Pure, deterministic evaluation independent of HTTP, FastAPI, and database.
"""

from typing import Any, Dict, List, Optional, Tuple, Union


def _is_number(val: Any) -> bool:
    """Return True if val is an int or float, but not a bool."""
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def _eval_equals(actual: Any, expected: Any) -> bool:
    """Evaluate '=' with strict type awareness."""
    # Prevent Python's implicit True == 1 or False == 0
    if isinstance(expected, bool) or isinstance(actual, bool):
        if not (isinstance(actual, bool) and isinstance(expected, bool)):
            return False
        return actual == expected

    # Both are numbers
    if _is_number(actual) and _is_number(expected):
        return actual == expected

    # Both are strings
    if isinstance(actual, str) and isinstance(expected, str):
        return actual == expected

    # Fallback to direct equality for identical types
    if type(actual) is type(expected):
        return actual == expected

    return False


def _eval_not_equals(actual: Any, expected: Any) -> bool:
    """Evaluate '!=' with strict type awareness."""
    return not _eval_equals(actual, expected)


def _eval_compare(actual: Any, expected: Any, op: str) -> bool:
    """Evaluate numeric/ordered comparisons (>=, <=, >, <) safely."""
    # Both must be numbers, and neither can be boolean
    if _is_number(actual) and _is_number(expected):
        if op == ">=":
            return actual >= expected
        if op == "<=":
            return actual <= expected
        if op == ">":
            return actual > expected
        if op == "<":
            return actual < expected

    # Both are strings (e.g. ISO dates 'YYYY-MM-DD')
    if isinstance(actual, str) and isinstance(expected, str):
        if op == ">=":
            return actual >= expected
        if op == "<=":
            return actual <= expected
        if op == ">":
            return actual > expected
        if op == "<":
            return actual < expected

    # Incompatible types cannot be compared
    return False


def _eval_in(actual: Any, expected: Any) -> bool:
    """Evaluate 'in' ensuring expected is a collection and types match strictly."""
    if not isinstance(expected, (list, tuple, set)):
        return False

    for item in expected:
        if _eval_equals(actual, item):
            return True
    return False


def _eval_not_in(actual: Any, expected: Any) -> bool:
    """Evaluate 'not_in'."""
    return not _eval_in(actual, expected)


def _eval_between(actual: Any, expected: Any) -> bool:
    """Evaluate 'between' inclusive: min <= actual <= max.

    Expected format: {"min": number, "max": number}
    """
    if not isinstance(expected, dict):
        return False

    if "min" not in expected or "max" not in expected:
        return False

    min_val = expected["min"]
    max_val = expected["max"]

    if not (_is_number(min_val) and _is_number(max_val)):
        return False

    if not _is_number(actual):
        return False

    return min_val <= actual <= max_val


def _eval_exists(actual: Any, field_present: bool, expected: Any) -> bool:
    """Evaluate 'exists'.

    expected = True: PASS when field is present and value is not None.
    expected = False: PASS when field is absent or None.
    """
    is_present_and_not_none = field_present and (actual is not None)

    if expected is True:
        return is_present_and_not_none
    elif expected is False:
        return not is_present_and_not_none
    else:
        # Malformed expected value for exists
        return False


SUPPORTED_OPERATORS = {
    "=",
    "!=",
    ">=",
    "<=",
    ">",
    "<",
    "in",
    "not_in",
    "exists",
    "between",
}


def evaluate_condition(
    operator: str,
    actual: Any,
    expected: Any,
    field_present: bool = True,
) -> Tuple[bool, Optional[str]]:
    """Evaluate a single rule condition deterministically.

    Returns:
        (passed: bool, error_message: Optional[str])
    """
    if operator not in SUPPORTED_OPERATORS:
        return False, f"Unsupported operator: '{operator}'"

    try:
        if operator == "exists":
            return _eval_exists(actual, field_present, expected), None

        if operator == "=":
            return _eval_equals(actual, expected), None

        if operator == "!=":
            return _eval_not_equals(actual, expected), None

        if operator in {">=", "<=", ">", "<"}:
            return _eval_compare(actual, expected, operator), None

        if operator == "in":
            return _eval_in(actual, expected), None

        if operator == "not_in":
            return _eval_not_in(actual, expected), None

        if operator == "between":
            return _eval_between(actual, expected), None

    except Exception as e:
        return False, f"Evaluation error: {str(e)}"

    return False, "Unknown evaluation error"
