"""Operator bootstrap creates three identities and then refuses to run again."""

from __future__ import annotations

import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from modules.access.models import Role, TenantMembership, TenantUserRole
from modules.audit.models import AuditLog
from modules.identity.application.bootstrap import (
    COMPLETED_ACTION,
    BootstrapError,
    BootstrapRequest,
    bootstrap_initial,
)
from modules.identity.management.commands.bootstrap_initial_tenant import (
    CONFIRM_ENV,
    CONFIRM_VALUE,
)
from modules.identity.models import User
from modules.tenants.models import Tenant
from tests.support import PASSWORD, SessionClient, grant, login, make_tenant, make_user

pytestmark = pytest.mark.django_db

PLATFORM_EMAIL = "platform@ameen.test"
OWNER_EMAIL = "owner@ameen.test"
PLATFORM_PASSWORD = "platform-horse-battery"
TENANT_SLUG = "harbor"


def test_command_refuses_without_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(CONFIRM_ENV, raising=False)
    with pytest.raises(CommandError, match=CONFIRM_VALUE):
        call_command("bootstrap_initial_tenant")
    assert User.objects.count() == 0
    assert Tenant.objects.count() == 0


def test_command_refuses_a_missing_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(CONFIRM_ENV, CONFIRM_VALUE)
    monkeypatch.delenv("AMEEN_BOOTSTRAP_PLATFORM_PASSWORD", raising=False)
    with pytest.raises(CommandError, match="AMEEN_BOOTSTRAP_PLATFORM_PASSWORD"):
        call_command("bootstrap_initial_tenant")
    assert Tenant.objects.count() == 0


def test_bootstrap_rejects_invalid_input_without_writing() -> None:
    with pytest.raises(BootstrapError, match="IANA timezone"):
        bootstrap_initial(_request(tenant_timezone="Not/AZone"))
    with pytest.raises(BootstrapError, match="different email"):
        bootstrap_initial(_request(owner_email=PLATFORM_EMAIL))
    with pytest.raises(BootstrapError, match="at least 12"):
        bootstrap_initial(_request(owner_password="short"))
    assert User.objects.count() == 0
    assert Tenant.objects.count() == 0
    assert not AuditLog.objects.filter(action=COMPLETED_ACTION).exists()


def test_bootstrap_refuses_an_email_or_slug_that_already_exists() -> None:
    make_user(PLATFORM_EMAIL)
    with pytest.raises(BootstrapError, match="platform administrator email"):
        bootstrap_initial(_request())
    assert Tenant.objects.count() == 0

    make_tenant(TENANT_SLUG)
    with pytest.raises(BootstrapError, match="slug"):
        bootstrap_initial(_request(platform_email="other-platform@ameen.test"))
    assert User.objects.filter(email="other-platform@ameen.test").count() == 0


def test_bootstrap_creates_separate_identities_and_then_refuses(
    api: SessionClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = StringIO()
    _set_env(monkeypatch)
    call_command("bootstrap_initial_tenant", stdout=stdout)
    printed = stdout.getvalue()
    assert PLATFORM_PASSWORD not in printed
    assert PASSWORD not in printed
    assert "password" not in printed.lower()

    platform = User.objects.get(email=PLATFORM_EMAIL)
    owner = User.objects.get(email=OWNER_EMAIL)
    tenant = Tenant.objects.get(slug=TENANT_SLUG)
    assert platform.id != owner.id
    assert platform.status == "ACTIVE"
    assert owner.status == "ACTIVE"
    assert tenant.status == "ACTIVE"
    assert tenant.business_type == "RETAIL"
    assert tenant.timezone == "Africa/Mogadishu"
    assert tenant.country_code == "SO"
    assert not TenantMembership.objects.filter(user=platform).exists()

    membership = TenantMembership.objects.get(user=owner, tenant=tenant)
    assert membership.is_owner is True
    assert membership.status == "ACTIVE"
    assignment = TenantUserRole.objects.get(membership=membership)
    assert assignment.role.name == "Business Owner"
    assert assignment.role.tenant_id is None
    assert assignment.role.is_system_role is True
    assert assignment.branch_id is None
    assert assignment.applies_to_all_branches is True
    assert not Role.objects.filter(tenant__isnull=False).exists()

    stored = _audit_text()
    assert PLATFORM_PASSWORD not in stored
    assert PASSWORD not in stored
    assert "password_hash" not in stored
    assert AuditLog.objects.filter(action=COMPLETED_ACTION, tenant=tenant).count() == 1
    assert AuditLog.objects.filter(action="bootstrap.platform_admin_created").count() == 1
    assert AuditLog.objects.filter(action="bootstrap.owner_created", tenant=tenant).count() == 1

    other = make_tenant("market")
    hidden = make_user("hidden@market.test")
    grant(hidden, other, "Cashier")

    assert login(api, OWNER_EMAIL).status_code == 200
    me = api.client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["tenant"]["id"] == str(tenant.id)
    assert me.json()["data"]["roles"] == ["Business Owner"]
    assert all(not code.startswith("platform.") for code in me.json()["data"]["permissions"])
    assert "users.view" in me.json()["data"]["permissions"]

    listing = api.client.get("/api/v1/users")
    assert listing.status_code == 200
    assert [item["email"] for item in listing.json()["data"]] == [OWNER_EMAIL]
    hidden_read = api.client.get(f"/api/v1/users/{hidden.id}")
    assert hidden_read.status_code == 404
    platform_read = api.client.get(f"/api/v1/users/{platform.id}")
    assert platform_read.status_code == 404

    api.use_tenant(other.id)
    denied = api.client.get("/api/v1/users")
    assert denied.status_code == 403
    assert denied.json()["errors"][0]["code"] == "TENANT_ACCESS_DENIED"

    platform_api = _client()
    assert login(platform_api, PLATFORM_EMAIL, PLATFORM_PASSWORD).status_code == 200
    platform_me = platform_api.client.get("/api/v1/auth/me")
    assert platform_me.status_code == 200
    assert platform_me.json()["data"]["tenant"] is None
    assert platform_me.json()["data"]["memberships"] == []
    assert platform_me.json()["data"]["permissions"] == []
    platform_api.use_tenant(tenant.id)
    platform_denied = platform_api.client.get("/api/v1/users")
    assert platform_denied.status_code == 403
    assert platform_denied.json()["errors"][0]["code"] == "TENANT_ACCESS_DENIED"

    missing = api.client.get("/api/v1/bootstrap")
    assert missing.status_code == 404
    tenants = api.client.post("/api/v1/tenants", {}, format="json")
    assert tenants.status_code == 404

    before_users = User.objects.count()
    before_tenants = Tenant.objects.count()
    _set_env(monkeypatch)
    with pytest.raises(CommandError, match="does not run again"):
        call_command("bootstrap_initial_tenant", stdout=StringIO())
    assert User.objects.count() == before_users
    assert Tenant.objects.count() == before_tenants
    assert AuditLog.objects.filter(action=COMPLETED_ACTION).count() == 1


def _request(**overrides: str) -> BootstrapRequest:
    payload = {
        "platform_email": PLATFORM_EMAIL,
        "platform_password": PLATFORM_PASSWORD,
        "platform_first_name": "Platform",
        "platform_last_name": "Admin",
        "tenant_name": "Harbor",
        "tenant_slug": TENANT_SLUG,
        "tenant_timezone": "Africa/Mogadishu",
        "tenant_country_code": "SO",
        "owner_email": OWNER_EMAIL,
        "owner_password": PASSWORD,
        "owner_first_name": "Amina",
        "owner_last_name": "Hassan",
    }
    payload.update(overrides)
    return BootstrapRequest(**payload)


def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(CONFIRM_ENV, CONFIRM_VALUE)
    monkeypatch.setenv("AMEEN_BOOTSTRAP_PLATFORM_EMAIL", PLATFORM_EMAIL)
    monkeypatch.setenv("AMEEN_BOOTSTRAP_PLATFORM_PASSWORD", PLATFORM_PASSWORD)
    monkeypatch.setenv("AMEEN_BOOTSTRAP_PLATFORM_FIRST_NAME", "Platform")
    monkeypatch.setenv("AMEEN_BOOTSTRAP_PLATFORM_LAST_NAME", "Admin")
    monkeypatch.setenv("AMEEN_BOOTSTRAP_TENANT_NAME", "Harbor")
    monkeypatch.setenv("AMEEN_BOOTSTRAP_TENANT_SLUG", TENANT_SLUG)
    monkeypatch.setenv("AMEEN_BOOTSTRAP_TENANT_TIMEZONE", "Africa/Mogadishu")
    monkeypatch.setenv("AMEEN_BOOTSTRAP_TENANT_COUNTRY", "so")
    monkeypatch.setenv("AMEEN_BOOTSTRAP_OWNER_EMAIL", OWNER_EMAIL)
    monkeypatch.setenv("AMEEN_BOOTSTRAP_OWNER_PASSWORD", PASSWORD)
    monkeypatch.setenv("AMEEN_BOOTSTRAP_OWNER_FIRST_NAME", "Amina")
    monkeypatch.setenv("AMEEN_BOOTSTRAP_OWNER_LAST_NAME", "Hassan")


def _client() -> SessionClient:
    client = APIClient(enforce_csrf_checks=True)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    return SessionClient(client, response.cookies["csrftoken"].value)


def _audit_text() -> str:
    chunks: list[str] = []
    for row in AuditLog.objects.all():
        chunks.append(json.dumps(row.old_values, default=str))
        chunks.append(json.dumps(row.new_values, default=str))
    return "\n".join(chunks)
