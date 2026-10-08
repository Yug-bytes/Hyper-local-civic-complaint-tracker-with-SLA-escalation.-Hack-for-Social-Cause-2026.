# Database

Supabase (Postgres). Three tables. All access goes through `db.py`.

## Tables

### `departments`

| Column | Type | Notes |
|---|---|---|
| `id` | serial, PK | |
| `category` | text, unique | e.g. `pothole`, `water`, `streetlight`, `garbage`, `other` |
| `department_name` | text | Verify the local name on the official website |
| `responsible_role` | text | First contact, e.g. junior engineer / sanitary inspector |
| `escalation_role` | text | Next role when overdue |
| `sla_days` | int | Days allowed before overdue |

Seeded from `data/departments.json`.

### `complaints`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | default `gen_random_uuid()` |
| `tracking_id` | text, unique | format `CT-YYMMDD-XXXX` |
| `category` | text, FK to `departments.category` | |
| `description` | text | max 1000 chars |
| `locality` | text | colony / ward / landmark |
| `photo_url` | text, nullable | Supabase Storage URL |
| `reporter_name` | text, nullable | private |
| `reporter_phone` | text, nullable | private |
| `status` | text | `submitted`, `assigned`, `in_progress`, `resolved` |
| `created_at` | timestamptz | default `now()` |
| `due_at` | timestamptz | `created_at + sla_days` |
| `resolved_at` | timestamptz, nullable | set when status becomes `resolved` |

### `status_history`

| Column | Type | Notes |
|---|---|---|
| `id` | serial, PK | |
| `complaint_id` | uuid, FK to `complaints.id` | |
| `status` | text | |
| `note` | text, nullable | admin comment, max 500 chars |
| `changed_by` | text | `system` or `admin` |
| `changed_at` | timestamptz | default `now()` |

## Derived values (not stored)

- **Overdue:** `status != 'resolved'` and `now() > due_at`.
- **Escalation level:** 0 on time, 1 when overdue, 2 when overdue by more than half the SLA.
- **Resolution time:** `resolved_at - created_at`.

## Indexes

- `complaints(tracking_id)` unique.
- `complaints(status, due_at)` for overdue queries.
- `status_history(complaint_id, changed_at)`.

## SQL sketch

```sql
create table departments (
  id serial primary key,
  category text unique not null,
  department_name text not null,
  responsible_role text not null,
  escalation_role text not null,
  sla_days int not null check (sla_days > 0)
);

create table complaints (
  id uuid primary key default gen_random_uuid(),
  tracking_id text unique not null,
  category text not null references departments(category),
  description text not null check (char_length(description) <= 1000),
  locality text not null,
  photo_url text,
  reporter_name text,
  reporter_phone text,
  status text not null default 'submitted'
    check (status in ('submitted','assigned','in_progress','resolved')),
  created_at timestamptz not null default now(),
  due_at timestamptz not null,
  resolved_at timestamptz
);

create table status_history (
  id serial primary key,
  complaint_id uuid not null references complaints(id) on delete cascade,
  status text not null,
  note text,
  changed_by text not null default 'system',
  changed_at timestamptz not null default now()
);

create index on complaints (status, due_at);
create index on status_history (complaint_id, changed_at);
```

## Row-level security

See `security.md`. Public reads must never include `reporter_name` or `reporter_phone`.

## Seed data

`scripts/seed.py` inserts departments plus 20-30 sample complaints in mixed statuses so the dashboard is never empty during the demo. Mark seeded rows clearly (for example, a `[DEMO]` prefix in the description) and keep them separate from real pilot data.

## Retention

Delete pilot personal data (names, phones) after the hackathon results, or anonymise it.
