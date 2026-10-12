# Ameen Retail v1 — Frozen Decisions

**Status:** Binding for implementation. Overrides conflicting prose in the numbered design docs.

**Updated:** 2026-10-08 (docs 01–07; permission matrix in 07)

---

## 1. Product and architecture

- Retail-only SaaS. `business_type = RETAIL`. Do not add other verticals.
- **Modular monolith:** one repo, one Django app deploy, one PostgreSQL database, strongly separated modules.
- **Not** microservices, Kafka, Kubernetes, event sourcing, CQRS-everywhere, GraphQL, or a generic ERP metadata engine.
- Layers: **API → Application use case → Domain → Infrastructure**. Thin views. Domain does not import HTTP, Django request, Celery, Redis, or React.
- **No cross-module ORM writes.** Sales never `UPDATE` inventory tables. Use module contracts: `inventory.issue_stock()`, `accounting.post_sale()`, etc.
- Shared kernel only: Money, Currency, DateTime, TenantContext, DomainError, EntityId, Pagination, DomainEvent. Not `Sale`, not `ERPHelper`.
- Monorepo: `backend/`, `frontend/`, `infrastructure/`, `docs/`.
- Backend modules live at `backend/modules/...` (not a second `src/` tree).
- PostgreSQL **schemas** match domains: `identity`, `organization`, `catalog`, `inventory`, `sales`, `purchasing`, `customers`, `suppliers`, `payments`, `expenses`, `accounting`, `tax`, `audit`, `system`.

## 2. Stack

| Layer | Choice |
|---|---|
| Frontend | React, TypeScript, Vite, React Router, TanStack Query, React Hook Form, Zod |
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL |
| Infra | Redis, Celery, Nginx, Docker, S3-compatible storage |
| CI / host | GitHub Actions, DigitalOcean |
| Tests | Pytest, Vitest, React Testing Library, Playwright |

POS is **online only** in v1. Do not promise offline POS.

## 3. Naming map (domain → schema/API)

| Domain design | Database / API |
|---|---|
| Business | `tenants` / tenant |
| Location | `branches` + `warehouses` (distinct) |
| Sale | `sales.sales_orders` exposed as `/sales` |
| Goods receipt | `purchase_receipts` |
| Cash register / session | `pos_terminals` / `pos_sessions` |
| Confirm sale (API) | Completes the sale (`COMPLETED`) |

**Distinct concepts:** Tenant ≠ Branch ≠ Warehouse ≠ POS terminal.

Inventory balance key: **`warehouse_id` + `product_variant_id`**.  
API may accept `product_id` + `branch_id` and resolve **default variant** + **branch default warehouse**. Document the resolution; do not let clients pick a random warehouse by accident.

## 4. Catalog vs inventory

- Product ≠ stock. Never `product.quantity`.
- Every product has **at least one variant** (simple products: one default variant). SKU, barcodes, cost/selling price, tax assignment live on the **variant** (API may facade this on `POST /products`).
- **Multiple barcodes** per variant: `catalog.barcodes` with `UNIQUE(tenant_id, value)` and `is_primary`. Do not rely on a single `product_variants.barcode` column as the only barcode store.
- SKU ≠ barcode. `UNIQUE(tenant_id, sku)` on variants.
- Hierarchical categories. Optional brand (0 or 1).
- `track_batch` / `track_serial` / expiry flags may exist but must stay **disabled** until lot/serial tables exist. Do not allow tracking without storage.
- Units: v1 may ship **piece-oriented** selling/stock unit on the variant. Do not build a full UOM engine unless a later spec adds `unit_conversions`. If carton purchasing is required, that spec must land before purchasing slice.
- Pricing: `price_lists` + `product_prices` is the model. Variant `selling_price` is the default/base. Server is authoritative for totals.
- Tax: assign **`tax_rate_id`** (or category), never a raw percent on the product payload. Tax module/schema owns rates; catalog references them.
- Product lifecycle: DRAFT → ACTIVE → INACTIVE. Do not hard-delete products with history; `POST /products/{id}/deactivate`. `DELETE` returns conflict if referenced.

## 5. Inventory

- Source of truth: **immutable `inventory_movements`**. `inventory_balances` are materialized (`available = on_hand - reserved`).
- v1: `reserved = 0` until reservations are implemented. Do not fake reservations.
- Costing: **weighted average** only. Do not let tenants pick FIFO in v1. Store cost on movements; maintain value/unit cost on balances.
- Negative stock: **forbidden** unless `inventory.negative_stock_policy` is explicitly enabled later. Default deny. Concurrent last-item sales: `SELECT … FOR UPDATE` (or equivalent); loser gets `INSUFFICIENT_STOCK`.
- Stock changes only via movements: `PURCHASE_RECEIPT`, `SALE`, `SALE_RETURN`, `PURCHASE_RETURN`, `ADJUSTMENT_IN`, `ADJUSTMENT_OUT`, `TRANSFER_IN`, `TRANSFER_OUT`, `OPENING_BALANCE`, `STOCK_COUNT`.
- Adjustments have a **header** (reason: DAMAGED, LOST, EXPIRED, THEFT, COUNT_CORRECTION, OTHER) — never silent overwrite of quantity.
- Stock **counts** are in domain/architecture. Include count documents when building Inventory beyond adjust/transfer; do not skip the approve → movement path.
- Transfers: `stock_transfers` + lines, then `TRANSFER_OUT` / `TRANSFER_IN` movements.

## 6. Sales, POS, payments

**Sale states (v1):**

```
DRAFT  →  COMPLETED  →  VOIDED
                   →  PARTIALLY_REFUNDED  →  REFUNDED
DRAFT  →  CANCELLED   (never completed)
```

- `POST /sales` creates **DRAFT** (cart). Cart is not a completed sale.
- `POST /sales/{id}/payments` attaches tenders to the **draft** (split payments allowed).
- `POST /sales/{id}/confirm` = **CompleteSale** (atomic). Result status is **`COMPLETED`**. Do not persist a lingering `CONFIRMED` / `PAID` retail status.
- `POST /sales/{id}/void` from COMPLETED only (permission + audit).
- Returns are **new documents** (`POST /sales/{id}/return`). Never edit completed sale lines.
- Sale lines store **snapshots**: product name, SKU, unit price, tax, discount, line total.
- Customer optional: `customer_id` may be null (walk-in). Do not require customer on POS.
- Client `unit_price` is a requested override; server re-prices unless the user has price-override permission. **Server calculates** subtotal, discount, tax, total, change. Change is not revenue.
- Payment methods v1: `cash`, `card`, `mobile_money`, `bank_transfer`, `other`.
- **Store credit / AR is out of POS v1** unless a later product decision turns it on. Do not enable `credit` as a tender until AR is explicitly in Starter.
- POS owns register/session/cash movements/receipt UX. **Sales owns Sale.** POS never updates inventory or journals directly.
- POS APIs to add with the sales slice: `POST /pos/sessions`, `POST /pos/sessions/{id}/close`, `GET /products/lookup?barcode=` (fast). Checkout still uses sales + payments + confirm.
- One **open session per register**. Close stores expected, actual, variance. Variance is preserved; never rewrite sales to force cash to match.
- `pos_cash_movements` for cash in/out with reason.

**CompleteSale transaction (synchronous, one DB transaction):**

1. Auth, tenant, permission, register open (for POS cash)
2. Load draft sale, status = DRAFT
3. Recalculate totals
4. Lock inventory rows, check availability
5. Persist sale completed + lines
6. Record payments (sum >= amount due; cash may produce change)
7. Issue stock movements + update balances
8. Post accounting journals (must balance)
9. Audit + outbox row
10. COMMIT

If any critical step fails: **ROLLBACK**. Inventory and journals are **not** async. Celery only after commit (email, PDF, analytics).

Idempotency-Key required on confirm, payment, receive, return/refund, transfer complete.

## 7. Purchasing

**States:**

```
DRAFT → CONFIRMED → PARTIALLY_RECEIVED → RECEIVED
DRAFT → CANCELLED
CONFIRMED → CANCELLED
```

- API `POST /purchase-orders/{id}/approve` maps to **CONFIRMED** (do not add extra APPROVED/ORDERED/CLOSED states in v1).
- PO does **not** change inventory. Receipt does.
- Partial receiving required. Track received qty per line.
- `RECEIVED` cannot be cancelled; use purchase return.
- Payable is created from **receipt** (or a later supplier-invoice spec). Do not invent `supplier-invoices` at implementation time without a schema addendum.
- Purchasing calls Inventory and Accounting interfaces; never writes those tables.

## 8. Accounting, expenses, money, time

- Double-entry. Posted journal: **debits = credits** or it does not post.
- POS/Sales/Purchasing/Expenses do not `UPDATE account_balance`. They call `accounting.post_*`.
- Clients **GET** accounts, journals, TB, P&amp;L. They do **not** `POST /journal-entries` to record a sale.
- Expenses **are in v1** (module was missing from one architecture table; restored). Posted expenses: reverse/cancel, do not `DELETE`.
- Money: `Decimal` / `NUMERIC(19,4)`. API JSON amounts as **strings**. Never float.
- Timestamps: **timestamptz UTC** in DB. Tenant timezone for business-day reports (“today” = local calendar day, not UTC midnight).
- Document numbers human-readable (`SALE-000001`), unique per `(tenant_id, document_type, number)`. UUID is the public/internal id. Sequences are not security.

## 9. API conventions

- Base: `/api/v1`. No `/api/latest`.
- **Flat paths:** `/products`, `/sales`, `/inventory/movements` — not `/catalog/products` in the public URL.
- Envelope: `{ success, data, meta, errors[] }` with `code`, `message`, `field`.
- Always JSON envelope (avoid 204 for APIs that promised an envelope).
- Pagination: `page`, `page_size` default 25, max 100. Sort whitelist.
- Headers: `X-Request-Id`, `Idempotency-Key` on money/stock commands, `If-Match` on concurrent edits.
- `X-Tenant-Id` is a **hint**. Server verifies membership. Request bodies must not include `tenant_id`.
- Status: 401 unauthenticated, 403 missing permission, **404** for cross-tenant IDOR (do not reveal existence), 409 stock/status conflict, 422 validation.
- OpenAPI 3.x is the machine contract once implementation starts.
- Breaking changes require `/api/v2`.

## 10. Auth and security

- **No public tenant self-registration.** Platform admins create tenants.
- Identity: email + password, **Argon2id**. Invite employee → they set password. Do not have admins set employee passwords.
- **Web:** server session, token **hashed** in `sessions`, cookie **HttpOnly + Secure + SameSite**, CSRF on. Do not put access/refresh tokens in `localStorage`.
- Logout **revokes** server session. Password change invalidates sessions.
- Bearer tokens may be added later for mobile; do not make localStorage the web strategy.
- User statuses: ACTIVE, INVITED, SUSPENDED, DISABLED. Do not hard-delete users with history.
- Membership `UNIQUE(tenant_id, user_id)`. Operate only if user, membership, and tenant are ACTIVE.
- **Owner** is a protected system role. Admins cannot assign/remove Owner. Ownership transfer is an explicit audited command.
- RBAC only (no ABAC/OPA in v1). `authorize(user, tenant, permission, resource?)`.
- Domain policies: `ALLOW | DENY | REQUIRE_APPROVAL` (refund/discount thresholds).
- Platform permissions (`platform.tenants.*`) ≠ tenant permissions. **No impersonation in MVP.**
- Deny by default. Same permission codes drive UI and API.
- Mass assignment: explicit allow-lists. Never bind `is_owner` / role from JSON blindly.
- Rate-limit login harder than `GET /products`. Generic login error: “Invalid email or password.”
- Secrets in env, never git. HTTPS only in production. CORS allowlist. Security headers.
- MFA, SSO, API keys: **out of MVP**; identity must allow adding MFA later.
- Audit: append-only for tenants. No passwords/tokens/PAN in logs or audit metadata.

## 11. Roles, screens, and permission keys (v1)

**Canonical registry:** `docs/architecture/07-permission-matrix-and-screens.md`.

**System roles (exactly these eight):** Business Owner, Administrator, Accountant, Sales Manager, Inventory Manager, Cashier, Purchasing Officer, Viewer.

There is **no** generic “Manager” role. Tenants **cannot** edit roles/permissions; they only `users.assign_roles` from this list. Owner cannot be assigned/removed except via ownership transfer. No tenant Roles admin UI.

**Screen rule:** `*.view` is the screen boundary. Action codes control buttons. Direct URL without view → 403. API still checks the same codes. Dashboard widgets require domain view (cashier does not see finance).

**Permission ≠ branch scope ≠ plan.** Atomic codes; no `manage_*` parents.

**Key mappings (replaces older `sales.confirm` / `pos.register.open` names):**

| API / screen | Permission |
|---|---|
| GET /products, Products screen | `products.view` |
| POST /products | `products.create` |
| POST /products/{id}/deactivate | `products.archive` |
| POS checkout confirm | `pos.create_sale` |
| Back-office sale confirm | `sales.create` |
| POST /sales/{id}/void | `sales.void` |
| Sales returns | `sales_returns.*` (not `sales.refund`) |
| POST /pos/sessions | `pos.open_register` |
| POST /pos/sessions/{id}/close | `pos.close_register` |
| Adjustments screen + API | `inventory.view` **and** `inventory.adjust` |
| Transfers | `inventory.transfer` (not implied by adjust) |
| Reports | `reports.<domain>.view` — **not** implied by `sales.view` |

Do not use `expenses.delete` for posted expenses. `inventory.count` is added when stock-count screens are implemented.

## 12. Frontend

- Feature folders: `features/pos`, `features/sales`, … not a global `components/` dump.
- Server state: TanStack Query. Forms: RHF + Zod. No giant Redux store for API data.
- Routes: `/login`, `/app/*` tenant workspace, `/platform/*` platform admin — never mixed.
- UI permission checks are UX only.
- **Visual tokens (binding):** seed/primary `#147D78`; Inter for headline, body, and label; default corner radius **12px** (`ROUND_TWELVE`). Full roles and CSS: `docs/architecture/08-ui-design-tokens.md` and `docs/architecture/tokens.css`. Do not introduce a second brand hue or display font.

## 13. Testing that is mandatory

- Tenant A cannot access Tenant B for every major resource.
- Cashier cannot invite users, adjust stock, change settings, or refund above policy.
- Complete sale is atomic; retry with same idempotency key does not double-charge or double-issue stock.
- Two cashiers, stock = 1 → one success, one `INSUFFICIENT_STOCK`.
- Journal posts balance.
- Return qty cannot exceed eligible qty.
- No float money in API responses.

## 14. Out of v1

Manufacturing, BOM/MRP, hospitals, universities, construction, travel, field service, payroll, CRM automation, e-commerce marketplace, advanced WMS, offline POS, FIFO costing switch, store credit/AR (until explicit decision), platform impersonation, custom role designer (system roles first), Kafka/K8s/microservices.

## 15. First vertical slice (when coding starts)

1. Identity + tenant + membership + RBAC  
2. Branch + warehouse + POS terminal  
3. Product + default variant + barcode + category  
4. Opening balance or adjustment-in  
5. Open register → scan → draft sale → pay → confirm  
6. Stock down, payment recorded, journal posted, sale on report  

Purchasing receive is **slice 2**.
