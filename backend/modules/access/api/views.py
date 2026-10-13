"""User and role HTTP adapters."""

from __future__ import annotations

import uuid

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.access.api.serializers import (
    InviteSerializer,
    RoleAssignmentSerializer,
    UserUpdateSerializer,
)
from modules.access.application.directory import (
    get_member,
    invite_member,
    list_members,
    list_roles,
    replace_roles,
    set_member_active,
    update_member,
)
from modules.identity.api.serializers import parse
from modules.identity.domain.actor import Actor
from modules.identity.infrastructure.mail import get_mailer
from modules.identity.models import PasswordResetToken
from shared.api.clients import request_ip, request_user_agent
from shared.api.pagination import pagination_meta, read_page
from shared.api.responses import success_body

_USER_SORTS = {
    "email": "user__email",
    "-email": "-user__email",
    "created_at": "created_at",
    "-created_at": "-created_at",
}


class UserCollectionView(APIView):
    required_permissions = {"GET": "users.view", "POST": "users.create"}

    def get(self, request: Request) -> Response:
        actor = _actor(request)
        page, page_size, order_by = read_page(request.query_params, allowed_sorts=_USER_SORTS)
        rows, total = list_members(
            tenant_id=_tenant(actor),
            page=page,
            page_size=page_size,
            order_by=order_by,
        )
        return Response(
            success_body(rows, pagination_meta(page=page, page_size=page_size, total=total))
        )

    def post(self, request: Request) -> Response:
        actor = _actor(request)
        payload = parse(InviteSerializer(data=request.data))
        result = invite_member(
            tenant_id=_tenant(actor),
            actor_id=actor.id,
            email=str(payload["email"]),
            first_name=str(payload["first_name"]),
            last_name=str(payload["last_name"]),
            phone=str(payload.get("phone", "")),
            role_id=_uuid(payload["role_id"]),
            ip=request_ip(request._request),
            user_agent=request_user_agent(request._request),
        )
        if result.token and result.token_purpose == PasswordResetToken.PURPOSE_INVITE:
            get_mailer().send_invite(email=result.email, token=result.token)
        return Response(success_body(result.public), status=201)


class UserDetailView(APIView):
    required_permissions = {"GET": "users.view", "PATCH": "users.update"}

    def get(self, request: Request, user_id: uuid.UUID) -> Response:
        actor = _actor(request)
        return Response(success_body(get_member(tenant_id=_tenant(actor), user_id=user_id)))

    def patch(self, request: Request, user_id: uuid.UUID) -> Response:
        actor = _actor(request)
        payload = parse(UserUpdateSerializer(data=request.data))
        changes = {key: str(value) for key, value in payload.items()}
        return Response(
            success_body(
                update_member(
                    tenant_id=_tenant(actor),
                    user_id=user_id,
                    actor_id=actor.id,
                    changes=changes,
                    ip=request_ip(request._request),
                    user_agent=request_user_agent(request._request),
                )
            )
        )


class ActivateUserView(APIView):
    required_permission = "users.activate"

    def post(self, request: Request, user_id: uuid.UUID) -> Response:
        return _set_active(request, user_id, active=True)


class DeactivateUserView(APIView):
    required_permission = "users.deactivate"

    def post(self, request: Request, user_id: uuid.UUID) -> Response:
        return _set_active(request, user_id, active=False)


class UserRoleView(APIView):
    required_permissions = {"GET": "users.view", "POST": "users.assign_roles"}

    def get(self, request: Request, user_id: uuid.UUID) -> Response:
        actor = _actor(request)
        member = get_member(tenant_id=_tenant(actor), user_id=user_id)
        return Response(success_body({"roles": member["roles"]}))

    def post(self, request: Request, user_id: uuid.UUID) -> Response:
        actor = _actor(request)
        payload = parse(RoleAssignmentSerializer(data=request.data))
        member = replace_roles(
            tenant_id=_tenant(actor),
            user_id=user_id,
            actor_id=actor.id,
            role_ids=_uuids(payload["role_ids"]),
            ip=request_ip(request._request),
            user_agent=request_user_agent(request._request),
        )
        return Response(success_body({"roles": member["roles"]}))


class RoleCollectionView(APIView):
    required_permission = "users.view"

    def get(self, request: Request) -> Response:
        _actor(request)
        page, page_size, _order = read_page(request.query_params, allowed_sorts={})
        rows, total = list_roles(page=page, page_size=page_size)
        return Response(
            success_body(rows, pagination_meta(page=page, page_size=page_size, total=total))
        )


def _set_active(request: Request, user_id: uuid.UUID, *, active: bool) -> Response:
    actor = _actor(request)
    return Response(
        success_body(
            set_member_active(
                tenant_id=_tenant(actor),
                user_id=user_id,
                actor_id=actor.id,
                active=active,
                ip=request_ip(request._request),
                user_agent=request_user_agent(request._request),
            )
        )
    )


def _uuid(value: object) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _uuids(value: object) -> list[uuid.UUID]:
    if not isinstance(value, list):
        return []
    return [_uuid(item) for item in value]


def _actor(request: Request) -> Actor:
    user = request.user
    if isinstance(user, Actor):
        return user
    raise RuntimeError("Authenticated request is missing an actor.")


def _tenant(actor: Actor) -> uuid.UUID:
    if actor.tenant_id is None:
        raise RuntimeError("Tenant permission check did not bind a tenant.")
    return actor.tenant_id
