"""Two-tier rate limiting for citizen complaint submissions.

Tier 1: Anonymous session cookie tracking:
  - 30-second cooldown between complaints (COMPLAINT_COOLDOWN_SECONDS = 30).
  - Maximum 5 complaints per session (MAX_COMPLAINTS_PER_SESSION = 5).

Tier 2: IP-based sliding window abuse protection:
  - Maximum 10 complaints per hour per IP.
"""

import secrets
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from constants import (
    COMPLAINT_COOLDOWN_SECONDS,
    MAX_COMPLAINTS_PER_SESSION,
)
from errors import RateLimitError


@dataclass
class CitizenSessionRecord:
    session_id: str
    submission_count: int
    last_submitted_at: Optional[datetime]
    created_at: datetime


class ComplaintRateLimiter:
    """Enforces both session-based cooldown/limits and IP-based rate limits."""

    def __init__(
        self,
        cooldown_seconds: int = COMPLAINT_COOLDOWN_SECONDS,
        max_session_submissions: int = MAX_COMPLAINTS_PER_SESSION,
        max_ip_hourly: int = 10,
    ) -> None:
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self.max_session_submissions = max_session_submissions
        self.max_ip_hourly = max_ip_hourly
        self.ip_window = timedelta(hours=1)

        self._session_records: dict[str, CitizenSessionRecord] = {}
        self._ip_records: dict[str, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def generate_session_id(self) -> str:
        """Create a new unique citizen session identifier."""
        return secrets.token_hex(16)

    def check_submission_allowed(
        self, session_id: Optional[str], ip_address: Optional[str]
    ) -> None:
        """Check both Tier 1 (session) and Tier 2 (IP) limits before submission.

        Raises RateLimitError if any limit is violated.
        """
        now = datetime.now(timezone.utc)

        with self._lock:
            # 1. Tier 2: Check IP-based burst limit
            if ip_address:
                cutoff = now - self.ip_window
                recent_ip_hits = [t for t in self._ip_records[ip_address] if t > cutoff]
                self._ip_records[ip_address] = recent_ip_hits
                if len(recent_ip_hits) >= self.max_ip_hourly:
                    raise RateLimitError(
                        "Rate limit exceeded from this IP address. "
                        "Please try again later."
                    )

            # 2. Tier 1: Check session-based cooldown and max limits
            if session_id and session_id in self._session_records:
                record = self._session_records[session_id]

                # Check max count per session
                if record.submission_count >= self.max_session_submissions:
                    raise RateLimitError(
                        f"Submission limit reached for this session "
                        f"({self.max_session_submissions} complaints max)."
                    )

                # Check cooldown
                if record.last_submitted_at:
                    elapsed = now - record.last_submitted_at
                    if elapsed < self.cooldown:
                        wait_remaining = (
                            int((self.cooldown - elapsed).total_seconds()) + 1
                        )
                        raise RateLimitError(
                            f"Please wait {wait_remaining} seconds "
                            "before submitting another complaint."
                        )

    def record_submission(self, session_id: str, ip_address: Optional[str]) -> None:
        """Record a successful complaint submission against session and IP."""
        now = datetime.now(timezone.utc)

        with self._lock:
            # Update session record
            if session_id not in self._session_records:
                self._session_records[session_id] = CitizenSessionRecord(
                    session_id=session_id,
                    submission_count=1,
                    last_submitted_at=now,
                    created_at=now,
                )
            else:
                record = self._session_records[session_id]
                record.submission_count += 1
                record.last_submitted_at = now

            # Update IP record
            if ip_address:
                self._ip_records[ip_address].append(now)

    def get_session_stats(self, session_id: Optional[str]) -> tuple[int, Optional[int]]:
        """Get (submission_count, seconds_until_next_allowed) for client info."""
        if not session_id:
            return 0, 0

        now = datetime.now(timezone.utc)
        with self._lock:
            record = self._session_records.get(session_id)
            if not record:
                return 0, 0
            wait = 0
            if record.last_submitted_at:
                elapsed = now - record.last_submitted_at
                if elapsed < self.cooldown:
                    wait = int((self.cooldown - elapsed).total_seconds()) + 1
            return record.submission_count, wait

    def clear(self) -> None:
        """Reset rate limiter state (useful for tests)."""
        with self._lock:
            self._session_records.clear()
            self._ip_records.clear()


# Global singleton instance
complaint_rate_limiter = ComplaintRateLimiter()
