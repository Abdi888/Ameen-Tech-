"""Overlapping requests keep the lockout cap and the tenant boundary."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable, Iterator
from typing import Any, cast

import pytest
from django.db import connection
from rest_framework.test import APIClient

from modules.access.infrastructure.seed import sync_permission_catalog
from modules.identity.domain.passwords import verify_password
from modules.identity.domain.tokens import hash_secret
from modules.identity.infrastructure.mail import NullMailer, set_mailer
from modules.identity.models import LoginAttempt, PasswordResetToken, User
from tests.support import PASSWORD, grant, make_tenant, make_user

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(scope="module", autouse=True)
def _restore_permission_catalog(
    django_db_setup: None,
    django_db_blocker: Any,
) -> Iterator[None]:
    del django_db_setup
    yield
    from django.db import close_old_connections

    close_old_connections()
    with django_db_blocker.unblock():
        sync_permission_catalog()


def test_concurrent_login_failures_stop_at_five() -> None:
    sync_permission_catalog()
    user = make_user(f"cashier-{uuid.uuid4().hex[:8]}@harbor.test")
    statuses = _burst(
        8,
        lambda client, _index: (
            client.post(
                "/api/v1/auth/login",
                {"email": user.email, "password": "wrong-password-value"},
                format="json",
            ).status_code
        ),
    )
    assert sorted(statuses) == [401, 401, 401, 401, 401, 429, 429, 429]
    assert (
        LoginAttempt.objects.filter(email=user.email, purpose="login", succeeded=False).count() == 5
    )


def test_concurrent_password_reset_keeps_one_live_token() -> None:
    sync_permission_catalog()
    user = make_user(f"cashier-{uuid.uuid4().hex[:8]}@harbor.test")
    sent: list[str] = []
    lock = threading.Lock()

    class CapturingMailer:
        def send_invite(self, *, email: str, token: str) -> None:
            del email, token

        def send_password_reset(self, *, email: str, token: str) -> None:
            del email
            with lock:
                sent.append(token)

    set_mailer(CapturingMailer())
    try:
        statuses = _burst(
            6,
            lambda client, _index: (
                client.post(
                    "/api/v1/auth/password/reset",
                    {"email": user.email},
                    format="json",
                ).status_code
            ),
        )
    finally:
        set_mailer(NullMailer())
    assert sorted(statuses) == [200, 200, 200, 200, 200, 429]
    assert LoginAttempt.objects.filter(email=user.email, purpose="password_reset").count() == 5
    live = PasswordResetToken.objects.get(user=user, used_at__isnull=True)
    assert len(live.token_hash) == 64
    assert sum(hash_secret(token) == live.token_hash for token in sent) == 1


def test_concurrent_confirmations_of_one_token_apply_one_password() -> None:
    sync_permission_catalog()
    user = make_user(f"cashier-{uuid.uuid4().hex[:8]}@harbor.test")
    token = _issue_reset(user.email)
    passwords = ("first-password-one", "second-password-two")
    statuses = _burst(
        2,
        lambda client, index: (
            client.post(
                "/api/v1/auth/password/reset/confirm",
                {"token": token, "password": passwords[index]},
                format="json",
            ).status_code
        ),
    )
    assert sorted(statuses) == [200, 401]
    user.refresh_from_db()
    matched = [item for item in passwords if verify_password(item, user.password_hash)]
    assert len(matched) == 1
    stored = PasswordResetToken.objects.get(token_hash=hash_secret(token))
    assert stored.used_at is not None
    again = _ready_client().post(
        "/api/v1/auth/password/reset/confirm",
        {"token": token, "password": "third-password-value"},
        format="json",
    )
    assert again.status_code == 401
    user.refresh_from_db()
    assert verify_password(matched[0], user.password_hash)


def test_concurrent_tenant_lists_stay_separate() -> None:
    sync_permission_catalog()
    suffix = uuid.uuid4().hex[:8]
    harbor = make_tenant(f"harbor-{suffix}")
    market = make_tenant(f"market-{suffix}")
    user = make_user(f"admin-{suffix}@shared.test")
    harbor_only = make_user(f"only-{suffix}@harbor.test")
    market_only = make_user(f"only-{suffix}@market.test")
    grant(user, harbor, "Administrator")
    grant(user, market, "Administrator")
    grant(harbor_only, harbor, "Cashier")
    grant(market_only, market, "Cashier")
    session = _login(user.email)
    tenants = (harbor.id, market.id)

    def listing(client: APIClient, index: int) -> set[str]:
        client.cookies["ameen_session"] = session
        client.credentials(
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
            HTTP_X_TENANT_ID=str(tenants[index]),
        )
        response = client.get("/api/v1/users")
        assert response.status_code == 200
        return {item["email"] for item in response.json()["data"]}

    results = _burst(2, listing)
    assert results[0] == {user.email, harbor_only.email}
    assert results[1] == {user.email, market_only.email}


def test_concurrent_cashier_cannot_invite_while_an_admin_reads() -> None:
    sync_permission_catalog()
    suffix = uuid.uuid4().hex[:8]
    tenant = make_tenant(f"harbor-{suffix}")
    admin = make_user(f"admin-{suffix}@harbor.test")
    cashier = make_user(f"cashier-{suffix}@harbor.test")
    grant(admin, tenant, "Administrator")
    grant(cashier, tenant, "Cashier")
    sessions = (_login(admin.email), _login(cashier.email))

    def call(client: APIClient, index: int) -> int:
        client.cookies["ameen_session"] = sessions[index]
        client.credentials(
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        if index == 0:
            return client.get("/api/v1/users").status_code
        return client.post(
            "/api/v1/users",
            {
                "email": f"racer-{suffix}@harbor.test",
                "first_name": "Race",
                "last_name": "Condition",
                "role_id": "00000000-0000-0000-0000-000000000000",
            },
            format="json",
        ).status_code

    assert sorted(_burst(2, call)) == [200, 403]
    assert not User.objects.filter(email=f"racer-{suffix}@harbor.test").exists()


def _issue_reset(email: str) -> str:
    sent: list[str] = []

    class CapturingMailer:
        def send_invite(self, *, email: str, token: str) -> None:
            del email, token

        def send_password_reset(self, *, email: str, token: str) -> None:
            del email
            sent.append(token)

    set_mailer(CapturingMailer())
    try:
        response = _ready_client().post(
            "/api/v1/auth/password/reset",
            {"email": email},
            format="json",
        )
    finally:
        set_mailer(NullMailer())
    assert response.status_code == 200
    assert len(sent) == 1
    return sent[0]


def _login(email: str) -> str:
    client = _ready_client()
    response = client.post(
        "/api/v1/auth/login",
        {"email": email, "password": PASSWORD},
        format="json",
    )
    assert response.status_code == 200
    return str(client.cookies["ameen_session"].value)


def _ready_client() -> APIClient:
    client = APIClient(enforce_csrf_checks=True)
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    client.credentials(HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
    return client


def _burst[T](count: int, call: Callable[[APIClient, int], T]) -> list[T]:
    results: list[T] = cast(list[T], [None] * count)
    errors: list[BaseException] = []
    barrier = threading.Barrier(count)

    def worker(index: int) -> None:
        try:
            client = _ready_client()
            barrier.wait(timeout=10)
            results[index] = call(client, index)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        if thread.is_alive():
            errors.append(TimeoutError("worker did not finish"))
    if errors:
        raise errors[0]
    return results
