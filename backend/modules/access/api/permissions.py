"""Fail closed unless the view names a Document 07 permission."""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from modules.access.application.authorization import authorize
from modules.audit.application import record_audit
from modules.identity.domain.actor import Actor
from shared.api.clients import request_ip, request_user_agent
from shared.exceptions import ApiError


class DenyByDefault(BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user
        if not isinstance(user, Actor):
            return False
        code = _required_permission(view, request.method or "")
        ip = request_ip(request._request)
        user_agent = request_user_agent(request._request)
        if not code:
            _audit_denied(user, ip, user_agent, permission="")
            raise ApiError(
                "PERMISSION_DENIED",
                "You do not have permission to perform this action.",
            )
        if user.tenant_id is None or user.membership_id is None:
            record_audit(
                action="tenant.access_denied",
                entity_type="tenant",
                result="failure",
                user_id=user.id,
                ip=ip,
                user_agent=user_agent,
            )
            raise ApiError("TENANT_ACCESS_DENIED", "You do not have access to this tenant.")
        if not authorize(membership_id=user.membership_id, permission=code):
            _audit_denied(user, ip, user_agent, permission=code)
            raise ApiError(
                "PERMISSION_DENIED",
                "You do not have permission to perform this action.",
            )
        return True


def _required_permission(view: Any, method: str) -> str | None:
    mapping = getattr(view, "required_permissions", None)
    if isinstance(mapping, dict):
        code = mapping.get(method)
        return code if isinstance(code, str) else None
    code = getattr(view, "required_permission", None)
    return code if isinstance(code, str) else None


def _audit_denied(user: Actor, ip: str | None, user_agent: str, *, permission: str) -> None:
    metadata = {"permission": permission} if permission else None
    record_audit(
        action="permission.denied",
        entity_type="permission",
        result="failure",
        tenant_id=user.tenant_id,
        user_id=user.id,
        metadata=metadata,
        ip=ip,
        user_agent=user_agent,
    )
