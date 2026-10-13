from __future__ import annotations

from collections.abc import Iterator

import pytest
from rest_framework.test import APIClient

from modules.identity.infrastructure.mail import NullMailer, set_mailer
from tests.support import SessionClient


@pytest.fixture
def api(db: None) -> SessionClient:
    del db
    client = APIClient(enforce_csrf_checks=True)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "csrftoken" in response.cookies
    return SessionClient(client, response.cookies["csrftoken"].value)


@pytest.fixture
def mail() -> Iterator[list[tuple[str, str, str]]]:
    sent: list[tuple[str, str, str]] = []

    class CapturingMailer:
        def send_invite(self, *, email: str, token: str) -> None:
            sent.append(("invite", email, token))

        def send_password_reset(self, *, email: str, token: str) -> None:
            sent.append(("reset", email, token))

    set_mailer(CapturingMailer())
    yield sent
    set_mailer(NullMailer())
