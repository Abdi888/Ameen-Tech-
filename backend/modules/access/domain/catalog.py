"""Document 07 permission registry and the grants that text makes explicit.

Full means every atomic key in that matrix row. View means view actions only.
A Limited cell with no key list grants nothing. Cashier's explicit list wins
over the matrix cell that says POS Full. Keys that sit outside the matrix
rows (sales returns, categories, brands, units) are granted only to Business
Owner and Administrator, because those roles are full-tenant roles.
"""

from __future__ import annotations

BUSINESS_OWNER = "Business Owner"
ADMINISTRATOR = "Administrator"
ACCOUNTANT = "Accountant"
SALES_MANAGER = "Sales Manager"
INVENTORY_MANAGER = "Inventory Manager"
CASHIER = "Cashier"
PURCHASING_OFFICER = "Purchasing Officer"
VIEWER = "Viewer"

ROLE_ORDER: tuple[str, ...] = (
    BUSINESS_OWNER,
    ADMINISTRATOR,
    ACCOUNTANT,
    SALES_MANAGER,
    INVENTORY_MANAGER,
    CASHIER,
    PURCHASING_OFFICER,
    VIEWER,
)

ROLE_DESCRIPTIONS: dict[str, str] = {
    BUSINESS_OWNER: "Protected system role. Full tenant permissions. Cannot erase audit.",
    ADMINISTRATOR: "Full operational access. Cannot assign or remove Business Owner.",
    ACCOUNTANT: (
        "Expenses and finance. View on sales, customers, products, inventory, and purchasing."
    ),
    SALES_MANAGER: "Sales, POS, and customers. View on products, inventory, and finance.",
    INVENTORY_MANAGER: "Products, inventory, and purchasing. View on sales and customers.",
    CASHIER: "POS workflow and the explicit cashier grant list.",
    PURCHASING_OFFICER: "Purchasing. View on products, inventory, sales, and customers.",
    VIEWER: "View-only access. No mutations.",
}

PROTECTED_ROLE_NAMES = frozenset({BUSINESS_OWNER})

_VIEW_ACTIONS = frozenset({"view", "view_movements", "view_transactions"})


def _codes(resource: str, *actions: str) -> tuple[str, ...]:
    return tuple(f"{resource}.{action}" for action in actions)


ALL_PERMISSION_CODES: tuple[str, ...] = (
    *_codes("dashboard", "view"),
    *_codes("sales", "view", "create", "update", "cancel", "void", "export", "print"),
    *_codes("sales_returns", "view", "create", "approve", "cancel", "refund"),
    *_codes(
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
    ),
    *_codes(
        "customers",
        "view",
        "create",
        "update",
        "archive",
        "restore",
        "export",
        "view_transactions",
    ),
    *_codes("products", "view", "create", "update", "archive", "restore", "export", "print"),
    *_codes("product_categories", "view", "create", "update", "archive"),
    *_codes("brands", "view", "create", "update", "archive"),
    *_codes("units", "view", "create", "update", "archive"),
    *_codes("inventory", "view", "view_movements", "adjust", "transfer", "receive", "export"),
    *_codes("suppliers", "view", "create", "update", "archive"),
    *_codes("purchase_orders", "view", "create", "update", "approve", "cancel", "export"),
    *_codes("goods_receipts", "view", "create", "post", "cancel"),
    *_codes("purchase_returns", "view", "create", "approve", "cancel"),
    *_codes("expenses", "view", "create", "update", "approve", "cancel", "export"),
    *_codes("finance_accounts", "view", "create", "update", "archive"),
    *_codes("finance_transactions", "view", "create", "post", "void"),
    *_codes("payments", "view", "create", "void", "refund"),
    *_codes("receivables", "view", "create_payment", "export"),
    *_codes("payables", "view", "create_payment", "export"),
    *_codes(
        "reports.sales",
        "view",
    ),
    *_codes("reports.inventory", "view"),
    *_codes("reports.purchasing", "view"),
    *_codes("reports.customers", "view"),
    *_codes("reports.expenses", "view"),
    *_codes("reports.finance", "view"),
    "reports.export",
    *_codes("users", "view", "create", "update", "activate", "deactivate", "assign_roles"),
    *_codes("settings.business", "view", "update"),
    *_codes("branches", "view", "create", "update", "archive"),
    *_codes("tax", "view", "create", "update", "archive"),
    *_codes("currency", "view", "update"),
    *_codes("numbering", "view", "update"),
    *_codes("audit", "view", "export"),
)

ALL_CODES = frozenset(ALL_PERMISSION_CODES)

CASHIER_GRANTS = frozenset(
    {
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
)


def permission_module(code: str) -> str:
    if code == "reports.export":
        return "reports"
    return code.rsplit(".", 1)[0]


def danger_level(code: str) -> str:
    action = code.rsplit(".", 1)[-1]
    if code == "users.deactivate":
        return "CRITICAL"
    if action in {"refund", "adjust", "void", "cash_in", "cash_out"}:
        return "HIGH"
    if action in _VIEW_ACTIONS or action in {"export", "print"}:
        return "LOW"
    return "MEDIUM"


def _prefixed(*prefixes: str) -> frozenset[str]:
    heads = tuple(f"{prefix}." for prefix in prefixes)
    return frozenset(code for code in ALL_PERMISSION_CODES if code.startswith(heads))


def _view(codes: frozenset[str]) -> frozenset[str]:
    return frozenset(code for code in codes if code.rsplit(".", 1)[-1] in _VIEW_ACTIONS)


def _union(*parts: frozenset[str]) -> frozenset[str]:
    granted: set[str] = set()
    for part in parts:
        granted.update(part)
    return frozenset(granted)


_DASHBOARD = frozenset({"dashboard.view"})
_SALES = _prefixed("sales")
_POS = _prefixed("pos")
_CUSTOMERS = _prefixed("customers")
_PRODUCTS = _prefixed("products")
_INVENTORY = _prefixed("inventory")
_PURCHASING = _prefixed("suppliers", "purchase_orders", "goods_receipts", "purchase_returns")
_EXPENSES = _prefixed("expenses")
_FINANCE = _prefixed(
    "finance_accounts",
    "finance_transactions",
    "payments",
    "receivables",
    "payables",
)
_AUDIT = _prefixed("audit")
_REPORTS = _prefixed("reports")

# Purchasing Officer expenses are "Limited" with no key list. Fail closed.
_PURCHASING_EXPENSES: frozenset[str] = frozenset()

_FULL_TENANT = frozenset(ALL_PERMISSION_CODES)

ROLE_GRANTS: dict[str, frozenset[str]] = {
    BUSINESS_OWNER: _FULL_TENANT,
    ADMINISTRATOR: _FULL_TENANT,
    ACCOUNTANT: _union(
        _DASHBOARD,
        _view(_SALES),
        _view(_CUSTOMERS),
        _view(_PRODUCTS),
        _view(_INVENTORY),
        _view(_PURCHASING),
        _EXPENSES,
        _FINANCE,
        frozenset({"reports.finance.view"}),
        _view(_AUDIT),
    ),
    SALES_MANAGER: _union(
        _DASHBOARD,
        _SALES,
        _POS,
        _CUSTOMERS,
        _view(_PRODUCTS),
        _view(_INVENTORY),
        _view(_FINANCE),
        frozenset({"reports.sales.view"}),
    ),
    INVENTORY_MANAGER: _union(
        _DASHBOARD,
        _view(_SALES),
        _view(_CUSTOMERS),
        _PRODUCTS,
        _INVENTORY,
        _PURCHASING,
        frozenset({"reports.inventory.view"}),
    ),
    CASHIER: CASHIER_GRANTS,
    PURCHASING_OFFICER: _union(
        _DASHBOARD,
        _view(_SALES),
        _view(_CUSTOMERS),
        _view(_PRODUCTS),
        _view(_INVENTORY),
        _PURCHASING,
        _PURCHASING_EXPENSES,
        frozenset({"reports.purchasing.view"}),
    ),
    VIEWER: _union(
        _DASHBOARD,
        _view(_SALES),
        _view(_CUSTOMERS),
        _view(_PRODUCTS),
        _view(_INVENTORY),
        _view(_PURCHASING),
        _view(_EXPENSES),
        _view(_FINANCE),
        _view(_REPORTS),
    ),
}


def decide(granted: set[str], permission: str) -> str:
    """ALLOW or DENY. Unknown keys and missing grants deny."""
    if permission not in ALL_CODES or permission not in granted:
        return "DENY"
    return "ALLOW"
