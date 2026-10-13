"""Invite preparation, password change, and password reset. No role writes."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from modules.audit.application import record_audit
from modules.identity.application.throttle import locked, pause, record, serialize_attempts
from modules.identity.domain.passwords import hash_password, password_rejection, verify_password
from modules.identity.domain.tokens import hash_secret, new_secret
from modules.identity.models import LoginAttempt, PasswordResetToken, Session, User
from shared.exceptions import ApiError

_GENERIC = "Invalid email or password."


@dataclass(frozen=True)
class PreparedUser:
    user: User
    token: str | None
    token_purpose: str | None


def normalize_email(email: str) -> str:
    return email.strip().lower()


def prepare_invited_user(
    *,
    email: str,
    first_name: str,
    last_name: str,
    phone: str,
) -> PreparedUser:
    normalized = normalize_email(email)
    existing = User.objects.filter(email=normalized).first()
    if existing is not None:
        if existing.status in {"SUSPENDED", "DISABLED"}:
            raise ApiError("RESOURCE_CONFLICT", "This user cannot be invited.")
        token = None
        purpose = None
        if existing.status == "INVITED":
            token = _store_token(existing, PasswordResetToken.PURPOSE_INVITE)
            purpose = PasswordResetToken.PURPOSE_INVITE
        return PreparedUser(existing, token, purpose)
    user = User.objects.create(
        email=normalized,
        phone=phone,
        password_hash="",
        first_name=first_name,
        last_name=last_name,
        status="INVITED",
    )
    token = _store_token(user, PasswordResetToken.PURPOSE_INVITE)
    return PreparedUser(user, token, PasswordResetToken.PURPOSE_INVITE)


def change_password(
    *,
    user_id: uuid.UUID,
    current_password: str,
    new_password: str,
    ip: str | None,
    user_agent: str,
    tenant_id: uuid.UUID | None,
) -> None:
    problem = password_rejection(
        new_password,
        minimum=settings.PASSWORD_MIN_LENGTH,
        maximum=settings.PASSWORD_MAX_LENGTH,
    )
    if problem:
        raise ApiError("VALIDATION_ERROR", problem, field="password")
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)
        if not verify_password(current_password, user.password_hash):
            raise ApiError(
                "VALIDATION_ERROR",
                "Current password is incorrect.",
                field="current_password",
            )
        user.password_hash = hash_password(new_password)
        user.save(update_fields=["password_hash", "updated_at"])
        _revoke_sessions(
            user_id=user.id,
            tenant_id=tenant_id,
            ip=ip,
            user_agent=user_agent,
            reason="password_changed",
        )
        record_audit(
            action="password.changed",
            entity_type="user",
            entity_id=user.id,
            result="success",
            tenant_id=tenant_id,
            user_id=user.id,
            ip=ip,
            user_agent=user_agent,
        )


def request_password_reset(*, email: str, ip: str | None, user_agent: str) -> str | None:
    normalized = normalize_email(email)
    del user_agent
    with transaction.atomic():
        serialize_attempts(
            email=normalized,
            ip=ip,
            purpose=LoginAttempt.PURPOSE_PASSWORD_RESET,
        )
        if locked(email=normalized, ip=ip, purpose=LoginAttempt.PURPOSE_PASSWORD_RESET):
            state = "locked"
            token = None
        else:
            record(
                email=normalized,
                ip=ip,
                purpose=LoginAttempt.PURPOSE_PASSWORD_RESET,
                succeeded=False,
            )
            user = User.objects.filter(email=normalized, status__in=["ACTIVE", "INVITED"]).first()
            token = _store_token(user, PasswordResetToken.PURPOSE_RESET) if user else None
            state = "sent"
    if state == "locked":
        pause(email=normalized, ip=ip, purpose=LoginAttempt.PURPOSE_PASSWORD_RESET)
        raise ApiError(
            "AUTH_INVALID_TOKEN",
            "Too many attempts. Try again later.",
            status_code=429,
        )
    return token


def confirm_password_reset(
    *,
    token: str,
    new_password: str,
    ip: str | None,
    user_agent: str,
) -> uuid.UUID:
    problem = password_rejection(
        new_password,
        minimum=settings.PASSWORD_MIN_LENGTH,
        maximum=settings.PASSWORD_MAX_LENGTH,
    )
    if problem:
        raise ApiError("VALIDATION_ERROR", problem, field="password")
    token_hash = hash_secret(token)
    with transaction.atomic():
        row = (
            PasswordResetToken.objects.select_for_update()
            .select_related("user")
            .filter(token_hash=token_hash)
            .first()
        )
        if row is None or row.used_at is not None:
            raise ApiError("AUTH_INVALID_TOKEN", "Authentication failed.")
        if row.expires_at <= timezone.now():
            raise ApiError("AUTH_TOKEN_EXPIRED", "Session expired.")
        user = User.objects.select_for_update().get(pk=row.user_id)
        if user.status in {"SUSPENDED", "DISABLED"}:
            raise ApiError("AUTH_INVALID_TOKEN", "Authentication failed.")
        user.password_hash = hash_password(new_password)
        if user.status == "INVITED":
            user.status = "ACTIVE"
        if user.email_verified_at is None:
            user.email_verified_at = timezone.now()
        user.save(update_fields=["password_hash", "status", "email_verified_at", "updated_at"])
        row.used_at = timezone.now()
        row.save(update_fields=["used_at"])
        _revoke_sessions(
            user_id=user.id,
            tenant_id=None,
            ip=ip,
            user_agent=user_agent,
            reason="password_reset",
        )
        record_audit(
            action="password.reset",
            entity_type="user",
            entity_id=user.id,
            result="success",
            user_id=user.id,
            ip=ip,
            user_agent=user_agent,
        )
        return user.id


def _store_token(user: User, purpose: str) -> str:
    raw = new_secret()
    now = timezone.now()
    PasswordResetToken.objects.filter(user=user, purpose=purpose, used_at__isnull=True).update(
        used_at=now
    )
    PasswordResetToken.objects.create(
        user=user,
        token_hash=hash_secret(raw),
        purpose=purpose,
        expires_at=now + timedelta(seconds=settings.PASSWORD_RESET_TTL_SECONDS),
    )
    return raw


def _revoke_sessions(
    *,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID | None,
    ip: str | None,
    user_agent: str,
    reason: str,
) -> None:
    updated = Session.objects.filter(user_id=user_id, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
    if not updated:
        return
    record_audit(
        action="session.revoked",
        entity_type="session",
        result="success",
        tenant_id=tenant_id,
        user_id=user_id,
        metadata={"reason": reason},
        ip=ip,
        user_agent=user_agent,
    )
