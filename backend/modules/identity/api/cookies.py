from __future__ import annotations

from datetime import datetime
from typing import Literal, cast

from django.conf import settings
from django.utils import timezone
from rest_framework.response import Response


def set_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
    remaining = int((expires_at - timezone.now()).total_seconds())
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        token,
        max_age=max(remaining, 0),
        httponly=True,
        secure=bool(settings.SESSION_COOKIE_SECURE),
        samesite=_samesite(),
        path=settings.SESSION_COOKIE_PATH,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.SESSION_COOKIE_NAME,
        path=settings.SESSION_COOKIE_PATH,
        samesite=_samesite(),
    )


def _samesite() -> Literal["Lax", "Strict", "None"]:
    value = settings.SESSION_COOKIE_SAMESITE
    if value in {"Lax", "Strict", "None"}:
        return cast(Literal["Lax", "Strict", "None"], value)
    return "Lax"
