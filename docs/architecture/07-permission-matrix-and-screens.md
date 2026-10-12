# Ameen Retail — Permission Matrix & Screen Boundary Design v1

**Status:** Binding for screens, navigation, and the permission registry.  
**Conflicts:** `00-frozen-decisions.md` still wins on sale lifecycle, cookies, no credit tender, and layering. **This document wins** on role names, permission **keys**, screen entry rules, and “no tenant role editor.”

---

## 1. Core principle

A user can **enter a screen** only with that screen’s **view** permission. Every mutation on the screen needs its **action** permission.

```
Frontend route
  → screen permission (view)
  → user opens screen
  → action permission
  → API
  → backend permission (final)
  → domain (tenant / branch / register / business rules)
  → database
```

Never rely on the frontend alone. Hiding a nav item is not security. Direct URLs must be denied (403) without the view permission.

**View permission = screen boundary.** Do not add `products.screen.view` or `products.product.view`. Use `products.view`.

Do not use `can_do_everything`, `manage_products`, or `sales.manage` parent permissions. Assign atomic codes to roles.

**Permission ≠ plan.** Starter vs Professional is tenant capability, not a second permission tree.

**Permission ≠ data scope.** Branch assignment is evaluated separately.

---

## 2. Key format and actions

Format: `<resource>.<action>` (resource may be dotted: `reports.sales.view`, `settings.business.update`).

Controlled actions: `view`, `create`, `update`, `archive`, `restore`, `approve`, `post`, `cancel`, `void`, `refund`, `receive`, `adjust`, `transfer`, `open`, `close`, `export`, `print`, plus POS-specific keys listed below.

Fail closed: missing permission → **DENY**.

Engine:

```
authorize(user, permission, tenant, resource?, branch?) → ALLOW | DENY
```

Then domain policy may still REQUIRE_APPROVAL (refund/discount thresholds from security design).

---

## 3. Screen map (MVP)

| Area | Screens (target routes) |
|---|---|
| Dashboard | `/app/dashboard` |
| Sales | `/app/sales`, create, `:id`, returns, refunds |
| POS | `/app/pos`, open register, sessions, cash movements |
| Customers | `/app/customers`, `:id`, transactions |
| Products | `/app/products`, new, `:id`, categories, brands, units |
| Inventory | `/app/inventory`, stock details, adjustments, transfers, movements |
| Purchasing | suppliers, purchase orders, goods receipts, purchase returns |
| Expenses | `/app/expenses`, `:id` |
| Finance | accounts, transactions, payments, receivables, payables, financial reports |
| Reports | sales, inventory, purchasing, customers, financial |
| Users | `/app/settings/users`, `:id` |
| Settings | business, branches, tax, currencies, numbering |
| Audit | `/app/audit` |

**No tenant screen** for Roles, Permissions, or Role-permission mapping. Platform owns the registry and system roles. Tenant users only **assign available roles**.

---

## 4. Permission registry (canonical keys)

### Dashboard

- `dashboard.view` — open dashboard. Widgets still require domain view (`sales.view`, `inventory.view`, `reports.finance.view` / finance view). Cashier dashboard must **not** show finance widgets.

### Sales

- `sales.view` — list + details  
- `sales.create` — create draft / back-office sale  
- `sales.update` — edit **DRAFT** only (completed sales are immutable)  
- `sales.cancel` — cancel DRAFT  
- `sales.void` — void COMPLETED  
- `sales.export` · `sales.print`  

API `POST /sales/{id}/confirm` from **back-office Sales** requires `sales.create` (complete is the create workflow’s final command). Do not add `sales.confirm` as a separate registry key.

### Sales returns (separate from sales)

- `sales_returns.view` · `create` · `approve` · `cancel` · `refund`  

Cashier may have `sales.view` / POS sale without `sales_returns.refund`.

### POS (not the same as Sales)

- `pos.view` — POS screen  
- `pos.create_sale` — complete POS checkout (`POST /sales/{id}/confirm` from POS)  
- `pos.open_register` · `pos.close_register`  
- `pos.view_sessions`  
- `pos.cash_in` · `pos.cash_out`  
- `pos.refund` · `pos.reprint`  

A user may run POS without `sales.export` or historical sales admin.

### Customers

- `customers.view` · `create` · `update` · `archive` · `restore` · `export` · `view_transactions`

### Products

- `products.view` · `create` · `update` · `archive` · `restore` · `export` · `print`

### Categories / brands / units

- `product_categories.view` · `create` · `update` · `archive`  
- `brands.view` · `create` · `update` · `archive` (implied by Products screens; same pattern)  
- `units.view` · `create` · `update` · `archive`

### Inventory

- `inventory.view` — stock screen  
- `inventory.view_movements`  
- `inventory.adjust` — **not** implied by transfer  
- `inventory.transfer`  
- `inventory.receive`  
- `inventory.export`  

Stock Adjustment **screen** requires `inventory.view` **AND** `inventory.adjust`.  
Stock counts: add `inventory.count` when that screen is built (domain still requires counts).

### Purchasing

Suppliers: `suppliers.view` · `create` · `update` · `archive`  

POs: `purchase_orders.view` · `create` · `update` · `approve` (CONFIRMED) · `cancel` · `export`  

Receipts: `goods_receipts.view` · `create` · `post` · `cancel`  

Purchase returns: `purchase_returns.view` · `create` · `approve` · `cancel`

### Expenses

- `expenses.view` · `create` · `update` · `approve` · `cancel` · `export`  
No `expenses.delete` for posted expenses.

### Finance

Accounts: `finance_accounts.view` · `create` · `update` · `archive`  

Journals: `finance_transactions.view` · `create` · `post` · `void`  
Clients still must **not** post a sale by calling journal create; `create`/`post` are for explicit accounting ops if ever exposed. Sale posting stays inside CompleteSale.

Payments: `payments.view` · `create` · `void` · `refund`  

Receivables: `receivables.view` · `create_payment` · `export`  
Payables: `payables.view` · `create_payment` · `export`  

AR **create** stays unused in POS until credit sales are an explicit Starter feature. Accountant may still **view** AP from receipts.

### Reports

- `reports.sales.view`  
- `reports.inventory.view`  
- `reports.purchasing.view`  
- `reports.customers.view`  
- `reports.expenses.view`  
- `reports.finance.view`  
- `reports.export`  

`sales.view` does **not** imply `reports.sales.view`.

### Users (tenant)

- `users.view` · `create` · `update` · `activate` · `deactivate` · `assign_roles`  

`users.assign_roles` cannot assign/remove **Business Owner**.

### Settings

- `settings.business.view` · `settings.business.update`  
- `branches.view` · `create` · `update` · `archive`  
- `tax.view` · `create` · `update` · `archive`  
- `currency.view` · `currency.update`  
- `numbering.view` · `numbering.update`

### Audit

- `audit.view` · `audit.export`  
No `audit.update` / `audit.delete` for tenant users.

---

## 5. Screen definitions (entry + actions)

| Screen | Route (tenant `/app`) | Enter | Actions |
|---|---|---|---|
| Dashboard | `/dashboard` | `dashboard.view` | widgets gated by domain view |
| Sales list / details | `/sales`, `/sales/:id` | `sales.view` | create/update/cancel/void/export/print as listed |
| Create sale | `/sales/new` | `sales.create` | |
| Returns | `/sales/returns` | `sales_returns.view` | create/approve/cancel/refund |
| POS | `/pos` | `pos.view` | `pos.create_sale`, reprint, refund as granted |
| Open register | `/pos` flow | `pos.open_register` | |
| Sessions | `/pos/sessions` | `pos.view_sessions` | close: `pos.close_register` |
| Cash movements | `/pos/sessions/:id` | `pos.cash_in` or `pos.cash_out` | |
| Customers | `/customers` | `customers.view` | CRUD/archive/export/transactions |
| Products | `/products` | `products.view` | create/update/archive/restore/export/print |
| Categories | `/products/categories` | `product_categories.view` | |
| Inventory | `/inventory` | `inventory.view` | |
| Movements | `/inventory/movements` | `inventory.view_movements` | |
| Adjustments | `/inventory/adjustments` | `inventory.view` **and** `inventory.adjust` | |
| Transfers | `/inventory/transfers` | `inventory.view` **and** `inventory.transfer` | |
| Financial reports | `/reports/finance` | `reports.finance.view` | export: `reports.export` |
| Users | `/settings/users` | `users.view` | |
| Tax settings | `/settings/tax` | `tax.view` | |
| Audit | `/audit` | `audit.view` | export: `audit.export` |

If the user has `products.view` but not `products.create`, hide Create; API still 403 on `POST /products`.

---

## 6. Roles (v1 system roles)

1. **Business Owner** — protected; cannot be deleted/replaced; full tenant permissions except they still cannot erase audit.  
2. **Administrator** — full operational access; **not** Owner; cannot transfer ownership or assign Owner.  
3. **Accountant** — expenses + finance full; sales/customers/products/inventory/purchasing **view**; POS none; reports finance; audit view; no users/settings.  
4. **Sales Manager** — sales + POS + customers full; products/inventory view; finance view/limited; reports sales.  
5. **Inventory Manager** — products + inventory + purchasing full; sales view; POS none; reports inventory.  
6. **Cashier** — operational only: dashboard, POS full (as granted), customers view/create, products view, sales limited (POS workflow, not exports/void/admin). No inventory/purchasing/expenses/finance/reports/users/settings/audit.  
7. **Purchasing Officer** — purchasing full; products/inventory/sales/customers view; expenses limited; reports purchasing.  
8. **Viewer** — dashboard + view on sales/customers/products/inventory/purchasing/expenses + reports view; **no mutations**.

Do not ship 20+ roles. Do not let tenants invent roles.

Generic “Manager” from earlier docs is **replaced** by Sales Manager + Inventory Manager + Purchasing Officer.

---

## 7. Compact role matrix

Full = all atomic permissions for that domain. Limited = subset (see cashier/purchasing notes). View = view-only.

| Module | Owner | Admin | Accountant | Sales Mgr | Inv Mgr | Cashier | Purchasing | Viewer |
|---|---|---|---|---|---|---|---|---|
| Dashboard | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Sales | Full | Full | View | Full | View | Limited | View | View |
| POS | Full | Full | — | Full | — | Full | — | — |
| Customers | Full | Full | View | Full | View | Limited | View | View |
| Products | Full | Full | View | View | Full | View | View | View |
| Inventory | Full | Full | View | View | Full | — | View | View |
| Purchasing | Full | Full | View | — | Full | — | Full | View |
| Expenses | Full | Full | Full | — | — | — | Limited | View |
| Finance | Full | Full | Full | View | — | — | — | View |
| Reports | Full | Full | Finance | Sales | Inventory | — | Purchasing | View |
| Users | Full | Full | — | — | — | — | — | — |
| Settings | Full | Full | — | — | — | — | — | — |
| Audit | Full | Full | View | — | — | — | — | — |

### Cashier limited (explicit)

Grant: `dashboard.view`, `pos.view`, `pos.create_sale`, `pos.open_register`, `pos.close_register`, `pos.view_sessions`, `pos.cash_in`, `pos.cash_out`, `pos.reprint`, `customers.view`, `customers.create`, `products.view`.  
POS refund (`pos.refund`) and `sales.view` only if needed for receipt lookup — **not** `sales.void`, `sales.export`, `sales_returns.refund` unless policy says so. Default: **no** `pos.refund` until a discount/refund policy grants it (may REQUIRE_APPROVAL).

### POS complete-sale extra checks (not permissions)

Authenticated → tenant membership → `pos.create_sale` → branch in scope → terminal belongs to branch → register **open** → payment method allowed → inventory/accounting rules.

---

## 8. Backend mapping (examples)

`GET /api/products` → `products.view`  
`POST /api/products` → `products.create`  
POS `POST /api/sales/{id}/confirm` → `pos.create_sale`  
Back-office `POST /api/sales/{id}/confirm` → `sales.create`  
`POST /api/sales/{id}/void` → `sales.void`  
`POST /api/inventory/adjustments` → `inventory.adjust`  
`POST /api/pos/sessions` → `pos.open_register`  
`POST /api/pos/sessions/{id}/close` → `pos.close_register`

Then tenant isolation, branch scope, domain rules, transaction, audit.

---

## 9. What not to do

- `if user.role == "ADMIN"` in business logic  
- Plan names inside permission codes (`starter_products_create`)  
- Screen access only by hiding navigation  
- Permission inheritance trees  
- Tenant-editable role/permission designer in v1  

---

## 10. Architecture chain

User → Role → Permissions → Screen (`*.view`) → Action → Domain (tenant/branch/register) → API → Database.
