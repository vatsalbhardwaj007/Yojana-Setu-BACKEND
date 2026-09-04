"""WhatsApp message text templates."""

from typing import Optional


def welcome_menu() -> str:
    return (
        "Welcome to *YojanaSetu*!\n\n"
        "I help you discover Indian government schemes and check eligibility.\n\n"
        "Choose an option:\n"
        "1. Find schemes\n"
        "2. Check eligibility\n"
        "3. Required documents\n"
        "4. How to apply"
    )


def scheme_list(schemes: list[dict]) -> str:
    if not schemes:
        return "No schemes found in the database."
    lines = ["*Government Schemes*\n"]
    for s in schemes:
        idx = s.get("index", "")
        name = s.get("name", "")
        stype = s.get("scheme_type", "")
        lines.append(f"{idx}. *{name}* ({stype})")
    lines.append("\nReply with a number to select a scheme.")
    return "\n".join(lines)


def scheme_detail(scheme: dict) -> str:
    name = scheme.get("name", "")
    desc = scheme.get("description", "")
    benefits = scheme.get("benefits", [])
    url = scheme.get("official_url")
    ministry = scheme.get("ministry", "")
    stype = scheme.get("scheme_type", "")

    lines = [f"*{name}*\n"]
    lines.append(f"Type: {stype}")
    lines.append(f"Ministry: {ministry}\n")

    if desc:
        if len(desc) > 400:
            desc = desc[:397] + "..."
        lines.append(desc)

    if benefits:
        lines.append("\n*Benefits:*")
        for b in benefits[:5]:
            lines.append(f"  - {b}")

    if url:
        lines.append(f"\nOfficial: {url}")

    lines.append("\nReply:\n3 for documents\n4 for application steps\n0 for main menu")
    return "\n".join(lines)


def scheme_documents(documents: list[dict], scheme_name: str) -> str:
    if not documents:
        return f"No document requirements listed for *{scheme_name}*."
    lines = [f"*Documents for {scheme_name}*\n"]
    mandatory = [d for d in documents if d.get("is_mandatory", True)]
    optional = [d for d in documents if not d.get("is_mandatory", True)]

    if mandatory:
        lines.append("*Mandatory:*")
        for d in mandatory:
            dtype = d.get("document_type", "")
            dname = d.get("document_name", "")
            lines.append(f"  - {dname} ({dtype})")

    if optional:
        lines.append("\n*Recommended:*")
        for d in optional:
            dtype = d.get("document_type", "")
            dname = d.get("document_name", "")
            lines.append(f"  - {dname} ({dtype})")

    lines.append("\n0 for main menu")
    return "\n".join(lines)


def scheme_tutorial(steps: list[dict], scheme_name: str) -> str:
    if not steps:
        return f"No application steps listed for *{scheme_name}*."
    lines = [f"*How to Apply: {scheme_name}*\n"]
    for step in steps:
        num = step.get("step_number", "")
        title = step.get("title", "")
        desc = step.get("description", "")
        lines.append(f"*Step {num}: {title}*")
        if desc:
            if len(desc) > 250:
                desc = desc[:247] + "..."
            lines.append(f"  {desc}")
        lines.append("")

    lines.append("0 for main menu")
    return "\n".join(lines)


def scheme_benefits(benefits: list[str], scheme_name: str) -> str:
    if not benefits:
        return f"No benefits listed for *{scheme_name}*."
    lines = [f"*Benefits: {scheme_name}*\n"]
    for b in benefits:
        lines.append(f"  - {b}")
    lines.append("\n0 for main menu")
    return "\n".join(lines)


def eligibility_pending(required_fields: Optional[list[str]] = None) -> str:
    lines = [
        "*Eligibility Check*\n",
        "Eligibility checking requires the M2 backend integration.",
        "This feature will be available soon.\n",
    ]
    if required_fields:
        lines.append("Required profile data for this scheme:")
        for f in required_fields:
            lines.append(f"  - {f}")
    lines.append("\n0 for main menu")
    return "\n".join(lines)


def eligibility_eligible(result: dict) -> str:
    """Display eligibility result: ELIGIBLE."""
    scheme_code = result.get("scheme_code", "")
    scheme = _resolve_scheme_name(scheme_code)
    lines = [
        f"*Eligibility Result: {scheme}*",
        "",
        "You are *eligible* for this scheme.",
    ]
    reasons = result.get("reasons", [])
    if reasons:
        lines.append("")
        lines.append("*Details:*")
        for r in reasons:
            lines.append(f"  - {r}")
    lines.append("\n0 for main menu")
    return "\n".join(lines)


def eligibility_not_eligible(result: dict) -> str:
    """Display eligibility result: NOT ELIGIBLE."""
    scheme_code = result.get("scheme_code", "")
    scheme = _resolve_scheme_name(scheme_code)
    lines = [
        f"*Eligibility Result: {scheme}*",
        "",
        "You are *not eligible* for this scheme.",
    ]
    reasons = result.get("reasons", [])
    if reasons:
        lines.append("")
        lines.append("*Reasons:*")
        for r in reasons:
            lines.append(f"  - {r}")
    lines.append("\n0 for main menu")
    return "\n".join(lines)


def eligibility_potentially_eligible(result: dict) -> str:
    """Display eligibility result: POTENTIALLY ELIGIBLE."""
    scheme_code = result.get("scheme_code", "")
    scheme = _resolve_scheme_name(scheme_code)
    missing = result.get("missing_fields", [])
    lines = [
        f"*Eligibility Result: {scheme}*",
        "",
        "You are *potentially eligible*, but we need more information.",
    ]
    if missing:
        lines.append("")
        lines.append("*Missing information:*")
        for f in missing:
            label = f.replace("_", " ").strip()
            lines.append(f"  - {label}")
    lines.append("")
    lines.append("Please provide your profile details to get a final result.")
    lines.append("You can reply with key:value pairs, e.g.:")
    lines.append("  age:30, land:true")
    lines.append("\n0 for main menu")
    return "\n".join(lines)


def eligibility_error(message: str) -> str:
    """Display a user-friendly eligibility error."""
    lines = [
        "*Eligibility Check*\n",
        "Sorry, we couldn't check your eligibility right now.",
        message,
        "\nPlease try again later.",
        "\n0 for main menu",
    ]
    return "\n".join(lines)


def _resolve_scheme_name(scheme_code: str) -> str:
    """Resolve a scheme_code to its display name."""
    from whatsapp.scheme_service import get_scheme
    scheme = get_scheme(scheme_code)
    if scheme:
        return scheme.get("name", scheme_code)
    return scheme_code.replace("_", " ").title()


def unknown_message() -> str:
    return (
        "I didn't understand that.\n\n"
        "Please choose an option:\n"
        "1. Find schemes\n"
        "2. Check eligibility\n"
        "3. Required documents\n"
        "4. How to apply\n"
        "0. Main menu"
    )


def no_scheme_selected() -> str:
    return "Please select a scheme first. Reply 1 to see available schemes."


def invalid_selection() -> str:
    return "Invalid selection. Please choose from the available options."


def error_message() -> str:
    return "Sorry, something went wrong. Please try again."
