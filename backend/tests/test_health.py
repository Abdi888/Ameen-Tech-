from __future__ import annotations

import importlib
import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml
from django.db import DatabaseError, connection
from django.test import Client
from rest_framework.test import APIClient

from shared.database.checks import database_is_reachable
from shared.exceptions import STATUS_BY_CODE

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.django_db
def test_health_reports_database_ok() -> None:
    request_id = str(uuid.uuid4())
    response = APIClient().get("/api/v1/health", HTTP_X_REQUEST_ID=request_id)
    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == request_id
    assert response.json() == {
        "success": True,
        "data": {"status": "ok", "database": "ok"},
        "meta": {},
    }


@pytest.mark.django_db
def test_health_ignores_an_unsafe_request_id_and_a_tenant_hint() -> None:
    response = APIClient().get(
        "/api/v1/health",
        HTTP_X_REQUEST_ID="bad id\ninjected",
        HTTP_X_TENANT_ID=str(uuid.uuid4()),
    )
    assert response.status_code == 200
    echoed = response.headers["X-Request-Id"]
    assert "\n" not in echoed
    assert echoed != "bad id\ninjected"
    uuid.UUID(echoed)
    assert "tenant_id" not in response.json()["data"]


def test_debug_mode_404_stays_json(settings: Any) -> None:
    settings.DEBUG = True
    response = Client().get("/api/v1/products/does-not-exist")
    assert response.status_code == 404
    assert response["Content-Type"].startswith("application/json")
    assert response.json()["errors"][0]["code"] == "RESOURCE_NOT_FOUND"
    assert "URLconf" not in response.content.decode()


def test_debug_mode_500_hides_the_exception(settings: Any) -> None:
    settings.DEBUG = True
    settings.ROOT_URLCONF = "tests.urlconfs"
    response = Client(raise_request_exception=False).get("/api/v1/raw-crash")
    assert response.status_code == 500
    text = response.content.decode()
    assert "marker-do-not-leak" not in text
    assert "Traceback" not in text
    assert response.json()["errors"][0]["code"] == "INTERNAL_ERROR"


def test_post_health_is_method_not_allowed() -> None:
    response = APIClient().post("/api/v1/health", data={}, format="json")
    assert response.status_code == 405
    assert response["Content-Type"].startswith("application/json")
    body = response.json()
    assert body == {
        "success": False,
        "data": None,
        "meta": {},
        "errors": [
            {
                "code": "METHOD_NOT_ALLOWED",
                "message": "This method is not allowed.",
                "field": None,
            }
        ],
    }
    assert "INVALID_VALUE" not in response.content.decode()


def test_trailing_slash_is_not_rewritten() -> None:
    response = APIClient().get("/api/v1/health/")
    assert response.status_code == 404
    assert response.json()["errors"][0]["code"] == "RESOURCE_NOT_FOUND"


def test_database_check_swallows_driver_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*args: object, **kwargs: object) -> object:
        raise DatabaseError("password=super-secret")

    monkeypatch.setattr(connection, "cursor", explode)
    assert database_is_reachable() is False


@pytest.mark.django_db
def test_health_failure_does_not_leak_the_driver_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shared.api.health.database_is_reachable", lambda: False)
    response = APIClient().get("/api/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["errors"][0]["code"] == "SERVICE_UNAVAILABLE"
    assert "password" not in response.content.decode().lower()


def test_unhandled_api_error_hides_the_exception(settings: Any) -> None:
    settings.ROOT_URLCONF = "tests.urlconfs"
    response = APIClient().get("/api/v1/crash")
    assert response.status_code == 500
    assert response.json()["errors"][0] == {
        "code": "INTERNAL_ERROR",
        "message": "An unexpected error occurred.",
        "field": None,
    }
    text = response.content.decode()
    assert "marker-do-not-leak" not in text
    assert "Traceback" not in text


def test_unhandled_django_error_hides_the_exception(settings: Any) -> None:
    settings.ROOT_URLCONF = "tests.urlconfs"
    response = Client(raise_request_exception=False).get("/api/v1/raw-crash")
    assert response.status_code == 500
    assert response.json()["errors"][0]["code"] == "INTERNAL_ERROR"
    assert "marker-do-not-leak" not in response.content.decode()


def test_invalid_json_uses_invalid_format(settings: Any) -> None:
    settings.ROOT_URLCONF = "tests.urlconfs"
    response = Client().post(
        "/api/v1/echo",
        data="{",
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json()["errors"][0]["code"] == "INVALID_FORMAT"
    assert "Expecting" not in response.content.decode()


@pytest.mark.django_db
def test_domain_schemas_exist() -> None:
    migration = importlib.import_module("shared.database.migrations.0001_domain_schemas")
    names = list(migration.DOMAIN_SCHEMAS)
    placeholders = ", ".join(["%s"] * len(names))
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name IN ({placeholders})
            """,
            names,
        )
        found = {row[0] for row in cursor.fetchall()}
    assert found == set(names)


def test_openapi_lists_the_health_route_and_document_05_codes() -> None:
    spec = yaml.safe_load((BACKEND_ROOT / "openapi.yaml").read_text(encoding="utf-8"))
    operation = spec["paths"]["/api/v1/health"]["get"]
    assert "200" in operation["responses"]
    assert "503" in operation["responses"]
    assert set(spec["components"]["schemas"]["ErrorCode"]["enum"]) == set(STATUS_BY_CODE)
