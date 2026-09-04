"""Integration tests for FastAPI webhook endpoints."""

import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from whatsapp.app import app, config


client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "yojanasetu-whatsapp"


class TestWebhookVerification:
    def test_valid_verification_when_configured(self):
        old_token = config.verify_token
        config.verify_token = "my-secret-token"
        try:
            resp = client.get(
                "/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "my-secret-token",
                    "hub.challenge": "challenge-123",
                },
            )
            assert resp.status_code == 200
            assert resp.text == "challenge-123"
        finally:
            config.verify_token = old_token

    def test_invalid_token_returns_403(self):
        resp = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "challenge-123",
            },
        )
        assert resp.status_code == 403

    def test_missing_params(self):
        resp = client.get("/webhook")
        assert resp.status_code == 403


class TestWebhookReceive:
    def _make_payload(self, sender="919876543210", text="Hi"):
        return {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": sender,
                            "type": "text",
                            "id": "msg-test-001",
                            "text": {"body": text},
                        }]
                    }
                }]
            }]
        }

    def test_valid_text_message_returns_ok(self):
        payload = self._make_payload()
        resp = client.post(
            "/webhook",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_ignored_payload_returns_ok(self):
        # Status notifications don't have messages
        payload = {"entry": [{"changes": [{"value": {"statuses": []}}]}]}
        resp = client.post(
            "/webhook",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ignored"

    def test_invalid_json_returns_400(self):
        resp = client.post(
            "/webhook",
            content="not-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    def test_signature_validation_rejects_bad_sig(self):
        # Temporarily ensure app_secret is set
        old_secret = config.app_secret
        config.app_secret = "test-secret"
        try:
            payload = self._make_payload()
            body = json.dumps(payload).encode()
            resp = client.post(
                "/webhook",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": "sha256=invalid",
                },
            )
            assert resp.status_code == 403
        finally:
            config.app_secret = old_secret

    def test_signature_validation_passes_valid_sig(self):
        old_secret = config.app_secret
        config.app_secret = "test-secret"
        try:
            payload = self._make_payload()
            body = json.dumps(payload).encode()
            sig = "sha256=" + hmac.new(
                b"test-secret", body, hashlib.sha256
            ).hexdigest()
            resp = client.post(
                "/webhook",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": sig,
                },
            )
            assert resp.status_code == 200
        finally:
            config.app_secret = old_secret

    def test_no_secret_skips_signature_check(self):
        old_secret = config.app_secret
        config.app_secret = ""
        try:
            payload = self._make_payload()
            resp = client.post(
                "/webhook",
                content=json.dumps(payload),
                headers={"Content-Type": "application/json"},
            )
            assert resp.status_code == 200
        finally:
            config.app_secret = old_secret
