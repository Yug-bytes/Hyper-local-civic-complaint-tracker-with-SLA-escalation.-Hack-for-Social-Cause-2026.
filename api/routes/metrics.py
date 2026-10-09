"""Public metrics endpoints."""

from fastapi import APIRouter

import db
from api.schemas import DepartmentMetricOut

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get(
    "/metrics",
    response_model=list[DepartmentMetricOut],
    summary="Get aggregated municipal performance metrics",
)
def get_public_metrics() -> list[DepartmentMetricOut]:
    """Return per-department resolution rates and SLA compliance (zero PII)."""
    raw_stats = db.get_public_metrics()
    depts = {d["category"]: d for d in db.get_departments()}

    results = []
    for s in raw_stats:
        cat = s["category"]
        dept_info = depts.get(cat, {})
        tot = s.get("total", 0)
        res = s.get("resolved", 0)
        rate = round((res / tot) * 100, 1) if tot > 0 else 0.0
        results.append(
            DepartmentMetricOut(
                category=cat,
                total=tot,
                resolved=res,
                open=s.get("open", tot - res),
                overdue=s.get("overdue", 0),
                avg_resolution_hours=s.get("avg_resolution_hours", 0.0),
                department_name=dept_info.get("department_name", cat.title()),
                resolution_rate_pct=rate,
                sla_days=dept_info.get("sla_days"),
            )
        )
    return results
