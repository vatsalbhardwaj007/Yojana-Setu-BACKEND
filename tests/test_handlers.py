"""Tests for message handlers and routing."""

import pytest

from whatsapp.handlers import handle_message, clear_sessions, get_session_state
from whatsapp.m2_client import M2EligibilityClient


def _mock_m2_result(status: str, **kwargs) -> dict:
    """Helper to build a mock M2 client result."""
    base = {"status": "success", "m2_status": status, "scheme_code": "pm_kisan"}
    base.update(kwargs)
    return base


class TestWelcomeAndMenu:
    def setup_method(self):
        clear_sessions()

    @pytest.mark.asyncio
    async def test_hi_triggers_welcome(self):
        reply = await handle_message("919876543210", "Hi")
        assert "Welcome" in reply
        assert "YojanaSetu" in reply
        assert "1." in reply
        assert "2." in reply
        assert "3." in reply
        assert "4." in reply

    @pytest.mark.asyncio
    async def test_hello_triggers_welcome(self):
        reply = await handle_message("919876543210", "Hello")
        assert "Welcome" in reply

    @pytest.mark.asyncio
    async def test_start_triggers_welcome(self):
        reply = await handle_message("919876543210", "Start")
        assert "Welcome" in reply

    @pytest.mark.asyncio
    async def test_menu_triggers_welcome(self):
        reply = await handle_message("919876543210", "Menu")
        assert "Welcome" in reply

    @pytest.mark.asyncio
    async def test_zero_triggers_welcome(self):
        reply = await handle_message("919876543210", "0")
        assert "Welcome" in reply

    @pytest.mark.asyncio
    async def test_help_triggers_fallback(self):
        reply = await handle_message("919876543210", "help")
        assert "didn't understand" in reply.lower() or "choose" in reply.lower()

    @pytest.mark.asyncio
    async def test_empty_text(self):
        reply = await handle_message("919876543210", "")
        assert "didn't understand" in reply.lower() or "choose" in reply.lower()


class TestSchemeDiscovery:
    def setup_method(self):
        clear_sessions()

    @pytest.mark.asyncio
    async def test_find_schemes_shows_list(self):
        reply = await handle_message("919876543210", "1")
        assert "Government Schemes" in reply
        assert "PM-KISAN" in reply or "Pradhan Mantri" in reply

    @pytest.mark.asyncio
    async def test_schemes_keyword(self):
        reply = await handle_message("919876543210", "schemes")
        assert "Government Schemes" in reply

    @pytest.mark.asyncio
    async def test_scheme_keyword(self):
        reply = await handle_message("919876543210", "scheme")
        assert "Government Schemes" in reply


class TestSchemeSelection:
    def setup_method(self):
        clear_sessions()

    @pytest.mark.asyncio
    async def test_select_scheme_by_number(self):
        await handle_message("919876543210", "1")
        reply = await handle_message("919876543210", "1")
        assert "Benefits" in reply or "Ministry" in reply or "Type:" in reply

    @pytest.mark.asyncio
    async def test_invalid_scheme_number(self):
        await handle_message("919876543210", "1")
        reply = await handle_message("919876543210", "999")
        assert "Invalid" in reply or "didn't understand" in reply.lower()


class TestDocumentsAndTutorial:
    def setup_method(self):
        clear_sessions()

    @pytest.mark.asyncio
    async def test_documents_without_scheme(self):
        reply = await handle_message("919876543210", "3")
        assert "select" in reply.lower() or "first" in reply.lower() or "Find" in reply.lower()

    @pytest.mark.asyncio
    async def test_tutorial_without_scheme(self):
        reply = await handle_message("919876543210", "4")
        assert "select" in reply.lower() or "first" in reply.lower() or "Find" in reply.lower()

    @pytest.mark.asyncio
    async def test_documents_after_scheme_selection(self):
        await handle_message("919876543210", "1")
        await handle_message("919876543210", "1")
        reply = await handle_message("919876543210", "3")
        assert "Documents" in reply or "documents" in reply or "No document" in reply

    @pytest.mark.asyncio
    async def test_tutorial_after_scheme_selection(self):
        await handle_message("919876543210", "1")
        await handle_message("919876543210", "1")
        reply = await handle_message("919876543210", "4")
        assert "How to Apply" in reply or "Step" in reply or "No application" in reply


class TestEligibility:
    def setup_method(self):
        clear_sessions()

    @pytest.mark.asyncio
    async def test_eligibility_without_scheme_shows_pending(self):
        reply = await handle_message("919876543210", "2")
        assert "M2" in reply or "pending" in reply.lower() or "backend" in reply.lower()

    @pytest.mark.asyncio
    async def test_eligibility_calls_m2_and_shows_eligible(self):
        """When M2 returns Eligible, handler shows eligible message."""
        import whatsapp.handlers as h

        old_client = h.m2_client
        try:
            h.m2_client = M2EligibilityClient(backend_url="http://fake-m2")

            async def mock_check(scheme_code, profile):
                return _mock_m2_result(
                    "Eligible",
                    eligible=True,
                    reasons=[],
                    missing_fields=[],
                )

            h.m2_client.check_eligibility = mock_check

            await handle_message("919876543210", "1")
            await handle_message("919876543210", "1")
            reply = await handle_message("919876543210", "2")
            assert "eligible" in reply.lower()
            assert "not eligible" not in reply.lower()
        finally:
            h.m2_client = old_client

    @pytest.mark.asyncio
    async def test_eligibility_calls_m2_and_shows_not_eligible(self):
        """When M2 returns Not Eligible, handler shows not eligible with reasons."""
        import whatsapp.handlers as h

        old_client = h.m2_client
        try:
            h.m2_client = M2EligibilityClient(backend_url="http://fake-m2")

            async def mock_check(scheme_code, profile):
                return _mock_m2_result(
                    "Not Eligible",
                    eligible=False,
                    reasons=["Income tax exclusion triggered."],
                    reason_codes=["EXCLUSION_TRIGGERED"],
                    missing_fields=[],
                )

            h.m2_client.check_eligibility = mock_check

            await handle_message("919876543210", "1")
            await handle_message("919876543210", "1")
            reply = await handle_message("919876543210", "2")
            assert "not eligible" in reply.lower()
            assert "Income tax" in reply
        finally:
            h.m2_client = old_client

    @pytest.mark.asyncio
    async def test_eligibility_calls_m2_and_shows_potentially_eligible(self):
        """When M2 returns Potentially Eligible, handler shows missing fields."""
        import whatsapp.handlers as h

        old_client = h.m2_client
        try:
            h.m2_client = M2EligibilityClient(backend_url="http://fake-m2")

            async def mock_check(scheme_code, profile):
                return _mock_m2_result(
                    "Potentially Eligible",
                    eligible=None,
                    reasons=[],
                    reason_codes=["MISSING_INFORMATION"],
                    missing_fields=["has_cultivable_land_in_name", "is_nri"],
                )

            h.m2_client.check_eligibility = mock_check

            await handle_message("919876543210", "1")
            await handle_message("919876543210", "1")
            reply = await handle_message("919876543210", "2")
            assert "potentially eligible" in reply.lower()
            assert "has cultivable land in name" in reply.lower()
            assert "is nri" in reply.lower()
        finally:
            h.m2_client = old_client

    @pytest.mark.asyncio
    async def test_eligibility_backend_error_shows_friendly_message(self):
        """When M2 is unavailable, handler shows friendly error."""
        import whatsapp.handlers as h

        old_client = h.m2_client
        try:
            h.m2_client = M2EligibilityClient(backend_url="http://fake-m2")

            async def mock_check(scheme_code, profile):
                return {
                    "status": "error",
                    "error_type": "backend_unavailable",
                    "message": "The eligibility service is currently unreachable.",
                }

            h.m2_client.check_eligibility = mock_check

            await handle_message("919876543210", "1")
            await handle_message("919876543210", "1")
            reply = await handle_message("919876543210", "2")
            assert "couldn't check" in reply.lower() or "unreachable" in reply.lower()
        finally:
            h.m2_client = old_client

    @pytest.mark.asyncio
    async def test_eligibility_with_profile_data(self):
        """Profile data from user message is parsed and sent to M2."""
        import whatsapp.handlers as h

        old_client = h.m2_client
        try:
            h.m2_client = M2EligibilityClient(backend_url="http://fake-m2")
            captured = {}

            async def mock_check(scheme_code, profile):
                captured["profile"] = profile
                return _mock_m2_result(
                    "Eligible",
                    eligible=True,
                    reasons=[],
                    missing_fields=[],
                )

            h.m2_client.check_eligibility = mock_check

            await handle_message("919876543210", "1")
            await handle_message("919876543210", "1")
            reply = await handle_message(
                "919876543210", "eligibility age:30,land:true"
            )
            assert "eligible" in reply.lower()
            assert captured["profile"]["age"] == 30
            assert captured["profile"]["land"] is True
        finally:
            h.m2_client = old_client


class TestNavigation:
    def setup_method(self):
        clear_sessions()

    @pytest.mark.asyncio
    async def test_zero_returns_to_menu(self):
        await handle_message("919876543210", "1")
        await handle_message("919876543210", "1")
        reply = await handle_message("919876543210", "0")
        assert "Welcome" in reply

    @pytest.mark.asyncio
    async def test_session_isolation(self):
        await handle_message("919876543210", "1")
        await handle_message("911111111111", "1")
        s1 = get_session_state("919876543210")
        s2 = get_session_state("911111111111")
        assert s1["state"] == "browsing_schemes"
        assert s2["state"] == "browsing_schemes"


class TestProfileParsing:
    def test_parse_key_value_pairs(self):
        from whatsapp.handlers import _parse_profile

        result = _parse_profile("age:30, land:true")
        assert result["age"] == 30
        assert result["land"] is True

    def test_parse_newline_separated(self):
        from whatsapp.handlers import _parse_profile

        result = _parse_profile("age:25\nincome:50000")
        assert result["age"] == 25
        assert result["income"] == 50000

    def test_parse_string_value(self):
        from whatsapp.handlers import _parse_profile

        result = _parse_profile("state:Maharashtra")
        assert result["state"] == "Maharashtra"

    def test_parse_no_pairs_returns_empty(self):
        from whatsapp.handlers import _parse_profile

        result = _parse_profile("hello world")
        assert result == {}

    def test_extract_profile_strips_menu_keywords(self):
        from whatsapp.handlers import _extract_profile_from_text

        result = _extract_profile_from_text("eligibility age:30")
        assert result["age"] == 30

    def test_extract_profile_strips_check_keyword(self):
        from whatsapp.handlers import _extract_profile_from_text

        result = _extract_profile_from_text("check eligibility age:25")
        assert result["age"] == 25

    def test_extract_profile_strips_number_prefix(self):
        from whatsapp.handlers import _extract_profile_from_text

        result = _extract_profile_from_text("2 age:30,land:true")
        assert result["age"] == 30
        assert result["land"] is True
