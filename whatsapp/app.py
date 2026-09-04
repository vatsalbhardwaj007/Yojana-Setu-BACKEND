"""FastAPI application — WhatsApp Cloud API webhook endpoints."""

import asyncio
import logging
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Response

from whatsapp.config import WhatsAppConfig
from whatsapp.handlers import handle_message
from whatsapp.message_utils import split_message
from whatsapp.webhook import parse_incoming_message, verify_signature, verify_webhook

logger = logging.getLogger("yojanasetu.whatsapp")

app = FastAPI(title="YojanaSetu WhatsApp Bot", version="0.1.0")

config = WhatsAppConfig.from_env()

WHATSAPP_API_BASE = "https://graph.facebook.com"


@app.get("/health")
async def health():
    return {"status": "ok", "service": "yojanasetu-whatsapp"}


@app.get("/webhook")
async def webhook_verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode", "")
    token = params.get("hub.verify_token", "")
    challenge = params.get("hub.challenge", "")

    result = verify_webhook(mode, token, challenge, config.verify_token)
    if result:
        return Response(content=result, media_type="text/plain")
    return Response(status_code=403, content="Forbidden")


@app.post("/webhook")
async def webhook_receive(request: Request):
    # Read body early for signature verification and JSON parsing
    body_bytes = await request.body()

    # Verify signature if app_secret is configured
    if config.app_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_signature(body_bytes, signature, config.app_secret):
            logger.warning("Invalid webhook signature")
            return Response(status_code=403, content="Invalid signature")

    # Parse the JSON payload
    import json

    try:
        payload = json.loads(body_bytes)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Invalid JSON in webhook payload")
        return Response(status_code=400, content="Invalid JSON")

    # Parse the incoming message
    parsed = parse_incoming_message(payload)
    if not parsed:
        return {"status": "ignored"}

    sender = parsed["sender"]
    text = parsed.get("text", "")

    # Return 200 immediately so Meta does not retry
    # Process the message and send reply asynchronously in the background
    if config.is_whatsapp_configured():
        asyncio.create_task(_process_and_reply(sender, text))

    return {"status": "ok"}


async def _process_and_reply(sender: str, text: str) -> None:
    """Process message and send reply. Runs as a background task."""
    try:
        reply_text = await handle_message(sender, text)
        await _send_whatsapp_message(sender, reply_text)
    except Exception:
        logger.exception("Failed to process message for sender=%s", sender[:4] + "****")


async def _send_whatsapp_message(to: str, text: str) -> None:
    """Send one or more text messages via WhatsApp Cloud API.

    Long messages are split at newline boundaries to stay within
    the 4096-character WhatsApp text message limit.
    """
    chunks = split_message(text, max_length=4096)

    url = f"{WHATSAPP_API_BASE}/{config.graph_api_version}/{config.phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {config.access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        for chunk in chunks:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": chunk},
            }
            try:
                resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
                if resp.status_code == 429:
                    # Rate limited — log and stop sending further chunks
                    logger.warning(
                        "WhatsApp API rate limited (429) for recipient=%s",
                        to[:4] + "****",
                    )
                    break
                elif resp.status_code >= 400:
                    logger.error(
                        "WhatsApp API error %d for recipient=%s: %s",
                        resp.status_code,
                        to[:4] + "****",
                        _safe_error_body(resp),
                    )
                else:
                    logger.info(
                        "WhatsApp message sent to=%s chars=%d",
                        to[:4] + "****",
                        len(chunk),
                    )
            except httpx.TimeoutException:
                logger.warning(
                    "WhatsApp API timeout sending to=%s", to[:4] + "****"
                )
            except httpx.RequestError as exc:
                logger.warning(
                    "WhatsApp API request error for recipient=%s: %s",
                    to[:4] + "****",
                    type(exc).__name__,
                )


def _safe_error_body(resp: httpx.Response) -> str:
    """Extract a safe error description from the response, masking secrets."""
    try:
        data = resp.json()
        error = data.get("error", {})
        msg = error.get("message", "")
        code = error.get("code", "")
        sub = error.get("error_subcode", "")
        parts = []
        if code:
            parts.append(f"code={code}")
        if sub:
            parts.append(f"sub={sub}")
        if msg:
            # Mask any accidentally embedded tokens
            safe_msg = msg
            if config.access_token:
                safe_msg = safe_msg.replace(config.access_token, "***")
            if config.app_secret:
                safe_msg = safe_msg.replace(config.app_secret, "***")
            parts.append(safe_msg)
        return " ".join(parts) if parts else str(resp.status_code)
    except Exception:
        return str(resp.status_code)
