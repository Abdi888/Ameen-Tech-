"""Auth HTTP adapters. Rules stay in the application use cases."""

from __future__ import annotations

from django.db import transaction
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.application.queries import activate_invited_memberships, profile_for
from modules.identity.api.cookies import clear_session_cookie, set_session_cookie
from modules.identity.api.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    parse,
)
from modules.identity.application.accounts import (
    change_password,
    confirm_password_reset,
    request_password_reset,
)
from modules.identity.application.sessions import login_user, logout_user
from modules.identity.domain.actor import Actor
from modules.identity.infrastructure.mail import get_mailer
from shared.api.authentication import CsrfAuthentication
from shared.api.clients import request_ip, request_user_agent
from shared.api.context import read_context
from shared.api.responses import success_body


class LoginView(APIView):
    authentication_classes = [CsrfAuthentication]
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        payload = parse(LoginSerializer(data=request.data))
        context = read_context(request._request)
        result = login_user(
            email=str(payload["email"]),
            password=str(payload["password"]),
            tenant_hint=context.tenant_hint if context else None,
            ip=request_ip(request._request),
            user_agent=request_user_agent(request._request),
        )
        response = Response(success_body(result.profile))
        set_session_cookie(response, result.token, result.expires_at)
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        actor = _actor(request)
        token_hash = request.auth if isinstance(request.auth, str) else ""
        logout_user(
            token_hash=token_hash,
            user_id=actor.id,
            tenant_id=actor.tenant_id,
            ip=request_ip(request._request),
            user_agent=request_user_agent(request._request),
        )
        response = Response(success_body({}))
        clear_session_cookie(response)
        return response


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        actor = _actor(request)
        return Response(
            success_body(profile_for(user_id=actor.id, membership_id=actor.membership_id))
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        payload = parse(ChangePasswordSerializer(data=request.data))
        actor = _actor(request)
        change_password(
            user_id=actor.id,
            current_password=str(payload["current_password"]),
            new_password=str(payload["password"]),
            ip=request_ip(request._request),
            user_agent=request_user_agent(request._request),
            tenant_id=actor.tenant_id,
        )
        response = Response(success_body({}))
        clear_session_cookie(response)
        return response


class PasswordResetView(APIView):
    authentication_classes = [CsrfAuthentication]
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        payload = parse(PasswordResetSerializer(data=request.data))
        email = str(payload["email"]).strip().lower()
        token = request_password_reset(
            email=email,
            ip=request_ip(request._request),
            user_agent=request_user_agent(request._request),
        )
        if token:
            get_mailer().send_password_reset(email=email, token=token)
        return Response(success_body({}))


class PasswordResetConfirmView(APIView):
    authentication_classes = [CsrfAuthentication]
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        payload = parse(PasswordResetConfirmSerializer(data=request.data))
        ip = request_ip(request._request)
        user_agent = request_user_agent(request._request)
        with transaction.atomic():
            user_id = confirm_password_reset(
                token=str(payload["token"]),
                new_password=str(payload["password"]),
                ip=ip,
                user_agent=user_agent,
            )
            activate_invited_memberships(user_id=user_id, ip=ip, user_agent=user_agent)
        response = Response(success_body({}))
        clear_session_cookie(response)
        return response


def _actor(request: Request) -> Actor:
    user = request.user
    if isinstance(user, Actor):
        return user
    raise RuntimeError("Authenticated request is missing an actor.")
