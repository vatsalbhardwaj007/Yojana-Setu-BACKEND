"""FastAPI dependencies for authentication and authorization."""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import (
    AuthTokenError,
    TokenExpiredError,
    TokenInvalidError,
    TokenSecretMissingError,
    verify_jwt_token,
)
from app.schemas.auth import AuthenticatedUser

logger = logging.getLogger(__name__)

# Security scheme for OpenAPI Swagger docs and credential extraction
http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(http_bearer)] = None,
) -> AuthenticatedUser:
    """Validate incoming Supabase Bearer JWT and return authenticated user identity.

    Extracts user_id from the verified JWT 'sub' claim.
    Rejects missing, malformed, expired, or invalid tokens with HTTP 401 Unauthorized.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate header structure
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format; expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    if not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty Bearer token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = verify_jwt_token(token)
    except TokenSecretMissingError as exc:
        logger.error("Authentication rejected: server lacks JWT secret configuration.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication configuration error",
        ) from exc
    except TokenExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except (TokenInvalidError, AuthTokenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return AuthenticatedUser(
        id=str(claims["sub"]),
        email=claims.get("email"),
        phone=claims.get("phone"),
        role=claims.get("role"),
        app_metadata=claims.get("app_metadata", {}),
        user_metadata=claims.get("user_metadata", {}),
    )


CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]
