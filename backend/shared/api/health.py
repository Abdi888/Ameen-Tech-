"""Operational health check. Not a Document 05 business resource.

The pack requires health checks and does not name a path. This uses the
`/api/v1` base from Document 05.
"""

from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.api.context import remember_error
from shared.api.responses import error_body, success_body
from shared.database.checks import database_is_reachable


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        if not database_is_reachable():
            remember_error(request._request, "SERVICE_UNAVAILABLE")
            return Response(
                error_body(code="SERVICE_UNAVAILABLE", message="Database is unavailable."),
                status=503,
            )
        return Response(success_body({"status": "ok", "database": "ok"}))
