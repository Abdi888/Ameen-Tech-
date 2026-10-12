"""Request identity that does not trust the client for tenant scope.

`X-Tenant-Id` is stored as a hint. `authorized_tenant_id` is the only value
later code may treat as the tenant, and it stays empty until membership is
proven. Document 00 §9: request bodies must not include `tenant_id`.
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


def request_id_from_header(value: str | None) -> str:
    """Echo a safe client id, or generate one. Do not echo control characters."""
    if value is not None and _REQUEST_ID.fullmatch(value):
        return value
    return str(uuid.uuid4())


def tenant_hint_from_header(value: str | None) -> str | None:
    if value is not None and _UUID.fullmatch(value):
        return value.lower()
    return None


def authorized_tenant_id(*, user_id: str | None, tenant_hint: str | None) -> str | None:
    """Return a tenant id only after an active membership is proven.

    Login and membership are not part of this foundation. The arguments are
    accepted so callers have one function to change later. They are not proof.
    """
    del user_id, tenant_hint
    return None


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
