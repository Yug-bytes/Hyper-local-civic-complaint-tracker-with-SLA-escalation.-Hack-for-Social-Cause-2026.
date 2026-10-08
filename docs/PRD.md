# PRD: Civic Complaint Tracker

Hackathon: Hack for Social Cause (MY Bharat) | Theme: Governance & Civic Technology
Status: Draft v0.1 | Deadline: 15 Oct 2026

> Fill every `[PLACEHOLDER]` before submission.

## 1. Problem

Residents of `[AREA_NAME]`, `[STATE]` report civic issues (potholes, garbage, water supply, streetlights) but rarely know who is responsible, whether anyone saw the complaint, or what happens next. Complaints go unanswered with no deadline and no escalation.

Evidence to collect (source for the problem statement):
- Local poll results: `[N]` responses, `[X%]` have complained before, `[Y%]` got no response.
- Official context from `[LOCAL_BODY]` website and a relevant public report. Cite the source and date.

## 2. Target users

| User | Need |
|---|---|
| Resident / citizen | File a complaint in under 1 minute, get a tracking ID, check status without logging in |
| Ward/area volunteer or officer (admin) | See all complaints, update status, spot overdue ones |
| Observer (judges, community group) | See a public dashboard of how fast each department resolves issues |

## 3. Goals

1. A complaint is routed to the correct department automatically.
2. Every complaint has a deadline (SLA), and missed deadlines escalate automatically.
3. A public dashboard shows resolution speed per department.
4. Prove it in one real community with measured results.

## 4. Non-goals (do not build)

- Real integration with government portals or SMS/WhatsApp alerts.
- User accounts for citizens.
- Mobile native app.
- ML or AI features at runtime.

## 5. MVP features

1. **Complaint form:** category, description, locality, optional photo, optional name and phone.
2. **Tracking ID** generated on submit (format `CT-YYMMDD-XXXX`).
3. **Status lookup:** enter the tracking ID to see the status history.
4. **Routing table:** category maps to department, responsible role and SLA days (`data/departments.json`).
5. **Status flow:** Submitted, Assigned, In progress, Resolved.
6. **Auto-escalation:** complaint past its due date is flagged as overdue and escalated to the next role.
7. **Admin dashboard:** filter and update complaints; charts for category, status and average resolution time.
8. **Public accountability view:** department-wise average resolution time and overdue count (no personal data).

## 6. Pilot plan

- Community: `[AREA_NAME]`.
- Duration: `[2-3]` days, between 12 and 13 Oct.
- Participants: 10-15 residents filing real complaints.
- Metrics recorded: complaints filed, by category, escalated count, resolved count, average time to resolve or to first response.
- Report honestly. A result such as "0 resolved in 48 hours, all escalated" is still a valid finding.

## 7. Success criteria

- Working end-to-end demo: file, route, track, escalate, dashboard.
- At least 10 real complaints in the pilot.
- Live deployed link and public GitHub repo with README.

## 8. Risks

| Risk | Mitigation |
|---|---|
| Pilot complaints not actually resolved | Frame the result as accountability data, not resolution |
| Existing apps (Swachhata, CM helpline portals) | Position as hyper-local accountability with public SLA tracking |
| Privacy of reporters | Phone optional, hidden from public views (see `security.md`) |
| Time (about 7 days) | Strict scope in section 4; seed data for the demo |

## 9. AI usage disclosure (required by the hackathon)

- Tools: Claude Code, Antigravity.
- Used for: code generation and boilerplate, drafting docs.
- Human work: problem selection, routing rules, local research, pilot, testing, code review.
- Keep `AI_USAGE.md` updated as you build.

## 10. Open questions

- Exact `[AREA_NAME]`, `[STATE]`, `[LOCAL_BODY]`.
- Which departments and officer roles are correct locally (verify on official websites).
- Who files and who administers during the pilot.
