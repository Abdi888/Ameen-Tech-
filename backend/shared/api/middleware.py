"""Request id, request log, JSON error pages, and rejection of a client tenant id."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token

from shared.api.context import (
    RequestContext,
    authorized_tenant_id,
    json_contains_tenant_id,
    read_context,
    read_error_code,
    remember_context,
    remember_error,
    request_id_from_header,
    tenant_hint_from_header,
)
from shared.api.responses import error_json

logger = logging.getLogger("ameen.request")

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


class RequestContextLogFilter(logging.Filter):
    """Supply log fields when a record was not created by the request logger."""

    def filter(self, record: logging.LogRecord) -> bool:
        for name in ("request_id", "tenant_id", "user_id", "endpoint", "error_code"):
            if not hasattr(record, name):
                setattr(record, name, "-")
        return True


class RequestContextMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        hint = tenant_hint_from_header(request.headers.get("X-Tenant-Id"))
        context = RequestContext(
            request_id=request_id_from_header(request.headers.get("X-Request-Id")),
            user_id=None,
            tenant_id=authorized_tenant_id(user_id=None, tenant_hint=hint),
            tenant_hint=hint,
        )
        remember_context(request, context)
        response = self.get_response(request)
        response["X-Request-Id"] = context.request_id
        return response


class ApiEnvelopeMiddleware:
    """Keep `/api/` responses on the JSON envelope.

    With DEBUG on, Django replaces handler404 and handler500 with HTML debug
    pages. Those pages list URL patterns and exception text. This middleware
    discards that HTML for API paths.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if not request.path.startswith("/api/"):
            return response
        if "text/html" not in response.headers.get("Content-Type", ""):
            return response
        if response.status_code == 404:
            remember_error(request, "RESOURCE_NOT_FOUND")
            return error_json(status=404, code="RESOURCE_NOT_FOUND", message="Not found.")
        if response.status_code >= 500:
            remember_error(request, "INTERNAL_ERROR")
            return error_json(
                status=500,
                code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
            )
        return response


class RequestLogMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        context = read_context(request)
        logger.info(
            "%s %s",
            request.method,
            response.status_code,
            extra={
                "request_id": context.request_id if context else "-",
                "tenant_id": (context.tenant_id if context and context.tenant_id else "-"),
                "user_id": (context.user_id if context and context.user_id else "-"),
                "endpoint": request.path,
                "error_code": read_error_code(request),
            },
        )
        return response


class EnsureCsrfCookieMiddleware:
    """Set the CSRF cookie on API responses so cookie POSTs can send it back.

    This sits inside CsrfViewMiddleware so that middleware writes the cookie.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith("/api/"):
            get_token(request)
        return self.get_response(request)


class RejectTenantIdMiddleware:
    """Document 00 §9: clients do not choose the tenant by sending tenant_id."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method not in _SAFE_METHODS and _body_sets_tenant_id(request):
            remember_error(request, "VALIDATION_ERROR")
            return error_json(
                status=422,
                code="VALIDATION_ERROR",
                message="Request bodies must not include tenant_id.",
                field="tenant_id",
            )
        return self.get_response(request)


def _body_sets_tenant_id(request: HttpRequest) -> bool:
    content_type = request.META.get("CONTENT_TYPE", "")
    if "application/json" in content_type:
        if not request.body:
            return False
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return False
        return json_contains_tenant_id(payload)
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        return "tenant_id" in request.POST
    return False
