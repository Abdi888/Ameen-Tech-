"""Request-context permissions come from the proven membership, not the client."""

from __future__ import annotations

import uuid

import pytest
from django.http import HttpRequest

from modules.access.application.authorization import granted_permission_codes
from modules.access.domain.catalog import CASHIER_GRANTS
from shared.api.context import RequestContext, bind_actor, read_context
from tests.support import SessionClient, grant, login, make_tenant, make_user

pytestmark = pytest.mark.django_db


def test_proven_membership_permissions_are_copied_onto_the_request(
    api: SessionClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tenant = make_tenant("harbor")
    cashier = make_user("cashier@harbor.test")
    membership = grant(cashier, tenant, "Cashier")
    assert login(api, cashier.email, tenant=tenant).status_code == 200

    seen = _record_bound_contexts(monkeypatch)
    response = api.client.get("/api/v1/auth/me")

    assert response.status_code == 200
    context = seen[-1]
    assert context.tenant_id == str(tenant.id)
    assert context.permissions == CASHIER_GRANTS
    assert context.permissions == frozenset(
        granted_permission_codes(membership_id=membership.id, branch_id=None)
    )
    assert context.permissions == frozenset(response.json()["data"]["permissions"])
    assert "users.create" not in context.permissions


def test_client_cannot_supply_or_replace_context_permissions(
    api: SessionClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tenant = make_tenant("harbor")
    cashier = make_user("cashier@harbor.test")
    administrator = make_user("admin@harbor.test")
    grant(cashier, tenant, "Cashier")
    admin_membership = grant(administrator, tenant, "Administrator")
    assert login(api, cashier.email, tenant=tenant).status_code == 200
    seen = _record_bound_contexts(monkeypatch)

    listed = api.client.get(
        "/api/v1/auth/me",
        {"permissions": "users.create"},
        HTTP_X_PERMISSIONS="users.create",
        HTTP_PERMISSIONS="users.create",
    )
    assert listed.status_code == 200
    assert seen[-1].permissions == CASHIER_GRANTS
    assert "users.create" not in seen[-1].permissions

    posted = api.client.post(
        "/api/v1/users",
        {"permissions": ["users.create"], "email": "injected@harbor.test"},
        format="json",
        HTTP_X_PERMISSIONS="users.create",
    )
    assert posted.status_code == 403
    assert seen[-1].permissions == CASHIER_GRANTS

    assert login(api, administrator.email, tenant=tenant).status_code == 200
    narrowed = api.client.get(
        "/api/v1/auth/me",
        {"permissions": "dashboard.view"},
        HTTP_X_PERMISSIONS="dashboard.view",
    )
    assert narrowed.status_code == 200
    admin_permissions = frozenset(
        granted_permission_codes(membership_id=admin_membership.id, branch_id=None)
    )
    assert seen[-1].permissions == admin_permissions
    assert "users.create" in seen[-1].permissions
    assert seen[-1].permissions == frozenset(narrowed.json()["data"]["permissions"])


def test_permissions_stay_empty_without_a_proven_membership(
    api: SessionClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = make_tenant("harbor")
    second = make_tenant("market")
    user = make_user("both@harbor.test")
    grant(user, first, "Cashier")
    grant(user, second, "Administrator")
    assert login(api, user.email).status_code == 200
    seen = _record_bound_contexts(monkeypatch)

    response = api.client.get(
        "/api/v1/auth/me",
        {"permissions": "users.create"},
        HTTP_X_PERMISSIONS="users.create",
    )

    assert response.status_code == 200
    assert seen[-1].tenant_id is None
    assert seen[-1].permissions == frozenset()
    assert response.json()["data"]["permissions"] == []


def test_branch_scoped_grants_are_not_attached_while_branch_is_unset(
    api: SessionClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tenant = make_tenant("harbor")
    cashier = make_user("scoped@harbor.test")
    grant(cashier, tenant, "Cashier", branch_id=uuid.uuid4(), all_branches=False)
    assert login(api, cashier.email, tenant=tenant).status_code == 200
    seen = _record_bound_contexts(monkeypatch)

    response = api.client.get("/api/v1/auth/me", HTTP_X_PERMISSIONS="pos.view")

    assert response.status_code == 200
    assert seen[-1].permissions == frozenset()
    assert "pos.view" not in seen[-1].permissions
    assert response.json()["data"]["permissions"] == []


def _record_bound_contexts(monkeypatch: pytest.MonkeyPatch) -> list[RequestContext]:
    seen: list[RequestContext] = []
    original = bind_actor

    def spy(
        request: HttpRequest,
        *,
        user_id: str,
        proven_tenant_id: str | None,
        permissions: frozenset[str] | None = None,
    ) -> None:
        original(
            request,
            user_id=user_id,
            proven_tenant_id=proven_tenant_id,
            permissions=permissions,
        )
        current = read_context(request)
        assert current is not None
        seen.append(current)

    monkeypatch.setattr("modules.identity.application.sessions.bind_actor", spy)
    return seen
