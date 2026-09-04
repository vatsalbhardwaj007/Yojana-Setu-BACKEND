"""Tests for configuration and app-level functionality."""

import os

from whatsapp.config import WhatsAppConfig
from whatsapp.app import _safe_error_body


class TestWhatsAppConfig:
    def test_default_graph_api_version(self):
        cfg = WhatsAppConfig()
        assert cfg.graph_api_version == "v23.0"

    def test_from_env_with_defaults(self):
        # Clear any existing env vars
        for key in [
            "WHATSAPP_VERIFY_TOKEN",
            "WHATSAPP_ACCESS_TOKEN",
            "WHATSAPP_PHONE_NUMBER_ID",
            "WHATSAPP_APP_SECRET",
            "GRAPH_API_VERSION",
            "M2_BACKEND_URL",
            "M2_API_KEY",
            "M2_TIMEOUT",
        ]:
            os.environ.pop(key, None)

        cfg = WhatsAppConfig.from_env()
        assert cfg.verify_token == ""
        assert cfg.access_token == ""
        assert cfg.phone_number_id == ""
        assert cfg.app_secret == ""
        assert cfg.graph_api_version == "v23.0"
        assert cfg.m2_backend_url == "http://localhost:8000"
        assert cfg.m2_api_key == ""
        assert cfg.m2_timeout == 10.0

    def test_from_env_with_custom_version(self):
        os.environ["GRAPH_API_VERSION"] = "v21.0"
        try:
            cfg = WhatsAppConfig.from_env()
            assert cfg.graph_api_version == "v21.0"
        finally:
            os.environ.pop("GRAPH_API_VERSION", None)

    def test_is_whatsapp_configured(self):
        cfg = WhatsAppConfig(
            verify_token="token",
            access_token="access",
            phone_number_id="123",
        )
        assert cfg.is_whatsapp_configured() is True

    def test_is_whatsapp_configured_missing_token(self):
        cfg = WhatsAppConfig(
            verify_token="",
            access_token="access",
            phone_number_id="123",
        )
        assert cfg.is_whatsapp_configured() is False

    def test_is_whatsapp_configured_missing_phone(self):
        cfg = WhatsAppConfig(
            verify_token="token",
            access_token="access",
            phone_number_id="",
        )
        assert cfg.is_whatsapp_configured() is False


class TestSafeErrorBody:
    def test_extracts_error_info(self):
        class FakeResponse:
            def json(self):
                return {
                    "error": {
                        "message": "Invalid access token",
                        "code": 190,
                        "error_subcode": 102,
                    }
                }
            status_code = 401

        result = _safe_error_body(FakeResponse())
        assert "code=190" in result
        assert "sub=102" in result
        assert "Invalid access token" in result

    def test_masks_access_token(self):
        class FakeResponse:
            def json(self):
                return {
                    "error": {
                        "message": "Token abc123xyz is invalid",
                        "code": 190,
                    }
                }
            status_code = 401

        from whatsapp.config import WhatsAppConfig
        # Temporarily set access token to something that appears in error
        import whatsapp.app as app_module
        old_token = app_module.config.access_token
        app_module.config.access_token = "abc123xyz"
        try:
            result = _safe_error_body(FakeResponse())
            assert "abc123xyz" not in result
            assert "***" in result
        finally:
            app_module.config.access_token = old_token

    def test_handles_no_error_field(self):
        class FakeResponse:
            def json(self):
                return {"unexpected": "format"}
            status_code = 400

        result = _safe_error_body(FakeResponse())
        assert "400" in result

    def test_handles_json_parse_error(self):
        class FakeResponse:
            def json(self):
                raise ValueError("not json")
            status_code = 500

        result = _safe_error_body(FakeResponse())
        assert "500" in result
