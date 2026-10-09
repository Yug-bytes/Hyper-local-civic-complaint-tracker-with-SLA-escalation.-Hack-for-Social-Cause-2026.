"""Brute-force protection for Admin Login endpoint."""

import threading
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from errors import RateLimitError


class LoginRateLimiter:
    """Tracks failed login attempts per client IP."""

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 900,  # 15 minutes
    ) -> None:
        self.max_attempts = max_attempts
        self.window = timedelta(seconds=window_seconds)
        self._attempts: dict[str, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def check_allowed(self, ip_address: Optional[str]) -> None:
        """Check if IP is allowed to attempt login. Raises RateLimitError."""
        if not ip_address:
            return

        now = datetime.now(timezone.utc)
        cutoff = now - self.window

        with self._lock:
            # Filter attempts older than the window
            recent = [t for t in self._attempts[ip_address] if t > cutoff]
            self._attempts[ip_address] = recent

            if len(recent) >= self.max_attempts:
                wait_mins = self.window.seconds // 60
                raise RateLimitError(
                    f"Too many failed login attempts. "
                    f"Please wait {wait_mins} minutes before trying again."
                )

    def record_failure(self, ip_address: Optional[str]) -> None:
        """Record a failed login attempt for the IP."""
        if not ip_address:
            return

        now = datetime.now(timezone.utc)
        cutoff = now - self.window
        with self._lock:
            recent = [t for t in self._attempts[ip_address] if t > cutoff]
            recent.append(now)
            self._attempts[ip_address] = recent

    def record_success(self, ip_address: Optional[str]) -> None:
        """Clear failed attempts upon successful authentication."""
        if not ip_address:
            return

        with self._lock:
            if ip_address in self._attempts:
                del self._attempts[ip_address]

    def clear(self) -> None:
        """Reset rate limiter state (useful for tests)."""
        with self._lock:
            self._attempts.clear()


# Global singleton instance
login_rate_limiter = LoginRateLimiter()
