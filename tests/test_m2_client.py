"""Tests for M2 eligibility client — real HTTP integration."""

import pytest
import httpx

from whatsapp.m2_client import M2EligibilityClient


class TestM2ClientInit:
    def test_client_init_defaults(self):
        client = M2EligibilityClient()
        assert client.backend_url == "http://localhost:8000"
        assert client.api_key == ""
        assert client.timeout == 10.0

    def test_client_init_custom(self):
        client = M2EligibilityClient(
            backend_url="https://m2.example.com",
            api_key="key123",
            timeout=5.0,
        )
        assert client.backend_url == "https://m2.example.com"
        assert client.api_key == "key123"
        assert client.timeout == 5.0

    def test_is_configured(self):
        client = M2EligibilityClient(backend_url="http://localhost:8000")
        assert client.is_configured() is True

    def test_is_not_configured_when_empty(self):
        client = M2EligibilityClient(backend_url="")
        assert client.is_configured() is False

    def test_backend_url_trailing_slash_stripped(self):
        client = M2EligibilityClient(backend_url="http://localhost:8000/")
        assert client.backend_url == "http://localhost:8000"


class TestCheckEligibilityEligible:
    @pytest.mark.asyncio
    async def test_eligible_response(self):
        client = M2EligibilityClient(backend_url="http://fake-m2")
        mock_response = {
            "scheme_code": "pm_kisan",
            "status": "Eligible",
            "eligible": True,
            "reason_codes": [],
            "reasons": [],
            "missing_fields": [],
            "evaluated_rules": [],
        }

        async def mock_post(url, json, headers, timeout):
            class FakeResp:
                status_code = 200

                def json(self):
                    return mock_response

            return FakeResp()

        with pytest.MonkeyPatch.context() as m:
            import httpx as _httpx

            original_client = _httpx.AsyncClient

            class MockAsyncClient:
                def __init__(self, *a, **kw):
                    pass

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *a):
                    pass

                async def post(self, url, json, headers, timeout):
                    return await mock_post(url, json, headers, timeout)

            m.setattr(_httpx, "AsyncClient", MockAsyncClient)
            result = await client.check_eligibility("pm_kisan", {})

        assert result["status"] == "success"
        assert result["m2_status"] == "Eligible"
        assert result["eligible"] is True
        assert result["missing_fields"] == []
        assert result["reasons"] == []


class TestCheckEligibilityNotEligible:
    @pytest.mark.asyncio
    async def test_not_eligible_response(self):
        client = M2EligibilityClient(backend_url="http://fake-m2")
        mock_response = {
            "scheme_code": "pm_kisan",
            "status": "Not Eligible",
            "eligible": False,
            "reason_codes": ["EXCLUSION_TRIGGERED"],
            "reasons": ["Persons who paid income tax are excluded."],
            "missing_fields": [],
            "evaluated_rules": [],
        }

        class MockAsyncClient:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def post(self, url, json, headers, timeout):
                class FakeResp:
                    status_code = 200

                    def json(self):
                        return mock_response

                return FakeResp()

        import httpx as _httpx

        with pytest.MonkeyPatch.context() as m:
            m.setattr(_httpx, "AsyncClient", MockAsyncClient)
            result = await client.check_eligibility("pm_kisan", {})

        assert result["status"] == "success"
        assert result["m2_status"] == "Not Eligible"
        assert result["eligible"] is False
        assert "EXCLUSION_TRIGGERED" in result["reason_codes"]
        assert len(result["reasons"]) > 0


class TestCheckEligibilityPotentiallyEligible:
    @pytest.mark.asyncio
    async def test_potentially_eligible_response(self):
        client = M2EligibilityClient(backend_url="http://fake-m2")
        mock_response = {
            "scheme_code": "pm_kisan",
            "status": "Potentially Eligible",
            "eligible": None,
            "reason_codes": ["MISSING_INFORMATION"],
            "reasons": [],
            "missing_fields": ["has_cultivable_land_in_name", "is_nri"],
            "evaluated_rules": [],
        }

        class MockAsyncClient:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def post(self, url, json, headers, timeout):
                class FakeResp:
                    status_code = 200

                    def json(self):
                        return mock_response

                return FakeResp()

        import httpx as _httpx

        with pytest.MonkeyPatch.context() as m:
            m.setattr(_httpx, "AsyncClient", MockAsyncClient)
            result = await client.check_eligibility("pm_kisan", {})

        assert result["status"] == "success"
        assert result["m2_status"] == "Potentially Eligible"
        assert result["eligible"] is None
        assert "has_cultivable_land_in_name" in result["missing_fields"]
        assert "is_nri" in result["missing_fields"]


class TestCheckEligibilitySchemeNotFound:
    @pytest.mark.asyncio
    async def test_404_returns_scheme_not_found(self):
        client = M2EligibilityClient(backend_url="http://fake-m2")

        class MockAsyncClient:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def post(self, url, json, headers, timeout):
                raise httpx.HTTPStatusError(
                    "Not Found",
                    request=httpx.Request("POST", url),
                    response=httpx.Response(404),
                )

        import httpx as _httpx

        with pytest.MonkeyPatch.context() as m:
            m.setattr(_httpx, "AsyncClient", MockAsyncClient)
            result = await client.check_eligibility("nonexistent", {})

        assert result["status"] == "error"
        assert result["error_type"] == "scheme_not_found"
        assert "not found" in result["message"].lower()


class TestCheckEligibilityBackendUnavailable:
    @pytest.mark.asyncio
    async def test_connect_error_returns_unavailable(self):
        client = M2EligibilityClient(backend_url="http://fake-m2")

        class MockAsyncClient:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def post(self, url, json, headers, timeout):
                raise httpx.ConnectError("Connection refused")

        import httpx as _httpx

        with pytest.MonkeyPatch.context() as m:
            m.setattr(_httpx, "AsyncClient", MockAsyncClient)
            result = await client.check_eligibility("pm_kisan", {})

        assert result["status"] == "error"
        assert result["error_type"] == "backend_unavailable"
        assert "unreachable" in result["message"].lower()


class TestCheckEligibilityTimeout:
    @pytest.mark.asyncio
    async def test_timeout_returns_timeout_error(self):
        client = M2EligibilityClient(backend_url="http://fake-m2")

        class MockAsyncClient:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def post(self, url, json, headers, timeout):
                raise httpx.TimeoutException("Read timed out")

        import httpx as _httpx

        with pytest.MonkeyPatch.context() as m:
            m.setattr(_httpx, "AsyncClient", MockAsyncClient)
            result = await client.check_eligibility("pm_kisan", {})

        assert result["status"] == "error"
        assert result["error_type"] == "timeout"
        assert "timed out" in result["message"].lower()


class TestCheckEligibilityServerError:
    @pytest.mark.asyncio
    async def test_500_returns_server_error(self):
        client = M2EligibilityClient(backend_url="http://fake-m2")

        class MockAsyncClient:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def post(self, url, json, headers, timeout):
                raise httpx.HTTPStatusError(
                    "Internal Server Error",
                    request=httpx.Request("POST", url),
                    response=httpx.Response(500),
                )

        import httpx as _httpx

        with pytest.MonkeyPatch.context() as m:
            m.setattr(_httpx, "AsyncClient", MockAsyncClient)
            result = await client.check_eligibility("pm_kisan", {})

        assert result["status"] == "error"
        assert result["error_type"] == "server_error"


class TestCheckEligibilityMalformedResponse:
    @pytest.mark.asyncio
    async def test_bad_json_returns_invalid_response(self):
        client = M2EligibilityClient(backend_url="http://fake-m2")

        class MockAsyncClient:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def post(self, url, json, headers, timeout):
                class FakeResp:
                    status_code = 200

                    def json(self):
                        raise ValueError("Invalid JSON")

                return FakeResp()

        import httpx as _httpx

        with pytest.MonkeyPatch.context() as m:
            m.setattr(_httpx, "AsyncClient", MockAsyncClient)
            result = await client.check_eligibility("pm_kisan", {})

        assert result["status"] == "error"
        assert result["error_type"] == "invalid_response"

    @pytest.mark.asyncio
    async def test_missing_required_keys_returns_invalid(self):
        client = M2EligibilityClient(backend_url="http://fake-m2")

        class MockAsyncClient:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def post(self, url, json, headers, timeout):
                class FakeResp:
                    status_code = 200

                    def json(self):
                        return {"unexpected": "format"}

                return FakeResp()

        import httpx as _httpx

        with pytest.MonkeyPatch.context() as m:
            m.setattr(_httpx, "AsyncClient", MockAsyncClient)
            result = await client.check_eligibility("pm_kisan", {})

        assert result["status"] == "error"
        assert result["error_type"] == "invalid_response"


class TestCheckEligibilityNotConfigured:
    @pytest.mark.asyncio
    async def test_empty_url_returns_unavailable(self):
        client = M2EligibilityClient(backend_url="")
        result = await client.check_eligibility("pm_kisan", {})
        assert result["status"] == "error"
        assert result["error_type"] == "backend_unavailable"


class TestRequiredFieldsForScheme:
    def test_pm_kisan_fields(self):
        client = M2EligibilityClient()
        fields = client._required_fields_for_scheme("pm_kisan")
        assert isinstance(fields, list)
        assert len(fields) > 0
        assert "has_cultivable_land_in_name" in fields

    def test_unknown_scheme_returns_empty(self):
        client = M2EligibilityClient()
        fields = client._required_fields_for_scheme("nonexistent")
        assert fields == []
