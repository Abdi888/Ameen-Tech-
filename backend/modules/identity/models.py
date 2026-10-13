"""Credentials and sessions. Roles stay in the access module."""

from __future__ import annotations

from django.db import models

from shared.database.models import TimestampedModel, UuidModel


class User(TimestampedModel):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True, default="")
    password_hash = models.TextField(blank=True, default="")
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    status = models.CharField(max_length=32)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = '"identity"."users"'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["ACTIVE", "INVITED", "SUSPENDED", "DISABLED"]),
                name="users_status_known",
            ),
        ]

    def __str__(self) -> str:
        return self.email


class Session(UuidModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sessions")
    tenant = models.ForeignKey(
        "tenants.Tenant",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_used_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    class Meta:
        db_table = '"identity"."sessions"'
        indexes = [
            models.Index(fields=["user", "revoked_at"], name="sessions_user_revoked_idx"),
        ]


class LoginAttempt(UuidModel):
    PURPOSE_LOGIN = "login"
    PURPOSE_PASSWORD_RESET = "password_reset"

    email = models.CharField(max_length=254)
    ip = models.GenericIPAddressField(null=True, blank=True)
    succeeded = models.BooleanField(default=False)
    purpose = models.CharField(max_length=32, default=PURPOSE_LOGIN)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = '"identity"."login_attempts"'
        indexes = [
            models.Index(
                fields=["email", "purpose", "attempted_at"],
                name="login_attempt_email_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(purpose__in=["login", "password_reset"]),
                name="login_attempt_purpose",
            ),
        ]


class PasswordResetToken(UuidModel):
    PURPOSE_INVITE = "invite"
    PURPOSE_RESET = "reset"

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="password_reset_tokens")
    token_hash = models.CharField(max_length=64, unique=True)
    purpose = models.CharField(max_length=32)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = '"identity"."password_reset_tokens"'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(purpose__in=["invite", "reset"]),
                name="reset_token_purpose",
            ),
        ]
