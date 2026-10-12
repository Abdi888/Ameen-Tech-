"""Test settings. Never load `.env` and never accept a remote database host."""

from __future__ import annotations

import os
from urllib.parse import urlparse

from config.env import assert_local_database

os.environ.setdefault("SECRET_KEY", "test-only-not-for-production")
os.environ["DEBUG"] = "false"
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
# Django's test client requests the host "testserver".
_allowed_hosts = [item.strip() for item in os.environ["ALLOWED_HOSTS"].split(",") if item.strip()]
if "testserver" not in _allowed_hosts:
    _allowed_hosts.append("testserver")
os.environ["ALLOWED_HOSTS"] = ",".join(_allowed_hosts)
os.environ.setdefault("DATABASE_URL", "postgres://ameen:ameen@localhost:5432/ameen_retail")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

assert_local_database(urlparse(os.environ["DATABASE_URL"]).hostname or "")

from .base import *  # noqa: E402,F403
