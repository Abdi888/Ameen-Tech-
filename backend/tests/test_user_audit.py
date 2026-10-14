"""Persisted audit rows for tenant user activation, deactivation, and role assignment."""

from __future__ import annotations

from typing import cast

import pytest

from modules.access.models import Role, TenantMembership
from modules.audit.models import AuditLog
from modules.identity.models import User
from modules.tenants.models import Tenant
from tests.support import SessionClient, grant, login, make_tenant, make_user

pytestmark = pytest.mark.django_db

_PASSWORD = "replacement-password"


def test_password_setup_persists_user_activated(
    api: SessionClient,
    mail: list[tuple[str, str, str]],
) -> None:
    tenant, admin = _admin(api)
    invited = _invite(api, mail, role_name="Cashier", email="new-cashier@harbor.test")
    confirmed = api.client.post(
        "/api/v1/auth/password/reset/confirm",
        {"token": mail[-1][2], "password": _PASSWORD},
        format="json",
    )
    assert confirmed.status_code == 200
    membership = TenantMembership.objects.get(tenant=tenant, user=invited)
    assert membership.status == "ACTIVE"
    row = AuditLog.objects.get(action="user.activated", entity_id=membership.id)
    assert row.tenant_id == tenant.id
    assert row.user_id == invited.id
    assert row.user_id != admin.id
    assert row.entity_type == "tenant_membership"
    assert row.old_values is None
    recorded = cast(dict[str, object], row.new_values)
    assert recorded["result"] == "success"
    assert _PASSWORD not in str(recorded)
    assert mail[-1][2] not in str(recorded)
    assert row.created_at is not None


def test_deactivation_and_reactivation_persist_separate_audit_rows(api: SessionClient) -> None:
    tenant, admin = _admin(api)
    staff = make_user("staff@harbor.test")
    membership = grant(staff, tenant, "Cashier")

    deactivated = api.client.post(f"/api/v1/users/{staff.id}/deactivate", {}, format="json")
    assert deactivated.status_code == 200
    membership.refresh_from_db()
    assert membership.status == "SUSPENDED"
    suspended = AuditLog.objects.get(action="user.deactivated", entity_id=membership.id)
    assert suspended.tenant_id == tenant.id
    assert suspended.user_id == admin.id
    assert suspended.entity_type == "tenant_membership"
    assert suspended.old_values is None
    assert cast(dict[str, object], suspended.new_values)["result"] == "success"

    activated = api.client.post(f"/api/v1/users/{staff.id}/activate", {}, format="json")
    assert activated.status_code == 200
    membership.refresh_from_db()
    assert membership.status == "ACTIVE"
    restored = AuditLog.objects.get(action="user.activated", entity_id=membership.id)
    assert restored.tenant_id == tenant.id
    assert restored.user_id == admin.id
    assert restored.entity_type == "tenant_membership"
    assert restored.id != suspended.id
    assert cast(dict[str, object], restored.new_values)["result"] == "success"
    assert AuditLog.objects.filter(action="user.deactivated", entity_id=membership.id).count() == 1


def test_role_assignment_persists_previous_and_current_roles(api: SessionClient) -> None:
    tenant, admin = _admin(api)
    staff = make_user("staff@harbor.test")
    membership = grant(staff, tenant, "Cashier")
    viewer = Role.objects.get(name="Viewer", tenant__isnull=True)

    assigned = api.client.post(
        f"/api/v1/users/{staff.id}/roles",
        {"role_ids": [str(viewer.id)]},
        format="json",
    )
    assert assigned.status_code == 200
    row = AuditLog.objects.get(action="role.assigned", entity_id=membership.id)
    assert row.tenant_id == tenant.id
    assert row.user_id == admin.id
    assert row.entity_type == "tenant_membership"
    assert row.old_values == {"roles": ["Cashier"]}
    recorded = cast(dict[str, object], row.new_values)
    assert recorded["result"] == "success"
    assert recorded["roles"] == ["Viewer"]
    assert row.created_at is not None


def test_rejected_owner_changes_do_not_persist_activation_or_role_audit(
    api: SessionClient,
) -> None:
    tenant, _admin_user = _admin(api)
    owner = make_user("owner@harbor.test")
    staff = make_user("staff@harbor.test")
    owner_membership = grant(owner, tenant, "Business Owner", is_owner=True)
    staff_membership = grant(staff, tenant, "Cashier")
    owner_role = Role.objects.get(name="Business Owner", tenant__isnull=True)
    viewer = Role.objects.get(name="Viewer", tenant__isnull=True)

    assigned = api.client.post(
        f"/api/v1/users/{staff.id}/roles",
        {"role_ids": [str(owner_role.id)]},
        format="json",
    )
    assert assigned.status_code == 403
    removed = api.client.post(
        f"/api/v1/users/{owner.id}/roles",
        {"role_ids": [str(viewer.id)]},
        format="json",
    )
    assert removed.status_code == 403
    deactivated = api.client.post(f"/api/v1/users/{owner.id}/deactivate", {}, format="json")
    assert deactivated.status_code == 403

    assert not AuditLog.objects.filter(
        action="role.assigned",
        entity_id__in=[owner_membership.id, staff_membership.id],
    ).exists()
    assert not AuditLog.objects.filter(
        action="user.deactivated",
        entity_id=owner_membership.id,
    ).exists()
    assert not AuditLog.objects.filter(
        action="user.activated",
        entity_id=owner_membership.id,
    ).exists()


def _admin(api: SessionClient) -> tuple[Tenant, User]:
    tenant = make_tenant("harbor")
    admin = make_user("admin@harbor.test")
    grant(admin, tenant, "Administrator")
    assert login(api, admin.email, tenant=tenant).status_code == 200
    return tenant, admin


def _invite(
    api: SessionClient,
    mail: list[tuple[str, str, str]],
    *,
    role_name: str,
    email: str,
) -> User:
    role_id = str(Role.objects.get(name=role_name, tenant__isnull=True).id)
    created = api.client.post(
        "/api/v1/users",
        {
            "email": email,
            "first_name": "New",
            "last_name": "Member",
            "role_id": role_id,
        },
        format="json",
    )
    assert created.status_code == 201
    assert mail[-1][0] == "invite"
    return User.objects.get(email=email)
