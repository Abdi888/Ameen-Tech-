"""Turn exceptions into the Document 05 error envelope.

Client responses never include stack traces, SQL, permission keys, or the
exception text. Unexpected failures are logged with a traceback for operators.
"""

from __future__ import annotations

import logging
from typing import Any

from django.http import Http404, HttpRequest
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response

from shared.api.context import remember_error
from shared.api.responses import error_body, error_json
from shared.exceptions import ApiError

logger = logging.getLogger("ameen.request")


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    if isinstance(exc, ApiError):
        return _respond(context, exc.status_code, exc.code, exc.message, exc.field)
    if isinstance(exc, NotAuthenticated):
        return _respond(context, 401, "AUTH_REQUIRED", "Authentication is required.")
    if isinstance(exc, AuthenticationFailed):
        return _respond(context, 401, "AUTH_INVALID_TOKEN", "Authentication failed.")
    if isinstance(exc, PermissionDenied):
        return _respond(
            context,
            403,
            "PERMISSION_DENIED",
            "You do not have permission to perform this action.",
        )
    if isinstance(exc, (Http404, NotFound)):
        return _respond(context, 404, "RESOURCE_NOT_FOUND", "Not found.")
    if isinstance(exc, MethodNotAllowed):
        # Document 05 has no method-not-allowed code. INVALID_VALUE is the
        # closest request-value code and keeps the real HTTP status of 405.
        return _respond(context, 405, "INVALID_VALUE", "This method is not allowed.")
    if isinstance(exc, ParseError):
        return _respond(context, 400, "INVALID_FORMAT", "Request body is not valid JSON.")
    if isinstance(exc, ValidationError):
        errors = _validation_errors(exc.detail)
        _mark(context, "VALIDATION_ERROR")
        return Response(
            error_body(code="VALIDATION_ERROR", message="", errors=errors),
            status=422,
        )
    logger.exception("unhandled %s", type(exc).__name__)
    return _respond(context, 500, "INTERNAL_ERROR", "An unexpected error occurred.")


def csrf_failure(request: HttpRequest, **kwargs: object) -> object:
    del kwargs
    remember_error(request, "PERMISSION_DENIED")
    return error_json(
        status=403,
        code="PERMISSION_DENIED",
        message="CSRF verification failed.",
    )


def not_found(request: HttpRequest, exception: Exception) -> object:
    del exception
    remember_error(request, "RESOURCE_NOT_FOUND")
    return error_json(status=404, code="RESOURCE_NOT_FOUND", message="Not found.")


def server_error(request: HttpRequest) -> object:
    remember_error(request, "INTERNAL_ERROR")
    return error_json(
        status=500,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
    )


def _respond(
    context: dict[str, Any],
    status: int,
    code: str,
    message: str,
    field: str | None = None,
) -> Response:
    _mark(context, code)
    return Response(error_body(code=code, message=message, field=field), status=status)


def _mark(context: dict[str, Any], code: str) -> None:
    request = context.get("request")
    if request is None:
        return
    django_request = getattr(request, "_request", request)
    if isinstance(django_request, HttpRequest):
        remember_error(django_request, code)


def _validation_errors(detail: object) -> list[dict[str, object]]:
    if isinstance(detail, dict):
        errors: list[dict[str, object]] = []
        for field, messages in detail.items():
            field_name = None if field == "non_field_errors" else str(field)
            for message in _messages(messages):
                errors.append({"code": "VALIDATION_ERROR", "message": message, "field": field_name})
        return errors or [
            {"code": "VALIDATION_ERROR", "message": "Invalid request.", "field": None}
        ]
    return [
        {"code": "VALIDATION_ERROR", "message": message, "field": None}
        for message in _messages(detail)
    ]


def _messages(detail: object) -> list[str]:
    if isinstance(detail, list):
        if not detail:
            return ["Invalid request."]
        return [str(item) for item in detail]
    return [str(detail)]
