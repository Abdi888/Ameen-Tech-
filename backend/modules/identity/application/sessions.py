"""Login, logout, and session loading."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from modules.access.application.authorization import granted_permission_codes
from modules.access.application.queries import profile_for, resolve_access
from modules.audit.application import record_audit
from modules.identity.application.accounts import normalize_email
from modules.identity.application.throttle import locked, pause, record, serialize_attempts
from modules.identity.domain.actor import Actor
from modules.identity.domain.passwords import verify_password
from modules.identity.domain.tokens import hash_secret, new_secret
from modules.identity.models import LoginAttempt, Session, User
from shared.api.context import bind_actor, read_context
from shared.exceptions import ApiError

_GENERIC = "Invalid email or password."


@dataclass(frozen=True)
class LoginResult:
    token: str
    expires_at: datetime
    profile: dict[str, object]


def login_user(
    *,
    email: str,
    password: str,
    tenant_hint: str | None,
    ip: str | None,
    user_agent: str,
) -> LoginResult:
    normalized = normalize_email(email)
    accepted: User | None = None
    with transaction.atomic():
        serialize_attempts(email=normalized, ip=ip, purpose=LoginAttempt.PURPOSE_LOGIN)
        if locked(email=normalized, ip=ip, purpose=LoginAttempt.PURPOSE_LOGIN):
            state = "locked"
        else:
            user = User.objects.filter(email=normalized).first()
            password_ok = verify_password(password, user.password_hash if user else None)
            failed = user is None or not password_ok or user.status != "ACTIVE"
            if failed:
                record(
                    email=normalized,
                    ip=ip,
                    purpose=LoginAttempt.PURPOSE_LOGIN,
                    succeeded=False,
                )
                record_audit(
                    action="login.failure",
                    entity_type="user",
                    entity_id=user.id if user else None,
                    result="failure",
                    user_id=user.id if user else None,
                    metadata={"email": normalized},
                    ip=ip,
                    user_agent=user_agent,
                )
                state = "bad"
            else:
                accepted = user
                state = "good"
    if state == "locked":
        pause(email=normalized, ip=ip, purpose=LoginAttempt.PURPOSE_LOGIN)
        raise ApiError("AUTH_INVALID_TOKEN", "Too many attempts. Try again later.", status_code=429)
    if accepted is None:
        pause(email=normalized, ip=ip, purpose=LoginAttempt.PURPOSE_LOGIN)
        raise ApiError("AUTH_INVALID_TOKEN", _GENERIC)
    user = accepted
    resolution = resolve_access(
        user_id=user.id,
        tenant_hint=tenant_hint,
        session_tenant_id=None,
    )
    if resolution.denied:
        record_audit(
            action="tenant.access_denied",
            entity_type="tenant",
            entity_id=resolution.hinted_tenant_id,
            result="failure",
            user_id=user.id,
            ip=ip,
            user_agent=user_agent,
        )
        raise ApiError("TENANT_ACCESS_DENIED", "You do not have access to this tenant.")
    with transaction.atomic():
        now = timezone.now()
        raw = new_secret()
        expires_at = now + timedelta(seconds=settings.SESSION_ABSOLUTE_SECONDS)
        tenant_id = resolution.context.tenant_id if resolution.context else None
        Session.objects.create(
            user=user,
            tenant_id=tenant_id,
            token_hash=hash_secret(raw),
            expires_at=expires_at,
            last_used_at=now,
            ip=ip,
            user_agent=user_agent,
        )
        user.last_login_at = now
        user.save(update_fields=["last_login_at", "updated_at"])
        record(
            email=normalized,
            ip=ip,
            purpose=LoginAttempt.PURPOSE_LOGIN,
            succeeded=True,
        )
        record_audit(
            action="login.success",
            entity_type="user",
            entity_id=user.id,
            result="success",
            tenant_id=tenant_id,
            user_id=user.id,
            ip=ip,
            user_agent=user_agent,
        )
    membership_id = resolution.context.membership_id if resolution.context else None
    return LoginResult(
        token=raw,
        expires_at=expires_at,
        profile=profile_for(user_id=user.id, membership_id=membership_id),
    )


def logout_user(
    *,
    token_hash: str,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID | None,
    ip: str | None,
    user_agent: str,
) -> None:
    with transaction.atomic():
        updated = Session.objects.filter(token_hash=token_hash, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )
        if updated:
            record_audit(
                action="logout",
                entity_type="session",
                result="success",
                tenant_id=tenant_id,
                user_id=user_id,
                ip=ip,
                user_agent=user_agent,
            )
            record_audit(
                action="session.revoked",
                entity_type="session",
                result="success",
                tenant_id=tenant_id,
                user_id=user_id,
                metadata={"reason": "logout"},
                ip=ip,
                user_agent=user_agent,
            )


def authenticate_session(request: HttpRequest) -> tuple[Actor, str] | None:
    raw = request.COOKIES.get(settings.SESSION_COOKIE_NAME, "")
    if not raw:
        return None
    if len(raw) > 200:
        raise ApiError("AUTH_INVALID_TOKEN", "Authentication failed.")
    token_hash = hash_secret(raw)
    session = Session.objects.select_related("user").filter(token_hash=token_hash).first()
    if session is None or session.revoked_at is not None or session.user.status != "ACTIVE":
        raise ApiError("AUTH_INVALID_TOKEN", "Authentication failed.")
    now = timezone.now()
    idle_deadline = session.last_used_at + timedelta(seconds=settings.SESSION_IDLE_SECONDS)
    if session.expires_at <= now or idle_deadline <= now:
        session.revoked_at = now
        session.save(update_fields=["revoked_at"])
        record_audit(
            action="session.revoked",
            entity_type="session",
            entity_id=session.id,
            result="failure",
            tenant_id=session.tenant_id,
            user_id=session.user_id,
            metadata={"reason": "expired"},
            ip=session.ip,
            user_agent=session.user_agent,
        )
        raise ApiError("AUTH_TOKEN_EXPIRED", "Session expired.")
    context = read_context(request)
    hint = context.tenant_hint if context else None
    resolution = resolve_access(
        user_id=session.user_id,
        tenant_hint=hint,
        session_tenant_id=session.tenant_id,
    )
    if resolution.denied:
        bind_actor(request, user_id=str(session.user_id), proven_tenant_id=None)
        record_audit(
            action="tenant.access_denied",
            entity_type="tenant",
            entity_id=resolution.hinted_tenant_id,
            result="failure",
            user_id=session.user_id,
            ip=session.ip,
            user_agent=session.user_agent,
        )
        raise ApiError("TENANT_ACCESS_DENIED", "You do not have access to this tenant.")
    tenant_id = resolution.context.tenant_id if resolution.context else None
    membership_id = resolution.context.membership_id if resolution.context else None
    session.last_used_at = now
    session.tenant_id = tenant_id
    session.save(update_fields=["last_used_at", "tenant"])
    permissions: frozenset[str] = frozenset()
    if membership_id is not None:
        permissions = frozenset(
            granted_permission_codes(membership_id=membership_id, branch_id=None)
        )
    bind_actor(
        request,
        user_id=str(session.user_id),
        proven_tenant_id=str(tenant_id) if tenant_id else None,
        permissions=permissions,
    )
    return (
        Actor(id=session.user_id, tenant_id=tenant_id, membership_id=membership_id),
        token_hash,
    )
