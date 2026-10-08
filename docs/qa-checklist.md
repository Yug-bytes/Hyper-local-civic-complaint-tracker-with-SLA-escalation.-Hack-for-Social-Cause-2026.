# QA Manual Test Checklist: Civic Complaint Tracker

> This checklist is a manual testing script for teammates, evaluators, and pilot volunteers.
> Follow each step sequentially and mark the check boxes as items pass.

---

## 1. Complaint Filing Flow (Citizen Tab)

### 1.1 Valid Complaint Submission
- **Action:** Select category `pothole`, enter locality `Main Market Road`, description `Large pothole near State Bank ATM`, leave name and phone blank. Click **Send complaint**.
- **Expected Result:** Success banner appears showing `"Your complaint has been sent!"` and a tracking ID in the format `CT-YYMMDD-XXXX`.
- **Status:** [ ] Pass / [ ] Fail

### 1.2 Empty Required Fields
- **Action:** Leave category unselected or description/locality completely blank and click **Send complaint**.
- **Expected Result:** Validation error appears (e.g., `"Description is required."` or `"Locality is required."`). Form does not submit.
- **Status:** [ ] Pass / [ ] Fail

### 1.3 Description Exceeding Max Length (>1000 characters)
- **Action:** Enter a description containing more than 1000 characters and attempt to submit.
- **Expected Result:** Validation error message appears: `"Description must be 1000 characters or fewer."`
- **Status:** [ ] Pass / [ ] Fail

### 1.4 Invalid Phone Format
- **Action:** Enter an invalid phone number such as `12345` or `abcdefghij` (less than 10 digits or letters).
- **Expected Result:** Validation error appears: `"Phone must be exactly 10 digits (e.g. 9876543210)."`. Form does not submit.
- **Status:** [ ] Pass / [ ] Fail

### 1.5 Valid 10-Digit Mobile Number
- **Action:** Enter `9876543210` with a valid description and submit.
- **Expected Result:** Submission succeeds and tracking ID is issued.
- **Status:** [ ] Pass / [ ] Fail

### 1.6 Oversized Photo Upload (>5 MB)
- **Action:** Attempt to upload an image file larger than 5 MB.
- **Expected Result:** Error message appears: `"Photo must be 5 MB or smaller."` Form rejects the file.
- **Status:** [ ] Pass / [ ] Fail

### 1.7 Wrong File Type Upload (Non-JPG/PNG)
- **Action:** Rename a `.txt` or `.pdf` file to `.jpg` and attempt to upload it.
- **Expected Result:** System sniffs file header bytes and rejects it with `"Photo must be a JPG or PNG file."`
- **Status:** [ ] Pass / [ ] Fail

### 1.8 Consent Notice Verification
- **Action:** Check text directly above the submit button.
- **Expected Result:** Consent line is visible: `"Name and phone are optional and only used by the area admin to follow up."`
- **Status:** [ ] Pass / [ ] Fail

---

## 2. Tracking ID Lookup (Citizen Tab)

### 2.1 Valid Tracking ID Lookup
- **Action:** Copy a generated tracking ID (e.g. `CT-261008-XXXX`), switch to the **Check status** tab, paste the ID, and click **Check status**.
- **Expected Result:** Status chip (e.g. `Submitted`), category, locality, filing date, SLA due date, and history timeline appear.
- **Privacy Check:** Reporter name and reporter phone number must **never** appear on this screen.
- **Status:** [ ] Pass / [ ] Fail

### 2.2 Unknown or Invalid Tracking ID Lookup
- **Action:** Enter a non-existent tracking ID (e.g., `CT-999999-ZZZZ`) and click **Check status**.
- **Expected Result:** Warning message appears: `"We couldn't find that ID. Check it and try again."` No server crash or raw database error.
- **Status:** [ ] Pass / [ ] Fail

---

## 3. Admin Authentication & Management (Admin Page)

### 3.1 Incorrect Admin Password
- **Action:** Go to the Admin page from the sidebar. Enter a wrong password and click **Log in**.
- **Expected Result:** Error message `"Incorrect password."` is displayed. The dashboard remains locked and inaccessible.
- **Status:** [ ] Pass / [ ] Fail

### 3.2 Correct Admin Password
- **Action:** Enter the valid `ADMIN_PASSWORD` from `.streamlit/secrets.toml` and click **Log in**.
- **Expected Result:** Admin dashboard unlocks, revealing KPI cards, complaints table, and analytics tabs.
- **Status:** [ ] Pass / [ ] Fail

### 3.3 Admin Logout
- **Action:** Click the **Log out** button in the header.
- **Expected Result:** Session is cleared and the view returns to the locked password prompt.
- **Status:** [ ] Pass / [ ] Fail

---

## 4. Status Progression & State Machine

### 4.1 Allowed Forward Progression
- **Action:** Select a complaint in `Submitted` status. The system presents the next allowed state (`Assigned`). Enter an optional note (e.g., `"Assigned to Junior Engineer"`) and click **Update status**.
- **Expected Result:** Status advances to `Assigned`. Timeline updates immediately with the admin note.
- **Action:** Advance from `Assigned` &rarr; `In progress` &rarr; `Resolved`.
- **Expected Result:** Each step succeeds. Once resolved, `resolved_at` is stamped and status update form indicates the complaint is resolved.
- **Status:** [ ] Pass / [ ] Fail

### 4.2 Forbidden Backwards or Skipped Transitions
- **Action:** Verify in the UI that the status dropdown only offers the valid next state in sequence (`submitted -> assigned -> in_progress -> resolved`).
- **Expected Result:** System prevents backwards movement (e.g. `Resolved` &rarr; `Submitted`) and skips (e.g. `Submitted` &rarr; `Resolved`).
- **Status:** [ ] Pass / [ ] Fail

---

## 5. Overdue & Auto-Escalation Display

### 5.1 On-Time Complaint Display
- **Action:** View a newly filed complaint in the admin list where `now <= due_at`.
- **Expected Result:** Normal status badge is shown with no red escalation chip.
- **Status:** [ ] Pass / [ ] Fail

### 5.2 Overdue (Level 1) Flagging
- **Action:** Check a demo complaint where current time is past the SLA due date (within half SLA window).
- **Expected Result:** A prominent red chip labeled `Overdue (Level 1)` appears next to the status.
- **Status:** [ ] Pass / [ ] Fail

### 5.3 Severely Overdue (Level 2) Flagging
- **Action:** Check a demo complaint where current time is past the SLA due date by more than half the SLA duration.
- **Expected Result:** A red chip labeled `Severely Overdue (Level 2)` appears next to the status.
- **Status:** [ ] Pass / [ ] Fail

### 5.4 Resolved Overdue Immunity
- **Action:** Check a complaint marked `Resolved` whose deadline was in the past.
- **Expected Result:** Shows as `Resolved` (green). Escalation level stays at `0` (no red overdue chip).
- **Status:** [ ] Pass / [ ] Fail

---

## 6. Public Accountability Dashboard (Dashboard Page)

### 6.1 Performance Metrics
- **Action:** Open the **Dashboard** page in the sidebar.
- **Expected Result:** Summary KPI counters appear (Total filed, Open, Resolved, Overdue), followed by the department table and two Plotly charts.
- **Status:** [ ] Pass / [ ] Fail

### 6.2 Timestamp & Plain-Language Explainer
- **Action:** Check the header area and expand the `"Understanding these numbers"` box.
- **Expected Result:** A live `"Updated at: ... UTC"` timestamp is displayed along with a friendly paragraph explaining what Open, Resolved, and Overdue mean.
- **Status:** [ ] Pass / [ ] Fail

### 6.3 Public Privacy & Leak Prevention
- **Action:** Inspect all cards, tables, charts, and text on the public dashboard.
- **Expected Result:** Zero citizen names, zero phone numbers, and zero raw complaint descriptions appear anywhere on this page.
- **Status:** [ ] Pass / [ ] Fail

---

## 7. Language Switcher (English & हिन्दी)

### 7.1 English Interface
- **Action:** Select **English** in the sidebar language toggle.
- **Expected Result:** All titles, tabs, form placeholders, buttons, and error messages render in clear English.
- **Status:** [ ] Pass / [ ] Fail

### 7.2 Hindi Interface (`हिन्दी`)
- **Action:** Select **हिन्दी** in the sidebar language toggle.
- **Expected Result:** Page headers, form labels (`शिकायत दर्ज करें`, `स्थिति जांचें`), category names, and button texts switch instantly to Hindi.
- **Status:** [ ] Pass / [ ] Fail

---

## 8. Mobile & Responsive Layout

### 8.1 Phone-Width Layout (~380px)
- **Action:** Open Developer Tools (`F12`), toggle mobile device view, and set viewport to 380px width (e.g. iPhone SE / Android).
- **Expected Result:** 
  - Layout flows vertically into a clean single column.
  - Buttons and input fields remain easily tappable.
  - No horizontal scrollbars or clipped text.
  - Status chips and timeline entries wrap cleanly.
- **Status:** [ ] Pass / [ ] Fail

---

## Summary Sign-Off

- **Tester Name:** _______________________
- **Date Tested:** _______________________
- **Result:** [ ] ALL PASSED / [ ] ISSUES FOUND
