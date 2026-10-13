"""Tenant profile.

Document 02 declares ``default_currency_id`` as a foreign key to ``currencies``.
That table is not part of identity, so the column stays a nullable UUID until
the currency table is created. Do not treat the value as a live reference.
"""

from __future__ import annotations

from django.db import models

from shared.database.models import TimestampedModel


class Tenant(TimestampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    business_type = models.CharField(max_length=32, default="RETAIL")
    default_currency_id = models.UUIDField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    country_code = models.CharField(max_length=2, default="")
    logo_url = models.TextField(blank=True, default="")
    status = models.CharField(max_length=32)

    class Meta:
        db_table = '"organization"."tenants"'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(business_type="RETAIL"),
                name="tenants_business_type_retail",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["ACTIVE", "SUSPENDED", "ARCHIVED"]),
                name="tenants_status_known",
            ),
        ]

    def __str__(self) -> str:
        return self.slug
