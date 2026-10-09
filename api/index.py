"""Vercel Serverless Function entrypoint for FastAPI.

Vercel automatically detects api/index.py and invokes the exported ASGI `app`.
"""

import sys
from pathlib import Path

# Ensure root project directory is on sys.path so modules like db, config,
# constants, and services can be imported cleanly in Vercel's serverless environment.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.main import app  # noqa: F401, E402
