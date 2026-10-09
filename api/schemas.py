"""Pydantic request and response schemas for Civic Complaint Tracker API."""

from typing import Optional

from pydantic import BaseModel, Field, computed_field

# ──────────────────────────────────────────────────────────────
# Error Models
# ──────────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


# ──────────────────────────────────────────────────────────────
# Public Models
# ──────────────────────────────────────────────────────────────


class StatusHistoryOut(BaseModel):
    status: str
    note: Optional[str] = None
    changed_by: str
    changed_at: Optional[str] = None


class ComplaintPublicOut(BaseModel):
    """Public complaint view: strictly excludes reporter_name and reporter_phone."""

    tracking_id: str
    category: str
    description: str
    locality: str
    photo_url: Optional[str] = None
    status: str
    created_at: str
    due_at: str
    resolved_at: Optional[str] = None
    history: list[StatusHistoryOut] = Field(default_factory=list)


class ComplaintCreatedOut(BaseModel):
    tracking_id: str


class DepartmentOut(BaseModel):
    id: Optional[int] = None
    category: str
    department_name: str
    responsible_role: str
    escalation_role: str
    sla_days: int


class DepartmentMetricOut(BaseModel):
    category: str
    total: int = 0
    resolved: int = 0
    open: int = 0
    overdue: int = 0
    avg_resolution_hours: float = 0.0
    department_name: Optional[str] = None
    resolution_rate_pct: Optional[float] = 0.0
    sla_days: Optional[int] = None

    @computed_field
    def total_complaints(self) -> int:
        return self.total

    @computed_field
    def resolved_complaints(self) -> int:
        return self.resolved

    @computed_field
    def open_complaints(self) -> int:
        return self.open

    @computed_field
    def overdue_complaints(self) -> int:
        return self.overdue


# ──────────────────────────────────────────────────────────────
# Admin Models
# ──────────────────────────────────────────────────────────────


class AdminLoginIn(BaseModel):
    password: str


class AdminLoginOut(BaseModel):
    status: str = "authenticated"


class AdminSessionOut(BaseModel):
    authenticated: bool


class StatusUpdateIn(BaseModel):
    new_status: str
    note: Optional[str] = None


class ComplaintAdminOut(BaseModel):
    """Admin complaint view: includes reporter fields and escalation level."""

    id: Optional[str] = None
    tracking_id: str
    category: str
    description: str
    locality: str
    photo_url: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    status: str
    created_at: str
    due_at: str
    resolved_at: Optional[str] = None
    escalation_level: int = 0
    is_overdue: bool = False


class AdminMetricsSummaryOut(BaseModel):
    total_complaints: int
    open_complaints: int
    overdue_complaints: int
    avg_resolution_hours: float
    departments: list[DepartmentMetricOut]
