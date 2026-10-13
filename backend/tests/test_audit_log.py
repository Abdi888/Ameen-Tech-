from __future__ import annotations

from typing import cast

import pytest
from django.db import transaction
from django.db.utils import ProgrammingError

from modules.audit.models import AuditLog
from tests.support import SessionClient, grant, login, make_tenant, make_user

pytestmark = pytest.mark.django_db


def test_login_failure_is_audited_without_the_password(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    user = make_user("cashier@harbor.test")
    grant(user, tenant, "Cashier")
    response = login(api, user.email, "wrong-password-value")
    assert response.status_code == 401
    row = AuditLog.objects.get(action="login.failure", user=user)
    assert row.tenant_id is None
    recorded = cast(dict[str, object], row.new_values)
    assert "wrong-password-value" not in str(recorded)
    assert recorded["result"] == "failure"


def test_audit_rows_cannot_be_updated_or_deleted(api: SessionClient) -> None:
    tenant = make_tenant("harbor")
    user = make_user("cashier@harbor.test")
    grant(user, tenant, "Cashier")
    assert login(api, user.email, tenant=tenant).status_code == 200
    row = AuditLog.objects.get(action="login.success", user=user)
    row.action = "tampered"
    with pytest.raises(RuntimeError, match="append-only"):
        row.save()
    with pytest.raises(RuntimeError, match="append-only"):
        row.delete()
    with pytest.raises(ProgrammingError, match="append-only"):
        with transaction.atomic():
            AuditLog.objects.filter(pk=row.id).update(action="tampered")
    row.refresh_from_db()
    assert row.action == "login.success"
