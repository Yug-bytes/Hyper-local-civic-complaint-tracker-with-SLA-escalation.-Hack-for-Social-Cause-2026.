"""FastAPI dependencies for authentication, sessions, and request metadata."""

from typing import Optional

from fastapi import Header, Request

from api.auth.session_store import session_store
from config import get_settings
from errors import AuthError

ADMIN_COOKIE_NAME = "admin_session"
CITIZEN_COOKIE_NAME = "citizen_session"


def get_client_ip(
    request: Request,
    x_forwarded_for: Optional[str] = Header(default=None),
) -> str:
    """Extract real client IP address, taking proxies/forwarded headers into account."""
    if x_forwarded_for:
        # First IP in the comma-separated list is the client
        return x_forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


def get_citizen_session_id(
    request: Request,
) -> Optional[str]:
    """Read the anonymous citizen session cookie from request."""
    return request.cookies.get(CITIZEN_COOKIE_NAME)


def require_admin_session(
    request: Request,
) -> str:
    """Dependency enforcing valid, unexpired, unrevoked admin session cookie."""
    session_id = request.cookies.get(ADMIN_COOKIE_NAME)
    if not session_id or not session_store.validate_session(session_id):
        raise AuthError("Admin authentication required.")
    return session_id


def get_cookie_security_params() -> dict[str, object]:
    """Return cookie security parameters tailored to the current environment."""
    settings = get_settings()
    is_prod = settings.env.lower() in ("production", "prod")
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": is_prod,  # True only over HTTPS in production
        "path": "/",
    }
