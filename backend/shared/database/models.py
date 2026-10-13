"""Shared primary-key columns and the idempotency table. Not a business module."""

from __future__ import annotations

import uuid

from django.db import models


class UuidModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(UuidModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IdempotencyKey(UuidModel):
    """Stored command result. Document 02: UNIQUE(tenant_id, key).

    The same key may be stored for two tenants. A second row for one tenant
    and key is rejected. ``response`` is the JSON body to replay and must not
    contain passwords, tokens, or card numbers. Document 02 does not set a
    length for ``key`` or ``endpoint``, so both are text.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="idempotency_keys",
    )
    key = models.TextField()
    endpoint = models.TextField()
    response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = '"system"."idempotency_keys"'
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "key"],
                name="idempotency_tenant_key",
            ),
        ]
