from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import (
    assert_local_database,
    assert_production_settings,
    cors_origins,
    postgresql_from_url,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_database_url_parser_accepts_postgres() -> None:
    config = postgresql_from_url("postgres://user:p%40ss@localhost:5433/ameen_retail")
    assert config["ENGINE"] == "django.db.backends.postgresql"
    assert config["NAME"] == "ameen_retail"
    assert config["USER"] == "user"
    assert config["PASSWORD"] == "p@ss"
    assert config["HOST"] == "localhost"
    assert config["PORT"] == "5433"


def test_database_url_rejects_other_engines() -> None:
    with pytest.raises(ImproperlyConfigured):
        postgresql_from_url("sqlite:///ameen.sqlite3")


def test_tests_refuse_a_remote_database_host() -> None:
    with pytest.raises(ImproperlyConfigured):
        assert_local_database("db.example.com")


def test_cors_allowlist_rejects_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")
    with pytest.raises(ImproperlyConfigured):
        cors_origins()


def test_production_guard_rejects_debug_placeholder_secret_and_wildcard_hosts() -> None:
    with pytest.raises(ImproperlyConfigured):
        assert_production_settings(
            debug=True, secret_key="x" * 40, allowed_hosts=["api.example.com"]
        )
    with pytest.raises(ImproperlyConfigured):
        assert_production_settings(
            debug=False,
            secret_key="dev-only-not-for-production",
            allowed_hosts=["api.example.com"],
        )
    with pytest.raises(ImproperlyConfigured):
        assert_production_settings(debug=False, secret_key="x" * 40, allowed_hosts=["*"])
    assert_production_settings(
        debug=False,
        secret_key="x" * 40,
        allowed_hosts=["api.example.com"],
    )


def test_loaded_test_settings_are_closed() -> None:
    from django.conf import settings

    assert settings.DEBUG is False
    assert settings.DATABASES["default"]["HOST"] in {"localhost", "127.0.0.1", "::1", "postgres"}
    assert "*" not in settings.CORS_ALLOWED_ORIGINS
    assert "django.contrib.auth" not in settings.INSTALLED_APPS
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"


def test_production_module_rejects_insecure_environment() -> None:
    env = os.environ.copy()
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings.production",
            "DEBUG": "true",
            "SECRET_KEY": "x" * 40,
            "ALLOWED_HOSTS": "api.example.com",
            "DATABASE_URL": "postgres://ameen:ameen@db.internal:5432/ameen_retail",
            "CORS_ALLOWED_ORIGINS": "https://app.example.com",
        }
    )
    completed = subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "DEBUG" in completed.stderr
