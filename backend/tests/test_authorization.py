from __future__ import annotations

import uuid
from typing import cast

import pytest

from modules.access.application.authorization import authorize
from modules.access.models import Role
from modules.audit.models import AuditLog
from modules.identity.models import User
from modules.tenants.models import Tenant
from tests.support import PASSWORD, SessionClient, grant, login, make_tenant, make_user

pytestmark = pytest.mark.django_db


def _admin(api: SessionClient, slug: str = "harbor") -> tuple[Tenant, User]:
    tenant = make_tenant(slug)
    admin = make_user(f"admin@{slug}.test")
    grant(admin, tenant, "Administrator")
    assert login(api, admin.email, tenant=tenant).status_code == 200
    return tenant, admin


def test_cashier_cannot_invite_or_assign_roles(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    cashier = make_user("cashier@harbor.test")
    grant(cashier, tenant, "Cashier")
    assert login(api, cashier.email, tenant=tenant).status_code == 200
    role_id = str(Role.objects.get(name="Viewer", tenant__isnull=True).id)

    invite = api.client.post(
        "/api/v1/users",
        {
            "email": "new@harbor.test",
            "first_name": "New",
            "last_name": "Person",
            "role_id": role_id,
        },
        format="json",
    )
    assert invite.status_code == 403
    assert invite.json()["errors"][0]["code"] == "PERMISSION_DENIED"
    assert "users.create" not in invite.content.decode()
    denied = AuditLog.objects.filter(action="permission.denied", user=cashier).get()
    recorded = cast(dict[str, object], denied.new_values)
    assert recorded["permission"] == "users.create"

    assign = api.client.post(
        f"/api/v1/users/{cashier.id}/roles",
        {"role_ids": [role_id]},
        format="json",
    )
    assert assign.status_code == 403
    assert "users.assign_roles" not in assign.content.decode()


def test_administrator_cannot_assign_or_remove_business_owner(api: SessionClient) -> None:
    tenant, admin = _admin(api)
    owner = make_user("owner@harbor.test")
    grant(owner, tenant, "Business Owner", is_owner=True)
    owner_role = str(Role.objects.get(name="Business Owner", tenant__isnull=True).id)
    viewer_role = str(Role.objects.get(name="Viewer", tenant__isnull=True).id)

    assigned = api.client.post(
        f"/api/v1/users/{admin.id}/roles",
        {"role_ids": [owner_role]},
        format="json",
    )
    assert assigned.status_code == 403
    assert assigned.json()["errors"][0]["message"] == "This role cannot be assigned."

    removed = api.client.post(
        f"/api/v1/users/{owner.id}/roles",
        {"role_ids": [viewer_role]},
        format="json",
    )
    assert removed.status_code == 403
    assert removed.json()["errors"][0]["message"] == "This role cannot be removed."
    assert "is_owner" not in removed.content.decode()

    kept = api.client.post(
        f"/api/v1/users/{owner.id}/roles",
        {"role_ids": [owner_role, viewer_role]},
        format="json",
    )
    assert kept.status_code == 200
    names = {item["name"] for item in kept.json()["data"]["roles"]}
    assert names == {"Business Owner", "Viewer"}

    deactivated = api.client.post(f"/api/v1/users/{owner.id}/deactivate", {}, format="json")
    assert deactivated.status_code == 403


def test_invite_rejects_owner_role_password_and_is_owner(
    api: SessionClient,
    mail: list[tuple[str, str, str]],
) -> None:
    tenant, _admin_user = _admin(api)
    owner_role = str(Role.objects.get(name="Business Owner", tenant__isnull=True).id)
    cashier_role = str(Role.objects.get(name="Cashier", tenant__isnull=True).id)

    owner_invite = api.client.post(
        "/api/v1/users",
        {
            "email": "second-owner@harbor.test",
            "first_name": "Second",
            "last_name": "Owner",
            "role_id": owner_role,
        },
        format="json",
    )
    assert owner_invite.status_code == 403

    flagged = api.client.post(
        "/api/v1/users",
        {
            "email": "flagged@harbor.test",
            "first_name": "Flag",
            "last_name": "User",
            "role_id": cashier_role,
            "is_owner": True,
            "password": PASSWORD,
        },
        format="json",
    )
    assert flagged.status_code == 422
    assert flagged.json()["errors"][0]["field"] in {"is_owner", "password"}

    created = api.client.post(
        "/api/v1/users",
        {
            "email": "new-cashier@harbor.test",
            "first_name": "New",
            "last_name": "Cashier",
            "role_id": cashier_role,
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.json()["data"]["status"] == "INVITED"
    assert "is_owner" not in created.json()["data"]
    assert mail[0][0] == "invite"
    assert mail[0][2] not in created.content.decode()
    assert AuditLog.objects.filter(action="user.invited", tenant=tenant).exists()


def test_branch_scope_does_not_grant_tenant_wide_access() -> None:
    tenant = make_tenant("harbor")
    user = make_user("scoped@harbor.test")
    branch_id = uuid.uuid4()
    other_branch = uuid.uuid4()
    membership = grant(
        user,
        tenant,
        "Administrator",
        branch_id=branch_id,
        all_branches=False,
    )
    assert authorize(membership_id=membership.id, permission="users.view", branch_id=None) is False
    assert (
        authorize(membership_id=membership.id, permission="users.view", branch_id=branch_id) is True
    )
    assert (
        authorize(membership_id=membership.id, permission="users.view", branch_id=other_branch)
        is False
    )
    assert (
        authorize(membership_id=membership.id, permission="users.create", branch_id=branch_id)
        is True
    )
    assert authorize(membership_id=None, permission="users.view") is False


def test_get_permissions_is_not_a_product_endpoint(api: SessionClient) -> None:
    _admin(api)
    response = api.client.get("/api/v1/permissions")
    assert response.status_code == 404
    assert response.json()["errors"][0]["code"] == "RESOURCE_NOT_FOUND"


def test_roles_require_users_view_and_do_not_add_a_role_key(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    viewer = make_user("viewer@harbor.test")
    grant(viewer, tenant, "Viewer")
    assert login(api, viewer.email, tenant=tenant).status_code == 200
    denied = api.client.get("/api/v1/roles")
    assert denied.status_code == 403

    admin = make_user("admin@harbor.test")
    grant(admin, tenant, "Administrator")
    assert login(api, admin.email, tenant=tenant).status_code == 200
    listed = api.client.get("/api/v1/roles")
    assert listed.status_code == 200
    payload = listed.json()["data"]
    names = [item["name"] for item in payload]
    assert names[0] == "Business Owner"
    assert "Salesperson" not in names
    assert len(names) == 8
    assert all(set(item) == {"id", "name", "description", "is_system_role"} for item in payload)
