# Code Style

Applies to all Python code in this repo, whether written by hand or by AI tools.

## Tooling

- Python 3.11+.
- Format with `black`, lint with `ruff`. Run both before every commit.
- Dependencies pinned in `requirements.txt`.

## Naming

| Thing | Style | Example |
|---|---|---|
| Files, modules | `snake_case` | `escalation.py` |
| Functions, variables | `snake_case` | `compute_due_date` |
| Classes | `PascalCase` | `Complaint` |
| Constants | `UPPER_SNAKE` | `MAX_PHOTO_MB` |
| Status values | lowercase strings from one enum | `submitted`, `assigned`, `in_progress`, `resolved` |

## Structure rules

1. **UI files only handle UI.** Pages call functions in `services/` and `db.py`. No SQL or business rules in `pages/`.
2. **All database access goes through `db.py`.** Nothing else imports the Supabase client.
3. **Business rules live in `services/`** (routing, escalation, metrics) as plain functions that are easy to test.
4. **One function, one job.** Aim for under 40 lines per function.
5. **No magic strings.** Statuses and categories come from one shared constants module.

## Types and docs

- Type hints on every function signature.
- A one-line docstring on every public function, saying *what* and *why*, not *how*.
- Comments explain why something is done, not what the line does.

## Errors

- Validate input at the page boundary and show a clear message the user can act on.
- `db.py` raises specific errors; pages catch them and show friendly text. Never show raw stack traces to users.
- Never use a bare `except:`.

## Secrets and config

- No keys, passwords or URLs with credentials in code. Use `st.secrets`.
- `.streamlit/secrets.toml` is in `.gitignore`. Commit `secrets.toml.example` with dummy values.

## Tests

- Use `pytest` for the logic that must not break: `routing.py`, `escalation.py`, `metrics.py`, tracking ID generation.
- UI is checked manually with a checklist before the demo.

## Git

- Small commits with messages like `feat: add tracking ID lookup`, `fix: handle empty photo`, `docs: update api.md`.
- Work on `main` for speed, but commit after every working step so you can roll back.

## Rules for AI-generated code

1. Read every file before committing. Be able to explain it in one sentence.
2. Run it and test a failure case, not just the happy path.
3. Remove unused code and unrequested features the AI added.
4. Never paste real keys or personal data into an AI prompt.
5. Record the tools and what they were used for in `AI_USAGE.md`.
