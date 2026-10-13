from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from modules.audit.models import AuditLog
from modules.identity.domain.tokens import hash_secret
from modules.identity.models import Session, User
from tests.support import PASSWORD, SessionClient, grant, login, make_tenant, make_user

pytestmark = pytest.mark.django_db


def test_login_sets_an_httponly_cookie_and_hides_the_token(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    user = make_user("cashier@harbor.test")
    grant(user, tenant, "Cashier")

    response = login(api, user.email, tenant=tenant)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["user"]["email"] == user.email
    assert body["data"]["roles"] == ["Cashier"]
    assert "pos.refund" not in body["data"]["permissions"]
    assert "password" not in response.content.decode().lower()
    cookie = response.cookies["ameen_session"]
    assert cookie.value not in response.content.decode()
    assert cookie["httponly"]
    assert cookie["samesite"] == "Lax"
    assert cookie["secure"] == ""
    session = Session.objects.get(user=user)
    assert session.token_hash == hash_secret(cookie.value)
    assert session.token_hash != cookie.value
    assert session.token_hash.startswith("$") is False


def test_wrong_password_and_unknown_email_share_one_message(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    user = make_user("cashier@harbor.test")
    grant(user, tenant, "Cashier")

    wrong = login(api, user.email, "not-the-password")
    missing = login(api, "nobody@harbor.test", PASSWORD)

    assert wrong.status_code == 401
    assert missing.status_code == 401
    assert wrong.json()["errors"] == missing.json()["errors"]
    assert wrong.json()["errors"][0] == {
        "code": "AUTH_INVALID_TOKEN",
        "message": "Invalid email or password.",
        "field": None,
    }
    assert "ameen_session" not in wrong.cookies
    assert Session.objects.filter(user=user).count() == 0


@pytest.mark.parametrize("status", ["INVITED", "SUSPENDED", "DISABLED"])
def test_inactive_users_cannot_login(api: SessionClient, status: str) -> None:
    tenant = make_tenant(f"shop-{status.lower()}")
    user = make_user(f"{status.lower()}@shop.test", status=status)
    grant(user, tenant, "Cashier")

    response = login(api, user.email, tenant=tenant)

    assert response.status_code == 401
    assert response.json()["errors"][0]["message"] == "Invalid email or password."
    assert status not in response.content.decode()
    assert Session.objects.filter(user=user).count() == 0


def test_missing_csrf_token_is_rejected(api: SessionClient) -> None:
    api.client.credentials()
    response = api.client.post(
        "/api/v1/auth/login",
        {"email": "cashier@harbor.test", "password": PASSWORD},
        format="json",
    )
    assert response.status_code == 403
    assert response.json()["errors"][0]["code"] == "PERMISSION_DENIED"


def test_logout_revokes_the_session(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    user = make_user("cashier@harbor.test")
    grant(user, tenant, "Cashier")
    assert login(api, user.email, tenant=tenant).status_code == 200

    raw_token = api.client.cookies["ameen_session"].value
    logged_out = api.client.post("/api/v1/auth/logout", {}, format="json")
    assert logged_out.status_code == 200
    assert Session.objects.get(user=user).revoked_at is not None

    api.client.cookies["ameen_session"] = raw_token
    again = api.client.get("/api/v1/auth/me")
    assert again.status_code == 401
    assert again.json()["errors"][0]["code"] == "AUTH_INVALID_TOKEN"


def test_expired_session_is_distinct_from_a_revoked_session(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    user = make_user("cashier@harbor.test")
    grant(user, tenant, "Cashier")
    assert login(api, user.email, tenant=tenant).status_code == 200
    session = Session.objects.get(user=user)
    session.last_used_at = timezone.now() - timedelta(hours=9)
    session.save(update_fields=["last_used_at"])

    expired = api.client.get("/api/v1/auth/me")
    assert expired.status_code == 401
    assert expired.json()["errors"][0]["code"] == "AUTH_TOKEN_EXPIRED"
    session.refresh_from_db()
    assert session.revoked_at is not None

    other = make_user("other@harbor.test")
    grant(other, tenant, "Viewer")
    assert login(api, other.email, tenant=tenant).status_code == 200
    current = Session.objects.get(user=other)
    current.revoked_at = timezone.now()
    current.save(update_fields=["revoked_at"])
    revoked = api.client.get("/api/v1/auth/me")
    assert revoked.status_code == 401
    assert revoked.json()["errors"][0]["code"] == "AUTH_INVALID_TOKEN"


def test_password_change_revokes_every_session(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    user = make_user("owner@harbor.test")
    grant(user, tenant, "Administrator")
    assert login(api, user.email, tenant=tenant).status_code == 200

    changed = api.client.post(
        "/api/v1/auth/password/change",
        {"current_password": PASSWORD, "password": "a-new-password-value"},
        format="json",
    )
    assert changed.status_code == 200
    assert Session.objects.filter(user=user, revoked_at__isnull=True).count() == 0
    assert api.client.get("/api/v1/auth/me").status_code == 401
    assert login(api, user.email, "a-new-password-value", tenant=tenant).status_code == 200


def test_login_lock_is_temporary(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    user = make_user("cashier@harbor.test")
    grant(user, tenant, "Cashier")
    for _ in range(5):
        response = login(api, user.email, "wrong-password-value")
        assert response.status_code == 401
    blocked = login(api, user.email, PASSWORD, tenant=tenant)
    assert blocked.status_code == 429
    assert blocked.json()["errors"][0]["message"] == "Too many attempts. Try again later."
    assert "ameen_session" not in blocked.cookies

    from modules.identity.models import LoginAttempt

    LoginAttempt.objects.filter(email=user.email).update(
        attempted_at=timezone.now() - timedelta(minutes=16)
    )
    assert login(api, user.email, PASSWORD, tenant=tenant).status_code == 200


def test_password_reset_does_not_reveal_whether_the_email_exists(
    api: SessionClient,
    mail: list[tuple[str, str, str]],
) -> None:
    tenant = make_tenant("harbor")
    user = make_user("cashier@harbor.test", status="INVITED", password=None)
    grant(user, tenant, "Cashier", membership_status="INVITED")

    unknown = api.client.post(
        "/api/v1/auth/password/reset",
        {"email": "missing@harbor.test"},
        format="json",
    )
    known = api.client.post(
        "/api/v1/auth/password/reset",
        {"email": user.email},
        format="json",
    )
    assert unknown.status_code == 200
    assert known.status_code == 200
    assert unknown.json() == known.json()
    assert unknown.json()["data"] == {}
    assert [item for item in mail if item[0] == "reset"] == [("reset", user.email, mail[-1][2])]
    token = mail[-1][2]
    assert token not in known.content.decode()

    confirmed = api.client.post(
        "/api/v1/auth/password/reset/confirm",
        {"token": token, "password": "replacement-password"},
        format="json",
    )
    assert confirmed.status_code == 200
    user.refresh_from_db()
    assert user.status == "ACTIVE"
    assert user.password_hash.startswith("$argon2id$")
    from modules.access.models import TenantMembership

    assert TenantMembership.objects.get(user=user).status == "ACTIVE"
    assert login(api, user.email, "replacement-password", tenant=tenant).status_code == 200
    assert AuditLog.objects.filter(action="password.reset", user=user).exists()
    stored = AuditLog.objects.filter(user=user).values_list("new_values", flat=True)
    assert all(token not in str(row) for row in stored)


def test_unauthenticated_me_does_not_trust_a_tenant_header(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    api.use_tenant(tenant.id)
    response = api.client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["errors"][0]["code"] == "AUTH_REQUIRED"
    assert str(tenant.id) not in response.content.decode()


def test_user_rows_are_not_deleted_by_deactivation(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    admin = make_user("admin@harbor.test")
    cashier = make_user("cashier@harbor.test")
    grant(admin, tenant, "Administrator")
    grant(cashier, tenant, "Cashier")
    assert login(api, admin.email, tenant=tenant).status_code == 200
    response = api.client.post(f"/api/v1/users/{cashier.id}/deactivate", {}, format="json")
    assert response.status_code == 200
    assert User.objects.filter(pk=cashier.id).exists()
    assert response.json()["data"]["membership_status"] == "SUSPENDED"
