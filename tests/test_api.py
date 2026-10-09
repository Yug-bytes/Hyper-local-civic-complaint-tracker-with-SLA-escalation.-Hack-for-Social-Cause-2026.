"""Comprehensive API acceptance tests.

Covers:
- Public-data privacy (reporter_name/phone never disclosed).
- Ephemeral 15-minute signed photo URLs.
- Admin authentication with server-managed session cookies.
- Admin login brute-force rate limiting (5 attempts).
- Session expiration: 60-min inactivity and 8-hour max lifetime.
- Session revocation on logout.
- Two-tier citizen rate limiting: 30s cooldown and 5-submission session limit.
- IP-based abuse rate limiting (10/hr).
- Duplicate complaint detection within 24h.
- File validation (magic bytes, 5MB limit).
- Forward-only status transitions.
- Admin photo unlinking.
- Credentialed CORS preflight headers.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import db
from api.auth.rate_limiter import login_rate_limiter
from api.auth.session_store import session_store
from api.dependencies import ADMIN_COOKIE_NAME, CITIZEN_COOKIE_NAME
from api.main import app
from api.rate_limiting import complaint_rate_limiter
from config import get_settings
from tests.mock_db import MockSupabaseClient

# Sample valid JPEG header + bytes
VALID_JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb"
    + b"\x00" * 100
)
# Sample invalid bytes (e.g. text file disguised as jpg)
INVALID_PHOTO_BYTES = b"This is a text file, not a real image!"


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch: pytest.MonkeyPatch):
    """Set up mock Supabase client and reset in-memory limiters before each test."""
    mock_sb = MockSupabaseClient()
    db.set_client(mock_sb)

    # Ensure admin password is known for tests
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_password", "test-admin-password")

    # Clear rate limiters and session stores
    session_store.clear()
    login_rate_limiter.clear()
    complaint_rate_limiter.clear()

    yield

    db.set_client(None)


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_health_check(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_departments_list(client: TestClient):
    response = client.get("/api/departments")
    assert response.status_code == 200
    depts = response.json()
    assert len(depts) >= 5
    categories = [d["category"] for d in depts]
    assert "pothole" in categories
    assert "water" in categories


def test_submit_complaint_and_public_privacy(client: TestClient):
    """Verify complaint filing and that public view never leaks reporter PII."""
    # 1. Citizen submits complaint with confidential contact details and photo
    files = {"photo": ("broken_road.jpg", VALID_JPEG_BYTES, "image/jpeg")}
    data = {
        "category": "pothole",
        "description": "Deep pothole near municipal library entrance.",
        "locality": "Sector 4",
        "name": "Aarav Sharma",
        "phone": "9876543210",
    }
    create_resp = client.post("/api/complaints", data=data, files=files)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert "tracking_id" in created
    tracking_id = created["tracking_id"]
    assert tracking_id.startswith("CT-")

    # Check citizen cookie was set
    assert CITIZEN_COOKIE_NAME in create_resp.cookies

    # 2. Public lookup of the complaint
    get_resp = client.get(f"/api/complaints/{tracking_id}")
    assert get_resp.status_code == 200
    complaint = get_resp.json()

    # Public fields present
    assert complaint["tracking_id"] == tracking_id
    assert complaint["category"] == "pothole"
    assert complaint["locality"] == "Sector 4"
    assert complaint["description"] == "Deep pothole near municipal library entrance."
    assert complaint["status"] == "submitted"
    assert len(complaint["history"]) >= 1

    # Privacy check: reporter name and phone MUST NOT be exposed
    assert "reporter_name" not in complaint
    assert "reporter_phone" not in complaint
    assert "name" not in complaint
    assert "phone" not in complaint

    # Photo URL must be an ephemeral signed URL
    assert complaint["photo_url"] is not None
    assert "signed" in complaint["photo_url"] or "?token=" in complaint["photo_url"]


def test_admin_auth_wrong_password(client: TestClient):
    """Verify failed login returns 401 error envelope."""
    resp = client.post("/api/admin/login", json={"password": "wrong-password"})
    assert resp.status_code == 401
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert ADMIN_COOKIE_NAME not in resp.cookies


def test_admin_auth_brute_force_lockout(client: TestClient):
    """Verify 5 failed login attempts trigger 429 lockout."""
    headers = {"X-Forwarded-For": "198.51.100.25"}
    for _ in range(5):
        resp = client.post(
            "/api/admin/login",
            json={"password": "wrong-password"},
            headers=headers,
        )
        assert resp.status_code == 401

    # 6th attempt should be blocked with 429
    blocked_resp = client.post(
        "/api/admin/login",
        json={"password": "test-admin-password"},  # even with correct password
        headers=headers,
    )
    assert blocked_resp.status_code == 429
    assert blocked_resp.json()["error"]["code"] == "RATE_LIMITED"


def test_admin_auth_success_sets_httponly_cookie(client: TestClient):
    """Verify successful login issues HttpOnly session cookie."""
    resp = client.post(
        "/api/admin/login",
        json={"password": "test-admin-password"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "authenticated"
    assert ADMIN_COOKIE_NAME in resp.cookies

    # Verify session check
    session_resp = client.get("/api/admin/session", cookies=resp.cookies)
    assert session_resp.status_code == 200
    assert session_resp.json()["authenticated"] is True


def test_admin_protected_endpoints_require_session(client: TestClient):
    """Verify unauthenticated access to admin endpoints returns 401."""
    assert client.get("/api/admin/complaints").status_code == 401
    assert (
        client.patch(
            "/api/admin/complaints/CT-TEST/status", json={"new_status": "assigned"}
        ).status_code
        == 401
    )
    assert client.delete("/api/admin/complaints/CT-TEST/photo").status_code == 401
    assert client.get("/api/admin/metrics").status_code == 401


def test_admin_session_revocation_on_logout(client: TestClient):
    """Verify calling logout revokes server session."""
    # 1. Login
    login_resp = client.post(
        "/api/admin/login", json={"password": "test-admin-password"}
    )
    cookies = login_resp.cookies

    # Can access admin complaints
    assert client.get("/api/admin/complaints", cookies=cookies).status_code == 200

    # 2. Logout
    logout_resp = client.post("/api/admin/logout", cookies=cookies)
    assert logout_resp.status_code == 200

    # 3. Old cookie is now revoked and rejected
    assert client.get("/api/admin/complaints", cookies=cookies).status_code == 401


def test_admin_session_inactivity_expiry(client: TestClient):
    """Verify 60-minute inactivity expires the session."""
    login_resp = client.post(
        "/api/admin/login", json={"password": "test-admin-password"}
    )
    session_id = login_resp.cookies.get(ADMIN_COOKIE_NAME)
    assert session_id is not None

    # Artificially age the session's last_accessed_at past 60 minutes
    session = session_store._sessions[session_id]
    session.last_accessed_at = datetime.now(timezone.utc) - timedelta(minutes=61)

    # Protected call should now fail with 401
    resp = client.get("/api/admin/complaints", cookies={ADMIN_COOKIE_NAME: session_id})
    assert resp.status_code == 401


def test_admin_session_max_lifetime_expiry(client: TestClient):
    """Verify 8-hour hard lifetime expires the session even with recent activity."""
    login_resp = client.post(
        "/api/admin/login", json={"password": "test-admin-password"}
    )
    session_id = login_resp.cookies.get(ADMIN_COOKIE_NAME)
    assert session_id is not None

    # Artificially age created_at past 8 hours
    session = session_store._sessions[session_id]
    session.created_at = datetime.now(timezone.utc) - timedelta(hours=8, minutes=5)
    session.last_accessed_at = datetime.now(timezone.utc)  # accessed recently

    # Should be rejected because max lifetime is 8 hours
    resp = client.get("/api/admin/complaints", cookies={ADMIN_COOKIE_NAME: session_id})
    assert resp.status_code == 401


def test_complaint_rate_limit_cooldown_30s(client: TestClient):
    """Verify 30-second cooldown is enforced on same session."""
    data1 = {
        "category": "water",
        "description": "Low water pressure in Sector 2 pipeline.",
        "locality": "Sector 2",
    }
    resp1 = client.post("/api/complaints", data=data1)
    assert resp1.status_code == 201
    cookies = resp1.cookies

    # Immediate second complaint with same cookie must be rate limited
    data2 = {
        "category": "garbage",
        "description": "Garbage bin overflowing near market.",
        "locality": "Market Road",
    }
    resp2 = client.post("/api/complaints", data=data2, cookies=cookies)
    assert resp2.status_code == 429
    assert "wait" in resp2.json()["error"]["message"].lower()


def test_complaint_rate_limit_session_max_5(client: TestClient):
    """Verify 5-complaint maximum per session limit is enforced."""
    session_id = "test-session-limit-id"
    # Seed session with 5 submissions in the limiter
    now = datetime.now(timezone.utc) - timedelta(minutes=1)
    complaint_rate_limiter._session_records[session_id] = (
        complaint_rate_limiter._session_records.get(
            session_id,
            type(
                "Rec",
                (),
                {
                    "session_id": session_id,
                    "submission_count": 5,
                    "last_submitted_at": now,
                    "created_at": now,
                },
            )(),
        )
    )

    data = {
        "category": "streetlight",
        "description": "Streetlight pole 45 flickering.",
        "locality": "Ring Road",
    }
    resp = client.post(
        "/api/complaints",
        data=data,
        cookies={CITIZEN_COOKIE_NAME: session_id},
    )
    assert resp.status_code == 429
    assert "limit reached" in resp.json()["error"]["message"].lower()


def test_complaint_rate_limit_ip_burst_10(client: TestClient):
    """Verify IP burst limit: >10 submissions within 1 hour rejected."""
    ip = "203.0.113.99"
    headers = {"X-Forwarded-For": ip}
    # Pre-populate 10 submissions for this IP
    now = datetime.now(timezone.utc)
    complaint_rate_limiter._ip_records[ip] = [now] * 10

    data = {
        "category": "garbage",
        "description": "Uncollected garbage behind school.",
        "locality": "School Lane",
    }
    resp = client.post("/api/complaints", data=data, headers=headers)
    assert resp.status_code == 429
    assert "rate limit exceeded from this ip" in resp.json()["error"]["message"].lower()


def test_duplicate_complaint_detection(client: TestClient):
    """Verify duplicate submission within 24h returns 400."""
    data = {
        "category": "pothole",
        "description": "Massive pothole in front of community centre.",
        "locality": "Sector 9",
    }
    # First submission
    resp1 = client.post("/api/complaints", data=data)
    assert resp1.status_code == 201

    # Second submission from different session (clear cookies to bypass cooldown)
    client.cookies.clear()
    resp2 = client.post(
        "/api/complaints",
        data=data,
        headers={"X-Forwarded-For": "198.51.100.77"},
    )
    assert resp2.status_code == 400
    assert "similar complaint" in resp2.json()["error"]["message"].lower()


def test_photo_validation_invalid_type(client: TestClient):
    """Verify non-image files are rejected even if named .jpg."""
    files = {"photo": ("test.jpg", INVALID_PHOTO_BYTES, "image/jpeg")}
    data = {
        "category": "water",
        "description": "Contaminated water supply.",
        "locality": "Block B",
    }
    resp = client.post("/api/complaints", data=data, files=files)
    assert resp.status_code == 400
    assert "jpg or png" in resp.json()["error"]["message"].lower()


def test_photo_validation_oversize(client: TestClient):
    """Verify photos larger than 5MB are rejected."""
    large_bytes = VALID_JPEG_BYTES + (b"\x00" * (5 * 1024 * 1024 + 10))
    files = {"photo": ("huge.jpg", large_bytes, "image/jpeg")}
    data = {
        "category": "streetlight",
        "description": "Dark street near park.",
        "locality": "Park Avenue",
    }
    resp = client.post("/api/complaints", data=data, files=files)
    assert resp.status_code == 400
    assert "5 mb" in resp.json()["error"]["message"].lower()


def test_forward_only_status_transitions(client: TestClient):
    """Verify status can only advance forward through valid stages."""
    # 1. Create a complaint
    data = {
        "category": "water",
        "description": "Pipeline leak on 5th cross.",
        "locality": "5th Cross",
    }
    create_resp = client.post("/api/complaints", data=data)
    tracking_id = create_resp.json()["tracking_id"]

    # 2. Login admin
    login_resp = client.post(
        "/api/admin/login", json={"password": "test-admin-password"}
    )
    admin_cookies = login_resp.cookies

    # Invalid: submitted -> in_progress (skipping assigned)
    bad_resp1 = client.patch(
        f"/api/admin/complaints/{tracking_id}/status",
        json={"new_status": "in_progress"},
        cookies=admin_cookies,
    )
    assert bad_resp1.status_code == 400

    # Invalid: submitted -> resolved (skipping assigned & in_progress)
    bad_resp2 = client.patch(
        f"/api/admin/complaints/{tracking_id}/status",
        json={"new_status": "resolved"},
        cookies=admin_cookies,
    )
    assert bad_resp2.status_code == 400

    # Valid step 1: submitted -> assigned
    step1_resp = client.patch(
        f"/api/admin/complaints/{tracking_id}/status",
        json={"new_status": "assigned", "note": "Assigned to Ward Engineer"},
        cookies=admin_cookies,
    )
    assert step1_resp.status_code == 200
    assert step1_resp.json()["status"] == "assigned"

    # Valid step 2: assigned -> in_progress
    step2_resp = client.patch(
        f"/api/admin/complaints/{tracking_id}/status",
        json={"new_status": "in_progress", "note": "Work order issued"},
        cookies=admin_cookies,
    )
    assert step2_resp.status_code == 200
    assert step2_resp.json()["status"] == "in_progress"

    # Valid step 3: in_progress -> resolved
    step3_resp = client.patch(
        f"/api/admin/complaints/{tracking_id}/status",
        json={"new_status": "resolved", "note": "Leak repaired successfully"},
        cookies=admin_cookies,
    )
    assert step3_resp.status_code == 200
    assert step3_resp.json()["status"] == "resolved"
    assert step3_resp.json()["resolved_at"] is not None

    # Invalid: trying to update already resolved complaint
    bad_resp3 = client.patch(
        f"/api/admin/complaints/{tracking_id}/status",
        json={"new_status": "in_progress"},
        cookies=admin_cookies,
    )
    assert bad_resp3.status_code == 400
    assert "already 'resolved'" in bad_resp3.json()["error"]["message"]


def test_admin_unlink_photo(client: TestClient):
    """Verify admin can delete/unlink a photo from complaint."""
    files = {"photo": ("road.jpg", VALID_JPEG_BYTES, "image/jpeg")}
    data = {
        "category": "pothole",
        "description": "Dangerous pothole.",
        "locality": "Sector 1",
    }
    create_resp = client.post("/api/complaints", data=data, files=files)
    tracking_id = create_resp.json()["tracking_id"]

    login_resp = client.post(
        "/api/admin/login", json={"password": "test-admin-password"}
    )
    admin_cookies = login_resp.cookies

    del_resp = client.delete(
        f"/api/admin/complaints/{tracking_id}/photo",
        cookies=admin_cookies,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["photo_url"] is None

    # Verify public status now has null photo_url
    pub_resp = client.get(f"/api/complaints/{tracking_id}")
    assert pub_resp.json()["photo_url"] is None


def test_cors_preflight_headers(client: TestClient):
    """Verify CORS headers for configured localhost dev origin."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    resp = client.options("/api/complaints", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert resp.headers.get("access-control-allow-credentials") == "true"


def test_public_metrics_zero_pii(client: TestClient):
    """Verify public metrics returns aggregated stats without personal info."""
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    metrics = resp.json()
    assert isinstance(metrics, list)
    for m in metrics:
        assert "category" in m
        assert "department_name" in m
        assert "total_complaints" in m
        assert "resolution_rate_pct" in m
        assert "reporter_name" not in m
        assert "reporter_phone" not in m
