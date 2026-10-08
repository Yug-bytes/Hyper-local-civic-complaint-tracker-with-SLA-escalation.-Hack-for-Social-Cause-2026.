"""Seed script for the Civic Complaint Tracker.

Inserts initial departments and 25 sample complaints in mixed statuses and ages.
Every seeded complaint description starts with '[DEMO]'.
NEVER deletes real data.
Refuses to run unless invoked with --confirm.
"""

import argparse
import json
import pathlib
import sys
import tomllib
from datetime import datetime, timedelta, timezone

# Ensure project root is on sys.path for direct script execution
_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from constants import Status  # noqa: E402
from services import ids, routing  # noqa: E402
from supabase import Client, create_client  # noqa: E402


def _load_secrets() -> tuple[str, str]:
    """Load Supabase URL and service role key from .streamlit/secrets.toml."""
    secrets_path = (
        pathlib.Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
    )
    if not secrets_path.exists():
        print(f"Error: Secrets file not found at {secrets_path}")
        sys.exit(1)

    data = tomllib.loads(secrets_path.read_text(encoding="utf-8"))

    url = data.get("SUPABASE_URL")
    key = data.get("SUPABASE_SERVICE_ROLE_KEY")

    if "supabase" in data:
        sb = data["supabase"]
        if not url:
            url = sb.get("url")
        if not key:
            key = sb.get("service_key") or sb.get("service_role_key") or sb.get("key")

    if not url or not key:
        print("Error: SUPABASE_URL or service key missing in secrets.toml")
        sys.exit(1)

    url_str = str(url).strip()
    if url_str.endswith("/rest/v1/"):
        url_str = url_str[:-9]
    elif url_str.endswith("/rest/v1"):
        url_str = url_str[:-8]
    url_str = url_str.rstrip("/")

    return url_str, str(key).strip()


def _seed_departments(client: Client) -> None:
    """Ensure departments are present in the database."""
    dept_file = (
        pathlib.Path(__file__).resolve().parent.parent / "data" / "departments.json"
    )
    with open(dept_file, encoding="utf-8") as f:
        depts = json.load(f)

    for d in depts:
        client.table("departments").upsert(
            {
                "category": d["category"],
                "department_name": d["department_name"],
                "responsible_role": d["responsible_role"],
                "escalation_role": d["escalation_role"],
                "sla_days": d["sla_days"],
            },
            on_conflict="category",
        ).execute()

    print(f"Seeded {len(depts)} departments.")


def _generate_demo_complaints() -> list[dict]:
    """Generate 25 sample complaints with varied ages, statuses, and SLAs."""
    now = datetime.now(timezone.utc)

    # Blueprint: (category, status, days_ago, is_overdue, locality, desc)
    blueprints = [
        # 1-6 Potholes
        (
            "pothole",
            Status.RESOLVED,
            8,
            False,
            "Main Market Road",
            "Pothole near State Bank ATM repaired promptly.",
        ),
        (
            "pothole",
            Status.RESOLVED,
            6,
            False,
            "Sector 4 Chowk",
            "Deep pothole filled with bitumen.",
        ),
        (
            "pothole",
            Status.IN_PROGRESS,
            10,
            True,
            "Ring Road Flyover",
            "Large crater on flyover descent creating traffic jam.",
        ),
        (
            "pothole",
            Status.ASSIGNED,
            4,
            False,
            "Civil Lines Ward 2",
            "Road caved in near community hall gate.",
        ),
        (
            "pothole",
            Status.SUBMITTED,
            1,
            False,
            "Shanti Nagar Gali 3",
            "Multiple potholes after monsoon shower.",
        ),
        (
            "pothole",
            Status.SUBMITTED,
            12,
            True,
            "Old Bus Stand Road",
            "Hazardous trench left unpaved for 2 weeks.",
        ),
        # 7-11 Water
        (
            "water",
            Status.RESOLVED,
            4,
            False,
            "Adarsh Colony Block B",
            "Low water pressure resolved after valve fix.",
        ),
        (
            "water",
            Status.IN_PROGRESS,
            5,
            True,
            "Gandhi Nagar Gali 1",
            "Contaminated muddy tap water supplying 30 houses.",
        ),
        (
            "water",
            Status.ASSIGNED,
            2,
            False,
            "Railway Colony Qtr 45",
            "Main distribution pipeline leaking water onto road.",
        ),
        (
            "water",
            Status.SUBMITTED,
            1,
            False,
            "Kisan Mandi Area",
            "No drinking water supply since yesterday morning.",
        ),
        (
            "water",
            Status.IN_PROGRESS,
            6,
            True,
            "Subhash Park Enclave",
            "Pipeline burst flooding entrance pathway.",
        ),
        # 12-16 Streetlights
        (
            "streetlight",
            Status.RESOLVED,
            5,
            False,
            "Nehru Chowk",
            "Streetlight blinking repaired by line staff.",
        ),
        (
            "streetlight",
            Status.ASSIGNED,
            3,
            False,
            "Govt School Road",
            "Dark patch outside primary school gate at night.",
        ),
        (
            "streetlight",
            Status.IN_PROGRESS,
            8,
            True,
            "Pocket C Outer Lane",
            "Entire row of 4 streetlights not functioning.",
        ),
        (
            "streetlight",
            Status.SUBMITTED,
            2,
            False,
            "Shivaji Marg Lane 4",
            "Damaged pole leaning precariously after storm.",
        ),
        (
            "streetlight",
            Status.SUBMITTED,
            10,
            True,
            "Behind Community Centre",
            "Broken bulb socket, completely dark alley.",
        ),
        # 17-21 Garbage
        (
            "garbage",
            Status.RESOLVED,
            3,
            False,
            "Sabzi Mandi Yard",
            "Overflowing waste bin cleared and disinfected.",
        ),
        (
            "garbage",
            Status.RESOLVED,
            2,
            False,
            "Hospital Gate No 2",
            "Biomedical waste dumped outside gate removed.",
        ),
        (
            "garbage",
            Status.IN_PROGRESS,
            4,
            True,
            "Park View Apartments",
            "Open garbage heap not cleared for 4 days.",
        ),
        (
            "garbage",
            Status.ASSIGNED,
            1,
            False,
            "Model Town Sector 9",
            "Animal carcass reported near corner bin.",
        ),
        (
            "garbage",
            Status.SUBMITTED,
            5,
            True,
            "Grain Market Exit",
            "Commercial waste dumped across pedestrian walkway.",
        ),
        # 22-25 Other
        (
            "other",
            Status.RESOLVED,
            9,
            False,
            "Ward 7 Office",
            "Fallen tree branch cleared from electrical wires.",
        ),
        (
            "other",
            Status.IN_PROGRESS,
            5,
            False,
            "Public Park Sector 3",
            "Broken swing and damaged boundary railing.",
        ),
        (
            "other",
            Status.SUBMITTED,
            11,
            True,
            "Old Court Compound",
            "Stray dog menace reported near post office.",
        ),
        (
            "other",
            Status.ASSIGNED,
            3,
            False,
            "Vikas Marg Crossing",
            "Blocked stormwater drain causing stagnant water.",
        ),
    ]

    complaints_data = []

    for cat, status, days_ago, is_overdue, locality, desc in blueprints:
        dept = routing.route(cat)
        sla_days = dept["sla_days"]
        created_at = now - timedelta(days=days_ago, hours=3)

        if is_overdue:
            # Due date was in the past
            due_at = created_at + timedelta(days=sla_days)
        else:
            # For non-overdue open items, set due date into the future
            if status != Status.RESOLVED:
                due_at = now + timedelta(days=sla_days - 1)
            else:
                due_at = created_at + timedelta(days=sla_days)

        resolved_at = None
        if status == Status.RESOLVED:
            # Resolved in 1 to 2 days
            resolved_at = (created_at + timedelta(days=1, hours=8)).isoformat()

        tracking_id = ids.generate_tracking_id(created_at)

        complaints_data.append(
            {
                "tracking_id": tracking_id,
                "category": cat,
                "description": f"[DEMO] {desc}",
                "locality": locality,
                "photo_url": None,
                "reporter_name": "Demo Citizen",
                "reporter_phone": "9876543210",
                "status": status,
                "created_at": created_at.isoformat(),
                "due_at": due_at.isoformat(),
                "resolved_at": resolved_at,
            }
        )

    return complaints_data


def seed_all() -> None:
    """Insert departments and demo complaints into Supabase."""
    url, key = _load_secrets()
    client = create_client(url, key)

    print("Connecting to Supabase...")
    _seed_departments(client)

    demo_items = _generate_demo_complaints()
    print(f"Inserting {len(demo_items)} demo complaints...")

    inserted_count = 0
    for item in demo_items:
        res = client.table("complaints").insert(item).execute()
        if res.data:
            inserted_count += 1
            cid = res.data[0]["id"]
            # Insert initial history row if table is available
            try:
                client.table("status_history").insert(
                    {
                        "complaint_id": cid,
                        "status": item["status"],
                        "note": f"[DEMO] Initial state: {item['status']}",
                        "changed_by": "system",
                        "changed_at": item["created_at"],
                    }
                ).execute()
            except Exception:
                pass

    print(f"Successfully seeded {inserted_count} demo complaints!")


def main() -> None:
    """CLI entry point enforcing safety confirmation."""
    parser = argparse.ArgumentParser(
        description="Seed demo data for the Civic Complaint Tracker."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm insertion of demo data. Required for safety.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print("Safety check: This script inserts demo data into your database.")
        print("To proceed, you must pass the --confirm flag:")
        print("    python scripts/seed.py --confirm")
        sys.exit(1)

    seed_all()


if __name__ == "__main__":
    main()
