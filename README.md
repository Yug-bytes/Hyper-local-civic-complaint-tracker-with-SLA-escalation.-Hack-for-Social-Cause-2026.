# Civic Complaint Tracker

> A hyper-local, transparent civic complaint tracking ecosystem with automated SLA-based routing, hierarchical escalation, and zero-PII public transparency.
>
> **Hackathon:** Hack for Social Cause (MY Bharat) | **Theme:** Governance & Civic Technology | **Team:** TASK FORCE 141

---

## 1. Problem Statement & Mission

Residents across Indian municipalities frequently encounter everyday civic hazards (road damage/potholes, erratic water supply, non-functional streetlights, and overflowing waste bins). However, grievances routinely fall into a "bureaucratic black hole" due to:
1. **No Time-Bound Enforcement:** Complaints sit in pending states for weeks with zero accountability.
2. **High Citizen Friction:** Compulsory account creation and complex forms discourage reporting.
3. **Missing Escalation:** Issues assigned to junior field staff are not escalated when neglected.
4. **Privacy Risks:** Portals either expose citizen phone numbers/names publicly or hide everything behind closed official doors.

### Our Solution
- **Zero-Barrier Intake:** Citizens report issues in under 60 seconds with photo proof and locality—no mandatory login required.
- **Unambiguous Tracking:** Every grievance receives a unique tracking ID (`CT-YYMMDD-XXXX`) for anonymous status tracking.
- **Deterministic Department Routing:** Direct dispatch to PWD, Water, Electrical, Sanitation, or General Administration.
- **Guaranteed SLA Countdown (2 to 7 Days):** Automated time-tracking against legally binding turnaround windows.
- **Automated Hierarchy Escalation:** If a deadline expires without resolution, complaints automatically escalate up the municipal chain (Junior Engineer $\rightarrow$ Executive Engineer $\rightarrow$ Municipal Commissioner).
- **Zero-PII Public Transparency:** Comprehensive resolution metrics and audit timelines without exposing personal citizen data.

---

## 2. Tech Stack & Architecture

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS | Fast, responsive citizen UI & admin portal |
| **Backend API** | FastAPI (Python), Pydantic v2, Uvicorn | High-performance REST API with OpenAPI docs |
| **Database & Storage** | Supabase (PostgreSQL 15), Supabase Storage | Encrypted storage, photo buckets & RLS policies |
| **Hosting & CI/CD** | Vercel (Unified Serverless Runtimes) | Atomic builds, serverless Python functions & CDN delivery |
| **Testing & Quality** | Pytest, Ruff, Black | 60/60 automated tests, strict linting & formatting |
| **Internationalization** | Bilingual (English & Hindi) | Grassroots accessibility across demographics |

---

## 3. How Routing & Escalation Work

### Department Routing Table (`data/departments.json`)
When a complaint is submitted, the system matches the category to an official department:

| Category | Department | Responsible Role (Level 0) | Escalation Role (Level 1/2) | SLA |
|---|---|---|---|---|
| `pothole` | Public Works Department | Junior Engineer | Executive Engineer | 7 days |
| `water` | Water Supply Department | Water Inspector | Assistant Engineer (Water) | 3 days |
| `streetlight` | Electrical Department | Line Inspector | Assistant Engineer (Electrical) | 5 days |
| `garbage` | Sanitation Department | Sanitary Inspector | Health Officer | 2 days |
| `other` | General Administration | Ward Officer | Municipal Commissioner | 7 days |

### SLA Deadline & Auto-Escalation Engine (`services/escalation.py`)
Escalation levels are calculated deterministically on every read:
- **Level 0 (On Time):** Current time is before the complaint's `due_at` deadline (or the issue is resolved).
- **Level 1 (Overdue):** Current time is past `due_at`, but within half the SLA duration.
- **Level 2 (Severely Overdue):** Current time is past `due_at + (SLA_days / 2)`.

### Forward-Only State Machine
To guarantee audit integrity, grievance statuses strictly follow a forward sequence:
$$\text{Submitted} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved}$$
Backwards or skipped transitions are rejected by the system.

---

## 4. Project Structure

```
civic-tracker/
├── frontend/                  # Modern React + Vite Single Page Application
│   ├── src/
│   │   ├── pages/             # LandingPage, CitizenPage, TrackPage, DashboardPage, AdminPage
│   │   ├── components/        # Header, Footer, Layout, StatusBadge, EscalationBadge, etc.
│   │   └── lib/               # api.ts (REST client), i18n.tsx (EN/HI), utils.ts, date.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── api/                       # FastAPI REST API Backend
│   ├── routes/                # complaints.py, metrics.py, admin.py
│   ├── auth/                  # session_store.py, rate_limiter.py
│   ├── schemas.py             # Pydantic v2 validation models & zero-PII responses
│   ├── main.py                # FastAPI application instance & middleware
│   └── index.py               # Vercel serverless function entrypoint
├── services/                  # Core Business Logic
│   ├── ids.py                 # Tracking ID generator (unambiguous alphabet)
│   ├── routing.py             # Category-to-department router & SLA calculator
│   ├── escalation.py          # Auto-escalation level evaluator (0, 1, 2)
│   └── metrics.py             # Statistical aggregations & resolution time analytics
├── data/
│   └── departments.json       # Municipal routing configuration
├── supabase/
│   └── schema.sql             # Postgres DDL: tables, indexes, constraints, RLS policies
├── tests/                     # 60 automated unit & API acceptance tests
├── vercel.json                # Unified Vercel deployment configuration & API rewrites
├── pyproject.toml             # Python PEP 621 dependencies & tooling config
├── requirements.txt           # Pinned production Python dependencies
├── LICENSE                    # MIT Open Source License
└── README.md
```

---

## 5. Local Setup & Development

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- A free [Supabase](https://supabase.com) project

### Step 1: Clone the repository
```bash
git clone https://github.com/Yug-bytes/Hyper-local-civic-complaint-tracker-with-SLA-escalation.-Hack-for-Social-Cause-2026.git
cd civic-tracker
```

### Step 2: Set up Database in Supabase
1. Open your Supabase project dashboard $\rightarrow$ **SQL Editor**.
2. Run the script in [`supabase/schema.sql`](supabase/schema.sql).
3. Under **Storage**, create a bucket named `complaint-photos`.

### Step 3: Run the FastAPI Backend
```bash
# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start FastAPI development server
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs are available at `http://127.0.0.1:8000/docs`.

### Step 4: Run the React Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### Step 5: Run the Test Suite
```bash
python -m pytest
```
All 60 tests will run and validate authentication, SLA calculations, routing, and transitions.

---

## 6. Production Deployment on Vercel

The application is architected for unified, single-project deployment on **Vercel** with continuous deployment (CI/CD) on every GitHub push.

### Step 1: Import Repository into Vercel
1. Log in to [Vercel](https://vercel.com) and click **Add New Project**.
2. Import the GitHub repository: `Yug-bytes/Hyper-local-civic-complaint-tracker-with-SLA-escalation.-Hack-for-Social-Cause-2026.`
3. Set **Root Directory** to `./`.

### Step 2: Configure Environment Variables
Expand **Environment Variables** in the Vercel import screen and add:
- `SUPABASE_URL` = Your Supabase project URL (`https://xyz.supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY` = Your Supabase `service_role` secret key
- `ADMIN_PASSWORD` = Your municipal officer portal password

### Step 3: Deploy & Continuous Delivery
Click **Deploy**. Vercel will:
1. Build the React frontend into `frontend/dist` via `npm run build`.
2. Package the Python backend via `uv` into serverless API functions (`/api/*`).
3. Serve the unified full-stack application on a single, secure HTTPS domain.
4. **Any future `git push` to `main` automatically triggers an atomic redeploy within 60 seconds.**

---

## 7. Security & Zero-PII Privacy Protection

1. **Zero-PII Public Queries:** Public endpoints (`/api/complaints/{id}`, `/api/metrics/summary`) strip reporter names, phone numbers, and internal audit notes.
2. **Server-Side Gatekeeper:** The browser client never touches Supabase directly; all queries pass through FastAPI validation and server-side service keys.
3. **Row Level Security (RLS):** All Postgres tables have RLS enabled with public access denied.
4. **Brute-Force Login Defense:** The officer portal implements in-memory IP rate limiting (5 attempts $\rightarrow$ lockout).
5. **Session Security:** Administrative session cookies use `HttpOnly`, `SameSite=Lax`, and sliding 60-minute inactivity timeouts.

---

## 8. AI Usage Disclosure

In compliance with hackathon regulations:
- **Tools Used:** Claude Code, Antigravity (Google DeepMind).
- **AI Contributions:** Boilerplate generation, initial schema drafting, CSS scaffolding, and test suite templates.
- **Human Work:** Problem identification, ground-level civic needs assessment, municipal routing architecture, local government SLA research, code reviews, and prototype testing.
- See [`AI_USAGE.md`](AI_USAGE.md) for the detailed disclosure log.

---

## 9. License

This project is open-source software licensed under the **[MIT License](LICENSE)** — copyright (c) 2026 Yug-bytes.