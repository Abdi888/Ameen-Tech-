"""API error codes from Document 05 and the HTTP status each one uses.

Document 05 names the codes and the status families (401, 403, 404, 405, 409,
422, 500, 503). It does not give every code its own status line. The mapping
below follows those families: auth failures are 401, permission and tenant
denial are 403, a hidden or missing resource is 404, an unsupported method is
405, stock and state conflicts are 409, validation is 422, a malformed body is
400, an unbalanced journal is a server invariant (500), and a down dependency
is 503.
"""

from __future__ import annotations

STATUS_BY_CODE: dict[str, int] = {
    "AUTH_REQUIRED": 401,
    "AUTH_INVALID_TOKEN": 401,
    "AUTH_TOKEN_EXPIRED": 401,
    "PERMISSION_DENIED": 403,
    "TENANT_ACCESS_DENIED": 403,
    "VALIDATION_ERROR": 422,
    "INVALID_FIELD": 422,
    "INVALID_FORMAT": 400,
    "INVALID_VALUE": 422,
    "METHOD_NOT_ALLOWED": 405,
    "RESOURCE_NOT_FOUND": 404,
    "RESOURCE_ALREADY_EXISTS": 409,
    "RESOURCE_CONFLICT": 409,
    "INSUFFICIENT_STOCK": 409,
    "INVALID_STATUS_TRANSITION": 409,
    "SALE_ALREADY_COMPLETED": 409,
    "SALE_ALREADY_VOIDED": 409,
    "PAYMENT_EXCEEDS_BALANCE": 409,
    "PRODUCT_SKU_EXISTS": 409,
    "REGISTER_NOT_OPEN": 409,
    "ACCOUNTING_ENTRY_UNBALANCED": 500,
    "INTERNAL_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}


class ApiError(Exception):
    """Raised by application code and rendered as the standard error envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        field: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        if code not in STATUS_BY_CODE:
            raise ValueError(f"Unknown API error code: {code}")
        self.code = code
        self.message = message
        self.field = field
        self.status_code = STATUS_BY_CODE[code] if status_code is None else status_code
