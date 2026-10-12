# Ameen Retail — API Contract Design v1

The API is the boundary between clients and backend. It is **not** the database schema.

**Authoritative behavior:** `00-frozen-decisions.md` (sale confirm = complete, flat URLs, cookies vs Bearer, inventory keys, no credit tender, PO confirm).

When implementing, add **OpenAPI 3.x** (`openapi.yaml`) and contract-test against it.

---

## Principles

- Resource nouns + HTTP methods. Commands for ERP operations (`POST /sales/{id}/confirm`).
- No physical delete of financial transactions (`POST …/void`).
- Tenant isolation mandatory. `X-Tenant-Id` is a hint; membership must match.
- Client does not send `tenant_id` or authoritative totals.
- Money as decimal **strings** + currency.
- Timestamps ISO 8601 UTC (`Z`). Business day = tenant timezone.
- URL versioning `/api/v1` only. No `/api/latest`.
- Production base: `https://api.ameenretail.com/api/v1`  
  Dev: `http://localhost:8000/api/v1`

## Methods

GET retrieve · POST create or command · PATCH partial update · DELETE only safely deletable masters (else deactivate).

## Headers

- `Authorization` — session cookie for web (see security). Bearer optional later for mobile.
- `X-Tenant-Id`
- `X-Request-Id` (echo; generate if missing)
- `Idempotency-Key` on payments, confirm, refunds, receive, transfers
- `If-Match` for optimistic concurrency on editable masters → 409

## Envelope

Success single: `{ "success": true, "data": {}, "meta": {} }`  
Collection: `meta.pagination` `{ page, page_size, total, total_pages }`  
Error: `{ "success": false, "data": null, "meta": {}, "errors": [{ "code", "message", "field" }] }`

Prefer always JSON (no 204 if envelope is required).

## Pagination / filter / sort / search

`page` default 1, `page_size` default 25, **max 100**.  
Filters: status, category_id, brand_id, supplier_id, customer_id, branch_id, date_from, date_to.  
`sort=name` / `sort=-created_at` (whitelist).  
`search=` server-defined fields only.

## HTTP status

200/201/202 · 400 invalid · 401 auth · 403 permission · **404** missing or cross-tenant IDOR · 409 conflict · 422 validation · 429 rate limit · 500/503.

## Error codes

AUTH_REQUIRED, AUTH_INVALID_TOKEN, AUTH_TOKEN_EXPIRED  
PERMISSION_DENIED, TENANT_ACCESS_DENIED  
VALIDATION_ERROR, INVALID_FIELD, INVALID_FORMAT, INVALID_VALUE  
RESOURCE_NOT_FOUND, RESOURCE_ALREADY_EXISTS, RESOURCE_CONFLICT  
INSUFFICIENT_STOCK, INVALID_STATUS_TRANSITION, SALE_ALREADY_COMPLETED, SALE_ALREADY_VOIDED, PAYMENT_EXCEEDS_BALANCE, PRODUCT_SKU_EXISTS, REGISTER_NOT_OPEN, ACCOUNTING_ENTRY_UNBALANCED  
INTERNAL_ERROR, SERVICE_UNAVAILABLE  

Do not leak required permission names to ordinary clients.

---

## Endpoints (Retail MVP)

### Auth

- `POST /auth/login` `{ email, password }` — web sets HttpOnly session cookie; do not instruct clients to store tokens in localStorage
- `POST /auth/refresh` if token transport used
- `POST /auth/logout` — revoke server session
- `GET /auth/me` — user, memberships, current tenant, roles, permissions

### Tenant / branches / users / roles

- `GET|PATCH /tenant`
- `GET|POST /branches` · `GET|PATCH /branches/{id}`
- `GET|POST /users` · `GET|PATCH /users/{id}` · `POST /users/{id}/activate|deactivate`
- Invite payload: name/email/role — employee sets password
- `GET /roles` · `GET /permissions` · `GET|POST /users/{id}/roles`  
  Role assign cannot set OWNER except via ownership-transfer command

### Catalog

- `POST /products` — facade: product + default variant + barcode  
  Fields: name, sku, barcode, category_id, unit_id, cost_price, selling_price, **tax_rate_id** (not raw percent)
- `GET /products` · `GET /products/{id}` · `PATCH /products/{id}`
- `POST /products/{id}/activate` · `POST /products/{id}/deactivate`
- `GET /products/lookup?barcode=` — POS fast path
- `GET|POST /categories` · `GET|PATCH /categories/{id}` · DELETE only if unused else 409
- `GET|POST /units` · `PATCH /units/{id}`
- Prices under products or `/price-lists` as implemented; server remains authoritative

### Inventory

- `GET /inventory/products/{product_id}?branch_id=` — on_hand, reserved, available (resolve default warehouse/variant)
- `GET /inventory/movements` filters: product, branch, dates
- `POST /inventory/adjustments` `{ branch_id, reason, items[], notes }`
- Transfers: `POST /inventory/transfers` · `POST /inventory/transfers/{id}/complete`
- Counts when built: create/enter/approve commands

### Customers / suppliers

Standard list/create/get/patch. Phone not unique identity.

### Sales

- `POST /sales` → **DRAFT** `{ branch_id, customer_id?, items[{ product_id, quantity, unit_price? }], discount? }`  
  Response totals **calculated by server**
- `POST /sales/{id}/payments` `{ payment_method, amount }` on **draft**; Idempotency-Key
- `POST /sales/{id}/confirm` — CompleteSale atomic; status **completed**
- `POST /sales/{id}/void` `{ reason }`
- `POST /sales/{id}/return` `{ items[{ sale_item_id, quantity }], reason }`  
  qty ≤ eligible
- `GET /sales` · `GET /sales/{id}`

**Do not** `DELETE /sales/{id}`.

### POS

- `POST /pos/sessions` open `{ terminal_id, opening_cash }`
- `POST /pos/sessions/{id}/close` `{ actual_cash }`
- Cash in/out endpoints on session with reason

### Purchasing (P1)

- `POST /purchase-orders` · `PATCH` while draft
- `POST /purchase-orders/{id}/approve` → CONFIRMED
- `POST /purchase-orders/{id}/receive` — partial OK; creates movements
- `POST /purchase-orders/{id}/cancel` — not from RECEIVED
- Receipts/returns as dedicated resources if needed
- Supplier payments against **payable/receipt**, not an unspecified invoice table

### Expenses

`GET|POST /expenses` · get/patch · `POST /expenses/{id}/approve` — no destroy of posted expense

### Accounting (read)

`GET /accounting/accounts` · `journal-entries` · `general-ledger` · `trial-balance`  
**No** client `POST /journal-entries` for sales.

### Reports / dashboard / audit

- `GET /reports/sales` · `sales-summary` · `inventory` · `profit-loss` · AR/AP only if those features exist
- `GET /dashboard` aggregated read model (one request)
- `GET /audit-logs` · `GET /audit-logs/{id}`

---

## State machines (API)

**Sale:** DRAFT → COMPLETED; DRAFT → CANCELLED; COMPLETED → VOIDED; returns are linked documents (PARTIAL/FULL refunded). Invalid: VOIDED → CONFIRMED.

**PO:** DRAFT → CONFIRMED → PARTIALLY_RECEIVED → RECEIVED; cancel draft/confirmed only.

## Financial rules

No float money. No client-controlled totals. Server recalculates. Confirm locks inventory rows.

## Confirm sale pipeline

Auth → tenant → `pos.create_sale` or `sales.create` → load DRAFT → totals → lock stock → deduct → payments already recorded / remaining cash → journals → mark COMPLETED → audit → commit.

## Permissions (endpoint mapping)

| Endpoint | Permission |
|---|---|
| GET /products | products.view |
| POST /products | products.create |
| PATCH /products | products.update |
| POST …/deactivate | products.archive |
| POST /sales | sales.create |
| POST /sales/{id}/confirm (POS) | pos.create_sale |
| POST /sales/{id}/confirm (back-office) | sales.create |
| POST /sales/{id}/void | sales.void |
| POST /sales/{id}/return | sales_returns.create (refund: sales_returns.refund) |
| POST /inventory/adjustments | inventory.adjust |
| POST /pos/sessions | pos.open_register |
| POST /pos/sessions/{id}/close | pos.close_register |

Branch-restricted users must not see other branches’ sales even if they pass `branch_id` in the query.

## Security requirements

TLS, auth, tenant isolation, authz, validation, rate limits (login stricter), request size limits, secure headers, audit, hashed passwords, token/session expiry. Never expose password_hash, stack traces, SQL, secrets.

CORS allowlist. Rate limit classes: auth vs general vs sensitive.

## Compatibility

v1 additive only (optional fields, new endpoints). Breaking → `/api/v2`.

## Out of API v1

Travel, field service, professional services, HR, payroll, university, hospital, construction, manufacturing.

## Implementation order

AUTH → TENANT → USERS/RBAC → BRANCHES → CATALOG → INVENTORY → SALES/POS/PAYMENTS → PURCHASING → ACCOUNTING → REPORTS.

## Tests per endpoint

Unauthenticated 401 · unauthorized 403 · wrong tenant 404/403 · validation 422 · duplicate SKU conflict · confirm stock race · idempotent confirm/payment · schema match OpenAPI · decimal strings.

## Layering

HTTP → router → view → request DTO → **use case** → domain + module contracts → transaction → response DTO. Not API → database.
