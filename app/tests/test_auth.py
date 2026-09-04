"""Unit and integration tests for Phase 4 Authentication and Protected APIs.

Covers all 13 authentication and security scenarios:
1. Valid authenticated request
2. Missing Authorization header (401)
3. Malformed Authorization header (401)
4. Invalid JWT signature/format (401)
5. Expired JWT (401)
6. Missing 'sub' claim in JWT (401)
7. GET /api/v1/auth/me authenticated (200)
8. GET /api/v1/auth/me unauthenticated (401)
9. GET /profile authenticated (200)
10. POST /profile authenticated (200)
11. PUT /profile authenticated (200)
12. Attempted access/tampering with another user's profile (IDOR protection)
13. Unauthenticated profile requests rejected (401)
"""

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import init_db
from app.main import app

client = TestClient(app)

TEST_SECRET = "test-jwt-secret-key-for-unit-tests-only-xyz123"


@pytest.fixture(autouse=True)
def setup_auth_environment() -> Generator[None, None, None]:
    """Configure test JWT secret and initialize database schema before each test."""
    original_secret = settings.SUPABASE_JWT_SECRET
    settings.SUPABASE_JWT_SECRET = TEST_SECRET
    init_db()
    yield
    settings.SUPABASE_JWT_SECRET = original_secret
    app.dependency_overrides.clear()


def make_auth_header(
    user_id: str = "test-user-uuid-1234",
    email: str = "citizen@example.com",
    secret: str = TEST_SECRET,
    expires_in_seconds: int = 3600,
    **extra_claims,
) -> dict[str, str]:
    """Helper to generate a Bearer authorization header with a valid signed token."""
    token = create_access_token(
        sub=user_id,
        email=email,
        secret=secret,
        expires_in_seconds=expires_in_seconds,
        **extra_claims,
    )
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1. JWT & HEADER VALIDATION SCENARIOS (Scenarios 1 - 6)
# =====================================================================


def test_01_valid_authenticated_request():
    """Verify that a valid signed JWT is accepted on /api/v1/auth/me."""
    headers = make_auth_header(user_id="user_valid_01", email="valid@example.com")
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "user_valid_01"
    assert data["email"] == "valid@example.com"
    assert data["role"] == "authenticated"


def test_02_missing_authorization_header():
    """Verify that missing Authorization header returns HTTP 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "Missing Authorization header" in resp.json()["detail"]
    assert "Bearer" in resp.headers.get("WWW-Authenticate", "")


def test_03_malformed_authorization_header():
    """Verify that malformed Authorization header formats return HTTP 401."""
    # Not Bearer prefix
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Basic 12345"})
    assert resp.status_code == 401
    assert "Bearer" in resp.headers.get("WWW-Authenticate", "")

    # Single token string without Bearer
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "RawTokenValue"})
    assert resp.status_code == 401

    # Empty token after Bearer
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer "})
    assert resp.status_code == 401


def test_04_invalid_jwt_signature():
    """Verify that a JWT with an invalid signature is rejected with HTTP 401."""
    # Token signed with an untrusted secret (>= 32 bytes)
    headers = make_auth_header(secret="wrong-untrusted-secret-key-999-at-least-32-chars-long")
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
    assert "Invalid authentication token" in resp.json()["detail"]

    # Random malformed JWT payload
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.string"})
    assert resp.status_code == 401


def test_05_expired_jwt():
    """Verify that an expired JWT token returns HTTP 401."""
    headers = make_auth_header(expires_in_seconds=-3600)  # Expired 1 hour ago
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_06_missing_sub_claim_in_jwt():
    """Verify that a token lacking a valid 'sub' claim returns HTTP 401."""
    import jwt as pyjwt
    # Generate token directly without 'sub'
    payload = {"aud": "authenticated", "email": "nosub@example.com"}
    token = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "sub" in resp.json()["detail"].lower()


# =====================================================================
# 2. /AUTH/ME ENDPOINT TESTS (Scenarios 7 - 8)
# =====================================================================


def test_07_auth_me_authenticated_both_mounts():
    """Verify /auth/me returns identity on both /api/v1/auth/me and /auth/me."""
    headers = make_auth_header(user_id="citizen_uid_777", email="citizen777@gov.in")
    for path in ["/api/v1/auth/me", "/auth/me"]:
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "citizen_uid_777"
        assert data["email"] == "citizen777@gov.in"


def test_08_auth_me_unauthenticated_rejected():
    """Verify unauthenticated requests to /auth/me return HTTP 401."""
    for path in ["/api/v1/auth/me", "/auth/me"]:
        resp = client.get(path)
        assert resp.status_code == 401


# =====================================================================
# 3. PROTECTED PROFILE APIS & IDOR PROTECTION (Scenarios 9 - 13)
# =====================================================================


def test_09_post_profile_authenticated():
    """Verify POST /profile creates profile bound strictly to verified JWT sub."""
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    headers = make_auth_header(user_id=user_id, email=f"{user_id}@test.com")

    payload = {
        "age": 32,
        "state": "Maharashtra",
        "gender": "female",
        "occupation": "farmer",
        "annual_income": 85000.0,
    }
    resp = client.post("/api/v1/profile", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user_id
    assert data["user_id"] == user_id
    assert data["profile"]["age"] == 32
    assert data["profile"]["occupation"] == "farmer"


def test_10_get_profile_authenticated():
    """Verify GET /profile retrieves the authenticated caller's profile."""
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    headers = make_auth_header(user_id=user_id)

    # Initially not found -> 404
    resp = client.get("/api/v1/profile", headers=headers)
    assert resp.status_code == 404

    # Create profile
    client.post(
        "/api/v1/profile",
        json={"age": 25, "state": "Kerala", "occupation": "student"},
        headers=headers,
    )

    # Now GET returns 200
    resp = client.get("/api/v1/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user_id
    assert data["profile"]["occupation"] == "student"


def test_11_put_profile_authenticated():
    """Verify PUT /profile partially updates caller's profile without data loss."""
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    headers = make_auth_header(user_id=user_id)

    # Create profile
    client.post(
        "/api/v1/profile",
        json={"age": 45, "state": "Gujarat", "occupation": "artisan"},
        headers=headers,
    )

    # Update annual income
    update_resp = client.put(
        "/api/v1/profile",
        json={"annual_income": 90000.0},
        headers=headers,
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["id"] == user_id
    assert data["profile"]["age"] == 45  # Preserved
    assert data["profile"]["state"] == "Gujarat"  # Preserved
    assert data["profile"]["annual_income"] == 90000.0


def test_12_idor_protection_attempted_access_to_other_user():
    """Verify a user cannot read, create, or modify another citizen's profile.

    Tests that user_id in query parameters or request body is ignored and cannot override
    current_user.id from the verified JWT.
    """
    user_alice = f"alice_{uuid.uuid4().hex[:8]}"
    user_bob = f"bob_{uuid.uuid4().hex[:8]}"

    alice_headers = make_auth_header(user_id=user_alice)
    bob_headers = make_auth_header(user_id=user_bob)

    # Alice creates her profile
    client.post(
        "/api/v1/profile",
        json={"age": 30, "state": "Punjab", "occupation": "doctor"},
        headers=alice_headers,
    )

    # Bob attempts to read Alice's profile (Bob has no profile yet)
    # Even if Bob passes ?user_id=alice, backend strictly uses Bob's token
    bob_get = client.get(f"/api/v1/profile?user_id={user_alice}", headers=bob_headers)
    assert bob_get.status_code == 404  # Bob has no profile, cannot see Alice's!

    # Bob attempts to overwrite Alice's profile by supplying Alice's user_id in payload
    bob_post = client.post(
        "/api/v1/profile",
        json={"user_id": user_alice, "age": 99, "occupation": "hacker"},
        headers=bob_headers,
    )
    assert bob_post.status_code == 200
    bob_data = bob_post.json()
    # The profile created is Bob's, NOT Alice's!
    assert bob_data["id"] == user_bob

    # Verify Alice's profile was NOT tampered with
    alice_check = client.get("/api/v1/profile", headers=alice_headers)
    assert alice_check.status_code == 200
    assert alice_check.json()["profile"]["age"] == 30
    assert alice_check.json()["profile"]["occupation"] == "doctor"


def test_13_unauthenticated_profile_requests_rejected():
    """Verify that unauthenticated access to /profile endpoints is strictly rejected."""
    for path in ["/api/v1/profile", "/profile"]:
        # GET
        get_res = client.get(path)
        assert get_res.status_code == 401
        assert "Bearer" in get_res.headers.get("WWW-Authenticate", "")

        # POST
        post_res = client.post(path, json={"age": 20})
        assert post_res.status_code == 401

        # PUT
        put_res = client.put(path, json={"age": 21})
        assert put_res.status_code == 401
