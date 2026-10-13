"""Test data helpers. Passwords use the production Argon2id settings."""

from __future__ import annotations

import uuid
from typing import Any

from rest_framework.test import APIClient

from modules.access.models import Role, TenantMembership, TenantUserRole
from modules.identity.domain.passwords import hash_password
from modules.identity.models import User
from modules.tenants.models import Tenant

PASSWORD = "correct-horse-battery"


class SessionClient:
    def __init__(self, client: APIClient, csrf: str) -> None:
        self.client = client
        self.csrf = csrf
        self.tenant_id: str | None = None
        self._apply()

    def _apply(self) -> None:
        headers = {"HTTP_X_CSRFTOKEN": self.csrf}
        if self.tenant_id:
            headers["HTTP_X_TENANT_ID"] = self.tenant_id
        self.client.credentials(**headers)

    def use_tenant(self, tenant_id: uuid.UUID | None) -> None:
        self.tenant_id = str(tenant_id) if tenant_id else None
        self._apply()


def make_tenant(slug: str, *, status: str = "ACTIVE") -> Tenant:
    return Tenant.objects.create(
        name=slug,
        slug=slug,
        business_type="RETAIL",
        status=status,
        timezone="Africa/Mogadishu",
        country_code="SO",
    )


def make_user(email: str, *, password: str | None = PASSWORD, status: str = "ACTIVE") -> User:
    return User.objects.create(
        email=email.strip().lower(),
        password_hash=hash_password(password) if password else "",
        first_name="Amina",
        last_name="Hassan",
        phone="",
        status=status,
    )


def grant(
    user: User,
    tenant: Tenant,
    role_name: str,
    *,
    membership_status: str = "ACTIVE",
    is_owner: bool = False,
    branch_id: uuid.UUID | None = None,
    all_branches: bool = True,
) -> TenantMembership:
    role = Role.objects.get(name=role_name, tenant__isnull=True, is_system_role=True)
    membership = TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        status=membership_status,
        is_owner=is_owner,
    )
    TenantUserRole.objects.create(
        membership=membership,
        role=role,
        branch_id=branch_id,
        applies_to_all_branches=all_branches,
    )
    return membership


def login(
    api: SessionClient,
    email: str,
    password: str = PASSWORD,
    *,
    tenant: Tenant | None = None,
) -> Any:
    if tenant is not None:
        api.use_tenant(tenant.id)
    return api.client.post(
        "/api/v1/auth/login",
        {"email": email, "password": password},
        format="json",
    )
