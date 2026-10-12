"""JSON envelope from Document 05. Success omits `errors`. Errors always include it."""

from __future__ import annotations

from django.http import JsonResponse


def success_body(data: object, meta: dict[str, object] | None = None) -> dict[str, object]:
    return {"success": True, "data": data, "meta": {} if meta is None else meta}


def error_body(
    *,
    code: str,
    message: str,
    field: str | None = None,
    errors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    body_errors: list[dict[str, object]]
    if errors is None:
        body_errors = [{"code": code, "message": message, "field": field}]
    else:
        body_errors = errors
    return {"success": False, "data": None, "meta": {}, "errors": body_errors}


def error_json(
    *,
    status: int,
    code: str,
    message: str,
    field: str | None = None,
) -> JsonResponse:
    return JsonResponse(error_body(code=code, message=message, field=field), status=status)
