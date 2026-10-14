"""Request identity that does not trust the client for tenant scope.

`X-Tenant-Id` is stored as a hint. `authorized_tenant_id` is the only value
later code may treat as the tenant, and it stays empty until membership is
proven. Permission codes are attached only after that proof, and only from
the server-side grant for the membership. Document 00 §9: request bodies
must not include `tenant_id`.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from django.http import HttpRequest

_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{1,64}$")
_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    user_id: str | None = None
    tenant_id: str | None = None
    tenant_hint: str | None = None
    permissions: frozenset[str] = frozenset()


def request_id_from_header(value: str | None) -> str:
    """Echo a safe client id, or generate one. Do not echo control characters."""
    if value is not None and _REQUEST_ID.fullmatch(value):
        return value
    return str(uuid.uuid4())


def tenant_hint_from_header(value: str | None) -> str | None:
    if value is not None and _UUID.fullmatch(value):
        return value.lower()
    return None


def authorized_tenant_id(
    *,
    user_id: str | None,
    tenant_hint: str | None,
    proven_tenant_id: str | None = None,
) -> str | None:
    """Return a tenant id only when the caller has already proven membership.

    `X-Tenant-Id` and a user id are not proof. `proven_tenant_id` is set only
    by the membership check.
    """
    del tenant_hint
    if user_id and proven_tenant_id:
        return proven_tenant_id
    return None


def bind_actor(
    request: HttpRequest,
    *,
    user_id: str,
    proven_tenant_id: str | None,
    permissions: frozenset[str] | None = None,
) -> None:
    """Attach the authenticated user, proven tenant, and server-side permissions.

    `permissions` is the grant set the caller already computed for a proven
    membership. This function does not read headers, query parameters, or bodies.
    """
    current = read_context(request)
    remember_context(
        request,
        RequestContext(
            request_id=current.request_id if current else request_id_from_header(None),
            user_id=user_id,
            tenant_id=authorized_tenant_id(
                user_id=user_id,
                tenant_hint=current.tenant_hint if current else None,
                proven_tenant_id=proven_tenant_id,
            ),
            tenant_hint=current.tenant_hint if current else None,
            permissions=frozenset(permissions or ()),
        ),
    )


def remember_context(request: HttpRequest, context: RequestContext) -> None:
    request.api_context = context  # type: ignore[attr-defined]


def read_context(request: HttpRequest) -> RequestContext | None:
    value = getattr(request, "api_context", None)
    if isinstance(value, RequestContext):
        return value
    return None


def remember_error(request: HttpRequest, code: str) -> None:
    request.api_error_code = code  # type: ignore[attr-defined]


def read_error_code(request: HttpRequest) -> str:
    value = getattr(request, "api_error_code", "-")
    if isinstance(value, str) and value:
        return value
    return "-"


def json_contains_tenant_id(value: object) -> bool:
    if isinstance(value, dict):
        if "tenant_id" in value:
            return True
        return any(json_contains_tenant_id(item) for item in value.values())
    if isinstance(value, list):
        return any(json_contains_tenant_id(item) for item in value)
    return False
