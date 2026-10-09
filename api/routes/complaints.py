"""Citizen complaints and department routes."""

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Request,
    Response,
    UploadFile,
    status,
)

import db
from api.dependencies import (
    CITIZEN_COOKIE_NAME,
    get_citizen_session_id,
    get_client_ip,
    get_cookie_security_params,
)
from api.rate_limiting import complaint_rate_limiter
from api.schemas import (
    ComplaintCreatedOut,
    ComplaintPublicOut,
    DepartmentOut,
)
from errors import NotFoundError

router = APIRouter(prefix="/api", tags=["complaints"])


@router.post(
    "/complaints",
    response_model=ComplaintCreatedOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a citizen complaint",
)
async def submit_complaint(
    request: Request,
    response: Response,
    category: str = Form(...),
    description: str = Form(...),
    locality: str = Form(...),
    name: Optional[str] = Form(default=None),
    phone: Optional[str] = Form(default=None),
    photo: Optional[UploadFile] = File(default=None),
    client_ip: str = Depends(get_client_ip),
    session_id: Optional[str] = Depends(get_citizen_session_id),
) -> ComplaintCreatedOut:
    """Submit a complaint with server-side limits and duplicate check."""
    # Ensure citizen session ID exists
    if not session_id:
        session_id = complaint_rate_limiter.generate_session_id()

    # 1. Enforce two-tier rate limits (session cooldown/limit + IP hourly limit)
    complaint_rate_limiter.check_submission_allowed(session_id, client_ip)

    # 2. Process optional photo
    photo_bytes: Optional[bytes] = None
    if photo and photo.filename:
        photo_bytes = await photo.read()
        if len(photo_bytes) == 0:
            photo_bytes = None

    # 3. Clean optional fields
    clean_name = name.strip() if name and name.strip() else None
    clean_phone = phone.strip() if phone and phone.strip() else None

    # 4. Create complaint in database (includes duplicate check & SLA calculation)
    tracking_id = db.create_complaint(
        category=category,
        description=description,
        locality=locality,
        photo_bytes=photo_bytes,
        name=clean_name,
        phone=clean_phone,
    )

    # 5. Record successful submission against rate limiter
    complaint_rate_limiter.record_submission(session_id, client_ip)

    # 6. Set or refresh citizen session cookie
    cookie_params = get_cookie_security_params()
    response.set_cookie(
        key=CITIZEN_COOKIE_NAME,
        value=session_id,
        max_age=30 * 24 * 3600,  # 30 days
        **cookie_params,
    )

    return ComplaintCreatedOut(tracking_id=tracking_id)


@router.get(
    "/complaints/{tracking_id}",
    response_model=ComplaintPublicOut,
    summary="Get public status of a complaint by tracking ID",
)
def get_complaint_status(tracking_id: str) -> ComplaintPublicOut:
    """Return public status and history (strictly excludes reporter PII)."""
    complaint = db.get_public_status(tracking_id)
    if not complaint:
        raise NotFoundError("We couldn't find that ID. Check it and try again.")
    return ComplaintPublicOut(**complaint)


@router.get(
    "/departments",
    response_model=list[DepartmentOut],
    summary="List all municipal departments and SLAs",
)
def list_departments() -> list[DepartmentOut]:
    """Retrieve municipal department routing and SLA metadata."""
    depts = db.get_departments()
    return [DepartmentOut(**d) for d in depts]
