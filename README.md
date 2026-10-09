# Civic Complaint Tracker

> A hyper-local, transparent civic complaint tracking system with automated SLA-based routing and auto-escalation. Built for local communities to bridge the gap between residents and municipal authorities.
>
> **Hackathon:** Hack for Social Cause (MY Bharat) | **Theme:** Governance & Civic Technology

---

## 1. Problem Statement & Pilot Context

Residents of **`[AREA_NAME]`, `[STATE]`** frequently report civic issues (such as road damage, erratic water supply, failed streetlights, and overflowing waste bins) to municipal bodies like **`[LOCAL_BODY]`**. However, complaints often go unanswered with no assigned responsibility, no deadlines, and no escalation.

This project introduces hyper-local accountability:
- Citizens file complaints in under 1 minute without needing an account.
- Every complaint receives an unambiguous tracking ID (`CT-YYMMDD-XXXX`) and an automatic service-level agreement (SLA) deadline.
- Unresolved issues past their deadline automatically escalate to senior supervisory roles.
- A public accountability dashboard tracks resolution speed and overdue issues per department without exposing personal citizen information.

---

## 2. Screenshots

*(Screenshots of the mobile and desktop views)*

| Citizen Complaint Form | Status Tracking & Timeline |
|:---:|:---:|
| *[Add citizen form screenshot]* | *[Add status tracking screenshot]* |

| Admin Dashboard & Analytics | Public Accountability View |
|:---:|:---:|
| *[Add admin dashboard screenshot]* | *[Add public dashboard screenshot]* |

---

## 3. How Routing & Escalation Work

### Routing Table (`data/departments.json`)
When a complaint is submitted, the system matches the category to a department routing table:

| Category | Department | Responsible Role (Level 0) | Escalation Role (Level 1/2) | SLA |
|---|---|---|---|---|
| `pothole` | Public Works Department | Junior Engineer | Executive Engineer | 7 days |
| `water` | Water Supply Department | Water Inspector | Assistant Engineer (Water) | 3 days |
| `streetlight` | Electrical Department | Line Inspector | Assistant Engineer (Electrical) | 5 days |
| `garbage` | Sanitation Department | Sanitary Inspector | Health Officer | 2 days |
| `other` | General Administration | Ward Officer | Municipal Commissioner | 7 days |

*(Department names, roles, and SLA days are verified against local municipal guidelines).*

### SLA Deadline & Auto-Escalation Engine (`services/escalation.py`)
Escalation is computed deterministically on read:
- **Level 0 (On Time):** Current time is before the complaint's `due_at` deadline (or the issue is resolved).
- **Level 1 (Overdue):** Current time is past `due_at`, but within half the SLA duration.
- **Level 2 (Severely Overdue):** Current time is past `due_at + (SLA_days / 2)`.

### State Machine Progression
To maintain data integrity, statuses progress in a strict forward sequence:
$$\text{Submitted} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved}$$
Backwards or skipped transitions are rejected by the system.

---

## 4. Project Structure

```
civic-tracker/
├── app.py                     # App entry point, navigation, language switcher (EN/HI)
├── db.py                      # Server-side Supabase client & gatekeeper (no direct browser access)
├── constants.py               # Shared enums, categories, limits, and color tokens
├── errors.py                  # Custom exceptions (ValidationError, NotFoundError, etc.)
├── strings.py                 # Bilingual dictionary (English & Hindi)
├── pages/
│   ├── citizen.py             # Citizen complaint filing & tracking ID lookup
│   ├── admin.py               # Protected admin portal (filters, status updates, Plotly charts)
│   └── public_dashboard.py    # Public accountability metrics & department performance
├── services/
│   ├── ids.py                 # Tracking ID generator (unambiguous alphabet)
│   ├── routing.py             # Category-to-department router and SLA deadline calculator
│   ├── escalation.py          # Auto-escalation level evaluator (0, 1, 2)
│   └── metrics.py             # Statistical aggregations & resolution time analytics
├── data/
│   └── departments.json       # Municipal routing configuration
├── assets/
│   └── style.css              # Design system stylesheet & tokens
├── scripts/
│   └── seed.py                # Safe demo data generator (refuses without --confirm)
├── supabase/
│   └── schema.sql             # Postgres DDL: tables, indexes, constraints, RLS policies
├── tests/                     # Comprehensive pytest test suite (40 tests)
├── .streamlit/
│   ├── config.toml            # Streamlit theme configuration
│   └── secrets.toml.example   # Template for local secrets
├── requirements.txt           # Pinned production dependencies
├── AI_USAGE.md                # Hackathon AI disclosure log
└── README.md
```

---

## 5. Local Setup Instructions

### Prerequisites
- Python 3.11+
- A free [Supabase](https://supabase.com) account

### Step 1: Clone the repository
```bash
git clone https://github.com/your-username/civic-tracker.git
cd civic-tracker
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Database setup in Supabase
1. Open your Supabase project dashboard and navigate to the **SQL Editor**.
2. Paste the contents of [`supabase/schema.sql`](supabase/schema.sql) and click **Run**.
3. Under **Storage**, create a public bucket named `complaint-photos`.

### Step 4: Configure secrets
Copy the example secrets file:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Open `.streamlit/secrets.toml` and configure your credentials:
```toml
[supabase]
url = "https://your-project-id.supabase.co"
service_key = "your-supabase-service-role-key"
bucket = "complaint-photos"

[admin]
password = "your-admin-password"
```

### Step 5: (Optional) Seed demo data
Populate the database with 25 sample complaints across departments and statuses:
```bash
python scripts/seed.py --confirm
```

### Step 6: Run the applications

#### Option A: Modern Web Frontend (React + FastAPI)
1. **Start the FastAPI Backend:**
   ```bash
   python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Interactive Swagger docs are available at `http://127.0.0.1:8000/docs`.

2. **Start the React Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

#### Option B: Streamlit Application (Dual Coexistence)
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 6. Deployment on Streamlit Community Cloud

Deploying the prototype to Streamlit Community Cloud makes it accessible via HTTPS to judges, teammates, and community pilot testers.

### Step 1: Push repository to GitHub
Ensure all code is committed and pushed to your GitHub repository (ensure `.streamlit/secrets.toml` remains in `.gitignore`):
```bash
git add .
git commit -m "feat: complete MVP complaint tracker with SLA escalation"
git push origin main
```

### Step 2: Create App on Streamlit Cloud
1. Sign in to [share.streamlit.io](https://share.streamlit.io) using your GitHub account.
2. Click **New app** (or **Create app**).
3. Select your repository, branch (`main`), and set **Main file path** to `app.py`.
4. (Optional) Choose a custom app URL name (e.g. `civic-tracker-[area]`).

### Step 3: Configure App Secrets
1. Before launching, click **Advanced settings** &rarr; **Secrets** (or navigate to **App Settings** &rarr; **Secrets** after creating the app).
2. Paste your secrets in the exact shape of `.streamlit/secrets.toml.example`:
   ```toml
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_SERVICE_ROLE_KEY = "your-supabase-service-role-key"
   ADMIN_PASSWORD = "your-chosen-admin-password"
   ```
   *(Alternatively, the nested table format `[supabase]` and `[admin]` is also fully supported).*
3. Click **Save** and **Deploy**.

### Step 4: What to verify after first deploy
Once the build completes and the app loads:
- [ ] **Public Dashboard:** Confirm summary KPIs, department table, and charts load with live data.
- [ ] **Citizen Complaint:** Submit a test complaint with an optional photo. Confirm you receive a valid tracking ID (`CT-YYMMDD-XXXX`).
- [ ] **Status Lookup:** Look up your new tracking ID. Verify that status chip, category, due date, and timeline appear, and that reporter name and phone are hidden.
- [ ] **Admin Portal:** Log in with your `ADMIN_PASSWORD`. Verify the complaint appears in the table, test moving it to `Assigned`, and verify the note updates in the timeline.
- [ ] **Mobile Layout:** Open the deployed URL on your smartphone browser to confirm single-column responsiveness.


---

## 7. Known Limitations (Stated Honestly)

1. **No direct government backend integration:** For this prototype, status changes are made by area administrators/officers via the web portal rather than integrating with official municipal ERP systems.
2. **No automated SMS/WhatsApp gateways:** Tracking relies on residents bookmarking their tracking ID or checking the public portal, avoiding telecom API dependencies.
3. **Admin authentication:** Admin access is secured using a single shared administrator password rather than individual multi-factor user accounts.
4. **Read-time escalation calculation:** Escalation flags are computed dynamically when complaints are retrieved rather than using a continuous background queue worker.

---

## 8. AI Usage Disclosure

In compliance with hackathon regulations:
- **Tools Used:** Claude Code, Antigravity (Google DeepMind).
- **AI Contributions:** Boilerplate generation, initial schema drafting, CSS token scaffolding, and test suite templates.
- **Human Work:** Problem discovery, community needs assessment, routing and escalation architecture, local municipal research, code reviews, and pilot execution.
- See [`AI_USAGE.md`](AI_USAGE.md) for the complete log of generation activities.

---

## 9. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.