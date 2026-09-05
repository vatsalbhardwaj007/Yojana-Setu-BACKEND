"""Speech-to-text transcription backed by the Gemini API."""

import base64
import re

import httpx

from app.core.config import settings

GEMINI_GENERATE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
GEMINI_STT_MODEL = "gemini-3.6-flash"
TRANSCRIPTION_PROMPT = (
    "Transcribe the speech in this audio verbatim to plain text. "
    "Output only the transcript, with no preamble, labels, or explanation."
)


class TranscriptionUnavailableError(OSError):
    """Raised when Gemini speech-to-text is not configured (no GEMINI_API_KEY)."""


class TranscriptionError(OSError):
    """Raised when the Gemini API returns an error or no transcript."""


class TranscriptionService:
    """Transcribes an uploaded audio blob using the Gemini generateContent API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY

    def is_configured(self) -> bool:
        """True when a Gemini API key is available for speech-to-text."""
        return bool(self.api_key)

    def transcribe(self, audio: bytes, filename: str = "audio.webm", content_type: str = "audio/webm") -> str:
        """Return recognised speech text from audio bytes."""
        if not self.is_configured():
            raise TranscriptionUnavailableError("GEMINI_API_KEY is not configured on the backend.")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": TRANSCRIPTION_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": content_type or "audio/webm",
                                "data": base64.b64encode(audio).decode("ascii"),
                            }
                        },
                    ]
                }
            ]
        }
        url = GEMINI_GENERATE_URL.format(model=GEMINI_STT_MODEL)
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                url,
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
            )
        if response.status_code != 200:
            raise TranscriptionError(
                f"Gemini transcription request failed (HTTP {response.status_code}): {response.text[:200]}"
            )
        data = response.json()
        try:
            text = "".join(
                part.get("text", "")
                for part in data["candidates"][0]["content"]["parts"]
            ).strip()
        except (KeyError, IndexError, TypeError):
            raise TranscriptionError(
                f"Gemini returned no transcript: {response.text[:200]}"
            )
        if not text:
            raise TranscriptionError("Gemini returned an empty transcript.")
        return _clean_transcript(text)


def _clean_transcript(text: str) -> str:
    """Strip a leading language label the model sometimes emits (e.g. 'English:')."""
    cleaned = re.sub(r"^\s*[A-Za-z]{2,20}\s*:\s*", "", text.strip())
    return cleaned.strip()