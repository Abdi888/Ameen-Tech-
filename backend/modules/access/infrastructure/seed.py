"""Idempotent Document 07 catalogue. System roles are replaced from the code list."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from modules.access.domain.catalog import (
    ALL_CODES,
    ALL_PERMISSION_CODES,
    ROLE_DESCRIPTIONS,
    ROLE_GRANTS,
    ROLE_ORDER,
    danger_level,
    permission_module,
)


def sync_permission_catalog() -> None:
    from modules.access.models import Permission, Role, RolePermission

    with transaction.atomic():
        _sync(Permission, Role, RolePermission)


def sync_historical_catalog(apps: Any) -> None:
    permission = apps.get_model("access", "Permission")
    role = apps.get_model("access", "Role")
    grant = apps.get_model("access", "RolePermission")
    with transaction.atomic():
        _sync(permission, role, grant)


def _sync(permission_model: Any, role_model: Any, grant_model: Any) -> None:
    for code in ALL_PERMISSION_CODES:
        permission_model.objects.update_or_create(
            code=code,
            defaults={
                "name": code,
                "module": permission_module(code),
                "description": "",
                "is_system": True,
                "danger_level": danger_level(code),
            },
        )
    stale = permission_model.objects.exclude(code__in=ALL_CODES)
    grant_model.objects.filter(permission__in=stale).delete()
    stale.delete()

    for name in ROLE_ORDER:
        role = role_model.objects.filter(tenant__isnull=True, name=name).first()
        if role is None:
            role = role_model.objects.create(
                name=name,
                description=ROLE_DESCRIPTIONS[name],
                is_system_role=True,
            )
        else:
            role.description = ROLE_DESCRIPTIONS[name]
            role.is_system_role = True
            role.save(update_fields=["description", "is_system_role", "updated_at"])
        grant_model.objects.filter(role=role).delete()
        codes = ROLE_GRANTS[name]
        permissions = {row.code: row for row in permission_model.objects.filter(code__in=codes)}
        for code in codes:
            grant_model.objects.create(role=role, permission=permissions[code])
