# Architecture

## Overview

A single Streamlit app (Python) with a Supabase Postgres database. No separate backend server. Routing and escalation are plain Python rules, with no ML at runtime.

```
Citizen (phone browser)          Admin (browser)
        │                              │
        ▼                              ▼
  pages/citizen.py              pages/admin.py
        │                              │
        └──────────┬───────────────────┘
                   ▼
           services/ (business logic)
        routing.py  escalation.py  metrics.py
                   │
                   ▼
                db.py  ──►  Supabase (Postgres + Storage)
                   ▲
          data/departments.json (routing table)
```

## Stack

| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit | Fast to build, Python only |
| Data | Supabase Postgres | Persists on Streamlit Cloud (SQLite files can reset) |
| Photos | Supabase Storage | Simple uploads, public URL per file |
| Charts | Pandas + Plotly | Quick dashboard |
| Map (optional) | Folium | Show complaint locations |
| Hosting | Streamlit Community Cloud | Free, live link for judges |
| Code | GitHub (public) | Required for submission |

## Folder structure

```
civic-tracker/
  app.py                  # entry, language toggle, loads CSS
  pages/
    citizen.py            # file complaint + check status
    admin.py              # login, manage complaints, charts
    public_dashboard.py   # department-wise accountability view
  services/
    routing.py            # category -> department, SLA, due date
    escalation.py         # overdue detection and escalation level
    metrics.py            # averages, counts for dashboards
  db.py                   # all database access (see api.md)
  data/
    departments.json      # routing table (verify locally)
  assets/style.css
  docs/                   # these markdown files
  tests/
  .streamlit/config.toml
  requirements.txt
  README.md
  AI_USAGE.md
```

## Key flows

**File a complaint**
1. Citizen fills the form on `citizen.py`.
2. Input is validated (see `security.md`).
3. `routing.py` looks up the department and SLA, then computes `due_at`.
4. `db.py` inserts into `complaints` and writes the first `status_history` row.
5. The app shows the tracking ID.

**Check status**
1. Citizen enters the tracking ID.
2. `db.py` returns only public fields and the status history (no personal data).

**Escalation**
1. On each admin or dashboard load, `escalation.py` compares `now` against `due_at`.
2. Open complaints past due get level 1; past due plus half the SLA get level 2.
3. The result is stored or computed on read. For the prototype, compute on read.

## Decisions

- Streamlit over React: faster for a 7-day build and fits the team's Python skills.
- Rules over AI at runtime: reliable demo, no API keys to fail.
- Escalation computed on read: no background jobs needed.
- Admin login with a secret password from `st.secrets`: enough for a prototype.

## Out of scope

SMS/WhatsApp notifications, citizen accounts, integration with official portals, background schedulers.
