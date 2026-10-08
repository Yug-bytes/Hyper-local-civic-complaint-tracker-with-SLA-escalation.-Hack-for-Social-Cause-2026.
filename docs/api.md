# API

The prototype has **no public REST API**. Streamlit calls Python functions directly, and `db.py` talks to Supabase. This file documents that internal contract, so every page and every AI prompt uses the same function names and shapes.

If a REST API is needed later, wrap these functions with FastAPI without changing their signatures.

## Data shapes

```python
Complaint = {
  "tracking_id": str,        # "CT-261012-A7K2"
  "category": str,
  "description": str,
  "locality": str,
  "photo_url": str | None,
  "status": str,             # submitted | assigned | in_progress | resolved
  "created_at": datetime,
  "due_at": datetime,
  "resolved_at": datetime | None,
}
# Admin-only extra fields: reporter_name, reporter_phone, id
```

## `db.py` functions

| Function | Purpose | Returns |
|---|---|---|
| `create_complaint(category, description, locality, photo_bytes=None, name=None, phone=None)` | Validate, route, insert complaint and first history row | `tracking_id` |
| `get_public_status(tracking_id)` | Public lookup by ID | `Complaint` (no personal fields) plus `history` list, or `None` |
| `list_complaints(status=None, category=None, overdue_only=False)` | Admin list with filters | list of `Complaint` (all fields) |
| `update_status(tracking_id, new_status, note=None)` | Admin status change, writes history, sets `resolved_at` | updated `Complaint` |
| `get_departments()` | Routing table | list of department rows |
| `get_public_metrics()` | Per-department counts and average resolution time | list of dicts, no personal data |

## `services/` functions

| Function | Purpose |
|---|---|
| `routing.route(category)` | Department, responsible role, SLA days |
| `routing.compute_due_at(created_at, sla_days)` | Due datetime |
| `escalation.escalation_level(complaint, now)` | 0, 1 or 2 |
| `metrics.avg_resolution_hours(complaints)` | Float, ignores unresolved |
| `ids.generate_tracking_id(now)` | `CT-YYMMDD-XXXX`, random suffix from an unambiguous alphabet |

## Errors

| Error | When | User-facing message |
|---|---|---|
| `ValidationError` | Bad or missing input | Say which field and what is wrong |
| `NotFoundError` | Unknown tracking ID | "We couldn't find that ID. Check it and try again." |
| `StorageError` | Photo upload failed | "Photo didn't upload. Your complaint was saved without it." |
| `AuthError` | Wrong admin password | "Incorrect password." |

## Rules

- Pages never call Supabase directly; they only call these functions.
- Public functions (`get_public_status`, `get_public_metrics`) must never return personal fields.
- Admin functions require the admin session flag set by the login on `pages/admin.py`.
- Every function has a docstring and type hints (see `code-style.md`).
