"""Reset and invite tokens are hashed, expiring, and single-use."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from modules.access.models import Role, TenantMembership
from modules.identity.domain.passwords import verify_password
from modules.identity.domain.tokens import hash_secret
from modules.identity.models import LoginAttempt, PasswordResetToken, User
from tests.support import PASSWORD, SessionClient, grant, login, make_tenant, make_user

pytestmark = pytest.mark.django_db

_NEXT = "replacement-password"


def test_reset_token_is_hashed_single_use_and_expires(
    api: SessionClient,
    mail: list[tuple[str, str, str]],
) -> None:
    tenant = make_tenant("harbor")
    user = make_user("cashier@harbor.test")
    grant(user, tenant, "Cashier")
    assert login(api, user.email, tenant=tenant).status_code == 200
    first = _reset(api, user.email, mail)
    second = _reset(api, user.email, mail)
    stored = list(PasswordResetToken.objects.filter(user=user).order_by("created_at"))
    assert len(stored) == 2
    assert stored[0].used_at is not None
    assert stored[1].used_at is None
    assert stored[1].token_hash == hash_secret(second)
    assert stored[1].token_hash != second
    assert stored[1].purpose == PasswordResetToken.PURPOSE_RESET

    stale = api.client.post(
        "/api/v1/auth/password/reset/confirm",
        {"token": first, "password": _NEXT},
        format="json",
    )
    assert stale.status_code == 401
    assert stale.json()["errors"][0]["code"] == "AUTH_INVALID_TOKEN"
    user.refresh_from_db()
    assert verify_password(PASSWORD, user.password_hash)

    stored[1].expires_at = timezone.now() - timedelta(seconds=1)
    stored[1].save(update_fields=["expires_at"])
    expired = api.client.post(
        "/api/v1/auth/password/reset/confirm",
        {"token": second, "password": _NEXT},
        format="json",
    )
    assert expired.status_code == 401
    assert expired.json()["errors"][0]["code"] == "AUTH_TOKEN_EXPIRED"
    stored[1].refresh_from_db()
    assert stored[1].used_at is None
    user.refresh_from_db()
    assert verify_password(PASSWORD, user.password_hash)

    stored[1].expires_at = timezone.now() + timedelta(minutes=30)
    stored[1].save(update_fields=["expires_at"])
    confirmed = api.client.post(
        "/api/v1/auth/password/reset/confirm",
        {"token": second, "password": _NEXT},
        format="json",
    )
    assert confirmed.status_code == 200
    assert second not in confirmed.content.decode()
    stored[1].refresh_from_db()
    assert stored[1].used_at is not None
    user.refresh_from_db()
    assert verify_password(_NEXT, user.password_hash)
    again = api.client.post(
        "/api/v1/auth/password/reset/confirm",
        {"token": second, "password": "yet-another-password"},
        format="json",
    )
    assert again.status_code == 401
    user.refresh_from_db()
    assert verify_password(_NEXT, user.password_hash)
    assert login(api, user.email, PASSWORD).status_code == 401
    assert login(api, user.email, _NEXT, tenant=tenant).status_code == 200


def test_invite_token_replacement_and_suspended_confirmation(
    api: SessionClient,
    mail: list[tuple[str, str, str]],
) -> None:
    harbor = make_tenant("harbor")
    market = make_tenant("market")
    admin = make_user("admin@harbor.test")
    grant(admin, harbor, "Administrator")
    grant(admin, market, "Administrator")
    assert login(api, admin.email).status_code == 200
    role_id = str(Role.objects.get(name="Viewer", tenant__isnull=True).id)
    api.use_tenant(harbor.id)
    first = api.client.post(
        "/api/v1/users",
        {
            "email": "new@harbor.test",
            "first_name": "New",
            "last_name": "Member",
            "role_id": role_id,
        },
        format="json",
    )
    assert first.status_code == 201
    api.use_tenant(market.id)
    second = api.client.post(
        "/api/v1/users",
        {
            "email": "new@harbor.test",
            "first_name": "New",
            "last_name": "Member",
            "role_id": role_id,
        },
        format="json",
    )
    assert second.status_code == 201
    invites = [item for item in mail if item[0] == "invite"]
    assert len(invites) == 2
    old_token, new_token = invites[0][2], invites[1][2]
    assert old_token != new_token
    rejected = api.client.post(
        "/api/v1/auth/password/reset/confirm",
        {"token": old_token, "password": _NEXT},
        format="json",
    )
    assert rejected.status_code == 401
    invited = User.objects.get(email="new@harbor.test")
    assert invited.status == "INVITED"
    assert invited.password_hash == ""

    confirmed = api.client.post(
        "/api/v1/auth/password/reset/confirm",
        {"token": new_token, "password": _NEXT},
        format="json",
    )
    assert confirmed.status_code == 200
    invited.refresh_from_db()
    assert invited.status == "ACTIVE"
    assert verify_password(_NEXT, invited.password_hash)
    assert set(TenantMembership.objects.filter(user=invited).values_list("status", flat=True)) == {
        "ACTIVE"
    }

    reset = _reset(api, invited.email, mail)
    invited.status = "SUSPENDED"
    invited.save(update_fields=["status", "updated_at"])
    blocked = api.client.post(
        "/api/v1/auth/password/reset/confirm",
        {"token": reset, "password": "a-different-password"},
        format="json",
    )
    assert blocked.status_code == 401
    assert blocked.json()["errors"][0]["code"] == "AUTH_INVALID_TOKEN"
    invited.refresh_from_db()
    assert verify_password(_NEXT, invited.password_hash)
    assert PasswordResetToken.objects.get(token_hash=hash_secret(reset)).used_at is None


def test_reset_lock_is_stored_and_expires(api: SessionClient) -> None:
    user = make_user("cashier@harbor.test")
    for _ in range(5):
        response = api.client.post(
            "/api/v1/auth/password/reset",
            {"email": user.email},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["data"] == {}
    blocked = api.client.post(
        "/api/v1/auth/password/reset",
        {"email": user.email},
        format="json",
    )
    assert blocked.status_code == 429
    assert (
        LoginAttempt.objects.filter(
            email=user.email,
            purpose=LoginAttempt.PURPOSE_PASSWORD_RESET,
            succeeded=False,
        ).count()
        == 5
    )
    LoginAttempt.objects.filter(email=user.email).update(
        attempted_at=timezone.now() - timedelta(minutes=16)
    )
    assert (
        api.client.post(
            "/api/v1/auth/password/reset",
            {"email": user.email},
            format="json",
        ).status_code
        == 200
    )


def _reset(api: SessionClient, email: str, mail: list[tuple[str, str, str]]) -> str:
    before = len(mail)
    response = api.client.post("/api/v1/auth/password/reset", {"email": email}, format="json")
    assert response.status_code == 200
    sent = mail[before:]
    assert len(sent) == 1
    assert sent[0][0] == "reset"
    assert sent[0][2] not in response.content.decode()
    return sent[0][2]
