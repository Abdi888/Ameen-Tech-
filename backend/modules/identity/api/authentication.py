"""Cookie session authentication. The raw token is never a response field."""

from __future__ import annotations

from typing import Any

from rest_framework.request import Request

from modules.identity.application.sessions import authenticate_session
from shared.api.authentication import CsrfAuthentication


class CookieSessionAuthentication(CsrfAuthentication):
    def authenticate(self, request: Request) -> tuple[Any, Any] | None:
        self.enforce_csrf(request)
        return authenticate_session(request._request)
