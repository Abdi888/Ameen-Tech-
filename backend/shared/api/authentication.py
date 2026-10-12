"""Web authentication foundation.

Document 00 §10 and Document 06: the browser uses an HttpOnly session cookie.
Bearer tokens and localStorage are not a web strategy. Sessions are not stored
yet, so this class authenticates nobody and protected routes fail closed.

DRF marks API views as CSRF-exempt and checks CSRF inside session
authentication. This class does that check on unsafe methods. The Django
reason is not returned to the client.
"""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

from shared.exceptions import ApiError


class _CsrfReason(CsrfViewMiddleware):
    def _reject(self, request: HttpRequest, reason: str) -> str:
        return reason


def _unused_response(_request: HttpRequest) -> HttpResponse:
    return HttpResponse()


class CookieSessionAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> tuple[Any, Any] | None:
        self._enforce_csrf(request)
        return None

    def _enforce_csrf(self, request: Request) -> None:
        check = _CsrfReason(_unused_response)
        check.process_request(request._request)
        reason = check.process_view(request._request, _unused_response, (), {})
        if reason:
            raise ApiError("PERMISSION_DENIED", "CSRF verification failed.")
