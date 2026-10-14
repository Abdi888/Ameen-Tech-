"""Create the Playwright database and fixture users. Not a product command."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
os.environ.setdefault("SECRET_KEY", "test-only-not-for-production")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault(
    "DATABASE_URL", "postgres://ameen:ameen@localhost:5432/ameen_retail_e2e"
)
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:5173")


def ensure_database() -> None:
    import psycopg
    from psycopg import sql

    parsed = urlparse(os.environ["DATABASE_URL"])
    name = parsed.path.lstrip("/")
    admin_url = urlunparse(parsed._replace(path="/postgres"))
    with psycopg.connect(admin_url, autocommit=True) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (name,),
        ).fetchone()
        if exists:
            return
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))


def seed() -> None:
    import django

    django.setup()
    from django.core.management import call_command

    from modules.access.models import TenantMembership, TenantUserRole
    from modules.identity.domain.passwords import hash_password
    from modules.identity.models import LoginAttempt, User
    from modules.tenants.models import Tenant
    from tests.support import PASSWORD, grant, make_tenant, make_user

    call_command("migrate", interactive=False)
    tenant = Tenant.objects.filter(slug="e2e-harbor").first()
    if tenant is None:
        tenant = make_tenant("e2e-harbor")
    tenant.name = "Harbor"
    tenant.status = "ACTIVE"
    tenant.save()

    def ensure_user(email: str) -> User:
        user = User.objects.filter(email=email).first()
        if user is None:
            return make_user(email)
        user.password_hash = hash_password(PASSWORD)
        user.status = "ACTIVE"
        user.first_name = "Amina"
        user.last_name = "Hassan"
        user.save()
        return user

    def ensure_member(user: User, role_name: str, *, is_owner: bool) -> None:
        membership = (
            TenantMembership.objects.filter(user=user, tenant=tenant).exclude(status="REMOVED").first()
        )
        if membership is None:
            grant(user, tenant, role_name, is_owner=is_owner)
            return
        membership.status = "ACTIVE"
        membership.is_owner = is_owner
        membership.save()
        from modules.access.models import Role

        role = Role.objects.get(name=role_name, tenant__isnull=True, is_system_role=True)
        TenantUserRole.objects.get_or_create(
            membership=membership,
            role=role,
            defaults={"branch_id": None, "applies_to_all_branches": True},
        )

    emails = (
        "owner@e2e.test",
        "admin@e2e.test",
        "cashier@e2e.test",
        "platform@e2e.test",
        "nobody@e2e.test",
    )
    LoginAttempt.objects.filter(email__in=emails).delete()
    ensure_member(ensure_user("owner@e2e.test"), "Business Owner", is_owner=True)
    ensure_member(ensure_user("admin@e2e.test"), "Administrator", is_owner=False)
    ensure_member(ensure_user("cashier@e2e.test"), "Cashier", is_owner=False)
    platform = ensure_user("platform@e2e.test")
    platform_memberships = TenantMembership.objects.filter(user=platform)
    TenantUserRole.objects.filter(membership__in=platform_memberships).delete()
    platform_memberships.delete()
    print("Playwright fixtures ready.")


if __name__ == "__main__":
    ensure_database()
    seed()
