"""Write an audit row. Callers keep this inside the business transaction."""

from __future__ import annotations

import uuid
from typing import Any

from modules.audit.models import AuditLog

_HIDDEN = ("password", "token", "secret", "pan")


def record_audit(
    *,
    action: str,
    entity_type: str,
    result: str,
    tenant_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    entity_id: uuid.UUID | None = None,
    old_values: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    ip: str | None = None,
    user_agent: str = "",
) -> None:
    new_values: dict[str, Any] = {"result": result}
    if metadata:
        new_values.update(_scrub(metadata))
    AuditLog.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=_scrub(old_values) if old_values else None,
        new_values=new_values,
        ip=ip,
        user_agent=user_agent[:512],
    )


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if _hidden(str(key)):
                cleaned[str(key)] = "[redacted]"
            else:
                cleaned[str(key)] = _scrub(item)
        return cleaned
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def _hidden(key: str) -> bool:
    normalized = key.lower()
    return any(part in normalized for part in _HIDDEN)
