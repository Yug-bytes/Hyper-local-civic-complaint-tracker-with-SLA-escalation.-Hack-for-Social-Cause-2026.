"""Server-managed session store for Administrator authentication.

Enforces:
- 60-minute inactivity expiration (sliding window).
- 8-hour maximum session lifetime from initial creation.
- Explicit session revocation on logout.
- Thread-safe in-memory session registry (suitable for single-process test/dev).
"""

import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class AdminSession:
    session_id: str
    created_at: datetime
    last_accessed_at: datetime
    ip_address: Optional[str] = None
    is_revoked: bool = False


class SessionStore:
    """Thread-safe in-memory store for server-managed admin sessions."""

    def __init__(
        self,
        inactivity_timeout_seconds: int = 3600,  # 60 minutes
        max_lifetime_seconds: int = 28800,  # 8 hours
    ) -> None:
        self.inactivity_timeout = timedelta(seconds=inactivity_timeout_seconds)
        self.max_lifetime = timedelta(seconds=max_lifetime_seconds)
        self._sessions: dict[str, AdminSession] = {}
        self._lock = threading.Lock()

    def create_session(self, ip_address: Optional[str] = None) -> str:
        """Create a new session and record its creation time."""
        session_id = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        session = AdminSession(
            session_id=session_id,
            created_at=now,
            last_accessed_at=now,
            ip_address=ip_address,
            is_revoked=False,
        )
        with self._lock:
            self._sessions[session_id] = session
        return session_id

    def validate_session(self, session_id: Optional[str]) -> bool:
        """Validate an existing session ID.

        Returns True and updates last_accessed_at if valid.
        Returns False if missing, revoked, or expired.
        """
        if not session_id:
            return False

        now = datetime.now(timezone.utc)
        with self._lock:
            session = self._sessions.get(session_id)
            if not session or session.is_revoked:
                return False

            # Check 8-hour max lifetime
            if (now - session.created_at) > self.max_lifetime:
                session.is_revoked = True
                return False

            # Check 60-minute inactivity timeout
            if (now - session.last_accessed_at) > self.inactivity_timeout:
                session.is_revoked = True
                return False

            # Session is valid: refresh last_accessed_at
            session.last_accessed_at = now
            return True

    def revoke_session(self, session_id: Optional[str]) -> None:
        """Revoke a session on logout."""
        if not session_id:
            return
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.is_revoked = True

    def cleanup_expired(self) -> int:
        """Purge revoked or expired sessions to prevent memory leaks."""
        now = datetime.now(timezone.utc)
        with self._lock:
            to_delete = [
                sid
                for sid, s in self._sessions.items()
                if s.is_revoked
                or (now - s.created_at) > self.max_lifetime
                or (now - s.last_accessed_at) > self.inactivity_timeout
            ]
            for sid in to_delete:
                del self._sessions[sid]
            return len(to_delete)

    def clear(self) -> None:
        """Clear all sessions (useful for test resets)."""
        with self._lock:
            self._sessions.clear()


# Global singleton instance for admin sessions
session_store = SessionStore()
