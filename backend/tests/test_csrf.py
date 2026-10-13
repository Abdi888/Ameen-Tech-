"""Cookie CSRF is enforced on every state-changing API route."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from rest_framework.test import APIClient

from modules.access.models import Role, TenantMembership
from modules.identity.models import Session, User
from tests.support import PASSWORD, SessionClient, grant, login, make_tenant, make_user

pytestmark = pytest.mark.django_db


def test_csrf_cookie_is_readable_and_session_cookie_can_be_marked_secure(
    settings: Any,
) -> None:
    client = APIClient(enforce_csrf_checks=True)
    issued = client.get("/api/v1/health")
    csrf = issued.cookies["csrftoken"]
    assert csrf["samesite"] == "Lax"
    assert not csrf["httponly"]

    settings.SESSION_COOKIE_SECURE = True
    settings.CSRF_COOKIE_SECURE = True
    tenant = make_tenant("harbor")
    user = make_user("cashier@harbor.test")
    grant(user, tenant, "Cashier")
    secured = APIClient(enforce_csrf_checks=True)
    health = secured.get("/api/v1/health")
    assert health.cookies["csrftoken"]["secure"]
    secured.credentials(HTTP_X_CSRFTOKEN=health.cookies["csrftoken"].value)
    logged = secured.post(
        "/api/v1/auth/login",
        {"email": user.email, "password": PASSWORD},
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert logged.status_code == 200
    assert logged.cookies["ameen_session"]["httponly"]
    assert logged.cookies["ameen_session"]["samesite"] == "Lax"
    assert logged.cookies["ameen_session"]["secure"]


def test_state_changing_routes_reject_a_missing_or_mismatched_csrf_token(
    api: SessionClient,
) -> None:
    tenant = make_tenant("harbor")
    admin = make_user("admin@harbor.test")
    cashier = make_user("cashier@harbor.test")
    grant(admin, tenant, "Administrator")
    grant(cashier, tenant, "Cashier")
    assert login(api, admin.email, tenant=tenant).status_code == 200
    session = api.client.cookies["ameen_session"].value
    csrf = api.csrf
    role_id = str(Role.objects.get(name="Cashier", tenant__isnull=True).id)
    invite = {
        "email": "newcomer@harbor.test",
        "first_name": "New",
        "last_name": "Member",
        "role_id": role_id,
    }
    calls: list[tuple[str, str, dict[str, Any]]] = [
        ("post", "/api/v1/auth/logout", {}),
        (
            "post",
            "/api/v1/auth/password/change",
            {"current_password": PASSWORD, "password": "another-password-ok"},
        ),
        ("post", "/api/v1/users", invite),
        ("patch", f"/api/v1/users/{cashier.id}", {"first_name": "Changed"}),
        ("post", f"/api/v1/users/{cashier.id}/deactivate", {}),
        ("post", f"/api/v1/users/{cashier.id}/roles", {"role_ids": [role_id]}),
    ]
    for method, path, body in calls:
        for header in (None, "not-the-csrf-token"):
            rejected = _session_client(session, header, tenant.id)
            response = getattr(rejected, method)(path, body, format="json")
            assert response.status_code == 403, path
            assert response.json()["errors"][0]["code"] == "PERMISSION_DENIED"
            assert response.json()["errors"][0]["message"] == "CSRF verification failed."

    cashier.refresh_from_db()
    assert cashier.first_name == "Amina"
    assert cashier.password_hash.startswith("$argon2id$")
    assert not User.objects.filter(email="newcomer@harbor.test").exists()
    assert TenantMembership.objects.get(user=cashier, tenant=tenant).status == "ACTIVE"
    assert Session.objects.filter(user=admin, revoked_at__isnull=True).count() == 1

    anonymous = [
        ("/api/v1/auth/login", {"email": admin.email, "password": PASSWORD}),
        ("/api/v1/auth/password/reset", {"email": admin.email}),
        (
            "/api/v1/auth/password/reset/confirm",
            {"token": "missing-token", "password": "another-password-ok"},
        ),
    ]
    for path, body in anonymous:
        for header in (None, "not-the-csrf-token"):
            client = APIClient(enforce_csrf_checks=True)
            client.cookies["csrftoken"] = csrf
            if header:
                client.credentials(HTTP_X_CSRFTOKEN=header)
            response = client.post(path, body, format="json")
            assert response.status_code == 403, path
            assert response.json()["errors"][0]["message"] == "CSRF verification failed."

    matched = APIClient(enforce_csrf_checks=True)
    matched.cookies["csrftoken"] = csrf
    matched.credentials(HTTP_X_CSRFTOKEN=csrf)
    wrong_password = matched.post(
        "/api/v1/auth/login",
        {"email": admin.email, "password": "wrong-password-value"},
        format="json",
    )
    assert wrong_password.status_code == 401

    quiet = _session_client(session, None, tenant.id)
    me = quiet.get("/api/v1/auth/me")
    assert me.status_code == 200
    listing = quiet.get("/api/v1/users")
    assert listing.status_code == 200


def _session_client(session: str, csrf_header: str | None, tenant_id: uuid.UUID) -> APIClient:
    client = APIClient(enforce_csrf_checks=True)
    client.cookies["ameen_session"] = session
    headers: dict[str, str] = {"HTTP_X_TENANT_ID": str(tenant_id)}
    if csrf_header is not None:
        headers["HTTP_X_CSRFTOKEN"] = csrf_header
    client.credentials(**headers)
    return client
