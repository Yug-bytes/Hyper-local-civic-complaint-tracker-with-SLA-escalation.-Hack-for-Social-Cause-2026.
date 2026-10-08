-- Civic Complaint Tracker: Database Schema
-- =========================================
-- HOW TO RUN:
--   1. Open your Supabase project dashboard.
--   2. Go to SQL Editor (left sidebar).
--   3. Click "New query".
--   4. Paste this entire file and click "Run".
--   5. Verify the tables appear under Table Editor.
--
-- This script creates all tables, indexes, constraints,
-- and enables Row Level Security with NO public policies.
-- All access is server-side via the service role key in db.py.

-- ============================================================
-- 1. Departments (routing table, seeded from departments.json)
-- ============================================================
create table if not exists departments (
  id serial primary key,
  category text unique not null,
  department_name text not null,
  responsible_role text not null,
  escalation_role text not null,
  sla_days int not null check (sla_days > 0)
);

-- ============================================================
-- 2. Complaints
-- ============================================================
create table if not exists complaints (
  id uuid primary key default gen_random_uuid(),
  tracking_id text unique not null,
  category text not null references departments(category),
  description text not null check (char_length(description) <= 1000),
  locality text not null,
  photo_url text,
  reporter_name text,
  reporter_phone text,
  status text not null default 'submitted'
    check (status in ('submitted', 'assigned', 'in_progress', 'resolved')),
  created_at timestamptz not null default now(),
  due_at timestamptz not null,
  resolved_at timestamptz
);

-- ============================================================
-- 3. Status history
-- ============================================================
create table if not exists status_history (
  id serial primary key,
  complaint_id uuid not null references complaints(id) on delete cascade,
  status text not null,
  note text check (note is null or char_length(note) <= 500),
  changed_by text not null default 'system',
  changed_at timestamptz not null default now()
);

-- ============================================================
-- 4. Indexes for common queries
-- ============================================================
create index if not exists idx_complaints_status_due
  on complaints (status, due_at);

create index if not exists idx_status_history_complaint
  on status_history (complaint_id, changed_at);

-- ============================================================
-- 5. Row Level Security
--    Enabled on ALL tables with NO public policies.
--    Only the service role key (used by db.py) bypasses RLS.
--    This means the Supabase anon key cannot read or write
--    any data, and the browser never talks to Supabase.
-- ============================================================
alter table departments enable row level security;
alter table complaints enable row level security;
alter table status_history enable row level security;

-- No policies are created. The service role key bypasses RLS.
-- db.py is the only gatekeeper for all data access.

-- ============================================================
-- 6. Seed departments (from data/departments.json)
-- ============================================================
insert into departments (category, department_name, responsible_role, escalation_role, sla_days)
values
  ('pothole', 'Public Works Department', 'Junior Engineer', 'Executive Engineer', 7),
  ('water', 'Water Supply Department', 'Water Inspector', 'Assistant Engineer (Water)', 3),
  ('streetlight', 'Electrical Department', 'Line Inspector', 'Assistant Engineer (Electrical)', 5),
  ('garbage', 'Sanitation Department', 'Sanitary Inspector', 'Health Officer', 2),
  ('other', 'General Administration', 'Ward Officer', 'Municipal Commissioner', 7)
on conflict (category) do nothing;
