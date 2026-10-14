"""Create a tenant profile. Callers do not pass ``tenant_id``."""

from __future__ import annotations

from modules.tenants.models import Tenant


def tenant_slug_in_use(slug: str) -> bool:
    return Tenant.objects.filter(slug=slug).exists()


def create_retail_tenant(
    *,
    name: str,
    slug: str,
    timezone_name: str,
    country_code: str,
) -> Tenant:
    """Insert one ACTIVE retail tenant. Document 02 has no provisioning status."""
    return Tenant.objects.create(
        name=name,
        slug=slug,
        business_type="RETAIL",
        status="ACTIVE",
        timezone=timezone_name,
        country_code=country_code,
    )
