"""URLs used only by tests. They are not mounted in config.urls."""

from collections.abc import Sequence

from django.http import HttpRequest, HttpResponse
from django.urls import path
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class ProtectedView(APIView):
    def get(self, request: Request) -> Response:
        return Response({"leaked": True})


class CrashView(APIView):
    authentication_classes: Sequence[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        raise RuntimeError("marker-do-not-leak")


class EchoView(APIView):
    authentication_classes: Sequence[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        return Response({"data": request.data})


def raw_crash(request: HttpRequest) -> HttpResponse:
    raise RuntimeError("marker-do-not-leak")


class CsrfProbeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        return Response({"ok": True})


urlpatterns = [
    path("api/v1/protected", ProtectedView.as_view()),
    path("api/v1/crash", CrashView.as_view()),
    path("api/v1/raw-crash", raw_crash),
    path("api/v1/echo", EchoView.as_view()),
    path("api/v1/csrf-probe", CsrfProbeView.as_view()),
]

handler404 = "shared.api.errors.not_found"
handler500 = "shared.api.errors.server_error"
