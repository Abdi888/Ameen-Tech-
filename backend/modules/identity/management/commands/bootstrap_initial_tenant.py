"""Create the initial platform administrator, tenant, and separate Owner.

Not an HTTP command. Passwords are read from the process environment or, on
an interactive terminal, from a hidden prompt. They are never command
arguments. See docs/operations/bootstrap.md.
"""

from __future__ import annotations

import getpass
import os
import sys
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from modules.identity.application.bootstrap import (
    BootstrapError,
    BootstrapRequest,
    bootstrap_initial,
)

CONFIRM_ENV = "AMEEN_BOOTSTRAP_CONFIRM"
CONFIRM_VALUE = "bootstrap-initial-tenant"
_PLATFORM_PASSWORD = "AMEEN_BOOTSTRAP_PLATFORM_PASSWORD"
_OWNER_PASSWORD = "AMEEN_BOOTSTRAP_OWNER_PASSWORD"


class Command(BaseCommand):
    help = (
        "Create the initial platform administrator, one retail tenant, and a "
        "separate Owner. Refuses to run again. Not a public API. "
        "See docs/operations/bootstrap.md."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        del args, options
        if os.environ.get(CONFIRM_ENV) != CONFIRM_VALUE:
            raise CommandError(
                f"Set {CONFIRM_ENV}={CONFIRM_VALUE} before running bootstrap. "
                "See docs/operations/bootstrap.md."
            )
        platform_password = _password(_PLATFORM_PASSWORD)
        owner_password = _password(_OWNER_PASSWORD)
        os.environ.pop(_PLATFORM_PASSWORD, None)
        os.environ.pop(_OWNER_PASSWORD, None)
        timezone_name = os.environ.get("AMEEN_BOOTSTRAP_TENANT_TIMEZONE", "UTC").strip() or "UTC"
        country_code = os.environ.get("AMEEN_BOOTSTRAP_TENANT_COUNTRY", "")
        request = BootstrapRequest(
            platform_email=_required("AMEEN_BOOTSTRAP_PLATFORM_EMAIL"),
            platform_password=platform_password,
            platform_first_name=_required("AMEEN_BOOTSTRAP_PLATFORM_FIRST_NAME"),
            platform_last_name=_required("AMEEN_BOOTSTRAP_PLATFORM_LAST_NAME"),
            tenant_name=_required("AMEEN_BOOTSTRAP_TENANT_NAME"),
            tenant_slug=_required("AMEEN_BOOTSTRAP_TENANT_SLUG"),
            tenant_timezone=timezone_name,
            tenant_country_code=country_code,
            owner_email=_required("AMEEN_BOOTSTRAP_OWNER_EMAIL"),
            owner_password=owner_password,
            owner_first_name=_required("AMEEN_BOOTSTRAP_OWNER_FIRST_NAME"),
            owner_last_name=_required("AMEEN_BOOTSTRAP_OWNER_LAST_NAME"),
        )
        try:
            result = bootstrap_initial(request)
        except BootstrapError as exc:
            raise CommandError(exc.message) from exc
        self.stdout.write(self.style.SUCCESS("Bootstrap completed."))
        self.stdout.write(f"platform_admin_id={result.platform_admin_id}")
        self.stdout.write(f"platform_admin_email={result.platform_admin_email}")
        self.stdout.write(f"tenant_id={result.tenant_id}")
        self.stdout.write(f"tenant_slug={result.tenant_slug}")
        self.stdout.write(f"owner_id={result.owner_id}")
        self.stdout.write(f"owner_email={result.owner_email}")
        self.stdout.write("This command will refuse to run again. It is not an HTTP API.")


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise CommandError(
            f"Set {name} before running bootstrap. See docs/operations/bootstrap.md."
        )
    return value


def _password(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    if sys.stdin.isatty():
        entered = getpass.getpass(f"{name}: ")
        if entered:
            return entered
    raise CommandError(f"Set {name} before running bootstrap. See docs/operations/bootstrap.md.")
