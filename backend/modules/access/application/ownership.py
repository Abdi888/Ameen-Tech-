"""Initial Owner for operator bootstrap.

``users.assign_roles`` cannot assign or remove Business Owner. This function
is not that HTTP command and is not ownership transfer. It records the first
Owner while creating the first tenant. It assigns the seeded system role and
does not copy a tenant-owned role.
"""

from __future__ import annotations

import uuid

from django.utils import timezone

from modules.access.domain.catalog import BUSINESS_OWNER
from modules.access.models import Role, TenantMembership, TenantUserRole
from modules.audit.application import record_audit


class OwnerEstablishmentError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def business_owner_role_ready() -> bool:
    return _owner_role() is not None


def establish_initial_owner(*, tenant_id: uuid.UUID, user_id: uuid.UUID) -> TenantMembership:
    role = _owner_role()
    if role is None:
        raise OwnerEstablishmentError(
            "The Business Owner system role is not available. Apply migrations before bootstrap."
        )
    if TenantMembership.objects.filter(tenant_id=tenant_id, is_owner=True).exists():
        raise OwnerEstablishmentError("This tenant already has an Owner.")
    if TenantMembership.objects.filter(tenant_id=tenant_id, user_id=user_id).exists():
        raise OwnerEstablishmentError("This user is already a member of the tenant.")
    membership = TenantMembership.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        status="ACTIVE",
        is_owner=True,
        joined_at=timezone.now(),
    )
    TenantUserRole.objects.create(
        membership=membership,
        role=role,
        branch_id=None,
        applies_to_all_branches=True,
    )
    record_audit(
        action="role.assigned",
        entity_type="tenant_membership",
        entity_id=membership.id,
        result="success",
        tenant_id=tenant_id,
        metadata={"roles": [BUSINESS_OWNER], "source": "bootstrap"},
    )
    return membership


def _owner_role() -> Role | None:
    return Role.objects.filter(
        tenant__isnull=True,
        name=BUSINESS_OWNER,
        is_system_role=True,
    ).first()
