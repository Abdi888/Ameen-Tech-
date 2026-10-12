"""Local settings. Loads the repository `.env` when it exists."""

from __future__ import annotations

import os
from pathlib import Path

from config.env import load_env_file

load_env_file(Path(__file__).resolve().parents[3] / ".env")

os.environ.setdefault("SECRET_KEY", "dev-only-not-for-production")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault("DATABASE_URL", "postgres://ameen:ameen@localhost:5432/ameen_retail")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

from .base import *  # noqa: E402,F403
