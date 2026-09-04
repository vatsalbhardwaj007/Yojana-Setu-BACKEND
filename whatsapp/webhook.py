"""WhatsApp Cloud API webhook verification and message parsing."""

import hashlib
import hmac
from typing import Optional


def verify_webhook(mode: str, token: str, challenge: str, verify_token: str) -> Optional[str]:
    """Verify WhatsApp webhook subscription.

    Returns the challenge string on success, None on failure.
    """
    if mode == "subscribe" and token == verify_token:
        return challenge
    return None


def parse_incoming_message(payload: dict) -> Optional[dict]:
    """Extract message info from a WhatsApp Cloud API webhook payload.

    Returns dict with keys: sender, message_type, text, message_id
    or None if the payload is not a text message.
    """
    try:
        entry = payload.get("entry", [])
        if not entry:
            return None

        changes = entry[0].get("changes", [])
        if not changes:
            return None

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        msg = messages[0]
        sender = msg.get("from", "")
        msg_type = msg.get("type", "")
        msg_id = msg.get("id", "")

        if msg_type == "text":
            text_body = msg.get("text", {}).get("body", "")
            return {
                "sender": sender,
                "message_type": "text",
                "text": text_body.strip(),
                "message_id": msg_id,
            }

        return {
            "sender": sender,
            "message_type": msg_type,
            "text": "",
            "message_id": msg_id,
        }
    except (KeyError, IndexError, TypeError):
        return None


def verify_signature(payload_bytes: bytes, signature: str, app_secret: str) -> bool:
    """Verify X-Hub-Signature-256 header.

    Returns True if valid or if no app_secret is configured.
    """
    if not app_secret:
        return True
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
