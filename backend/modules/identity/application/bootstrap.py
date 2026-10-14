"""One-time operator bootstrap. Not an HTTP use case and not provisioning.

Foundation decision D1: create a platform administrator, one initial tenant,
and a separate Owner. The command refuses to run again after
``bootstrap.completed`` is committed. A failure before that commit rolls the
whole attempt back, so the operator can retry. Document 02 tenant statuses
stay ACTIVE, SUSPENDED, or ARCHIVED. No platform permission keys are granted.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, validate_slug
from django.db import IntegrityError, connection, transaction

from modules.access.application.ownership import (
    OwnerEstablishmentError,
    business_owner_role_ready,
    establish_initial_owner,
)
from modules.audit.application import has_recorded_action, record_audit
from modules.identity.application.accounts import (
    AccountRejected,
    create_credentialed_user,
    normalize_email,
)
from modules.identity.domain.passwords import password_rejection
from modules.identity.models import User
from modules.tenants.application.profile import create_retail_tenant, tenant_slug_in_use
from shared.database.transactions import run_in_transaction

if TYPE_CHECKING:
    from modules.tenants.models import Tenant

COMPLETED_ACTION = "bootstrap.completed"
# Serializes the one-time guard. This is not a table and not a tenant setting.
_BOOTSTRAP_LOCK = 4_145_000_051


class BootstrapError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class BootstrapRequest:
    platform_email: str
    platform_password: str
    platform_first_name: str
    platform_last_name: str
    tenant_name: str
    tenant_slug: str
    tenant_timezone: str
    tenant_country_code: str
    owner_email: str
    owner_password: str
    owner_first_name: str
    owner_last_name: str

    def __repr__(self) -> str:
        return (
            "BootstrapRequest("
            f"platform_email={self.platform_email!r}, "
            f"tenant_slug={self.tenant_slug!r}, "
            f"owner_email={self.owner_email!r})"
        )


@dataclass(frozen=True)
class BootstrapResult:
    platform_admin_id: uuid.UUID
    platform_admin_email: str
    tenant_id: uuid.UUID
    tenant_slug: str
    owner_id: uuid.UUID
    owner_email: str


def bootstrap_initial(request: BootstrapRequest) -> BootstrapResult:
    normalized = _normalize(request)
    return run_in_transaction(lambda: _create(normalized))


def _normalize(request: BootstrapRequest) -> BootstrapRequest:
    platform_email = _email(request.platform_email, label="Platform administrator email")
    owner_email = _email(request.owner_email, label="Owner email")
    if platform_email == owner_email:
        raise BootstrapError(
            "The platform administrator and the Owner must be different email addresses."
        )
    _password(request.platform_password, label="Platform administrator")
    _password(request.owner_password, label="Owner")
    return BootstrapRequest(
        platform_email=platform_email,
        platform_password=request.platform_password,
        platform_first_name=_person_name(
            request.platform_first_name,
            label="Platform administrator first name",
        ),
        platform_last_name=_person_name(
            request.platform_last_name,
            label="Platform administrator last name",
        ),
        tenant_name=_tenant_name(request.tenant_name),
        tenant_slug=_slug(request.tenant_slug),
        tenant_timezone=_timezone(request.tenant_timezone),
        tenant_country_code=_country(request.tenant_country_code),
        owner_email=owner_email,
        owner_password=request.owner_password,
        owner_first_name=_person_name(request.owner_first_name, label="Owner first name"),
        owner_last_name=_person_name(request.owner_last_name, label="Owner last name"),
    )


def _create(request: BootstrapRequest) -> BootstrapResult:
    _lock()
    if has_recorded_action(COMPLETED_ACTION):
        raise BootstrapError(
            "Bootstrap has already been completed. This command does not run again."
        )
    if not business_owner_role_ready():
        raise BootstrapError(
            "The Business Owner system role is not available. Apply migrations before bootstrap."
        )
    if User.objects.filter(email=request.platform_email).exists():
        raise BootstrapError("The platform administrator email is already in use.")
    if User.objects.filter(email=request.owner_email).exists():
        raise BootstrapError("The Owner email is already in use.")
    if tenant_slug_in_use(request.tenant_slug):
        raise BootstrapError("The tenant slug is already in use.")

    platform_admin = _insert_user(
        email=request.platform_email,
        password=request.platform_password,
        first_name=request.platform_first_name,
        last_name=request.platform_last_name,
    )
    tenant = _insert_tenant(request)
    owner = _insert_user(
        email=request.owner_email,
        password=request.owner_password,
        first_name=request.owner_first_name,
        last_name=request.owner_last_name,
    )
    try:
        with transaction.atomic():
            membership = establish_initial_owner(tenant_id=tenant.id, user_id=owner.id)
    except OwnerEstablishmentError as exc:
        raise BootstrapError(exc.message) from exc

    record_audit(
        action="bootstrap.platform_admin_created",
        entity_type="user",
        entity_id=platform_admin.id,
        result="success",
        metadata={"email": platform_admin.email},
    )
    record_audit(
        action="bootstrap.tenant_created",
        entity_type="tenant",
        entity_id=tenant.id,
        result="success",
        tenant_id=tenant.id,
        metadata={"name": tenant.name, "slug": tenant.slug},
    )
    record_audit(
        action="bootstrap.owner_created",
        entity_type="tenant_membership",
        entity_id=membership.id,
        result="success",
        tenant_id=tenant.id,
        metadata={"email": owner.email, "role": "Business Owner"},
    )
    record_audit(
        action=COMPLETED_ACTION,
        entity_type="tenant",
        entity_id=tenant.id,
        result="success",
        tenant_id=tenant.id,
        metadata={
            "platform_admin_id": str(platform_admin.id),
            "owner_id": str(owner.id),
        },
    )
    return BootstrapResult(
        platform_admin_id=platform_admin.id,
        platform_admin_email=platform_admin.email,
        tenant_id=tenant.id,
        tenant_slug=tenant.slug,
        owner_id=owner.id,
        owner_email=owner.email,
    )


def _insert_user(*, email: str, password: str, first_name: str, last_name: str) -> User:
    try:
        with transaction.atomic():
            return create_credentialed_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
    except AccountRejected as exc:
        raise BootstrapError(exc.message) from exc
    except IntegrityError as exc:
        raise BootstrapError("A user with this email already exists.") from exc


def _insert_tenant(request: BootstrapRequest) -> Tenant:
    try:
        with transaction.atomic():
            return create_retail_tenant(
                name=request.tenant_name,
                slug=request.tenant_slug,
                timezone_name=request.tenant_timezone,
                country_code=request.tenant_country_code,
            )
    except IntegrityError as exc:
        raise BootstrapError("The tenant slug is already in use.") from exc


def _lock() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [_BOOTSTRAP_LOCK])


def _email(value: str, *, label: str) -> str:
    normalized = normalize_email(value)
    if not normalized or len(normalized) > 254:
        raise BootstrapError(f"{label} is not a valid email address.")
    try:
        validate_email(normalized)
    except ValidationError as exc:
        raise BootstrapError(f"{label} is not a valid email address.") from exc
    return normalized


def _person_name(value: str, *, label: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 150:
        raise BootstrapError(f"{label} must be 1 to 150 characters.")
    return cleaned


def _tenant_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 200:
        raise BootstrapError("Tenant name must be 1 to 200 characters.")
    return cleaned


def _slug(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or cleaned != cleaned.lower() or len(cleaned) > 80:
        raise BootstrapError("Tenant slug must be a lowercase slug of at most 80 characters.")
    try:
        validate_slug(cleaned)
    except ValidationError as exc:
        raise BootstrapError(
            "Tenant slug must be a lowercase slug of at most 80 characters."
        ) from exc
    return cleaned


def _timezone(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 64:
        raise BootstrapError("Tenant timezone must be an IANA timezone name.")
    try:
        ZoneInfo(cleaned)
    except ZoneInfoNotFoundError as exc:
        raise BootstrapError("Tenant timezone must be an IANA timezone name.") from exc
    return cleaned


def _country(value: str) -> str:
    cleaned = value.strip().upper()
    if cleaned and (len(cleaned) != 2 or not cleaned.isascii() or not cleaned.isalpha()):
        raise BootstrapError("Tenant country code must be two letters or empty.")
    return cleaned


def _password(value: str, *, label: str) -> None:
    problem = password_rejection(
        value,
        minimum=settings.PASSWORD_MIN_LENGTH,
        maximum=settings.PASSWORD_MAX_LENGTH,
    )
    if problem:
        detail = problem[0].lower() + problem[1:]
        raise BootstrapError(f"{label} {detail}")
