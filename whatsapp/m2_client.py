"""M2 Backend Eligibility API client — real HTTP integration.

Calls the M2 backend's POST /eligibility/check endpoint to evaluate
citizen profiles against government scheme rules.
"""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger("yojanasetu.m2_client")

_USER_FRIENDLY_ERRORS = {
    "backend_unavailable": (
        "The eligibility service is currently unreachable. "
        "Please try again in a few minutes."
    ),
    "timeout": (
        "The eligibility service timed out. "
        "Please try again."
    ),
    "scheme_not_found": (
        "The selected scheme was not found in the eligibility system."
    ),
    "bad_request": (
        "The eligibility request was invalid. Please try again."
    ),
    "server_error": (
        "The eligibility service is experiencing issues. "
        "Please try again later."
    ),
    "invalid_response": (
        "Received an invalid response from the eligibility service."
    ),
}


class M2EligibilityClient:
    """HTTP client for the M2 eligibility backend."""

    def __init__(
        self,
        backend_url: str = "http://localhost:8000",
        api_key: str = "",
        timeout: float = 10.0,
    ):
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def check_eligibility(
        self, scheme_code: str, profile: dict[str, Any]
    ) -> dict:
        """Check eligibility by calling the M2 backend.

        Args:
            scheme_code: Canonical scheme identifier (e.g. "pm_kisan").
            profile: Citizen profile attributes as key-value pairs.

        Returns:
            Dict with normalized result from M2, or an error dict with
            keys: status="error", error_type, message.
        """
        if not self.backend_url:
            return self._error("backend_unavailable")

        url = f"{self.backend_url}/eligibility/check"
        payload = {"scheme_code": scheme_code, "profile": profile}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url, json=payload, headers=headers, timeout=self.timeout
                )

            if resp.status_code == 200:
                return self._parse_success(resp, scheme_code)

            if resp.status_code == 404:
                return self._error("scheme_not_found")

            if 400 <= resp.status_code < 500:
                return self._error("bad_request")

            if resp.status_code >= 500:
                return self._error("server_error")

            return self._error("server_error")

        except httpx.TimeoutException:
            return self._error("timeout")
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 404:
                return self._error("scheme_not_found")
            if status >= 500:
                return self._error("server_error")
            return self._error("bad_request")
        except httpx.RequestError:
            return self._error("backend_unavailable")
        except Exception:
            logger.exception("Unexpected error calling M2 backend")
            return self._error("invalid_response")

    def _parse_success(self, resp: httpx.Response, scheme_code: str) -> dict:
        """Parse a successful M2 response into a normalized dict."""
        try:
            data = resp.json()
        except Exception:
            return self._error("invalid_response")

        required_keys = ("status", "eligible")
        if not all(k in data for k in required_keys):
            return self._error("invalid_response")

        return {
            "status": "success",
            "m2_status": data.get("status", ""),
            "eligible": data.get("eligible"),
            "reasons": data.get("reasons", []),
            "reason_codes": data.get("reason_codes", []),
            "missing_fields": data.get("missing_fields", []),
            "scheme_code": data.get("scheme_code", scheme_code),
        }

    @staticmethod
    def _error(error_type: str) -> dict:
        """Return a safe error dict for the caller."""
        message = _USER_FRIENDLY_ERRORS.get(
            error_type, "An unexpected error occurred."
        )
        return {
            "status": "error",
            "error_type": error_type,
            "message": message,
        }

    def _required_fields_for_scheme(self, scheme_code: str) -> list[str]:
        """Return profile field names that M2 will need for this scheme."""
        from whatsapp.scheme_service import get_scheme

        scheme = get_scheme(scheme_code)
        if not scheme:
            return []
        return [
            pf.get("field_name", "")
            for pf in scheme.get("profile_fields", [])
            if pf.get("is_required", False)
        ]

    def is_configured(self) -> bool:
        """Check if M2 backend URL is configured."""
        return bool(self.backend_url)
