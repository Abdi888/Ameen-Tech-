"""Password delivery. The default mailer drops the token instead of logging it."""

from __future__ import annotations

from typing import Protocol


class Mailer(Protocol):
    def send_invite(self, *, email: str, token: str) -> None: ...

    def send_password_reset(self, *, email: str, token: str) -> None: ...


class NullMailer:
    def send_invite(self, *, email: str, token: str) -> None:
        del email, token

    def send_password_reset(self, *, email: str, token: str) -> None:
        del email, token


_mailer: Mailer = NullMailer()


def get_mailer() -> Mailer:
    return _mailer


def set_mailer(mailer: Mailer) -> None:
    global _mailer
    _mailer = mailer
