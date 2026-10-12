# Ameen Retail — Implementation Specification v1.0

**Status:** Binding engineering rules for implementation.  
**Does not replace** Documents 00–08. Those remain frozen. This document **operationalizes** them.  
**Does not implement** application code.

If this file and a frozen design disagree, **`00-frozen-decisions.md` wins**, except **permission identifiers**, which **Document 07** owns (per Document 00 §11 and Document 07 header).

---

## 1. Greenfield implementation boundary

This repository is a **new greenfield** Ameen Retail product.

There is:

- no legacy ERP compatibility requirement
- no migration from an old ERP / Kinetic / previous Ameen ERP
- no reuse, copy, inspect, or adapt requirement from any other repository
- no old architecture to preserve
- no old database to adapt
- no old API to maintain

The architecture pack under `docs/architecture/` is the **only** authority for behavior.

Implementation agents **MUST NOT**:

- invent business rules, modules, entities, workflows, permissions, screens, or architectural patterns
- add Wholesale, Travel, HR, manufacturing, or other verticals
- introduce GraphQL, microservices, Kafka, Kubernetes, event sourcing, or CQRS-everywhere (Document 00 §1, Document 03)

Existing code in *this* repo, once written, is **evidence**. If it contradicts the pack: detect → document → obtain a decision → change code to match the pack. Do not silently change the pack to match code.

---

## 2. Source-of-truth hierarchy

Read in this order when implementing:

| Rank | Document | Authority |
|---|---|---|
| 1 | `00-frozen-decisions.md` | Binding resolutions when numbered docs conflict |
| 2 | `07-permission-matrix-and-screens.md` | **Only** permission keys, system roles, screen entry |
| 3 | `08-ui-design-tokens.md` + `tokens.css` | Visual tokens only (not layouts) |
| 4 | `01` … `06` | Domain, schema, architecture, modules, API, security |

File names in this pack:

- `01-system-requirements-and-domain.md` (not `…-domain-design.md`)
- `07-permission-matrix-and-screens.md`

**Do not invent** missing architecture. If a rule is absent from 00–08, **stop and ask**.

---

## 3. Project / repository structure

From Document 00 §1 and Document 03:

```
ameen-retail/
  backend/
    manage.py
    pyproject.toml
    config/settings/{base,development,test,production}.py
    config/{urls,asgi,wsgi}.py
    shared/{api,database,exceptions,pagination,money,datetime,events}
    modules/
      identity/  tenants/  branches/  access/
      catalog/  inventory/  customers/  suppliers/
      sales/  pos/  purchasing/  payments/
      expenses/  accounting/  reporting/  audit/  configuration/
    tests/
  frontend/
    src/
      app/{router,providers,layout}
      features/{auth,dashboard,products,inventory,customers,suppliers,sales,pos,purchasing,accounting,reports,settings}
      shared/{api,components,hooks,validation,formatters,types}
  infrastructure/
  docs/architecture/
  docker-compose.yml
```

Each backend module: `domain/`, `application/`, `infrastructure/`, `api/` (Document 03). Document 04’s `interfaces/api` is the same boundary; **use `api/`** as in 00/03.

PostgreSQL schemas (Document 00): `identity`, `organization`, `catalog`, `inventory`, `sales`, `purchasing`, `customers`, `suppliers`, `payments`, `expenses`, `accounting`, `tax`, `audit`, `system`.

Do not create a second `src/` Python tree. Do not create empty future-vertical packages.

---

## 4. Technology implementation rules

| Layer | Must use (Document 00 §2, Document 03) |
|---|---|
| Frontend | React, TypeScript, Vite, React Router, TanStack Query, React Hook Form, Zod |
| Visual | Document 08 + `tokens.css` |
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL |
| Infra | Redis, Celery, Nginx, Docker, S3-compatible storage |
| CI / host | GitHub Actions, DigitalOcean |
| Tests | Pytest, Vitest, React Testing Library, Playwright |

- REST only under `/api/v1`. No GraphQL.
- POS **online only**.
- Redis is cache/broker/rate-limit/locks — **not** system of record (Document 03).
- Celery is **not** on the CompleteSale path (Document 00 §6).
- Passwords: **Argon2id** (Document 06, Document 00 §10).

---

## 5. Domain / module implementation boundaries

One owner per responsibility (Documents 00, 03, 04):

| Responsibility | Owner module | Must not |
|---|---|---|
| Credentials, sessions | `identity` | Tenant RBAC, sales |
| Tenant profile, settings | `tenants` | Inventory |
| Branch / warehouse relationship | `branches` | Products |
| Roles, permissions, `authorize()` | `access` | Sales/inventory rules |
| Product, variant, barcode, price list | `catalog` | Stock quantity |
| Balance, movement, adjust, transfer, count | `inventory` | Product definition |
| Customer master | `customers` | Sales ledger, payments |
| Supplier master | `suppliers` | POs |
| PO, receipt, purchase return | `purchasing` | Inventory/accounting tables |
| Sale, lines, sales returns | `sales` | Ledger, POS session |
| Terminal, session, cash movements | `pos` | A second sale model; stock; journals |
| Payment records | `payments` | Provider-specific wallets in the core model |
| Expense | `expenses` | Sales |
| COA, journals, periods | `accounting` | POS UI; calculating sales |
| Reports/dashboard reads | `reporting` | Mutations |
| Audit log | `audit` | Owning business transactions |

**Forbidden:** `from inventory.models import InventoryBalance` then decrement inside Sales.

**Required contracts** (Document 03):

- Inventory: `get_availability`, `issue_stock`, `receive_stock`, `transfer_stock`, `adjust_stock`
- Accounting: `post_sale`, `post_purchase`, `post_payment`, `reverse_posting`
- Payments: `record_payment`, `refund_payment`

No `ERPService`, `BusinessService`, or `GenericRepository[T]` dumping grounds.

Naming map (Document 00 §3): Business → `tenants`; Location → `branches` + `warehouses`; Sale → `sales.sales_orders` as `/sales`; Goods receipt → `purchase_receipts`; register → `pos_terminals` / `pos_sessions`.

Tenant ≠ Branch ≠ Warehouse ≠ POS terminal.

---

## 6. Application / use-case implementation

Layers (Documents 00, 03, 04): **HTTP/API → application use case → domain → infrastructure**.

Views/serializers: parse, auth hook, map DTO, call use case, map HTTP. **No** pricing, tax, stock, journal, or permission business rules in React or in serializers alone.

Each use case: input → `authorize` → validate → **one defined transaction** → domain + module contracts → DTO → audit (and outbox if specified).

Named use cases from Document 04 / Document 00 (do not rename the business operation):

- Identity: `LoginUser`, `LogoutUser`, `ChangePassword`, `ResetPassword`, `GetCurrentUser`
- Catalog: `CreateProduct`, `UpdateProduct`, `ActivateProduct`, `DeactivateProduct`, …
- Inventory: `AdjustStock`, `TransferStock`, `CheckAvailability`, …
- Purchasing: `CreatePurchaseOrder`, `ConfirmPurchaseOrder` (API approve → CONFIRMED), `ReceivePurchase`, …
- Sales: `CreateSale` (DRAFT), `CompleteSale` (`POST /sales/{id}/confirm`), `VoidSale`, `CreateSalesReturn`
- POS: `OpenRegister`, `CloseRegister`, cash in/out
- Payments: `RecordPayment` on **draft** sale
- Expenses: create/approve/cancel (no posted delete)

Shared kernel **only** (Document 00): Money, Currency, DateTime, TenantContext, DomainError, EntityId, Pagination, DomainEvent.

---

## 7. Database implementation rules

Follow Document 02 as constrained by Document 00:

- `tenant_id NOT NULL` + FK on tenant-owned tables
- Prefer composite FKs `(customer_id, tenant_id)` so documents cannot point at another tenant’s masters
- Money/qty: `NUMERIC(19,4)` — never FLOAT/REAL/DOUBLE
- Timestamps: `TIMESTAMPTZ` UTC
- UUID public/internal ids; human numbers via `document_sequences`, unique `(tenant_id, document_type, number)`
- Catalog: SKU on **variant** `UNIQUE(tenant_id, sku)`; **`catalog.barcodes`** `UNIQUE(tenant_id, value)`; every product has ≥1 variant
- Inventory: `UNIQUE(warehouse_id, product_variant_id)`; movements immutable; WAC on movement + balance value
- `reserved = 0` until reservations exist (Document 00 §5)
- `track_batch` / `track_serial` stay unused until lot/serial tables exist
- No `supplier-invoices` table unless a later schema addendum (Document 00 §7)
- Soft-delete: masters `is_active` / archive; financial/stock **VOIDED / CANCELLED / REVERSED**
- `PRIMARY KEY (tenant_user_id, role_id, branch_id)` with NULL `branch_id` is invalid; use Document 02’s sentinel / partial unique / all-branches flag
- Idempotency table: `UNIQUE(tenant_id, key)` (Document 02)

API may accept `product_id` + `branch_id` and resolve **default variant** + **branch default warehouse**. Document that resolution in code comments/OpenAPI; do not let clients pick a random warehouse by accident (Document 00 §3).

---

## 8. Transaction boundaries

Transactions wrap **business operations**, not single UPDATEs (Documents 00 §6, 03, 04).

### CompleteSale (`POST /sales/{id}/confirm`) — one DB transaction

1. Auth, tenant, permission (`pos.create_sale` or `sales.create` — §14), register open for POS cash  
2. Load sale; status **DRAFT**  
3. Recalculate totals (server)  
4. `SELECT … FOR UPDATE` inventory rows; availability  
5. Persist COMPLETED + line snapshots  
6. Payments: sum ≥ amount due; cash change is not revenue  
7. `inventory.issue_stock` + balances  
8. `accounting.post_sale` — must balance or fail  
9. Audit + **outbox** row  
10. COMMIT  

Failure → **ROLLBACK**. Inventory and journals are **synchronous**. Celery only after commit (receipt email/PDF/analytics).

### ReceivePurchase — one DB transaction

Validate PO/qty → receipt + lines → `inventory.receive_stock` → payable from **receipt** → `accounting.post_purchase` → PO received qty / PARTIALLY_RECEIVED|RECEIVED → audit → COMMIT.

### Return / void / adjust / close register

Same pattern: domain docs + inventory contract + payment/accounting as specified + audit, one COMMIT. Original completed sale is **never rewritten**.

Never leave: sale completed + stock unchanged, or payment recorded + sale still draft.

---

## 9. API implementation rules

Document 05 + Document 00 §9.

- Base: `/api/v1`. No `/api/latest`. Flat resources: `/products`, `/sales`, `/inventory/movements`.
- Commands: `POST /sales/{id}/confirm`, `…/void`, `…/return`, `POST /purchase-orders/{id}/approve`, `POST /pos/sessions`, `POST /pos/sessions/{id}/close`. **Do not** `PATCH { "status": "approved" }` to bypass the state machine.
- Envelope (always JSON; avoid 204):

```json
{
  "success": true,
  "data": {},
  "meta": {}
}
```

Collections put pagination in **`meta.pagination`**: `page`, `page_size`, `total`, `total_pages` (Document 05). Document 05 examples that also show a top-level `pagination` key are **not** a second format — implement **`meta.pagination`** (Document 00 §9).

Errors:

```json
{
  "success": false,
  "data": null,
  "meta": {},
  "errors": [{ "code": "VALIDATION_ERROR", "message": "…", "field": "name" }]
}
```

- Money: decimal **strings** + currency. Server calculates subtotal, discount, tax, total, change. Clients send lines, not authoritative totals.
- Time: ISO 8601 UTC (`Z`). “Today” in reports = tenant local calendar day (Document 00 §8).
- Pagination: `page` default 1, `page_size` default 25, **max 100**. Sort whitelist. `search=` server-defined.
- Headers: `X-Request-Id` (echo or generate), `X-Tenant-Id` (hint), `Idempotency-Key` on confirm/payment/receive/return/refund/transfer complete, `If-Match` on concurrent master edits → 409.
- Status: 401 unauthenticated; 403 missing permission; **404** cross-tenant IDOR; 405 method not allowed; 409 stock/status; 422 validation; 429 rate limit.
- OpenAPI 3.x is the machine contract when coding starts. Breaking changes → `/api/v2`.
- No client `POST /journal-entries` to record a sale.
- `POST /products` creates product + default variant + optional barcode (facade).
- Tax on create: **`tax_rate_id`**, not a raw percent (Document 00 §4, Document 05).

---

## 10. API validation and error handling

Three layers (Documents 01, 05, 06): request (types, required, ranges) → domain (state, stock, return qty) → database (FKs).

Machine codes from Document 05 (do not invent replacements):  
`AUTH_REQUIRED`, `AUTH_INVALID_TOKEN`, `AUTH_TOKEN_EXPIRED`, `PERMISSION_DENIED`, `TENANT_ACCESS_DENIED`, `VALIDATION_ERROR`, `INVALID_FIELD`, `INVALID_FORMAT`, `INVALID_VALUE`, `METHOD_NOT_ALLOWED`, `RESOURCE_NOT_FOUND`, `RESOURCE_ALREADY_EXISTS`, `RESOURCE_CONFLICT`, `INSUFFICIENT_STOCK`, `INVALID_STATUS_TRANSITION`, `SALE_ALREADY_COMPLETED`, `SALE_ALREADY_VOIDED`, `PAYMENT_EXCEEDS_BALANCE`, `PRODUCT_SKU_EXISTS`, `REGISTER_NOT_OPEN`, `ACCOUNTING_ENTRY_UNBALANCED`, `INTERNAL_ERROR`, `SERVICE_UNAVAILABLE`.

Login failures: **“Invalid email or password.”** (Document 06).  
Do not leak `required permission = …` in 403 bodies (Documents 05, 06).  
Production: no stack traces, SQL, paths, secrets.

Domain errors map to HTTP (e.g. `INSUFFICIENT_STOCK` → 409) as in Document 03/05.

---

## 11. Tenant isolation

Every tenant-owned query is scoped (Documents 00, 02, 05, 06).

Pipeline: authenticated user → membership → active tenant → permissions → branch → operation.

- `X-Tenant-Id` is a **hint**. Verify membership. **403** if no membership.
- Request **bodies must not** set `tenant_id`.
- Cross-tenant resource by id → **404** (do not confirm existence).
- Operate only if user, membership, and tenant are **ACTIVE**. Suspended tenant → deny normal ops (Document 06).
- No public tenant self-registration. Platform creates tenants (Documents 00, 06).
- Test Tenant A ↛ Tenant B for products, customers, suppliers, sales, purchases, inventory, expenses, payments (Documents 00 §13, 06).

---

## 12. Authentication

Documents 00 §10, 05, 06.

- Email + password; Argon2id; invite → employee sets password (admins do not set employee passwords).
- **Web:** server session; token **hashed** in `sessions`; cookie **HttpOnly + Secure + SameSite**; **CSRF** required.
- Do **not** store access/refresh tokens in `localStorage`.
- Logout **revokes** the session. Password change/reset invalidates all sessions.
- User statuses: `ACTIVE`, `INVITED`, `SUSPENDED`, `DISABLED`. Do not hard-delete users with history.
- Idle ~8h, absolute ~30d (Document 06 starting values).
- Rate-limit login harder than `GET /products`. Progressive delay / temporary lock, not permanent lock after a few failures.
- MFA/SSO/API keys: **out of MVP**; identity must allow MFA later.
- Frontend guards: Auth → Tenant → Permission → page. Guards **do not** replace API checks.
- Routes: `/login`, `/app/*` tenant workspace, `/platform/*` platform — never mixed (Document 00 §12, Document 03).

Bearer for mobile is **later** (Document 00). Do not implement a second web auth that contradicts cookies.

---

## 13. Authorization

Fail **closed**. Deny by default (Documents 06, 07).

```
Authentication
  → Tenant membership + tenant active
  → Permission (Document 07 key)
  → Resource tenant_id (+ branch scope)
  → Domain policy ALLOW | DENY | REQUIRE_APPROVAL
  → Use case
```

- Never `if user.role == "ADMIN"` in domain logic. Use `authorize(user, tenant, permission, resource?, branch?)`.
- Same keys for UI, API, nav, tests (Document 07).
- **Owner** (Business Owner) is protected. Admins cannot assign/remove Owner. Ownership transfer is an explicit audited command (Documents 00, 06, 07).
- Tenants assign **system roles only**. No role-designer UI (Document 07 §3, Document 00 §11).
- Mass assignment allow-lists. Never bind `is_owner` / Owner from JSON.
- Permission ≠ branch scope ≠ plan (Documents 00 §11, 07 §1).
- POS extra checks (not extra keys): branch in scope, terminal belongs to branch, register **open**, payment method allowed (Document 07 §7).
- `sales.update` applies to **DRAFT only** (Document 07). Completed sales are immutable (Document 00 §6).

### Plan / capability (item 15)

Document 07: **Permission ≠ plan.** Do not encode `starter_*` / `professional_*` in permission keys.

The frozen pack does **not** define a plan table, plan codes, or server plan-check algorithm beyond “capability is separate.” **Do not implement plan gating** until a frozen plan model exists. Do not invent plan flags.

### Business type (item 16)

`business_type = RETAIL` only (Document 00 §1, Document 01). Do not add other types. Do not implement per-vertical permission variants.

### Branch / resource scope (item 17)

Document 07 §1 and Document 06: permission does not grant all branches. Users restricted to a branch must not read another branch’s sales via `?branch_id=`. Evaluate branch on the query, not only in the UI.

---

## 14. Exact permission-key usage (Document 07 only)

**Document 07 is the sole authority for permission identifiers** used in backend, API, frontend, route guards, navigation, UI actions, role seeds, and tests.

**Do not** invent, rename, or alias keys (`sales.confirm`, `sales.edit`, `sales.delete`, `catalog.view`, `pos.register.open`, `manage_products`, `products.screen.view` are **forbidden**).

### Canonical keys (copy of Document 07 registry)

**Dashboard:** `dashboard.view`

**Sales:** `sales.view`, `sales.create`, `sales.update`, `sales.cancel`, `sales.void`, `sales.export`, `sales.print`

**Sales returns:** `sales_returns.view`, `sales_returns.create`, `sales_returns.approve`, `sales_returns.cancel`, `sales_returns.refund`

**POS:** `pos.view`, `pos.create_sale`, `pos.open_register`, `pos.close_register`, `pos.view_sessions`, `pos.cash_in`, `pos.cash_out`, `pos.refund`, `pos.reprint`

**Customers:** `customers.view`, `customers.create`, `customers.update`, `customers.archive`, `customers.restore`, `customers.export`, `customers.view_transactions`

**Products:** `products.view`, `products.create`, `products.update`, `products.archive`, `products.restore`, `products.export`, `products.print`

**Categories / brands / units:** `product_categories.view|create|update|archive`, `brands.view|create|update|archive`, `units.view|create|update|archive`

**Inventory:** `inventory.view`, `inventory.view_movements`, `inventory.adjust`, `inventory.transfer`, `inventory.receive`, `inventory.export`  
(`inventory.count` is **not** in the v1 registry until count screens exist — Document 07 §4. Do not seed it now.)

**Suppliers:** `suppliers.view`, `suppliers.create`, `suppliers.update`, `suppliers.archive`

**Purchase orders:** `purchase_orders.view`, `purchase_orders.create`, `purchase_orders.update`, `purchase_orders.approve`, `purchase_orders.cancel`, `purchase_orders.export`

**Goods receipts:** `goods_receipts.view`, `goods_receipts.create`, `goods_receipts.post`, `goods_receipts.cancel`

**Purchase returns:** `purchase_returns.view`, `purchase_returns.create`, `purchase_returns.approve`, `purchase_returns.cancel`

**Expenses:** `expenses.view`, `expenses.create`, `expenses.update`, `expenses.approve`, `expenses.cancel`, `expenses.export`

**Finance:** `finance_accounts.view|create|update|archive`, `finance_transactions.view|create|post|void`, `payments.view|create|void|refund`, `receivables.view`, `receivables.create_payment`, `receivables.export`, `payables.view`, `payables.create_payment`, `payables.export`

**Reports:** `reports.sales.view`, `reports.inventory.view`, `reports.purchasing.view`, `reports.customers.view`, `reports.expenses.view`, `reports.finance.view`, `reports.export`

**Users:** `users.view`, `users.create`, `users.update`, `users.activate`, `users.deactivate`, `users.assign_roles`

**Settings:** `settings.business.view`, `settings.business.update`, `branches.view|create|update|archive`, `tax.view|create|update|archive`, `currency.view`, `currency.update`, `numbering.view`, `numbering.update`

**Audit:** `audit.view`, `audit.export`  
No `audit.update` / `audit.delete` for tenants.

### Screen entry (Document 07 §5)

| Screen | Required to enter |
|---|---|
| Dashboard | `dashboard.view` (widgets still need domain view) |
| Products | `products.view` |
| Categories | `product_categories.view` |
| Inventory | `inventory.view` |
| Movements | `inventory.view_movements` |
| Adjustments | `inventory.view` **and** `inventory.adjust` |
| Transfers | `inventory.view` **and** `inventory.transfer` |
| Sales list | `sales.view` |
| Create sale | `sales.create` |
| Returns | `sales_returns.view` |
| POS | `pos.view` |
| Sessions | `pos.view_sessions` |
| Financial reports | `reports.finance.view` |
| Users | `users.view` |
| Tax settings | `tax.view` |
| Audit | `audit.view` |

Direct URL without view → frontend 403 **and** API deny. Hide Create without `products.create`; API still 403 on `POST /products`.

`sales.view` does **not** imply `reports.sales.view`. Dashboard finance widgets require `reports.finance.view` (or finance view as in 07 §4) — cashier must not see finance.

### API mapping (Document 07 §8 + Document 00 §11)

| Operation | Permission |
|---|---|
| `GET /products` | `products.view` |
| `POST /products` | `products.create` |
| `POST /products/{id}/deactivate` | `products.archive` |
| `POST /sales` | `sales.create` |
| `POST /sales/{id}/confirm` from POS | `pos.create_sale` |
| `POST /sales/{id}/confirm` back-office | `sales.create` |
| `POST /sales/{id}/void` | `sales.void` |
| `POST /sales/{id}/return` | `sales_returns.create` (issue refund: `sales_returns.refund`) |
| `POST /inventory/adjustments` | `inventory.adjust` |
| `POST /pos/sessions` | `pos.open_register` |
| `POST /pos/sessions/{id}/close` | `pos.close_register` |

### System roles (exactly eight — Document 07 §6)

Business Owner, Administrator, Accountant, Sales Manager, Inventory Manager, Cashier, Purchasing Officer, Viewer.

Seed role_permissions from Document 07 §7 matrix and cashier explicit grant list. **Default cashier does not get `pos.refund`.** Owner cannot erase audit.

`users.assign_roles` cannot assign/remove Business Owner.

### Payment methods vs AR (Document 00 §6, Document 07)

POS tenders: `cash`, `card`, `mobile_money`, `bank_transfer`, `other`. **No `credit` tender.** `receivables.create_payment` is unused in POS until AR is an explicit Starter decision.

---

## 18. Frontend architecture rules

Document 00 §12, Document 03, Document 04, Document 07.

- Feature folders; no global dump of 500 unrelated components.
- Server state: TanStack Query. Forms: RHF + Zod. Auth/tenant/permissions as dedicated context — not one Redux bag of API data.
- Central API client: session cookie, CSRF, `X-Tenant-Id`, `X-Request-Id`, envelope unwrap, timeouts. No ad-hoc `fetch` per component with different headers.
- After mutations, invalidate the relevant queries (e.g. product list after create).
- Navigation from **effective Document 07 permissions**, not a hard-coded role menu.
- A screen exists because Document 07 lists it, not because a table exists.
- **Do not invent layouts.** Document 08 is tokens only. POS/admin layout sketches in Document 01 §34 are directional; pixel layout is not frozen — use tokens, do not invent a second IA.

Pages stay small: page → hook/query → form/table/modal. No 1000-line components that mix API, tax math, and routing.

---

## 19. Route and navigation authorization

Tenant app under `/app` (Document 07 routes are relative to `/app`). Platform under `/platform`.

Resolver: user → roles → Document 07 permissions → visible nav.  
Route guard uses the **same view key** as the screen table. Missing view → Access Denied, not a blank app shell.

---

## 20. UI token usage (Document 08)

Implementation **must** use:

- `docs/architecture/08-ui-design-tokens.md`
- `docs/architecture/tokens.css`

Frozen:

- Brand seed **`#147D78`** (only in the token file, not hard-coded in components)
- Material 3 palettes: primary, secondary, tertiary, neutral (semantic CSS variables)
- **Inter** for headline, body, and label
- Default radius **12px** (`radius-md` / `ROUND_TWELVE`)
- Large surfaces **16px** (`radius-lg` — dialogs, large POS panels, sheets)
- Pills (`radius-full`) **only** for avatars, switches, count badges
- **Light mode default** (`color-scheme: light`); dark tokens exist but are not the shipping default

Also from Document 08: tabular nums for money; 150ms/200ms motion; surface-container elevation over heavy shadows; focus ring 2px primary. Do not invent another palette or display font.

---

## 21. State management

Split: server (Query) / UI (React) / form (RHF) / auth session / tenant context / authorization (permission list from `GET /auth/me`).  
Do not cache authorization-sensitive lists in Redis without tenant+user+permission scope (Document 03 Redis rules).

---

## 22. Forms and validation

Zod + RHF for UX. Server remains authoritative for price, tax, stock, totals, permissions.  
States: schema errors, server `errors[]`, loading, success, duplicate-submit prevention (disable submit; Idempotency-Key on money/stock commands).

---

## 23. Loading / empty / error states

Every async screen: loading, empty, success, error, permission denied, network failure. No infinite blank page.

---

## 24. Audit logging

Documents 00, 02, 06: append-only for tenants. Fields: actor, tenant, action, resource type/id, timestamp, result, metadata, ip, user_agent.

Audit at least: login success/failure, logout, password change/reset, user invite/activate/suspend, role assign, product changes, stock adjust, sale confirm/void, returns, payments, expense approve, config changes (Document 06).

No passwords, tokens, PAN in logs or metadata.

---

## 25. State-transition enforcement

Implement **only** these machines (Document 00):

**Sale:** `DRAFT → COMPLETED`; `DRAFT → CANCELLED`; `COMPLETED → VOIDED`; `COMPLETED → PARTIALLY_REFUNDED → REFUNDED`. Invalid: `COMPLETED → DRAFT`, lingering `CONFIRMED`/`PAID`.

**PO:** `DRAFT → CONFIRMED → PARTIALLY_RECEIVED → RECEIVED`; cancel draft/confirmed only. API approve → **CONFIRMED**. `RECEIVED` cannot cancel.

**Product:** DRAFT → ACTIVE → INACTIVE (deactivate). Referenced product `DELETE` → 409.

**Expense:** DRAFT → APPROVED → PAID; posted → reverse/cancel, not DELETE.

**Cash session:** OPEN / CLOSED; one open session per register. Variance stored; never rewrite sales to match cash.

**Return:** new document; complete applies stock/finance (Document 01/04).

---

## 26. Idempotency

Required (Document 00 §6, Document 05): confirm sale, payment, receive, return/refund, transfer complete.

Same `Idempotency-Key` + tenant → return original result; no second movement or payment.

---

## 27. Background jobs

Celery only for: email, PDF, CSV/export, analytics refresh, integration callbacks, housekeeping (Documents 00, 03).  
Not: CompleteSale, receive, adjust, login. POS must work if workers are down. Outbox in the same COMMIT as the business transaction.

---

## 28. Caching

Redis optional for rate limit, session auxiliary data, idempotent locks. **Never** cache in a way that breaks tenant isolation, authz, stock, or money. PostgreSQL remains authoritative.

---

## 29. Database migrations

Django migrations only. Model change → generate → inspect → apply → test. No manual production DDL. Tenant-safe defaults; no data migrations that scan all tenants unsafely without a plan in a later spec.

---

## 30. Seed / reference data

Deterministic, idempotent, environment-safe:

- Document 07 permission rows (exact keys)  
- Eight system roles + role_permissions per Document 07 matrix  
- Currencies as needed from Document 02 (`USD`, `SOS`, `EUR` examples)  
- No duplicate permissions on second run  

Do not seed `inventory.count` until Document 07 adds it.  
Do not seed `credit` payment method for POS.

---

## 31–33. Testing

Pyramid (Documents 01, 03, 05, 06): unit/domain → application/integration → API/contract → few Playwright journeys.

**Must** (Document 00 §13):

- Cross-tenant deny on major resources  
- Cashier cannot invite users, adjust stock, change settings, or refund above policy (default cashier has no `pos.refund`)  
- CompleteSale atomic; idempotent retry  
- Two cashiers, stock = 1 → one `INSUFFICIENT_STOCK`  
- Journal balances  
- Return qty ≤ eligible  
- No float money in JSON  

**Also:** duplicate SKU; missing permission 403; unauthenticated 401; invalid PO `RECEIVED → cancel`; register not open; CompleteSale forced failure rolls back sale+stock+payment+journal.

Contract tests vs OpenAPI: status, envelope, types, pagination, error shape.

E2E (not every rule): login → tenant → product → opening/adjust stock → open register → sell → pay → confirm → stock down → report; return path; close register variance.

Security tests: privilege escalation (cashier → assign Owner), IDOR, CSRF on cookie POSTs.

Playwright does **not** replace domain tests for WAC, tax, or return eligibility.

---

## 34. Observability / logging

`request_id` on every request (Document 05, 03). Structured logs: level, request_id, tenant_id, user_id, endpoint, error_code. Health checks. Job failure logs. No secrets.

---

## 35. Environment / configuration

Env: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, CORS allowlist, email, storage (Documents 03, 06).  
Never commit secrets. Distinct development / test / production. Tests must not use production DBs. HTTPS + HSTS in production. CORS **not** `*`.

Feature flags (e.g. public registration **false**) are not a substitute for Document 07 checks.

---

## 36. Definition of Done

A feature is done only when (operationalizing Documents 00–08):

Requirement from the pack is implemented · schema/migration matches Document 02/00 · use case + transaction correct · API envelope and Document 07 permission · tenant + branch isolation · UI uses Document 08 tokens and Document 07 screen keys · audit if required · unit + integration (+ E2E if journey) · lint/types · no regression · **no new permission keys**.

---

## 37. Implementation constraints for AI coding agents

- Do **not** “build the entire ERP” in one task.  
- Do **not** inspect or copy any other ERP repo.  
- Every task: cite pack docs, name Document 07 keys, name transaction, name tests.  
- First code slice when asked (Document 00 §15): Identity + tenant + RBAC → branch/warehouse/terminal → product/default variant/barcode → opening/adjust stock → open register → scan → draft sale → pay → confirm → stock + journal + report. Purchasing is slice 2.  
- Bounded diffs; no drive-by refactors.  
- If pack conflict: record it; apply Document 00 (permissions: Document 07); do not silently pick.  
- Output: files, migrations, APIs, permissions used (exact 07 strings), tests added/run, unresolved pack gaps.

---

## 38. Architecture compliance gate (before merge)

- Correct module owns the write; no cross-table updates  
- Use case layer present; thin views  
- Transaction + locking for stock/money  
- Decimal money; UTC timestamps  
- Document 07 keys only; fail closed; Owner protected  
- Tenant 404 IDOR; no `tenant_id` in body  
- Commands not status PATCH  
- Celery not on CompleteSale  
- Tokens from Document 08; light default  
- Tests: authz, tenant, CompleSale rollback, idempotency  
- OpenAPI/envelope match Document 05  

Fail the gate if any invented permission or copied legacy module appears.

---

## Appendix A — Conflicts in Documents 00–08 (resolved for implementers)

These are **recorded**, not silently chosen. **Do not edit 00–08** from this spec.

| Topic | Tension | Resolution for implementers |
|---|---|---|
| Permission identifiers | Doc 05/06 historically used `sales.confirm`, `pos.register.open`, `sales.refund`, `users.invite`, `reports.financial.view` | **Document 07 + Document 00 §11.** Use §14 keys only. |
| Platform permission keys | Doc 06 lists `platform.tenants.*`, `platform.users.*`, `platform.audit.view`. Doc 07 does not list platform keys. User rule: 07 is sole identifier authority. | **Do not invent** `platform.tenants.view` etc. Implement tenant app first. Platform endpoints wait until platform keys are added to Document 07 (or an approved addendum). Doc 00 still forbids mixing platform and tenant namespaces. |
| Price override | Doc 00 §6 mentions “price-override permission.” Doc 07 has **no** such key. | **Do not invent a key.** Until 07 adds one, server **re-prices**; ignore client `unit_price` (no override). |
| `inventory.count` | Domain 01/03 require counts; 07 says add key when screens exist | Do not implement count **screens/API** or seed `inventory.count` until 07 is updated. |
| Sale confirm vs CONFIRMED status | Older API prose vs Doc 00 states | Confirm command → status **`COMPLETED`**. |
| Purchase APPROVED/ORDERED | Docs 03/05 extra states vs 00/04 | **CONFIRMED** only; approve API maps to CONFIRMED. |
| Auth Bearer vs cookies | Doc 05 vs 00/06 | **HttpOnly session cookies** for web. |
| API envelope pagination | Some envelopes show top-level `pagination` | **`meta.pagination`** (Doc 00 §9, Doc 05 collection example). |
| Module path `apps/` vs `modules/` | Informal vs Doc 03 | **`backend/modules/`**. |
| Returns as its own Django app | Some lists vs 03/00 Sales owns returns | **`sales` module** owns return documents; permissions are `sales_returns.*` (07). |
| AR/receivables | Schema/07 finance vs 00 no credit POS | Tables/view permissions may exist; **no POS credit tender**; do not auto-create AR from POS. |
| Doc 06 danger keys `ownership.transfer`, `security.settings.update` | Not in 07 registry | **Do not seed those strings.** Ownership transfer remains a **protected command** in domain/security (Doc 06) authorized as Owner-only until 07 adds a key. |
| UOM conversions | Domain 01 vs 00 piece-oriented v1 | No conversion engine until a later spec. |
| First slice vs full purchasing-first phases | Doc 04 phases vs Doc 00 §15 | **Doc 00 §15** when coding starts. |

---

## Appendix B — Assumptions not resolved in the frozen pack

Do **not** treat these as approved. Ask before building:

1. Exact numeric refund/discount thresholds for `REQUIRE_APPROVAL` (Doc 06 examples are illustrative).  
2. Full per-role expansion of “Full / Limited” into every 07 key except **cashier explicit grants** (07 §7). Seed Owner/Admin as all **tenant** 07 keys except audit mutate (none exist) and Owner-assign rules. Accountant/Sales Manager/Inventory Manager/Purchasing Officer/Viewer: follow 07 §7 compact matrix; if a specific key is ambiguous (e.g. Purchasing “expenses limited”), **ask** rather than invent a subset.  
3. Platform admin permission identifiers (see Appendix A).  
4. Price-override permission (see Appendix A).  
5. Complete visual layout/wireframes (Doc 08 explicitly excludes them).  
6. Whether `GET /roles` and `GET /permissions` (Doc 05) are Owner/Admin-only (`users.assign_roles` / `users.view`) — map to `users.view` for listing assignable roles; do not add `roles.view`.  
7. Object-storage signed URL lifetime, malware scanning vendor.  
8. Exact production rate-limit numbers (Doc 05 says load-test later).  
9. `legal_name` on tenant vs branch-only address (Doc 01 vs 02). Use Document 02 columns unless 00 lists extra tenant fields as required — 00 naming map uses `tenants`; include 02 tenant columns; add `legal_name` only if required by a later decision.  
10. Stock-count document API (blocked on `inventory.count`).

---

## Appendix C — Confirmations

- **No permission keys were invented in this specification.** The list in §14 is Document 07’s registry (plus explicit “do not seed `inventory.count`”).  
- **No previous ERP / Kinetic / Ameen ERP repository or code was inspected or referenced** as an implementation source. Greenfield only.
