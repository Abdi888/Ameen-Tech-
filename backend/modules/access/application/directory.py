"""Tenant user and role assignment. Business Owner cannot be assigned or removed here."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from modules.access.application.queries import membership_in_tenant
from modules.access.domain.catalog import BUSINESS_OWNER, PROTECTED_ROLE_NAMES, ROLE_ORDER
from modules.access.models import Role, TenantMembership, TenantUserRole
from modules.audit.application import record_audit
from modules.identity.application.accounts import prepare_invited_user
from shared.exceptions import ApiError

_ROLE_INDEX = {name: index for index, name in enumerate(ROLE_ORDER)}


@dataclass(frozen=True)
class InviteResult:
    public: dict[str, object]
    email: str
    token: str | None
    token_purpose: str | None


def invite_member(
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    email: str,
    first_name: str,
    last_name: str,
    phone: str,
    role_id: uuid.UUID,
    ip: str | None,
    user_agent: str,
) -> InviteResult:
    role = _assignable_role(role_id)
    with transaction.atomic():
        prepared = prepare_invited_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )
        _reject_existing_member(tenant_id=tenant_id, user_id=prepared.user.id)
        status = "ACTIVE" if prepared.user.status == "ACTIVE" else "INVITED"
        membership = TenantMembership.objects.create(
            tenant_id=tenant_id,
            user=prepared.user,
            status=status,
            is_owner=False,
            joined_at=timezone.now() if status == "ACTIVE" else None,
        )
        TenantUserRole.objects.create(
            membership=membership,
            role=role,
            applies_to_all_branches=True,
        )
        record_audit(
            action="user.invited",
            entity_type="tenant_membership",
            entity_id=membership.id,
            result="success",
            tenant_id=tenant_id,
            user_id=actor_id,
            metadata={"email": prepared.user.email, "role": role.name},
            ip=ip,
            user_agent=user_agent,
        )
        return InviteResult(
            public=_member_payload(membership),
            email=prepared.user.email,
            token=prepared.token,
            token_purpose=prepared.token_purpose,
        )


def list_members(
    *,
    tenant_id: uuid.UUID,
    page: int,
    page_size: int,
    order_by: str,
) -> tuple[list[dict[str, object]], int]:
    queryset = (
        TenantMembership.objects.select_related("user")
        .filter(tenant_id=tenant_id)
        .exclude(status="REMOVED")
    )
    total = queryset.count()
    ordering = order_by or "created_at"
    rows = list(queryset.order_by(ordering, "id")[(page - 1) * page_size : page * page_size])
    return [_member_payload(row) for row in rows], total


def get_member(*, tenant_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, object]:
    membership = membership_in_tenant(tenant_id=tenant_id, user_id=user_id)
    if membership is None:
        raise ApiError("RESOURCE_NOT_FOUND", "Not found.")
    return _member_payload(membership)


def update_member(
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    actor_id: uuid.UUID,
    changes: dict[str, str],
    ip: str | None,
    user_agent: str,
) -> dict[str, object]:
    if not changes:
        raise ApiError("VALIDATION_ERROR", "No fields to update.")
    with transaction.atomic():
        membership = _locked_membership(tenant_id=tenant_id, user_id=user_id)
        user = membership.user
        for field, value in changes.items():
            setattr(user, field, value)
        user.save(update_fields=[*changes.keys(), "updated_at"])
        record_audit(
            action="user.updated",
            entity_type="user",
            entity_id=user.id,
            result="success",
            tenant_id=tenant_id,
            user_id=actor_id,
            ip=ip,
            user_agent=user_agent,
        )
        return _member_payload(membership)


def set_member_active(
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    actor_id: uuid.UUID,
    active: bool,
    ip: str | None,
    user_agent: str,
) -> dict[str, object]:
    with transaction.atomic():
        membership = _locked_membership(tenant_id=tenant_id, user_id=user_id)
        _reject_protected_member(membership)
        if active:
            if membership.status != "SUSPENDED":
                raise ApiError("INVALID_STATUS_TRANSITION", "This member cannot be activated.")
            membership.status = "ACTIVE"
            action = "user.activated"
        else:
            if membership.status != "ACTIVE":
                raise ApiError("INVALID_STATUS_TRANSITION", "This member cannot be deactivated.")
            membership.status = "SUSPENDED"
            action = "user.deactivated"
        membership.save(update_fields=["status", "updated_at"])
        record_audit(
            action=action,
            entity_type="tenant_membership",
            entity_id=membership.id,
            result="success",
            tenant_id=tenant_id,
            user_id=actor_id,
            ip=ip,
            user_agent=user_agent,
        )
        return _member_payload(membership)


def list_roles(*, page: int, page_size: int) -> tuple[list[dict[str, object]], int]:
    roles = list(Role.objects.filter(tenant__isnull=True, is_system_role=True))
    roles.sort(key=lambda role: _ROLE_INDEX.get(role.name, len(ROLE_ORDER)))
    total = len(roles)
    window = roles[(page - 1) * page_size : page * page_size]
    return [_role_payload(role) for role in window], total


def replace_roles(
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    actor_id: uuid.UUID,
    role_ids: list[uuid.UUID],
    ip: str | None,
    user_agent: str,
) -> dict[str, object]:
    unique_ids = list(dict.fromkeys(role_ids))
    with transaction.atomic():
        membership = _locked_membership(tenant_id=tenant_id, user_id=user_id)
        requested = list(
            Role.objects.filter(id__in=unique_ids, tenant__isnull=True, is_system_role=True)
        )
        if len(requested) != len(unique_ids):
            raise ApiError("RESOURCE_NOT_FOUND", "Not found.")
        owner = Role.objects.get(tenant__isnull=True, name=BUSINESS_OWNER, is_system_role=True)
        has_owner = TenantUserRole.objects.filter(membership=membership, role=owner).exists()
        wants_owner = any(role.id == owner.id for role in requested)
        if has_owner != wants_owner:
            message = (
                "This role cannot be removed." if has_owner else "This role cannot be assigned."
            )
            raise ApiError("PERMISSION_DENIED", message)
        previous = sorted(
            TenantUserRole.objects.filter(membership=membership).values_list(
                "role__name", flat=True
            )
        )
        TenantUserRole.objects.filter(membership=membership).exclude(role=owner).delete()
        for role in requested:
            if role.id == owner.id:
                continue
            TenantUserRole.objects.create(
                membership=membership,
                role=role,
                applies_to_all_branches=True,
            )
        current = sorted(
            TenantUserRole.objects.filter(membership=membership).values_list(
                "role__name", flat=True
            )
        )
        record_audit(
            action="role.assigned",
            entity_type="tenant_membership",
            entity_id=membership.id,
            result="success",
            tenant_id=tenant_id,
            user_id=actor_id,
            old_values={"roles": previous},
            metadata={"roles": current},
            ip=ip,
            user_agent=user_agent,
        )
        return _member_payload(membership)


def _assignable_role(role_id: uuid.UUID) -> Role:
    role = Role.objects.filter(id=role_id, tenant__isnull=True, is_system_role=True).first()
    if role is None:
        raise ApiError("RESOURCE_NOT_FOUND", "Not found.")
    if role.name in PROTECTED_ROLE_NAMES:
        raise ApiError("PERMISSION_DENIED", "This role cannot be assigned.")
    return role


def _reject_existing_member(*, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
    existing = TenantMembership.objects.filter(tenant_id=tenant_id, user_id=user_id).first()
    if existing is None:
        return
    if existing.status == "REMOVED":
        raise ApiError("RESOURCE_CONFLICT", "This user cannot be invited.")
    raise ApiError("RESOURCE_ALREADY_EXISTS", "This user is already a member.")


def _locked_membership(*, tenant_id: uuid.UUID, user_id: uuid.UUID) -> TenantMembership:
    membership = (
        TenantMembership.objects.select_for_update()
        .select_related("user", "tenant")
        .filter(tenant_id=tenant_id, user_id=user_id)
        .exclude(status="REMOVED")
        .first()
    )
    if membership is None:
        raise ApiError("RESOURCE_NOT_FOUND", "Not found.")
    return membership


def _reject_protected_member(membership: TenantMembership) -> None:
    if membership.is_owner:
        raise ApiError("PERMISSION_DENIED", "This member cannot be changed.")
    if TenantUserRole.objects.filter(
        membership=membership,
        role__name=BUSINESS_OWNER,
        role__tenant__isnull=True,
    ).exists():
        raise ApiError("PERMISSION_DENIED", "This member cannot be changed.")


def _member_payload(membership: TenantMembership) -> dict[str, object]:
    roles = [
        {"id": str(assignment.role_id), "name": assignment.role.name}
        for assignment in TenantUserRole.objects.select_related("role").filter(
            membership=membership
        )
    ]
    roles.sort(key=lambda item: _ROLE_INDEX.get(str(item["name"]), len(ROLE_ORDER)))
    user = membership.user
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "status": user.status,
        "membership_status": membership.status,
        "roles": roles,
    }


def _role_payload(role: Role) -> dict[str, object]:
    return {
        "id": str(role.id),
        "name": role.name,
        "description": role.description,
        "is_system_role": role.is_system_role,
    }
