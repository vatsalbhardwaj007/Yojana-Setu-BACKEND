"""Security and JWT verification module for Supabase-issued tokens."""

import logging
from datetime import datetime, timezone
from typing import Any

import jwt
from jwt import PyJWKClient, PyJWKClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Cached JWKS client for modern Supabase signing keys (ES256/RS256).
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient | None:
    """Lazily build a JWKS client from the configured Supabase project URL."""
    global _jwks_client
    if not settings.SUPABASE_URL:
        return None
    if _jwks_client is None:
        url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(url, timeout=10)
    return _jwks_client


def _build_decode_kwargs() -> dict[str, Any]:
    """Build common decode options, verifying the audience only when configured."""
    decode_kwargs: dict[str, Any] = {
        "options": {
            "verify_signature": True,
            "verify_exp": True,
        },
    }
    if settings.JWT_AUDIENCE:
        decode_kwargs["audience"] = settings.JWT_AUDIENCE
        decode_kwargs["options"]["verify_aud"] = True
    else:
        decode_kwargs["options"]["verify_aud"] = False
    return decode_kwargs


def _require_sub(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate that the decoded token carries a subject ('sub') claim."""
    sub = payload.get("sub")
    if not sub or not str(sub).strip():
        raise TokenInvalidError("Token missing valid subject ('sub') claim.")
    return payload


class AuthTokenError(Exception):
    """Base exception for authentication token errors."""


class TokenExpiredError(AuthTokenError):
    """Raised when the JWT token signature is expired."""


class TokenInvalidError(AuthTokenError):
    """Raised when the JWT token is malformed, has invalid signature, or missing required claims."""


class TokenSecretMissingError(AuthTokenError):
    """Raised when the server lacks configuration for JWT verification secret."""


def verify_jwt_token(token: str, secret: str | None = None) -> dict[str, Any]:
    """Verify Supabase-issued JWT access token.

    Validates signature, expiration, and extracts standard claims.

    Args:
        token: Raw Bearer JWT string.
        secret: Optional secret override (defaults to settings.SUPABASE_JWT_SECRET).

    Returns:
        Decoded payload claims dictionary containing 'sub', 'email', etc.

    Raises:
        TokenSecretMissingError: If server secret is unconfigured.
        TokenExpiredError: If token expiration (exp) is in the past.
        TokenInvalidError: If signature, format, or claims are invalid.
    """
    signing_secret = secret if secret is not None else settings.SUPABASE_JWT_SECRET
    if not signing_secret:
        logger.error("SUPABASE_JWT_SECRET is not configured on the server.")
        raise TokenSecretMissingError("Supabase JWT secret is not configured on the server.")

    decode_kwargs = _build_decode_kwargs()

    # Path 1: legacy HS256 verification against the Supabase JWT secret.
    if signing_secret:
        try:
            payload = jwt.decode(
                token, signing_secret, algorithms=[settings.JWT_ALGORITHM], **decode_kwargs
            )
            return _require_sub(payload)
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError("Token has expired.") from exc
        except (jwt.InvalidSignatureError, jwt.InvalidAlgorithmError):
            # Not an HS256-secret-signed token (e.g. modern ES256/RS256 signing);
            # fall through to the JWKS path.
            pass
        except jwt.InvalidTokenError as exc:
            raise TokenInvalidError(f"Invalid token: {exc}") from exc

    # Path 2: modern Supabase signing keys verified against the project JWKS.
    jwks_client = _get_jwks_client()
    if jwks_client is not None:
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token, signing_key.key, algorithms=[signing_key.algorithm_name], **decode_kwargs
            )
            return _require_sub(payload)
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError("Token has expired.") from exc
        except (jwt.InvalidTokenError, PyJWKClientError) as exc:
            raise TokenInvalidError(f"Invalid token: {exc}") from exc

    raise TokenInvalidError("Invalid authentication token: no matching signing key was found.")


def create_access_token(
    sub: str,
    email: str | None = None,
    phone: str | None = None,
    role: str = "authenticated",
    secret: str | None = None,
    expires_in_seconds: int = 3600,
    **extra_claims: Any,
) -> str:
    """Create a signed JWT token (primarily for tests and local verification)."""
    signing_secret = secret if secret is not None else settings.SUPABASE_JWT_SECRET
    if not signing_secret:
        raise TokenSecretMissingError("Cannot create token: secret is not configured.")

    now = datetime.now(timezone.utc)
    now_ts = int(now.timestamp())
    exp_ts = now_ts + expires_in_seconds

    payload: dict[str, Any] = {
        "sub": str(sub),
        "role": role,
        "iat": now_ts,
        "exp": exp_ts,
    }
    if settings.JWT_AUDIENCE:
        payload["aud"] = settings.JWT_AUDIENCE
    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone
    payload.update(extra_claims)

    return jwt.encode(payload, signing_secret, algorithm=settings.JWT_ALGORITHM)
