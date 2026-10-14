"""HTTP 401, 403, 404, and 200 for the tenant user APIs.

Inapplicable cells, asserted by omission from the executed matrix:

- ``GET /api/v1/users`` and ``GET /api/v1/roles`` have no resource id. Another
  tenant's members are omitted from the caller's list, so HTTP 404 is not an
  outcome of those operations.
- ``POST /api/v1/users`` creates a membership. The success status is HTTP 201,
  so HTTP 200 is not the success outcome.
"""

from __future__ import annotations

import uuid

import pytest

from modules.access.models import Role
from tests.support import SessionClient, grant, login, make_tenant, make_user

pytestmark = pytest.mark.django_db


def test_unauthenticated_get_users_returns_401(api: SessionClient) -> None:
    response = api.client.get("/api/v1/users")
    assert response.status_code == 401
    assert response.json()["errors"][0]["code"] == "AUTH_REQUIRED"


def test_user_api_authorization_matrix(api: SessionClient) -> None:
    harbor = make_tenant("harbor")
    market = make_tenant("market")
    admin = make_user("admin@harbor.test")
    cashier = make_user("cashier@harbor.test")
    staff = make_user("staff@harbor.test")
    outsider = make_user("outsider@market.test")
    grant(admin, harbor, "Administrator")
    grant(cashier, harbor, "Cashier")
    grant(staff, harbor, "Cashier")
    grant(outsider, market, "Cashier")
    viewer_id = str(Role.objects.get(name="Viewer", tenant__isnull=True).id)
    cashier_role_id = str(Role.objects.get(name="Cashier", tenant__isnull=True).id)
    missing_role = str(uuid.uuid4())
    hidden = str(outsider.id)
    staff_id = str(staff.id)

    anonymous, anonymous_bodies = _outcomes(
        api,
        target_id=staff_id,
        invite_role_id=viewer_id,
        assign_role_id=viewer_id,
    )
    assert anonymous == {
        "GET /api/v1/users": (401, "AUTH_REQUIRED"),
        "POST /api/v1/users": (401, "AUTH_REQUIRED"),
        "GET /api/v1/users/{id}": (401, "AUTH_REQUIRED"),
        "PATCH /api/v1/users/{id}": (401, "AUTH_REQUIRED"),
        "POST /api/v1/users/{id}/activate": (401, "AUTH_REQUIRED"),
        "POST /api/v1/users/{id}/deactivate": (401, "AUTH_REQUIRED"),
        "GET /api/v1/users/{id}/roles": (401, "AUTH_REQUIRED"),
        "POST /api/v1/users/{id}/roles": (401, "AUTH_REQUIRED"),
        "GET /api/v1/roles": (401, "AUTH_REQUIRED"),
    }
    assert all("users." not in body for body in anonymous_bodies)

    assert login(api, cashier.email, tenant=harbor).status_code == 200
    denied, denied_bodies = _outcomes(
        api,
        target_id=staff_id,
        invite_role_id=viewer_id,
        assign_role_id=viewer_id,
    )
    assert denied == {
        "GET /api/v1/users": (403, "PERMISSION_DENIED"),
        "POST /api/v1/users": (403, "PERMISSION_DENIED"),
        "GET /api/v1/users/{id}": (403, "PERMISSION_DENIED"),
        "PATCH /api/v1/users/{id}": (403, "PERMISSION_DENIED"),
        "POST /api/v1/users/{id}/activate": (403, "PERMISSION_DENIED"),
        "POST /api/v1/users/{id}/deactivate": (403, "PERMISSION_DENIED"),
        "GET /api/v1/users/{id}/roles": (403, "PERMISSION_DENIED"),
        "POST /api/v1/users/{id}/roles": (403, "PERMISSION_DENIED"),
        "GET /api/v1/roles": (403, "PERMISSION_DENIED"),
    }
    for body in denied_bodies:
        assert "users.view" not in body
        assert "users.create" not in body
        assert "users.update" not in body
        assert "users.activate" not in body
        assert "users.deactivate" not in body
        assert "users.assign_roles" not in body
        assert outsider.email not in body

    assert login(api, admin.email, tenant=harbor).status_code == 200
    missing, missing_bodies = _outcomes(
        api,
        target_id=hidden,
        invite_role_id=missing_role,
        assign_role_id=viewer_id,
        invite_email="missing-role@harbor.test",
    )
    assert missing == {
        "GET /api/v1/users": (200, None),
        "POST /api/v1/users": (404, "RESOURCE_NOT_FOUND"),
        "GET /api/v1/users/{id}": (404, "RESOURCE_NOT_FOUND"),
        "PATCH /api/v1/users/{id}": (404, "RESOURCE_NOT_FOUND"),
        "POST /api/v1/users/{id}/activate": (404, "RESOURCE_NOT_FOUND"),
        "POST /api/v1/users/{id}/deactivate": (404, "RESOURCE_NOT_FOUND"),
        "GET /api/v1/users/{id}/roles": (404, "RESOURCE_NOT_FOUND"),
        "POST /api/v1/users/{id}/roles": (404, "RESOURCE_NOT_FOUND"),
        "GET /api/v1/roles": (200, None),
    }
    for body in missing_bodies:
        assert outsider.email not in body

    allowed = _allowed(
        api,
        staff_id=staff_id,
        viewer_id=viewer_id,
        invite_role_id=cashier_role_id,
    )
    assert allowed == {
        "GET /api/v1/users": 200,
        "POST /api/v1/users": 201,
        "GET /api/v1/users/{id}": 200,
        "PATCH /api/v1/users/{id}": 200,
        "POST /api/v1/users/{id}/deactivate": 200,
        "POST /api/v1/users/{id}/activate": 200,
        "GET /api/v1/users/{id}/roles": 200,
        "POST /api/v1/users/{id}/roles": 200,
        "GET /api/v1/roles": 200,
    }


def _outcomes(
    api: SessionClient,
    *,
    target_id: str,
    invite_role_id: str,
    assign_role_id: str,
    invite_email: str = "invited@harbor.test",
) -> tuple[dict[str, tuple[int, str | None]], list[str]]:
    calls = {
        "GET /api/v1/users": api.client.get("/api/v1/users"),
        "POST /api/v1/users": api.client.post(
            "/api/v1/users",
            _invite_body(invite_email, invite_role_id),
            format="json",
        ),
        "GET /api/v1/users/{id}": api.client.get(f"/api/v1/users/{target_id}"),
        "PATCH /api/v1/users/{id}": api.client.patch(
            f"/api/v1/users/{target_id}",
            {"first_name": "Hidden"},
            format="json",
        ),
        "POST /api/v1/users/{id}/activate": api.client.post(
            f"/api/v1/users/{target_id}/activate",
            {},
            format="json",
        ),
        "POST /api/v1/users/{id}/deactivate": api.client.post(
            f"/api/v1/users/{target_id}/deactivate",
            {},
            format="json",
        ),
        "GET /api/v1/users/{id}/roles": api.client.get(f"/api/v1/users/{target_id}/roles"),
        "POST /api/v1/users/{id}/roles": api.client.post(
            f"/api/v1/users/{target_id}/roles",
            {"role_ids": [assign_role_id]},
            format="json",
        ),
        "GET /api/v1/roles": api.client.get("/api/v1/roles"),
    }
    recorded: dict[str, tuple[int, str | None]] = {}
    bodies: list[str] = []
    for name, response in calls.items():
        code = None
        if response.status_code != 200:
            code = str(response.json()["errors"][0]["code"])
        recorded[name] = (response.status_code, code)
        bodies.append(response.content.decode())
    return recorded, bodies


def _allowed(
    api: SessionClient,
    *,
    staff_id: str,
    viewer_id: str,
    invite_role_id: str,
) -> dict[str, int]:
    listing = api.client.get("/api/v1/users")
    detail = api.client.get(f"/api/v1/users/{staff_id}")
    updated = api.client.patch(
        f"/api/v1/users/{staff_id}",
        {"first_name": "Nuur"},
        format="json",
    )
    current_roles = api.client.get(f"/api/v1/users/{staff_id}/roles")
    assigned = api.client.post(
        f"/api/v1/users/{staff_id}/roles",
        {"role_ids": [viewer_id]},
        format="json",
    )
    deactivated = api.client.post(f"/api/v1/users/{staff_id}/deactivate", {}, format="json")
    activated = api.client.post(f"/api/v1/users/{staff_id}/activate", {}, format="json")
    invited = api.client.post(
        "/api/v1/users",
        _invite_body("new-member@harbor.test", invite_role_id),
        format="json",
    )
    roles = api.client.get("/api/v1/roles")
    assert updated.json()["data"]["first_name"] == "Nuur"
    assert invited.json()["data"]["status"] == "INVITED"
    assert "password" not in invited.content.decode()
    assert deactivated.json()["data"]["membership_status"] == "SUSPENDED"
    assert activated.json()["data"]["membership_status"] == "ACTIVE"
    assert {item["name"] for item in assigned.json()["data"]["roles"]} == {"Viewer"}
    assert current_roles.status_code == 200
    return {
        "GET /api/v1/users": listing.status_code,
        "POST /api/v1/users": invited.status_code,
        "GET /api/v1/users/{id}": detail.status_code,
        "PATCH /api/v1/users/{id}": updated.status_code,
        "POST /api/v1/users/{id}/deactivate": deactivated.status_code,
        "POST /api/v1/users/{id}/activate": activated.status_code,
        "GET /api/v1/users/{id}/roles": current_roles.status_code,
        "POST /api/v1/users/{id}/roles": assigned.status_code,
        "GET /api/v1/roles": roles.status_code,
    }


def _invite_body(email: str, role_id: str) -> dict[str, str]:
    return {
        "email": email,
        "first_name": "New",
        "last_name": "Member",
        "role_id": role_id,
    }
