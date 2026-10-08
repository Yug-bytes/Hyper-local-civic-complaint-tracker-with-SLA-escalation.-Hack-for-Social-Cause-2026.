# Security and Privacy

Prototype-level security for a real community pilot. Keep it simple, but do these things properly.

## 1. Secrets

- Store the Supabase URL, keys and admin password in `st.secrets` (Streamlit Cloud secrets). Never in code, README or screenshots.
- `.streamlit/secrets.toml` is in `.gitignore`. Commit only `secrets.toml.example` with dummy values.
- All Supabase access is server-side in `db.py`, using the **service role key** from `st.secrets`. The browser never talks to Supabase, so the anon key is not used. Treat the service role key like a root password: never log it, print it, commit it or screenshot it.
- If a key is ever committed, rotate it immediately and treat it as leaked.
- Never paste real keys or personal data into AI tool prompts.

## 2. Personal data

| Data | Rule |
|---|---|
| Name, phone | Optional. Stored, but never shown on public pages |
| Photos | Warn users not to include faces, number plates or house numbers |
| Locality | Use a colony / ward / landmark, not an exact home address |
| Tracking ID | The only thing needed to see a complaint's status |

- Add a short consent line on the form: "Name and phone are optional and only used by the area admin to follow up."
- Delete or anonymise names and phones after the hackathon.

## 3. Access control

- **Public:** can create a complaint, look up by tracking ID, view the public dashboard.
- **Admin:** can list all complaints and update status. Protected by a password from `st.secrets`, compared with `hmac.compare_digest`. Admin state lives in `st.session_state`.
- Turn on Supabase **Row Level Security** on all tables with **no public policies**, so nothing is reachable except through our server code. Because the service role key bypasses RLS, `db.py` is the only gatekeeper: public functions select only safe columns (never `reporter_name` or `reporter_phone`), and admin functions require the admin session flag.
- Tracking IDs use a random suffix so they cannot be guessed in sequence.

## 4. Input validation

- Category must be in the known list.
- Description: required, max 1000 characters. Locality: required, max 100.
- Name max 80, phone digits only (10-digit Indian mobile format) if provided.
- Strip leading and trailing whitespace; reject empty strings.
- Always use the Supabase client's parameterised calls. Never build SQL from user text.

## 5. Output safety (XSS)

- Never render user-entered text with `unsafe_allow_html=True`.
- Use `st.text`, `st.write` or escape text before any HTML.
- Photo captions and descriptions are treated as plain text.

## 6. File uploads

- Allowed types: JPG, PNG. Check the real content type, not just the extension.
- Max size: 5 MB. Reject larger files with a clear message.
- Rename files to random names on upload; never trust the original filename.
- Store in a Supabase Storage bucket with no listing permission.

## 7. Abuse and spam

- Per-session cooldown: no more than 1 complaint every 30 seconds, and no more than 5 per session.
- Basic duplicate check: same category, same locality, same description within 24 hours is flagged.
- Admin can mark a complaint as spam instead of deleting it.

## 8. Dependencies and deployment

- Pin versions in `requirements.txt`; install only what is needed.
- Deploy over HTTPS (Streamlit Cloud provides this).
- Public GitHub repo: check history for secrets before making it public.

## 9. Pre-submission checklist

- [ ] No secrets in the repo or its history
- [ ] RLS enabled on all tables
- [ ] Public pages show no names or phones
- [ ] Admin page is locked behind a password
- [ ] Upload type and size checks work
- [ ] No `unsafe_allow_html` with user text
- [ ] Consent line is on the form
- [ ] Seed/demo data is clearly labelled
- [ ] README states known limitations honestly
