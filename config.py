"""Configuration module for Civic Complaint Tracker.

Supports environment variables first, falling back to st.secrets
when running inside Streamlit Cloud.
Fails safely with a clear ConfigurationError if required secrets are missing.
"""

import os
from functools import lru_cache
from typing import Any

from errors import ConfigurationError


def _get_raw_secret(key: str, default: Any = None) -> Any:
    """Get a configuration value from os.environ or st.secrets."""
    # 1. Check environment variables
    if key in os.environ:
        return os.environ[key]

    # 2. Check Streamlit secrets if running inside Streamlit
    try:
        import streamlit as st

        if hasattr(st, "secrets") and st.secrets is not None:
            val = st.secrets.get(key)
            if val is not None:
                return val
            if "supabase" in st.secrets and key.startswith("SUPABASE_"):
                sub_key = key.replace("SUPABASE_", "").lower()
                if sub_key in st.secrets["supabase"]:
                    return st.secrets["supabase"][sub_key]
                if sub_key == "service_role_key":
                    return st.secrets["supabase"].get("service_key") or st.secrets[
                        "supabase"
                    ].get("key")
            if "admin" in st.secrets and key == "ADMIN_PASSWORD":
                return st.secrets["admin"].get("password")
    except Exception:
        pass

    return default


class Settings:
    """Runtime settings loaded from environment or Streamlit secrets."""

    def __init__(self) -> None:
        raw_url = str(_get_raw_secret("SUPABASE_URL", "")).strip()
        if raw_url.endswith("/rest/v1/"):
            raw_url = raw_url[:-9]
        elif raw_url.endswith("/rest/v1"):
            raw_url = raw_url[:-8]
        self.supabase_url: str = raw_url.rstrip("/")

        self.supabase_service_role_key: str = str(
            _get_raw_secret("SUPABASE_SERVICE_ROLE_KEY", "")
        ).strip()
        if not self.supabase_service_role_key:
            self.supabase_service_role_key = str(
                _get_raw_secret("SUPABASE_SERVICE_KEY", "")
            ).strip()

        self.admin_password: str = str(_get_raw_secret("ADMIN_PASSWORD", "")).strip()

        self.photo_bucket: str = str(
            _get_raw_secret("PHOTO_BUCKET", "complaint-photos")
        ).strip()

        raw_session_secret = _get_raw_secret("ADMIN_SESSION_SECRET")
        if raw_session_secret:
            self.admin_session_secret: str = str(raw_session_secret).strip()
        else:
            self.admin_session_secret = (
                self.admin_password or "civic-tracker-dev-session-secret-change-in-prod"
            )

        raw_cors = _get_raw_secret(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
        )
        if isinstance(raw_cors, str):
            self.cors_origins: list[str] = [
                origin.strip() for origin in raw_cors.split(",") if origin.strip()
            ]
        elif isinstance(raw_cors, list):
            self.cors_origins = [str(o).strip() for o in raw_cors]
        else:
            self.cors_origins = [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
            ]

        self.signed_photo_url_ttl: int = int(
            _get_raw_secret("SIGNED_PHOTO_URL_TTL", 900)
        )
        self.env: str = str(_get_raw_secret("ENV", "development")).strip()

    def validate_required(self) -> None:
        """Ensure required secrets are present, raising ConfigurationError."""
        missing = []
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_service_role_key:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        if not self.admin_password:
            missing.append("ADMIN_PASSWORD")
        if missing:
            raise ConfigurationError(
                f"Missing required configuration/secrets: {', '.join(missing)}. "
                "Please set these in environment variables or .streamlit/secrets.toml."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached singleton Settings instance."""
    return Settings()
