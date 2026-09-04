"""Message handler router — maps incoming text to responses.

All public handlers are async to support awaiting M2 HTTP calls.
"""

import re
from typing import Any, Optional

from whatsapp import scheme_service, templates
from whatsapp.m2_client import M2EligibilityClient


# Per-user session state (phone -> state dict). MVP: in-memory only.
_sessions: dict[str, dict] = {}

m2_client = M2EligibilityClient()


def _get_session(phone: str) -> dict:
    if phone not in _sessions:
        _sessions[phone] = {
            "state": "idle",
            "selected_scheme_code": None,
            "selected_scheme_index": None,
        }
    return _sessions[phone]


def _reset_session(phone: str) -> None:
    _sessions[phone] = {
        "state": "idle",
        "selected_scheme_code": None,
        "selected_scheme_index": None,
    }


def _set_selected_scheme(phone: str, scheme_code: str, index: int) -> None:
    session = _get_session(phone)
    session["selected_scheme_code"] = scheme_code
    session["selected_scheme_index"] = index
    session["state"] = "scheme_selected"


def _parse_profile(text: str) -> dict[str, Any]:
    """Parse optional key:value pairs from user message.

    Supports formats like:
      "age:30, land:true"
      "age:30\nland:true"
      "applicant_age:25 has_cultivable_land_in_name:true"

    Returns empty dict if no parseable pairs found.
    """
    profile: dict[str, Any] = {}
    pairs = re.split(r"[,\n]+", text)
    for pair in pairs:
        pair = pair.strip()
        if ":" not in pair:
            continue
        key, _, value = pair.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        parsed = _coerce_value(value)
        profile[key] = parsed
    return profile


def _coerce_value(value: str) -> Any:
    """Coerce a string value to the appropriate Python type."""
    if value.lower() in ("true", "yes", "y"):
        return True
    if value.lower() in ("false", "no", "n"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


async def handle_message(sender: str, text: str) -> str:
    """Process an incoming text message and return the reply text."""
    if not text:
        return templates.unknown_message()

    text_lower = text.strip().lower()
    session = _get_session(sender)

    # Global commands — always handled regardless of state
    if text_lower in ("0", "menu", "main menu", "start", "hi", "hello"):
        _reset_session(sender)
        return templates.welcome_menu()

    if text_lower in ("help", "?"):
        return templates.unknown_message()

    # State: idle — show menu or process menu selection
    if session["state"] == "idle":
        return await _handle_menu_selection(sender, text_lower, text)

    # State: browsing_schemes — select a scheme by number
    if session["state"] == "browsing_schemes":
        return await _handle_browsing_action(sender, text_lower, text)

    # State: scheme_selected — process sub-menu
    if session["state"] == "scheme_selected":
        return await _handle_scheme_action(sender, text_lower, text)

    return templates.unknown_message()


async def _handle_browsing_action(
    sender: str, text: str, raw_text: str
) -> str:
    """Handle input while browsing scheme list."""
    if text.isdigit():
        return await _handle_scheme_selection(sender, int(text))

    if text in ("1", "find schemes", "schemes", "scheme"):
        schemes = scheme_service.get_scheme_names_indexed()
        return templates.scheme_list(schemes)

    if text in ("2", "check eligibility", "eligibility"):
        return templates.eligibility_pending()

    if text in ("0", "menu", "main menu"):
        _reset_session(sender)
        return templates.welcome_menu()

    return templates.unknown_message()


async def _handle_menu_selection(
    sender: str, text: str, raw_text: str
) -> str:
    """Handle top-level menu choices."""
    if text in ("1", "find schemes", "schemes", "scheme"):
        schemes = scheme_service.get_scheme_names_indexed()
        _get_session(sender)["state"] = "browsing_schemes"
        return templates.scheme_list(schemes)

    if text in ("2", "check eligibility", "eligibility"):
        return templates.eligibility_pending()

    if text in ("3", "required documents", "documents", "document"):
        return templates.no_scheme_selected()

    if text in ("4", "how to apply", "apply", "tutorial", "steps"):
        return templates.no_scheme_selected()

    # Check if user is browsing schemes and entered a number
    if text.isdigit():
        return await _handle_scheme_selection(sender, int(text))

    return templates.unknown_message()


async def _handle_scheme_selection(sender: str, index: int) -> str:
    """Handle numeric scheme selection while browsing."""
    scheme_code = scheme_service.get_scheme_code_by_index(index)
    if not scheme_code:
        return templates.invalid_selection()

    _set_selected_scheme(sender, scheme_code, index)
    scheme = scheme_service.get_scheme(scheme_code)
    return templates.scheme_detail(scheme)


async def _handle_scheme_action(
    sender: str, text: str, raw_text: str
) -> str:
    """Handle actions on a selected scheme."""
    session = _get_session(sender)
    scheme_code = session.get("selected_scheme_code")

    if not scheme_code:
        return templates.no_scheme_selected()

    if text in ("3", "documents", "document"):
        return _show_documents(scheme_code)

    if text in ("4", "how to apply", "apply", "tutorial", "steps"):
        return await _show_tutorial(scheme_code)

    if text in ("2",) or text.startswith("check eligibility") or text.startswith("eligibility"):
        return await _show_eligibility(sender, scheme_code, raw_text)

    if text in ("0", "menu", "main menu"):
        _reset_session(sender)
        return templates.welcome_menu()

    if text in ("1", "find schemes", "schemes", "scheme"):
        _get_session(sender)["state"] = "browsing_schemes"
        schemes = scheme_service.get_scheme_names_indexed()
        return templates.scheme_list(schemes)

    # Numeric input in scheme_selected: try as scheme index
    if text.isdigit():
        return await _handle_scheme_selection(sender, int(text))

    return templates.unknown_message()


def _show_documents(scheme_code: str) -> str:
    docs = scheme_service.get_scheme_documents(scheme_code)
    scheme = scheme_service.get_scheme(scheme_code)
    name = scheme.get("name", scheme_code) if scheme else scheme_code
    return templates.scheme_documents(docs, name)


async def _show_tutorial(scheme_code: str) -> str:
    steps = scheme_service.get_scheme_tutorial(scheme_code)
    scheme = scheme_service.get_scheme(scheme_code)
    name = scheme.get("name", scheme_code) if scheme else scheme_code
    return templates.scheme_tutorial(steps, name)


async def _show_eligibility(
    sender: str, scheme_code: str, raw_text: str
) -> str:
    """Check eligibility via M2 backend and display the result."""
    # Try to parse profile data from the user's message.
    # Look for text after the "eligibility" keyword, or after "2".
    profile = _extract_profile_from_text(raw_text)

    result = await m2_client.check_eligibility(scheme_code, profile)

    if result.get("status") == "error":
        return templates.eligibility_error(result.get("message", ""))

    m2_status = result.get("m2_status", "")

    if m2_status == "Eligible":
        return templates.eligibility_eligible(result)

    if m2_status == "Not Eligible":
        return templates.eligibility_not_eligible(result)

    if m2_status == "Potentially Eligible":
        return templates.eligibility_potentially_eligible(result)

    return templates.eligibility_error(
        "Received an unexpected response from the eligibility service."
    )


def _extract_profile_from_text(raw_text: str) -> dict[str, Any]:
    """Extract profile key:value pairs from user message text.

    Strips menu keywords (like "eligibility", "check eligibility", "2")
    and parses remaining text as key:value pairs.
    """
    text = raw_text.strip()

    # Remove leading menu keywords
    patterns = [
        r"^check\s+eligibility\s*",
        r"^eligibility\s*",
        r"^2\s+",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = text.strip()
    if not text:
        return {}

    return _parse_profile(text)


def get_session_state(phone: str) -> dict:
    """Return current session state for testing."""
    return _get_session(phone)


def clear_sessions() -> None:
    """Clear all sessions for testing."""
    _sessions.clear()
