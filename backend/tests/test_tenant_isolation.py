from __future__ import annotations

import uuid

import pytest

from modules.identity.models import Session
from tests.support import SessionClient, grant, login, make_tenant, make_user

pytestmark = pytest.mark.django_db


def test_a_member_cannot_read_another_tenants_user(api: SessionClient) -> None:
    tenant_a = make_tenant("harbor")
    tenant_b = make_tenant("market")
    admin = make_user("admin@harbor.test")
    other = make_user("other@market.test")
    grant(admin, tenant_a, "Administrator")
    grant(other, tenant_b, "Administrator")
    assert login(api, admin.email, tenant=tenant_a).status_code == 200

    hidden = api.client.get(f"/api/v1/users/{other.id}")
    assert hidden.status_code == 404
    assert hidden.json()["errors"][0]["code"] == "RESOURCE_NOT_FOUND"
    assert other.email not in hidden.content.decode()

    listing = api.client.get("/api/v1/users")
    assert listing.status_code == 200
    emails = [item["email"] for item in listing.json()["data"]]
    assert emails == [admin.email]

    api.use_tenant(tenant_b.id)
    denied = api.client.get("/api/v1/users")
    assert denied.status_code == 403
    assert denied.json()["errors"][0]["code"] == "TENANT_ACCESS_DENIED"
    assert Session.objects.get(user=admin).tenant_id == tenant_a.id


def test_suspended_tenant_and_membership_cannot_operate(api: SessionClient) -> None:
    suspended = make_tenant("closed", status="SUSPENDED")
    user = make_user("owner@closed.test")
    grant(user, suspended, "Administrator")
    blocked = login(api, user.email, tenant=suspended)
    assert blocked.status_code == 403
    assert blocked.json()["errors"][0]["code"] == "TENANT_ACCESS_DENIED"
    assert "ameen_session" not in blocked.cookies

    tenant = make_tenant("harbor")
    cashier = make_user("cashier@harbor.test")
    membership = grant(cashier, tenant, "Cashier")
    assert login(api, cashier.email, tenant=tenant).status_code == 200
    membership.status = "SUSPENDED"
    membership.save(update_fields=["status", "updated_at"])
    hinted = api.client.get("/api/v1/auth/me")
    assert hinted.status_code == 403
    assert hinted.json()["errors"][0]["code"] == "TENANT_ACCESS_DENIED"
    api.use_tenant(None)
    me = api.client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["tenant"] is None
    assert me.json()["data"]["permissions"] == []
    denied = api.client.get("/api/v1/users")
    assert denied.status_code == 403
    assert denied.json()["errors"][0]["code"] == "TENANT_ACCESS_DENIED"


def test_one_user_can_switch_tenants_without_seeing_both(api: SessionClient) -> None:
    first = make_tenant("harbor")
    second = make_tenant("market")
    user = make_user("admin@shared.test")
    colleague = make_user("colleague@market.test")
    grant(user, first, "Administrator")
    grant(user, second, "Administrator")
    grant(colleague, second, "Cashier")
    assert login(api, user.email).status_code == 200
    me = api.client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["tenant"] is None
    assert {item["tenant_name"] for item in me.json()["data"]["memberships"]} == {
        "harbor",
        "market",
    }

    api.use_tenant(second.id)
    market = {item["email"] for item in api.client.get("/api/v1/users").json()["data"]}
    assert market == {user.email, colleague.email}

    api.use_tenant(first.id)
    harbor = {item["email"] for item in api.client.get("/api/v1/users").json()["data"]}
    assert harbor == {user.email}


def test_unknown_tenant_hint_does_not_confirm_a_random_id(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    user = make_user("admin@harbor.test")
    grant(user, tenant, "Administrator")
    missing = uuid.uuid4()
    api.use_tenant(missing)
    response = login(api, user.email)
    assert response.status_code == 403
    assert str(missing) not in response.content.decode()
    assert response.json()["errors"][0]["code"] == "TENANT_ACCESS_DENIED"
