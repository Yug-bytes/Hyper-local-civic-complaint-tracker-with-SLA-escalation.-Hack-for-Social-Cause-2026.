# Design System

Product: Civic Complaint Tracker (Streamlit). Audience: residents of all ages on phones, plus an area admin on a laptop.

## Principles

1. **Phone first.** Most residents use a phone. Design for ~380px width, single column.
2. **Plain language.** Say what happens: "Send complaint", not "Submit". Same action, same name everywhere.
3. **Status is the hero.** The tracking page and dashboard show status and deadline before anything else.
4. **Color means state.** Colors are used for status, not decoration.
5. **Hindi and English.** Allow for longer text and Devanagari glyphs in every component.

## Color tokens

| Token | Hex | Use |
|---|---|---|
| `--paper` | `#F6F7F4` | Page background |
| `--ink` | `#1E2A32` | Body text |
| `--civic` | `#1D5C8A` | Primary buttons, links |
| `--line` | `#D5DADD` | Borders, dividers |
| `--status-submitted` | `#6B7785` | Submitted |
| `--status-assigned` | `#1D5C8A` | Assigned |
| `--status-progress` | `#B87600` | In progress |
| `--status-resolved` | `#2E7D4F` | Resolved |
| `--status-overdue` | `#B3261E` | Overdue / escalated |

Contrast: body text and buttons must meet WCAG AA (4.5:1). Check status chips with white or dark text before using.

## Typography

- One family: **Public Sans** (falls back to system sans-serif). Devanagari falls back to **Noto Sans Devanagari**.
- Scale: 28 / 22 / 18 / 16 (body) / 14 (helper text). Body never below 16px on mobile.
- Line length under 80 characters; line height 1.5.
- Sentence case everywhere. No all-caps labels.

## Layout

- Single column on mobile; admin dashboard may use 2-3 columns on desktop.
- Spacing scale: 4, 8, 16, 24, 32.
- Form fields stacked, labels above fields, one primary action per screen.
- Tracking result: status chip, deadline, then history timeline (newest first).

## Components

| Component | Rules |
|---|---|
| Primary button | `--civic` fill, white text, label is a verb ("Send complaint", "Check status") |
| Status chip | Rounded, uses status token color plus a text label (never color alone) |
| Complaint card | Tracking ID, category, locality, status chip, due date |
| Empty state | Say what to do next ("No complaints yet. File the first one.") |
| Error message | Say what went wrong and how to fix it. No apologies, no vague text |
| Charts (Plotly) | Use status tokens; label axes; readable on a phone |

## Accessibility

- Visible keyboard focus on all controls.
- Do not rely on color alone; always show the status text.
- Photo upload has a text alternative field (optional description).
- Test on a real phone browser before the demo.

## Implementation notes (Streamlit)

- Theme in `.streamlit/config.toml` (`primaryColor`, `backgroundColor`, `textColor`, `font`).
- Extra CSS goes in one file `assets/style.css`, loaded once from `app.py`.
- Never inject user-entered text with `unsafe_allow_html` (see `security.md`).
