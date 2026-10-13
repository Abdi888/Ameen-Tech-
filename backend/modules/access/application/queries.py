"""Membership reads. This module does not write credentials."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.access.application.authorization import granted_permission_codes
from modules.access.domain.catalog import ROLE_ORDER
from modules.access.models import TenantMembership, TenantUserRole
from modules.identity.models import User

_ROLE_INDEX = {name: index for index, name in enumerate(ROLE_ORDER)}


@dataclass(frozen=True)
class TenantContext:
    membership_id: uuid.UUID
    tenant_id: uuid.UUID
    tenant_name: str


@dataclass(frozen=True)
class AccessResolution:
    context: TenantContext | None
    denied: bool
    hinted_tenant_id: uuid.UUID | None = None


def resolve_access(
    *,
    user_id: uuid.UUID,
    tenant_hint: str | None,
    session_tenant_id: uuid.UUID | None,
) -> AccessResolution:
    active = list(
        TenantMembership.objects.select_related("tenant").filter(
            user_id=user_id,
            status="ACTIVE",
            tenant__status="ACTIVE",
            user__status="ACTIVE",
        )
    )
    by_tenant = {row.tenant_id: row for row in active}
    if tenant_hint:
        hinted = uuid.UUID(tenant_hint)
        row = by_tenant.get(hinted)
        if row is None:
            return AccessResolution(context=None, denied=True, hinted_tenant_id=hinted)
        return AccessResolution(context=_context(row), denied=False)
    if session_tenant_id in by_tenant:
        return AccessResolution(context=_context(by_tenant[session_tenant_id]), denied=False)
    if len(by_tenant) == 1:
        return AccessResolution(context=_context(active[0]), denied=False)
    return AccessResolution(context=None, denied=False)


def profile_for(*, user_id: uuid.UUID, membership_id: uuid.UUID | None) -> dict[str, object]:
    user = User.objects.get(pk=user_id)
    memberships = list(
        TenantMembership.objects.select_related("tenant")
        .filter(user_id=user_id)
        .exclude(status="REMOVED")
        .order_by("created_at")
    )
    assignment_rows = TenantUserRole.objects.select_related("role").filter(
        membership_id__in=[row.id for row in memberships]
    )
    roles_by_membership: dict[uuid.UUID, list[dict[str, str]]] = {}
    for assignment in assignment_rows:
        roles_by_membership.setdefault(assignment.membership_id, []).append(
            {"id": str(assignment.role_id), "name": assignment.role.name}
        )
    for names in roles_by_membership.values():
        names.sort(key=lambda item: _ROLE_INDEX.get(item["name"], len(ROLE_ORDER)))

    current = next((row for row in memberships if row.id == membership_id), None)
    permissions: list[str] = []
    current_roles: list[str] = []
    tenant: dict[str, str] | None = None
    if current is not None and current.status == "ACTIVE" and current.tenant.status == "ACTIVE":
        tenant = {"id": str(current.tenant_id), "name": current.tenant.name}
        current_roles = [item["name"] for item in roles_by_membership.get(current.id, [])]
        permissions = sorted(granted_permission_codes(membership_id=current.id, branch_id=None))

    return {
        "user": _user_payload(user),
        "memberships": [
            {
                "id": str(row.id),
                "tenant_id": str(row.tenant_id),
                "tenant_name": row.tenant.name,
                "status": row.status,
                "roles": roles_by_membership.get(row.id, []),
            }
            for row in memberships
        ],
        "tenant": tenant,
        "roles": current_roles,
        "permissions": permissions,
    }


def membership_in_tenant(*, tenant_id: uuid.UUID, user_id: uuid.UUID) -> TenantMembership | None:
    return (
        TenantMembership.objects.select_related("user", "tenant")
        .filter(tenant_id=tenant_id, user_id=user_id)
        .exclude(status="REMOVED")
        .first()
    )


def activate_invited_memberships(
    *,
    user_id: uuid.UUID,
    ip: str | None,
    user_agent: str,
) -> None:
    from django.utils import timezone

    from modules.audit.application import record_audit

    now = timezone.now()
    rows = list(TenantMembership.objects.filter(user_id=user_id, status="INVITED"))
    for row in rows:
        row.status = "ACTIVE"
        if row.joined_at is None:
            row.joined_at = now
        row.save(update_fields=["status", "joined_at", "updated_at"])
        record_audit(
            action="user.activated",
            entity_type="tenant_membership",
            entity_id=row.id,
            result="success",
            tenant_id=row.tenant_id,
            user_id=user_id,
            ip=ip,
            user_agent=user_agent,
        )


def _context(row: TenantMembership) -> TenantContext:
    return TenantContext(
        membership_id=row.id,
        tenant_id=row.tenant_id,
        tenant_name=row.tenant.name,
    )


def _user_payload(user: User) -> dict[str, str]:
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "status": user.status,
    }
