"""Parse process environment for Django settings.

Development loads a local `.env` before importing these helpers. Production
must already have its variables set. This module does not read secret files.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

# Hosts the test suite is allowed to reach. Blocks accidental production URLs.
LOCAL_DATABASE_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "postgres"})

INSECURE_SECRET_KEYS = frozenset(
    {
        "change-me",
        "dev-only-not-for-production",
        "test-only-not-for-production",
    }
)


def load_env_file(path: Path) -> None:
    """Fill missing environment variables from a KEY=VALUE file.

    Variables already set in the process are left unchanged.
    """
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def cors_origins(name: str = "CORS_ALLOWED_ORIGINS") -> list[str]:
    origins = env_list(name)
    if "*" in origins:
        raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS cannot contain *.")
    return origins


def csrf_trusted_origins(cors: list[str], name: str = "CSRF_TRUSTED_ORIGINS") -> list[str]:
    """Origins Django may accept on cookie-authenticated unsafe requests.

    CORS and CSRF are separate controls. When CSRF_TRUSTED_ORIGINS is unset,
    reuse the CORS allowlist so the SPA origin that may call the API with
    credentials is also trusted for Origin checks. An explicit CSRF list must
    stay a concrete allowlist; wildcards are rejected.
    """
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return list(cors)
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    if "*" in origins:
        raise ImproperlyConfigured("CSRF_TRUSTED_ORIGINS cannot contain *.")
    return origins


def postgresql_from_url(database_url: str) -> dict[str, object]:
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured("DATABASE_URL must use the postgres or postgresql scheme.")
    name = parsed.path.lstrip("/")
    if not name or "/" in name:
        raise ImproperlyConfigured("DATABASE_URL must include a database name.")
    config: dict[str, object] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or 5432),
        "CONN_MAX_AGE": 0,
        "OPTIONS": {"connect_timeout": 5},
    }
    return config


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} is required.")
    return value


def assert_local_database(host: str) -> None:
    if host not in LOCAL_DATABASE_HOSTS:
        raise ImproperlyConfigured(
            f"Refusing DATABASE_URL host {host!r}. Tests only run against a local PostgreSQL."
        )


def assert_production_settings(*, debug: bool, secret_key: str, allowed_hosts: list[str]) -> None:
    if debug:
        raise ImproperlyConfigured("Production cannot run with DEBUG enabled.")
    if secret_key.strip() in INSECURE_SECRET_KEYS or len(secret_key.strip()) < 32:
        raise ImproperlyConfigured(
            "Production SECRET_KEY must be a unique secret of at least 32 characters."
        )
    if not allowed_hosts or any(host.strip() == "*" for host in allowed_hosts):
        raise ImproperlyConfigured("Production ALLOWED_HOSTS must be an explicit list.")
