"""Phase 3 persistence: migrations, money, tenant constraints, idempotency."""

from __future__ import annotations

import json
import uuid
from decimal import Decimal
from importlib import import_module
from typing import Any, cast

import pytest
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor

from shared.database.fields import MoneyField
from shared.database.models import IdempotencyKey
from shared.database.transactions import run_in_transaction
from shared.money import MONEY_DECIMAL_PLACES, MONEY_MAX_DIGITS, money, money_to_json
from tests.support import make_tenant, make_user

pytestmark = pytest.mark.django_db

_PROJECT_APPS = frozenset({"ameen_database", "tenants", "identity", "access", "audit"})
_DOMAIN_SCHEMAS = cast(
    tuple[str, ...],
    import_module("shared.database.migrations.0001_domain_schemas").DOMAIN_SCHEMAS,
)
_EXPECTED_TABLES = {
    ("audit", "audit_logs"),
    ("identity", "login_attempts"),
    ("identity", "password_reset_tokens"),
    ("identity", "permissions"),
    ("identity", "role_permissions"),
    ("identity", "roles"),
    ("identity", "sessions"),
    ("identity", "tenant_memberships"),
    ("identity", "tenant_user_roles"),
    ("identity", "users"),
    ("organization", "tenants"),
    ("system", "idempotency_keys"),
}
# audit_logs stays nullable: a login failure may have no tenant.
# roles stays nullable: Document 02 uses NULL for a system role.
# sessions stays nullable: an accepted session can exist before a tenant is chosen.
_TENANT_ID_NULLABLE = {
    ("audit", "audit_logs"): True,
    ("identity", "roles"): True,
    ("identity", "sessions"): True,
    ("identity", "tenant_memberships"): False,
    ("system", "idempotency_keys"): False,
}
_DEFERRED_TABLES = frozenset(
    {
        "currencies",
        "document_sequences",
        "documents",
        "outbox",
        "outbox_events",
        "tenant_settings",
    }
)


def test_migrations_apply_and_roll_back_against_an_empty_database() -> None:
    executor = MigrationExecutor(connection)
    leaves = executor.loader.graph.leaf_nodes()
    savepoint = transaction.savepoint()
    try:
        executor.migrate([("ameen_database", None)])
        rolled_back = MigrationExecutor(connection)
        assert _project_migrations(rolled_back) == set()
        assert _domain_tables() == set()
        assert not _audit_trigger_exists()

        rolled_back.migrate(leaves)
        applied = MigrationExecutor(connection)
        assert _project_migrations(applied) == _project_nodes(applied)
        assert _domain_tables() == _EXPECTED_TABLES
        assert _audit_trigger_exists()
        _assert_idempotency_columns()
        assert _deferred_tables() == set()
    finally:
        transaction.savepoint_rollback(savepoint)

    assert ("system", "idempotency_keys") in _domain_tables()
    assert _audit_trigger_exists()


def test_money_values_use_numeric_19_4_and_reject_floats() -> None:
    assert money("0.10") + money("0.20") == Decimal("0.3000")
    assert money(10) == Decimal("10.0000")
    assert money_to_json("10.5") == "10.5000"
    assert money_to_json("-1.5") == "-1.5000"
    assert money("999999999999999.9999") == Decimal("999999999999999.9999")
    assert isinstance(money_to_json("1"), str)

    with pytest.raises(TypeError):
        money(cast(Any, 1.25))
    with pytest.raises(TypeError):
        money(True)
    with pytest.raises(ValueError):
        money("0.00001")
    with pytest.raises(ValueError):
        money("1000000000000000.0000")
    with pytest.raises(ValueError):
        money("not-money")

    db_type = MoneyField().db_type(connection)
    assert db_type == "numeric(19, 4)"
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE TEMP TABLE phase3_money_probe (amount {db_type})")
        cursor.execute(
            "INSERT INTO phase3_money_probe (amount) VALUES (%s)",
            [money("19.9900")],
        )
        cursor.execute(
            """
            SELECT numeric_precision, numeric_scale, data_type
            FROM information_schema.columns
            WHERE table_name = 'phase3_money_probe' AND column_name = 'amount'
            """
        )
        assert cursor.fetchone() == (19, 4, "numeric")
        cursor.execute("SELECT amount FROM phase3_money_probe")
        assert cursor.fetchone() == (Decimal("19.9900"),)
        cursor.execute(
            """
            SELECT table_schema, table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = ANY(%s)
              AND data_type IN ('real', 'double precision', 'money')
            """,
            [list(_DOMAIN_SCHEMAS)],
        )
        assert cursor.fetchall() == []


def test_money_field_rejects_floats_and_keeps_numeric_19_4() -> None:
    field = MoneyField()
    assert field.max_digits == MONEY_MAX_DIGITS
    assert field.decimal_places == MONEY_DECIMAL_PLACES
    assert field.db_type(connection) == "numeric(19, 4)"
    _name, _path, _args, kwargs = field.deconstruct()
    assert "max_digits" not in kwargs
    assert "decimal_places" not in kwargs

    amount = Decimal("19.9900")
    assert field.to_python(amount) == amount
    assert field.to_python(Decimal("-1.5000")) == Decimal("-1.5000")
    assert field.to_python(None) is None
    assert field.get_prep_value(amount) == amount

    with pytest.raises(TypeError, match="decimal string"):
        field.to_python(cast(Any, 1.25))
    with pytest.raises(TypeError, match="decimal string"):
        field.to_python(cast(Any, 0.1))
    with pytest.raises(TypeError, match="decimal string"):
        field.get_prep_value(cast(Any, 1.25))
    with pytest.raises(TypeError, match="decimal string"):
        field.get_db_prep_value(cast(Any, 0.1), connection)


def test_tenant_id_not_null_is_enforced_on_applicable_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_schema, table_name, is_nullable
            FROM information_schema.columns
            WHERE column_name = 'tenant_id' AND table_schema = ANY(%s)
            """,
            [list(_DOMAIN_SCHEMAS)],
        )
        found = {
            (str(schema), str(table)): nullable == "YES"
            for schema, table, nullable in cursor.fetchall()
        }
    assert found == _TENANT_ID_NULLABLE

    user = make_user("member@harbor.test")
    with pytest.raises(IntegrityError, match="tenant_id"):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO identity.tenant_memberships (
                        id, tenant_id, user_id, status, is_owner, created_at, updated_at
                    ) VALUES (%s, NULL, %s, 'ACTIVE', FALSE, NOW(), NOW())
                    """,
                    [uuid.uuid4(), user.id],
                )
    with pytest.raises(IntegrityError, match="tenant_id"):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO system.idempotency_keys (
                        id, tenant_id, key, endpoint, response, created_at
                    ) VALUES (%s, NULL, %s, %s, CAST(%s AS jsonb), NOW())
                    """,
                    [uuid.uuid4(), "null-tenant", "/api/v1/example", json.dumps({"success": True})],
                )


def test_idempotency_key_is_unique_inside_one_tenant() -> None:
    harbor = make_tenant("harbor")
    market = make_tenant("market")
    shared_key = "confirm-sale"
    IdempotencyKey.objects.create(
        tenant=harbor,
        key=shared_key,
        endpoint="/api/v1/sales/confirm",
        response={"success": True, "data": {"id": "harbor"}},
    )
    IdempotencyKey.objects.create(
        tenant=market,
        key=shared_key,
        endpoint="/api/v1/sales/confirm",
        response={"success": True, "data": {"id": "market"}},
    )
    harbor_rows = IdempotencyKey.objects.filter(tenant=harbor)
    assert list(harbor_rows.values_list("key", flat=True)) == [shared_key]
    assert harbor_rows.get().response["data"]["id"] == "harbor"
    assert not IdempotencyKey.objects.filter(tenant=harbor, response__data__id="market").exists()

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            IdempotencyKey.objects.create(
                tenant=harbor,
                key=shared_key,
                endpoint="/api/v1/sales/confirm",
                response={"success": True},
            )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO system.idempotency_keys (
                        id, tenant_id, key, endpoint, response, created_at
                    ) VALUES (%s, %s, %s, %s, CAST(%s AS jsonb), NOW())
                    """,
                    [
                        uuid.uuid4(),
                        uuid.uuid4(),
                        "missing-tenant",
                        "/api/v1/example",
                        json.dumps({"success": True}),
                    ],
                )
                # Foreign keys are deferred until the test transaction ends.
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")


def test_transaction_helper_rolls_back_a_failed_operation() -> None:
    tenant = make_tenant("harbor")

    def fail() -> None:
        IdempotencyKey.objects.create(
            tenant=tenant,
            key="fails",
            endpoint="/api/v1/example",
            response={"success": False},
        )
        raise RuntimeError("stop")

    with pytest.raises(RuntimeError, match="stop"):
        run_in_transaction(fail)
    assert not IdempotencyKey.objects.filter(tenant=tenant, key="fails").exists()

    def succeed() -> IdempotencyKey:
        return IdempotencyKey.objects.create(
            tenant=tenant,
            key="keeps",
            endpoint="/api/v1/example",
            response={"success": True},
        )

    saved = run_in_transaction(succeed)
    assert IdempotencyKey.objects.filter(pk=saved.id, tenant=tenant, key="keeps").exists()


def _project_migrations(executor: MigrationExecutor) -> set[tuple[str, str]]:
    return {key for key in executor.loader.applied_migrations if key[0] in _PROJECT_APPS}


def _project_nodes(executor: MigrationExecutor) -> set[tuple[str, str]]:
    return {key for key in executor.loader.graph.nodes if key[0] in _PROJECT_APPS}


def _domain_tables() -> set[tuple[str, str]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = ANY(%s) AND table_type = 'BASE TABLE'
            """,
            [list(_DOMAIN_SCHEMAS)],
        )
        return {(str(schema), str(name)) for schema, name in cursor.fetchall()}


def _deferred_tables() -> set[tuple[str, str]]:
    return {item for item in _domain_tables() if item[1] in _DEFERRED_TABLES}


def _audit_trigger_exists() -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM pg_trigger
            JOIN pg_class ON pg_class.oid = pg_trigger.tgrelid
            JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
            WHERE pg_namespace.nspname = 'audit'
              AND pg_class.relname = 'audit_logs'
              AND pg_trigger.tgname = 'audit_logs_append_only'
              AND NOT pg_trigger.tgisinternal
            """
        )
        return cursor.fetchone() is not None


def _assert_idempotency_columns() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'system' AND table_name = 'idempotency_keys'
            """
        )
        columns = {
            str(name): (str(data_type), str(nullable))
            for name, data_type, nullable in cursor.fetchall()
        }
        cursor.execute(
            """
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'idempotency_tenant_key'
            """
        )
        definition = cursor.fetchone()
    assert columns == {
        "id": ("uuid", "NO"),
        "tenant_id": ("uuid", "NO"),
        "key": ("text", "NO"),
        "endpoint": ("text", "NO"),
        "response": ("jsonb", "NO"),
        "created_at": ("timestamp with time zone", "NO"),
    }
    assert definition is not None
    assert "UNIQUE (tenant_id, key)" in str(definition[0])
