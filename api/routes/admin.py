"""Admin routes with server-managed session authentication and rate limiting."""

import secrets
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    Response,
)

import db
from api.auth.rate_limiter import login_rate_limiter
from api.auth.session_store import session_store
from api.dependencies import (
    ADMIN_COOKIE_NAME,
    get_client_ip,
    get_cookie_security_params,
    require_admin_session,
)
from api.schemas import (
    AdminLoginIn,
    AdminLoginOut,
    AdminMetricsSummaryOut,
    AdminSessionOut,
    ComplaintAdminOut,
    StatusUpdateIn,
)
from config import get_settings
from errors import AuthError
from services import metrics

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post(
    "/login",
    response_model=AdminLoginOut,
    summary="Authenticate as administrator",
)
def admin_login(
    credentials: AdminLoginIn,
    response: Response,
    client_ip: str = Depends(get_client_ip),
) -> AdminLoginOut:
    """Validate admin password, enforce brute-force rate limit, issue session cookie."""
    # 1. Enforce brute-force rate limiting per IP
    login_rate_limiter.check_allowed(client_ip)

    # 2. Constant-time password comparison
    settings = get_settings()
    is_valid = secrets.compare_digest(
        credentials.password.strip(),
        settings.admin_password.strip(),
    )

    if not is_valid:
        login_rate_limiter.record_failure(client_ip)
        raise AuthError("Invalid admin password.")

    # 3. Successful login: reset failed attempts counter
    login_rate_limiter.record_success(client_ip)

    # 4. Create server-side session
    session_id = session_store.create_session(ip_address=client_ip)

    # 5. Issue HttpOnly secure cookie
    cookie_params = get_cookie_security_params()
    response.set_cookie(
        key=ADMIN_COOKIE_NAME,
        value=session_id,
        max_age=28800,  # 8 hours maximum lifetime
        **cookie_params,
    )

    return AdminLoginOut(status="authenticated")


@router.post(
    "/logout",
    summary="Log out and revoke current admin session",
)
def admin_logout(
    request: Request,
    response: Response,
) -> dict[str, str]:
    """Revoke admin session on the server and expire the session cookie."""
    session_id = request.cookies.get(ADMIN_COOKIE_NAME)
    if session_id:
        session_store.revoke_session(session_id)

    response.delete_cookie(
        key=ADMIN_COOKIE_NAME,
        path="/",
    )
    return {"status": "logged_out"}


@router.get(
    "/session",
    response_model=AdminSessionOut,
    summary="Check current admin session validity",
)
def check_admin_session(
    request: Request,
) -> AdminSessionOut:
    """Check if the requesting client holds an active, valid admin session."""
    session_id = request.cookies.get(ADMIN_COOKIE_NAME)
    is_authenticated = bool(session_id and session_store.validate_session(session_id))
    return AdminSessionOut(authenticated=is_authenticated)


@router.get(
    "/complaints",
    response_model=list[ComplaintAdminOut],
    summary="List all complaints with full admin details",
)
def list_admin_complaints(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    category_filter: Optional[str] = Query(default=None, alias="category"),
    overdue_only: bool = Query(default=False),
    _admin_session: str = Depends(require_admin_session),
) -> list[ComplaintAdminOut]:
    """List complaints for admin with optional filters and reporter PII."""
    complaints = db.list_complaints(
        status=status_filter,
        category=category_filter,
        overdue_only=overdue_only,
        is_admin=True,
    )
    return [ComplaintAdminOut(**c) for c in complaints]


@router.patch(
    "/complaints/{tracking_id}/status",
    response_model=ComplaintAdminOut,
    summary="Update complaint status (forward-only progression)",
)
def update_complaint_status(
    tracking_id: str,
    body: StatusUpdateIn,
    _admin_session: str = Depends(require_admin_session),
) -> ComplaintAdminOut:
    """Advance status forward: submitted -> assigned -> in_progress -> resolved."""
    updated = db.update_status(
        tracking_id=tracking_id,
        new_status=body.new_status,
        note=body.note,
        is_admin=True,
    )
    return ComplaintAdminOut(**updated)


@router.delete(
    "/complaints/{tracking_id}/photo",
    summary="Admin unlink/delete of complaint photo",
)
def delete_complaint_photo(
    tracking_id: str,
    _admin_session: str = Depends(require_admin_session),
) -> dict[str, Optional[str]]:
    """Remove attached photo from a complaint for moderation/privacy reasons."""
    updated = db.unlink_photo(tracking_id=tracking_id, is_admin=True)
    return {
        "tracking_id": updated["tracking_id"],
        "photo_url": None,
    }


@router.get(
    "/metrics",
    response_model=AdminMetricsSummaryOut,
    summary="Get admin dashboard overview metrics",
)
def get_admin_metrics(
    _admin_session: str = Depends(require_admin_session),
) -> AdminMetricsSummaryOut:
    """Return overview metrics and per-department stats for admin dashboard."""
    all_complaints = db.list_complaints(is_admin=True)
    total = len(all_complaints)
    open_count = sum(1 for c in all_complaints if c.get("status") != "resolved")
    overdue_count = sum(1 for c in all_complaints if c.get("is_overdue"))
    avg_hours = metrics.avg_resolution_hours(all_complaints)
    from api.routes.metrics import get_public_metrics as fetch_public_metrics

    dept_stats = fetch_public_metrics()

    return AdminMetricsSummaryOut(
        total_complaints=total,
        open_complaints=open_count,
        overdue_complaints=overdue_count,
        avg_resolution_hours=avg_hours,
        departments=dept_stats,
    )
