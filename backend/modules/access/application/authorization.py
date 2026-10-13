"""Permission checks. Role names are not a substitute for a Document 07 key."""

from __future__ import annotations

import uuid

from modules.access.domain.catalog import ALL_CODES, decide
from modules.access.models import Permission, TenantUserRole


def granted_permission_codes(
    *,
    membership_id: uuid.UUID,
    branch_id: uuid.UUID | None,
) -> set[str]:
    role_ids: list[uuid.UUID] = []
    rows = TenantUserRole.objects.filter(membership_id=membership_id).values_list(
        "role_id",
        "branch_id",
        "applies_to_all_branches",
    )
    for role_id, assigned_branch, all_branches in rows:
        if branch_id is None:
            if all_branches:
                role_ids.append(role_id)
        elif all_branches or assigned_branch == branch_id:
            role_ids.append(role_id)
    if not role_ids:
        return set()
    found = set(
        Permission.objects.filter(grants__role_id__in=role_ids).values_list("code", flat=True)
    )
    return found & ALL_CODES


def authorize(
    *,
    membership_id: uuid.UUID | None,
    permission: str,
    branch_id: uuid.UUID | None = None,
) -> bool:
    if membership_id is None:
        return False
    granted = granted_permission_codes(membership_id=membership_id, branch_id=branch_id)
    return decide(granted, permission) == "ALLOW"
