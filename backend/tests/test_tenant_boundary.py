from __future__ import annotations

import json
import uuid
from typing import Any

import pytest
from django.test import Client
from rest_framework.exceptions import ValidationError

from shared.api.context import authorized_tenant_id, json_contains_tenant_id
from shared.api.errors import exception_handler
from shared.exceptions import STATUS_BY_CODE, ApiError

DOCUMENTED_CODES = {
    "AUTH_REQUIRED",
    "AUTH_INVALID_TOKEN",
    "AUTH_TOKEN_EXPIRED",
    "PERMISSION_DENIED",
    "TENANT_ACCESS_DENIED",
    "VALIDATION_ERROR",
    "INVALID_FIELD",
    "INVALID_FORMAT",
    "INVALID_VALUE",
    "METHOD_NOT_ALLOWED",
    "RESOURCE_NOT_FOUND",
    "RESOURCE_ALREADY_EXISTS",
    "RESOURCE_CONFLICT",
    "INSUFFICIENT_STOCK",
    "INVALID_STATUS_TRANSITION",
    "SALE_ALREADY_COMPLETED",
    "SALE_ALREADY_VOIDED",
    "PAYMENT_EXCEEDS_BALANCE",
    "PRODUCT_SKU_EXISTS",
    "REGISTER_NOT_OPEN",
    "ACCOUNTING_ENTRY_UNBALANCED",
    "INTERNAL_ERROR",
    "SERVICE_UNAVAILABLE",
}


def test_error_catalog_matches_document_05() -> None:
    assert set(STATUS_BY_CODE) == DOCUMENTED_CODES
    assert STATUS_BY_CODE["AUTH_REQUIRED"] == 401
    assert STATUS_BY_CODE["PERMISSION_DENIED"] == 403
    assert STATUS_BY_CODE["TENANT_ACCESS_DENIED"] == 403
    assert STATUS_BY_CODE["RESOURCE_NOT_FOUND"] == 404
    assert STATUS_BY_CODE["INSUFFICIENT_STOCK"] == 409
    assert STATUS_BY_CODE["VALIDATION_ERROR"] == 422
    assert STATUS_BY_CODE["INVALID_FORMAT"] == 400
    assert STATUS_BY_CODE["INVALID_VALUE"] == 422
    assert STATUS_BY_CODE["METHOD_NOT_ALLOWED"] == 405
    assert STATUS_BY_CODE["SERVICE_UNAVAILABLE"] == 503


def test_header_and_user_id_do_not_authorize_a_tenant() -> None:
    hint = str(uuid.uuid4())
    assert authorized_tenant_id(user_id=None, tenant_hint=hint) is None
    assert authorized_tenant_id(user_id=str(uuid.uuid4()), tenant_hint=hint) is None
    assert authorized_tenant_id(user_id=str(uuid.uuid4()), tenant_hint=None) is None


def test_nested_tenant_id_is_detected() -> None:
    assert json_contains_tenant_id({"sale": {"tenant_id": "other"}}) is True
    assert json_contains_tenant_id({"items": [{"sku": "A"}]}) is False


@pytest.mark.parametrize(
    "payload",
    [
        {"tenant_id": "0199"},
        {"line": {"tenant_id": "0199"}},
        [{"tenant_id": "0199"}],
    ],
)
def test_client_cannot_set_tenant_in_json_body(payload: object) -> None:
    client = Client(enforce_csrf_checks=True)
    response = client.post(
        "/api/v1/health",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["errors"] == [
        {
            "code": "VALIDATION_ERROR",
            "message": "Request bodies must not include tenant_id.",
            "field": "tenant_id",
        }
    ]


def test_missing_csrf_token_uses_the_error_envelope(settings: Any) -> None:
    settings.ROOT_URLCONF = "tests.urlconfs"
    client = Client(enforce_csrf_checks=True)
    response = client.post(
        "/api/v1/csrf-probe",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 403
    body = response.json()
    assert body["errors"][0]["code"] == "PERMISSION_DENIED"
    assert body["errors"][0]["message"] == "CSRF verification failed."
    assert "Traceback" not in response.content.decode()


def test_form_body_cannot_set_tenant() -> None:
    response = Client(enforce_csrf_checks=True).post("/api/v1/health", data={"tenant_id": "0199"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "tenant_id"


def test_validation_errors_use_422_and_the_field_name() -> None:
    response = exception_handler(
        ValidationError({"name": ["This field is required."]}),
        {},
    )
    assert response is not None
    assert response.status_code == 422
    assert response.data["errors"] == [
        {
            "code": "VALIDATION_ERROR",
            "message": "This field is required.",
            "field": "name",
        }
    ]


def test_unknown_error_code_is_rejected() -> None:
    with pytest.raises(ValueError):
        ApiError("NOT_A_CODE", "nope")


def test_unauthenticated_route_does_not_trust_tenant_header(settings: Any) -> None:
    settings.ROOT_URLCONF = "tests.urlconfs"
    tenant_id = str(uuid.uuid4())
    client = Client()
    response = client.get("/api/v1/protected", HTTP_X_TENANT_ID=tenant_id)
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["errors"][0]["code"] == "AUTH_REQUIRED"
    assert tenant_id not in response.content.decode()


def test_unknown_route_is_not_found_without_confirming_a_tenant() -> None:
    tenant_id = str(uuid.uuid4())
    response = Client().get(f"/api/v1/products/{tenant_id}", HTTP_X_TENANT_ID=tenant_id)
    assert response.status_code == 404
    body = response.json()
    assert body["errors"][0]["code"] == "RESOURCE_NOT_FOUND"
    assert tenant_id not in response.content.decode()
