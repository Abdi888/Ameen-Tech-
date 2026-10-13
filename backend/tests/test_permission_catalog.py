"""The permission catalogue is Document 07 and nothing else."""

from __future__ import annotations

import pytest

from modules.access.domain.catalog import (
    ALL_CODES,
    BUSINESS_OWNER,
    CASHIER,
    CASHIER_GRANTS,
    INVENTORY_MANAGER,
    PURCHASING_OFFICER,
    ROLE_GRANTS,
    ROLE_ORDER,
    SALES_MANAGER,
    VIEWER,
    decide,
)
from modules.access.models import Permission, Role, RolePermission

FORBIDDEN = {
    "inventory.count",
    "roles.view",
    "permissions.view",
    "platform.tenants.view",
    "platform.users.view",
    "platform.audit.view",
    "sales.override_price",
    "sales.confirm",
    "sales.refund",
    "pos.register.open",
    "ownership.transfer",
    "security.settings.update",
    "users.invite",
}


def _codes(resource: str, *actions: str) -> set[str]:
    return {f"{resource}.{action}" for action in actions}


DOCUMENTED_CODES = (
    _codes("dashboard", "view")
    | _codes("sales", "view", "create", "update", "cancel", "void", "export", "print")
    | _codes("sales_returns", "view", "create", "approve", "cancel", "refund")
    | _codes(
        "pos",
        "view",
        "create_sale",
        "open_register",
        "close_register",
        "view_sessions",
        "cash_in",
        "cash_out",
        "refund",
        "reprint",
    )
    | _codes(
        "customers",
        "view",
        "create",
        "update",
        "archive",
        "restore",
        "export",
        "view_transactions",
    )
    | _codes("products", "view", "create", "update", "archive", "restore", "export", "print")
    | _codes("product_categories", "view", "create", "update", "archive")
    | _codes("brands", "view", "create", "update", "archive")
    | _codes("units", "view", "create", "update", "archive")
    | _codes("inventory", "view", "view_movements", "adjust", "transfer", "receive", "export")
    | _codes("suppliers", "view", "create", "update", "archive")
    | _codes("purchase_orders", "view", "create", "update", "approve", "cancel", "export")
    | _codes("goods_receipts", "view", "create", "post", "cancel")
    | _codes("purchase_returns", "view", "create", "approve", "cancel")
    | _codes("expenses", "view", "create", "update", "approve", "cancel", "export")
    | _codes("finance_accounts", "view", "create", "update", "archive")
    | _codes("finance_transactions", "view", "create", "post", "void")
    | _codes("payments", "view", "create", "void", "refund")
    | _codes("receivables", "view", "create_payment", "export")
    | _codes("payables", "view", "create_payment", "export")
    | _codes("reports.sales", "view")
    | _codes("reports.inventory", "view")
    | _codes("reports.purchasing", "view")
    | _codes("reports.customers", "view")
    | _codes("reports.expenses", "view")
    | _codes("reports.finance", "view")
    | {"reports.export"}
    | _codes("users", "view", "create", "update", "activate", "deactivate", "assign_roles")
    | _codes("settings.business", "view", "update")
    | _codes("branches", "view", "create", "update", "archive")
    | _codes("tax", "view", "create", "update", "archive")
    | _codes("currency", "view", "update")
    | _codes("numbering", "view", "update")
    | _codes("audit", "view", "export")
)


def test_registry_matches_document_07_and_rejects_inactive_keys() -> None:
    assert ALL_CODES == DOCUMENTED_CODES
    assert ALL_CODES.isdisjoint(FORBIDDEN)
    assert set(ROLE_GRANTS) == set(ROLE_ORDER)
    for grants in ROLE_GRANTS.values():
        assert grants <= ALL_CODES


def test_cashier_grant_is_the_explicit_list() -> None:
    assert CASHIER_GRANTS == ROLE_GRANTS[CASHIER]
    assert CASHIER_GRANTS == {
        "dashboard.view",
        "pos.view",
        "pos.create_sale",
        "pos.open_register",
        "pos.close_register",
        "pos.view_sessions",
        "pos.cash_in",
        "pos.cash_out",
        "pos.reprint",
        "customers.view",
        "customers.create",
        "products.view",
    }
    assert "pos.refund" not in CASHIER_GRANTS
    assert "users.create" not in CASHIER_GRANTS
    assert "inventory.adjust" not in CASHIER_GRANTS
    assert "settings.business.update" not in CASHIER_GRANTS


def test_ambiguous_and_separated_keys_are_not_silently_granted() -> None:
    purchasing = ROLE_GRANTS[PURCHASING_OFFICER]
    assert not any(code.startswith("expenses.") for code in purchasing)
    viewer = ROLE_GRANTS[VIEWER]
    assert "reports.export" not in viewer
    assert not any(
        code.rsplit(".", 1)[-1] in {"create", "update", "void", "refund"} for code in viewer
    )
    sales_manager = ROLE_GRANTS[SALES_MANAGER]
    assert not any(code.startswith("sales_returns.") for code in sales_manager)
    inventory = ROLE_GRANTS[INVENTORY_MANAGER]
    assert "product_categories.create" not in inventory
    owner = ROLE_GRANTS[BUSINESS_OWNER]
    assert "audit.view" in owner and "audit.export" in owner
    assert "audit.delete" not in owner
    assert decide(set(), "users.view") == "DENY"
    assert decide({"users.view"}, "not.a.key") == "DENY"
    assert decide({"users.view"}, "users.view") == "ALLOW"


@pytest.mark.django_db
def test_seeded_rows_match_the_catalogue() -> None:
    assert set(Permission.objects.values_list("code", flat=True)) == ALL_CODES
    assert list(
        Role.objects.filter(tenant__isnull=True).order_by("name").values_list("name", flat=True)
    )
    names = set(
        Role.objects.filter(is_system_role=True, tenant__isnull=True).values_list("name", flat=True)
    )
    assert names == set(ROLE_ORDER)
    for name, grants in ROLE_GRANTS.items():
        stored = set(
            RolePermission.objects.filter(role__name=name, role__tenant__isnull=True).values_list(
                "permission__code",
                flat=True,
            )
        )
        assert stored == set(grants)
