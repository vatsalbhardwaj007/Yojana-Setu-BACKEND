"""Tests for webhook verification and message parsing."""

import hashlib
import hmac

from whatsapp.webhook import parse_incoming_message, verify_signature, verify_webhook


class TestWebhookVerification:
    def test_valid_verification(self):
        result = verify_webhook("subscribe", "my-token", "challenge-123", "my-token")
        assert result == "challenge-123"

    def test_invalid_token(self):
        result = verify_webhook("subscribe", "wrong-token", "challenge-123", "my-token")
        assert result is None

    def test_invalid_mode(self):
        result = verify_webhook("unsubscribe", "my-token", "challenge-123", "my-token")
        assert result is None

    def test_empty_params(self):
        result = verify_webhook("", "", "", "")
        assert result is None


class TestMessageParsing:
    def test_parse_text_message(self):
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "919876543210",
                            "type": "text",
                            "id": "msg-001",
                            "text": {"body": "Hello"}
                        }]
                    }
                }]
            }]
        }
        result = parse_incoming_message(payload)
        assert result is not None
        assert result["sender"] == "919876543210"
        assert result["text"] == "Hello"
        assert result["message_type"] == "text"
        assert result["message_id"] == "msg-001"

    def test_parse_empty_entry(self):
        result = parse_incoming_message({"entry": []})
        assert result is None

    def test_parse_no_messages(self):
        payload = {"entry": [{"changes": [{"value": {"messages": []}}]}]}
        result = parse_incoming_message(payload)
        assert result is None

    def test_parse_non_text_message(self):
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "919876543210",
                            "type": "image",
                            "id": "msg-002",
                        }]
                    }
                }]
            }]
        }
        result = parse_incoming_message(payload)
        assert result is not None
        assert result["message_type"] == "image"
        assert result["text"] == ""

    def test_parse_malformed_payload(self):
        result = parse_incoming_message({})
        assert result is None

    def test_parse_text_with_whitespace(self):
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "919876543210",
                            "type": "text",
                            "id": "msg-003",
                            "text": {"body": "  Hi  "}
                        }]
                    }
                }]
            }]
        }
        result = parse_incoming_message(payload)
        assert result["text"] == "Hi"


class TestSignatureVerification:
    def test_valid_signature(self):
        payload = b'{"test": "data"}'
        secret = "my-secret"
        sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        assert verify_signature(payload, sig, secret) is True

    def test_invalid_signature(self):
        payload = b'{"test": "data"}'
        assert verify_signature(payload, "sha256=wrong", "my-secret") is False

    def test_no_secret_allows_all(self):
        payload = b'{"test": "data"}'
        assert verify_signature(payload, "any", "") is True

    def test_empty_payload(self):
        assert verify_signature(b"", "sha256=" + hmac.new(b"s", b"", hashlib.sha256).hexdigest(), "s") is True
