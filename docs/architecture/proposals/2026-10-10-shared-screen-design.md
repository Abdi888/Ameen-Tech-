# Ameen Retail — Shared screen design package (revised)

**Date:** 2026-10-10  
**Revision:** Design direction accepted in principle. Architecture text is **not** this file.  
**Status:** **Not approved for implementation.** Documents **00–08 were not edited.** No frontend, backend, migrations, or UI.

**Normative amendment:** [`2026-10-10-amendment-proposal-r2.md`](./2026-10-10-amendment-proposal-r2.md). Section 2 below is the earlier contract draft. Approve r2 section by section, not §2 of this file, and not `2026-10-10-revised-amendment-set.md`.

| Decision | Status in r2 |
|---|---|
| SD-10 | Conditional. Schema and provisioning are r2 §3. |
| SD-19 | Proposed. POS API contract is r2 §4. Cashier does not gain `sales.create`. |
| SD-17 | Design approved. List uses `pos.view_sessions`. Close uses `pos.close_register`. GET contract is r2 §5. |
| SD-02 | Conditional. Restore stays unwired until r2 §6. Activate and restore are not the same for `DRAFT → ACTIVE`. |
| SD-01 | Proposed, not seeded. `roles.view` for Owner and Administrator only. `permissions.view` is out. |

**Authorities, in order:** `00-frozen-decisions.md`, then `07-permission-matrix-and-screens.md` for keys and screen entry, then `08-ui-design-tokens.md` for color, Inter, and 12px radius, then `05` and `06` for HTTP and sessions, then `01`–`04` for purpose. Where `01` names extra nav or roles, **07 wins**.

**One application.** Same routes and components for every role. Visibility and actions use the permission set from `GET /auth/me`. No `if role == "…"` in UI or API authorization. Business Owner still cannot be assigned or removed through `users.assign_roles` (Document 07). That is a protected-role rule, not a general role-name shortcut.

---

## 0. How to read status labels

| Label | Meaning |
|---|---|
| **Direction accepted** | You accepted this design choice. It is not a license to edit 00–08 or to write code. |
| **Frozen** | Already stated in 00, 05, or 07. Safe to treat as the contract. |
| **Contract gap** | The direction needs a document change before it can be implemented. The amendment text to approve is r2, not §2 of this file. |
| **Unresolved** | Still waiting on you. Not inferred. |

---

## 1. Accepted direction

### SD-10 — One default warehouse and one default terminal per branch

**Direction accepted.** MVP has no warehouse screen, no terminal screen, and no new permission keys. Users do not configure these rows.

**Not final.** Documents 01–05 do not yet describe this provisioning. See §2.1 and §11. Implementation waits on an approved amendment.

**Design consequence now:**

- Branch create is the only setup workflow that may provision the two defaults, and only after the §2.1 text is approved.
- Inventory screens send `branch_id`. The server resolves that branch’s default warehouse (Document 00 §3 already requires this resolution).
- POS open-register uses that branch’s default terminal. The user does not pick a warehouse or a terminal from a catalog.
- Transfers, which need two warehouses, stay **unspecified for MVP** until more than one warehouse exists. With one warehouse per branch, a transfer is branch-to-branch only, and Document 05’s transfer API has no list of warehouses. Do not add a warehouse picker.

### SD-19 — POS sale creation stays on `pos.create_sale`

**Direction accepted.** `sales.create` and `pos.create_sale` stay distinct. Cashier is **not** granted `sales.create`. Back-office `/app/sales/new` still requires `sales.create`. POS confirm, already in Document 05 and Document 07, stays `pos.create_sale` on `POST /sales/{id}/confirm`.

**Contract gap.** Document 05 has **no** POS operation for creating the draft, adding cart lines, or attaching a POS tender under `pos.create_sale`. See §2.2. POS Pay and the draft call are specified in the layout and **must not be implemented** until that amendment is approved.

### SD-17 — Close Register on the sessions list

**Direction accepted.** `/app/pos/sessions` opens with `pos.view_sessions`. The Close control on that list renders only with `pos.close_register`. The API stays `POST /pos/sessions/{id}/close` → `pos.close_register` (Document 05 and Document 07 §8). Cash movements stay on `/app/pos/sessions/:id`, entered only with `pos.cash_in` or `pos.cash_out`.

**No grant change.** The explicit cashier list in Document 07 §7 already includes both `pos.view_sessions` and `pos.close_register`. Owner, Administrator, and Sales Manager are “POS Full”, which includes both keys. No intended role is stuck with close and without the list. A grant of `pos.close_register` without `pos.view_sessions` would hide the list and still allow the API; that is independent gating, not a matrix bug, and this package does not add a grant to “fix” it.

**Contract gap (narrow):** Document 05 defines open and close and does **not** define `GET /pos/sessions`. The list screen cannot be implemented until §2.3 is approved.

### SD-02 — Restore, using `products.restore`

**Direction accepted.** The product control is labeled **Restore** and requires `products.restore`. There is no Activate button.

**Mismatch, unresolved as a binding map:** Document 05 defines `POST /products/{id}/activate` and does not name `products.restore`. Document 07 defines `products.restore` and does not name that URL. Document 00 names deactivate only. See §2.4. Do not call the activate URL until you approve a mapping.

### SD-01 — `roles.view` for the assignment dropdown

**Direction accepted as a proposal.** The users screen may load roles only with `roles.view`. There is still **no** tenant Roles screen. `users.view` does not imply `roles.view`. `users.assign_roles` does not imply `roles.view`.

**Not active.** The key is not in Document 07. Exact insert and the separate grant list are in §2.5. Do not seed the key and do not change live role assignments until you approve that amendment.

`GET /permissions` and `permissions.view` are **out of SD-01**. They stay unresolved.

---

## 2. Proposed document amendments (not applied)

Nothing in this section is authorized. Each block is the smallest text that would make the accepted direction implementable. Approving this design file does **not** approve these edits.

### 2.1 SD-10 — provisioning (Documents 02 and 05)

**What the frozen pack actually says**

| Document | Text | Fit |
|---|---|---|
| 00 §3 | Tenant ≠ Branch ≠ Warehouse ≠ POS terminal. Stock API may take `product_id` + `branch_id` and must resolve the **branch default warehouse**. | The idea of a default warehouse is frozen. How it is created is not. |
| 01 §8 | A store may have POS terminals (plural). Location types STORE and WAREHOUSE. | Plural terminals are allowed by the domain wording. 00 already replaced location types with `branches` + `warehouses`. |
| 02 | `warehouses`: `id, tenant_id, branch_id, name, code, is_active`. No default flag. No one-per-branch unique. `pos_terminals`: `id, tenant_id, branch_id, name, code, status, is_active`. Same gap. | Schema **cannot** identify “the” default if two rows exist. |
| 03 | Branches module owns the store/warehouse relationship. | No use case for provisioning. |
| 04 | No branch-create side effect. | — |
| 05 | `POST /branches` has no child resources. `POST /pos/sessions` **requires** `terminal_id`. No terminal list or create URL. | Client cannot discover a terminal without a new read or a server-side resolution. |

**Proposed 02 insert** (under `warehouses` and `pos_terminals`):

```
is_default BOOLEAN NOT NULL
Exactly one row with is_default = true per (tenant_id, branch_id)
  among active warehouses, and the same rule for active pos_terminals.
MVP setup creates that one default row. No tenant UI creates a second.
```

**Proposed 05 insert** (branches and POS):

```
POST /branches  (permission branches.create)
  In the same transaction, insert one default warehouse and one default
  POS terminal for the new branch (is_default = true).
  Response includes default_warehouse_id and default_terminal_id.
  No other MVP endpoint creates warehouses or terminals.
  If either insert fails, the branch insert rolls back.

POST /pos/sessions
  Body may send terminal_id. The server accepts it only when that terminal
  is the branch default, is active, and is in the caller's branch scope.
  Otherwise 404 (cross-branch) or 409 (not the default).
  Opening still requires pos.open_register.

Inventory GET /inventory/products/{product_id}?branch_id=
  Resolves the default warehouse. If the branch does not have exactly one
  active default, fail closed (409). Do not pick an arbitrary warehouse.
```

No new permission keys. No warehouse or terminal routes.

### 2.2 SD-19 — POS draft and POS tender (Document 05)

**Exact gap.** Document 05 today:

- `POST /sales` creates the DRAFT and the permission table maps it to **`sales.create`**.
- `POST /sales/{id}/confirm` from POS maps to **`pos.create_sale`**.
- `POST /sales/{id}/payments` is specified and is **absent** from the permission table.
- The cashier grant (Document 07 §7) has `pos.create_sale` and does **not** have `sales.create` or `payments.create`.
- `sales_orders` already has `terminal_id`, `session_id`, and `warehouse_id` (Document 02). The `POST /sales` body does not accept them.
- Document 04: POS owns the cart and calls `Sales.CompleteSale`. POS is not a second sales ledger.
- Document 05 has no `PATCH /sales/{id}` and no add-line command. Cart edits have no URL.

So a cashier can be authorized to **confirm** and cannot be authorized to **create** the draft without either a new POS operation or a grant of `sales.create`. This package does **not** grant `sales.create`.

**Proposed 05 insert:**

```
POST /pos/sales
  Permission: pos.create_sale. sales.create is neither required nor sufficient.
  Creates a DRAFT through the Sales use case (same sales_orders table).
  Body: { "terminal_id", "customer_id"?, "items": [{ "product_id", "quantity" }] }
  Server sets branch from the terminal, warehouse to that branch's default
  warehouse, and session to the open session for that terminal.
  Reject REGISTER_NOT_OPEN when no session is open.
  Do not accept unit_price or discount until those contracts are approved.
  Idempotency-Key required.

POST /pos/sales/{id}/lines
  Permission: pos.create_sale.
  Add, update, or remove DRAFT lines on a sale whose session is still open.
  sales.update is not required and does not authorize this URL.

POST /pos/sales/{id}/payments
  Permission: pos.create_sale.
  Body matches POST /sales/{id}/payments. Idempotency-Key required.
  payments.create is not required and does not authorize this URL.

POST /sales
  Unchanged. Permission sales.create. Back-office only.
  Must not set terminal_id or session_id.

POST /sales/{id}/payments
  Permission payments.create. Back-office drafts only.

POST /sales/{id}/confirm
  If the draft has session_id set, require pos.create_sale.
  If the draft has no session_id, require sales.create.
  Do not accept the other permission as a substitute.

GET /products/lookup?barcode=
  Allow when the caller has pos.view or products.view.
```

Cashier still does not receive `sales.create`, `sales.update`, or `payments.create`.

### 2.3 SD-17 — session list read (Document 05)

**Proposed 05 insert:**

```
GET /pos/sessions          → pos.view_sessions
GET /pos/sessions/{id}     → pos.view_sessions
POST /pos/sessions/{id}/close remains pos.close_register
```

Cash-in and cash-out URLs are still unnamed (unchanged gap, §10). Close does not move onto the cash-movement route.

### 2.4 SD-02 — restore versus activate (Documents 05 and 07)

**Mismatch**

| Source | Says |
|---|---|
| 07 | `products.archive`, `products.restore`. No URL. |
| 05 endpoints | `POST /products/{id}/activate` and `POST /products/{id}/deactivate`. |
| 05 permission table | deactivate → `products.archive`. **Activate has no row.** |
| 00 §4 | `POST /products/{id}/deactivate`. Lifecycle DRAFT → ACTIVE → INACTIVE. No restore verb. |

**Proposed mapping, not applied:**

```
POST /products/{id}/deactivate  → products.archive   (already in 05)
POST /products/{id}/activate    → products.restore
UI label: Restore. Do not add an Activate permission or an Activate button.
```

Until you approve that row, the Restore control is designed and **not wired**.

### 2.5 SD-01 — exact Document 07 change, and grants separately

**Proposed insert in Document 07 §4, after Users. Not applied.**

```
### Role catalog (read-only)

- roles.view — GET /roles. Returns the system role list so a user who can
  assign roles can populate the dropdown.
  Does not create, edit, or delete roles or permissions.
  Does not open a Roles screen.

users.view does not imply roles.view.
users.assign_roles does not imply roles.view.
There is still no tenant screen for Roles, Permissions, or role-permission mapping.
```

**Proposed insert in Document 07 §5 Users row:** “Dropdown data requires `roles.view`. If it is missing, show no role list (fail closed).”

**Proposed insert in Document 07 §8:** `GET /roles` → `roles.view`.

**Proposed grants (separate list). Not seeded until you approve this amendment.**

| Role | `roles.view` |
|---|---|
| Business Owner | Yes |
| Administrator | Yes |
| Accountant | No |
| Sales Manager | No |
| Inventory Manager | No |
| Cashier | No |
| Purchasing Officer | No |
| Viewer | No |

Owner and Administrator already have `users.assign_roles` in the frozen matrix. That existing key does **not** start authorizing `GET /roles` when this amendment is applied. Both keys are required for the dropdown. No other role gains either key from this proposal.

**Not in this proposal:** `permissions.view`, `GET /permissions`, any Roles route, any change to the cashier grant.

---

## 3. Screen inventory

Routes live under `/app` except login. `/platform/*` is out of scope (no Document 07 platform keys).

Direct URL without the entry permission → **403** `PERMISSION_DENIED`. Cross-tenant id → **404**. No session → **401**.

### 3.1 Entry frozen in Document 07 §5

| Screen | Route | Purpose | Entry | Contract |
|---|---|---|---|---|
| Login | `/login` | Email + password; HttpOnly session | Public | Frozen. 00 §10, 05 Auth |
| Dashboard | `/app/dashboard` | Read model. Widgets need a domain view too | `dashboard.view` | Frozen. `GET /dashboard` |
| Sales list | `/app/sales` | Draft and completed sales | `sales.view` | Frozen |
| Sale detail | `/app/sales/:id` | One sale | `sales.view` | Frozen |
| Create sale | `/app/sales/new` | Back-office draft | `sales.create` | Frozen entry. Not the POS path |
| Returns | `/app/sales/returns` | Return documents | `sales_returns.view` | Frozen entry. Refund URL unresolved (§10) |
| POS | `/app/pos` | Scan, cart, pay, confirm | `pos.view` | Screen frozen. Draft/pay URLs are §2.2 |
| Open register | Sheet on `/app/pos` | Open the default terminal | `pos.open_register` | Command frozen. Default terminal is §2.1 |
| Sessions | `/app/pos/sessions` | Session list and **Close** | `pos.view_sessions` | Entry frozen. List GET is §2.3 |
| Cash movements | `/app/pos/sessions/:id` | Cash in/out | `pos.cash_in` **or** `pos.cash_out` | Entry frozen. URLs unnamed (§10) |
| Customers | `/app/customers` | Customer master | `customers.view` | Frozen entry. URL wording in 05 is “standard” (§10) |
| Customer detail | `/app/customers/:id` | Profile. Transactions are a separate panel | `customers.view` | 07 §3 |
| Products | `/app/products` | Catalog | `products.view` | Frozen |
| Product detail | `/app/products/:id` | Variant, barcode, tax, status | `products.view` | Frozen. Restore wiring is §2.4 |
| Categories | `/app/products/categories` | Category tree | `product_categories.view` | Frozen. Delete vs archive **unresolved** (SD-03) |
| Inventory | `/app/inventory` | On-hand by branch | `inventory.view` | Frozen. Default warehouse is §2.1 |
| Movements | `/app/inventory/movements` | Immutable history | `inventory.view_movements` | Frozen |
| Adjustments | `/app/inventory/adjustments` | Reasoned quantity change | `inventory.view` **and** `inventory.adjust` | Frozen |
| Transfers | `/app/inventory/transfers` | Transfer documents | `inventory.view` **and** `inventory.transfer` | Entry frozen. Warehouse choice blocked by SD-10 MVP (one warehouse per branch, no picker) |
| Financial reports | `/app/reports/finance` | Finance read model | `reports.finance.view` | Route frozen. GET permission map is §10 SD-23 |
| Users | `/app/settings/users` | Invite and status | `users.view` | Frozen. Role dropdown waits on §2.5 |
| User detail | `/app/settings/users/:id` | One membership | `users.view` | 07 §3 |
| Tax | `/app/settings/tax` | Tax rates | `tax.view` | Frozen |
| Audit | `/app/audit` | Append-only audit | `audit.view` | Frozen. Export URL unnamed (§10) |

Product new (`/app/products/new`) is an action route gated by `products.create`, not a second entry permission.

There is no Roles, Permissions, warehouse, or terminal screen.

### 3.2 Permissions exist; Document 07 §5 does not name the path

Paths below are the naming proposal from the first draft. They are **not** the five accepted decisions. Treat the paths as proposed until you approve this inventory. Keys are already in Document 07.

| Screen | Proposed route | Entry |
|---|---|---|
| Brands | `/app/products/brands` | `brands.view` |
| Units | `/app/products/units` | `units.view` |
| Suppliers | `/app/purchasing/suppliers` | `suppliers.view` |
| Supplier detail | `/app/purchasing/suppliers/:id` | `suppliers.view` |
| Purchase orders | `/app/purchasing/orders` | `purchase_orders.view` |
| PO detail / new | `/app/purchasing/orders/:id`, `/new` | view / `purchase_orders.create` |
| Goods receipts | `/app/purchasing/receipts` | `goods_receipts.view` |
| Receipt detail | `/app/purchasing/receipts/:id` | `goods_receipts.view` |
| Purchase returns | `/app/purchasing/returns` | `purchase_returns.view` |
| Expenses | `/app/expenses`, `/app/expenses/:id` | `expenses.view` |
| Accounts | `/app/finance/accounts` | `finance_accounts.view` |
| Journals | `/app/finance/journals` | `finance_transactions.view` |
| Payments | `/app/finance/payments` | `payments.view` — **no GET in 05** (§10) |
| Receivables | `/app/finance/receivables` | `receivables.view` |
| Payables | `/app/finance/payables` | `payables.view` |
| Sales report | `/app/reports/sales` | `reports.sales.view` |
| Inventory report | `/app/reports/inventory` | `reports.inventory.view` |
| Purchasing report | `/app/reports/purchasing` | `reports.purchasing.view` |
| Customers report | `/app/reports/customers` | `reports.customers.view` |
| Expenses report | `/app/reports/expenses` | `reports.expenses.view` |
| Business | `/app/settings/business` | `settings.business.view` |
| Branches | `/app/settings/branches` | `branches.view` |
| Currency | `/app/settings/currency` | `currency.view` |
| Numbering | `/app/settings/numbering` | `numbering.view` |

### 3.3 Not screens

| Mention | Treatment |
|---|---|
| Roles admin | Forbidden (07 §3). Dropdown only, after §2.5 |
| Platform `/platform` | No keys. Unresolved SD-15 |
| Stock counts | `inventory.count` is not a live key. Unresolved SD-11 |
| Price lists, payment-method admin, expense-category master | No keys. Unresolved SD-12, SD-13, SD-14 |
| Warehouses, terminals | No screens (SD-10 direction) |
| Refunds as its own route | Action on returns (`sales_returns.refund`) and on POS (`pos.refund`) |
| Activate button | Not used (SD-02) |

---

## 4. Navigation

One left nav. A group shows when any child shows. Children use the entry rule in §3.

| Group | Item | Visible when |
|---|---|---|
| — | Dashboard | `dashboard.view` |
| POS | Register | `pos.view` |
| POS | Sessions | `pos.view_sessions` |
| Sales | Sales | `sales.view` |
| Sales | New sale | `sales.create` |
| Sales | Returns | `sales_returns.view` |
| Customers | Customers | `customers.view` |
| Products | Products | `products.view` |
| Products | Categories | `product_categories.view` |
| Products | Brands | `brands.view` |
| Products | Units | `units.view` |
| Inventory | Stock | `inventory.view` |
| Inventory | Movements | `inventory.view_movements` |
| Inventory | Adjustments | `inventory.view` **and** `inventory.adjust` |
| Inventory | Transfers | `inventory.view` **and** `inventory.transfer` |
| Purchasing | Suppliers | `suppliers.view` |
| Purchasing | Purchase orders | `purchase_orders.view` |
| Purchasing | Receipts | `goods_receipts.view` |
| Purchasing | Purchase returns | `purchase_returns.view` |
| Expenses | Expenses | `expenses.view` |
| Finance | Accounts | `finance_accounts.view` |
| Finance | Journals | `finance_transactions.view` |
| Finance | Payments | `payments.view` |
| Finance | Receivables | `receivables.view` |
| Finance | Payables | `payables.view` |
| Reports | Sales | `reports.sales.view` |
| Reports | Inventory | `reports.inventory.view` |
| Reports | Purchasing | `reports.purchasing.view` |
| Reports | Customers | `reports.customers.view` |
| Reports | Expenses | `reports.expenses.view` |
| Reports | Finance | `reports.finance.view` |
| Settings | Business | `settings.business.view` |
| Settings | Branches | `branches.view` |
| Settings | Tax | `tax.view` |
| Settings | Currency | `currency.view` |
| Settings | Numbering | `numbering.view` |
| Settings | Users | `users.view` |
| — | Audit | `audit.view` |

**Absent from nav:** Roles, Permissions, Stock counts, Price lists, Payment methods, Warehouses, Terminals, Platform.

**Shell, not nav:** tenant switcher only when `GET /auth/me` returns more than one active membership. Branch filter only when the user has more than one branch in scope. Logout calls `POST /auth/logout`.

**Default cashier** (07 §7 grant list only): Dashboard, POS Register, POS Sessions. Customers. Products. They do **not** see New sale, Sales, Returns, Categories, Inventory, Purchasing, Expenses, Finance, Reports, Settings, or Audit. Close appears on Sessions because that grant includes `pos.view_sessions` and `pos.close_register`. Refund stays hidden (`pos.refund` is not in the grant).

---

## 5. Layouts

Document 08 applies to every screen: light first, Inter, seed through `tokens.css`, radius 12px, semantic tokens only.

| Pattern | Regions | Screens |
|---|---|---|
| A List | Title, filters, table, empty state | Most indexes, including sessions |
| B Document | Status, action bar, lines, server totals | Sale, return, PO, receipt, expense, adjustment, transfer, session cash |
| C Form | Fields, server errors | Create/edit masters and drafts |
| D POS | Scan, results, cart, totals, Pay | `/app/pos` |
| E Report | Filters, figures, table, export | `/app/reports/*` |
| F Dashboard | Widget grid | Dashboard |
| G Settings | Read-only values; edit only with update | Business, currency, numbering |

**Sessions list (SD-17).** Columns: terminal (display name of the default terminal), opened at, status, expected, actual, variance. **Close** sits on the open row and renders only with `pos.close_register`. Close asks for actual cash. Variance is stored. Sales totals are not rewritten (00 §6).

**POS (SD-19).** Scan uses lookup. Cart has no unit-price box and no discount box (SD-04 and SD-05 unresolved). Pay and confirm render only with `pos.create_sale`. Open-register sheet renders with `pos.open_register` when no session is open; it does not ask the user to choose a terminal. Reprint renders with `pos.reprint`. Refund renders with `pos.refund` (hidden for the default cashier).

**Product detail (SD-02).** Deactivate when status is active and `products.archive`. **Restore** when status is inactive and `products.restore`. No Activate label. No Delete when the product has history (00 §4).

**Users.** Invite (`users.create`): name and email, no password. Assign-roles block renders only when **both** `users.assign_roles` and `roles.view` are held. Business Owner is not an option. Until §2.5 is approved, the block is specified and not implementable. No Roles page.

**Journals.** Read-only list. No New and no Post (SD-06 unresolved; 00 forbids client `POST /journal-entries` for a sale).

**Receivables.** View and export only. No record-payment (SD-07 unresolved; 00 withholds AR).

**Branches.** Name, code, address. No warehouse or terminal fields on the form (SD-10). Provisioning is a server side effect of create, after §2.1, not a set of extra inputs.

**Dashboard widgets**

| Widget | Extra permission |
|---|---|
| Today’s sales (tenant-local day) | `sales.view` |
| Stock | `inventory.view` |
| Finance snapshot | `reports.finance.view` |

A cashier with `dashboard.view` and without those keys sees no finance or stock figures (07 §4).

Money and quantities are API decimal strings, tabular numerals (00 §8).

---

## 6. User flows

### 6.1 Sign in

`/login` → `POST /auth/login` → cookie → `GET /auth/me` → first visible nav item, or an empty shell if the user has no screen permission. Failure copy is only “Invalid email or password.” (Document 06). Deep link without a session → 401 → login → original path if entry allows, otherwise the 403 page.

### 6.2 Missing permission

Example: cashier opens `/app/sales/new`. Guard requires `sales.create`, which the cashier grant does not include → 403 page, no `POST /sales`. A hand-built `POST /sales` returns 403 `PERMISSION_DENIED` without the permission name in the body (Document 05).

### 6.3 POS sale

**Designed flow, blocked on §2.2 for the draft and the tender:** open register (`pos.open_register`, default terminal) → scan → `POST /pos/sales` (`pos.create_sale`) → tenders `POST /pos/sales/{id}/payments` (`pos.create_sale`) → `POST /sales/{id}/confirm` (`pos.create_sale`, Idempotency-Key) → COMPLETED, stock down, journal posted. Customer may be null. Change is not revenue.

**Validation:** unknown barcode, quantity, sum of tenders below amount due, `REGISTER_NOT_OPEN`.  
**Conflict:** `INSUFFICIENT_STOCK`, full rollback (00 §6).  
**Unauthorized:** no `pos.create_sale` → Pay hidden; confirm returns 403. `sales.create` does not enable Pay.  
**Empty:** no open session → open-register sheet, cart disabled.  
**Retry:** same Idempotency-Key does not double-charge or double-issue.

### 6.4 Back-office sale

`/app/sales/new` requires `sales.create` → `POST /sales` → DRAFT with no `session_id`. Payments on that draft require `payments.create` (proposed binding in §2.2; the URL exists, the permission row does not). Confirm requires `sales.create`. Cancel (`sales.cancel`) from DRAFT. Void (`sales.void`) from COMPLETED, with reason. Completed lines stay immutable.

### 6.5 Close register

Sessions list (`pos.view_sessions`) → Close (`pos.close_register`) → `POST /pos/sessions/{id}/close`. User with only `pos.view_sessions` sees the row and no Close button; the close URL returns 403. User with only `pos.close_register` does not see the list. Cashier has both, so both the list and the button appear.

### 6.6 Restore product

Inactive product, `products.restore` → Restore. The HTTP call is **not chosen** until §2.4 is approved. User without `products.restore` does not see Restore; any activate or restore URL returns 403.

### 6.7 Assign a role

Users detail, both `users.assign_roles` and `roles.view` → dropdown from `GET /roles` → `POST /users/{id}/roles`. Missing `roles.view` → no options, even if assign is held. Business Owner id is rejected by the API. This flow waits on §2.5.

### 6.8 Shared list states

| State | Screen |
|---|---|
| Empty | Filters remain. “No records”. Create only with the create permission |
| 422 | Form stays; `errors[].field` |
| 403 | Control already hidden, or a 403 page when entry failed |
| 404 | “Not found” for missing and cross-tenant ids |
| 409 | Status or stock conflict; document unchanged |

---

## 7. Permission-to-action mapping

Keys are Document 07 §4 only, plus `roles.view` marked **proposed**. “Wire” says whether an approved endpoint already enforces the key.

| Surface | Action | Permission | Wire |
|---|---|---|---|
| Dashboard | Open | `dashboard.view` | `GET /dashboard`. Widget slices still need domain view |
| Sales list/detail | Open | `sales.view` | `GET /sales`, `GET /sales/{id}` |
| Sales | Export / print | `sales.export` / `sales.print` | **No export/print URL in 05** |
| Create sale | Open and back-office confirm | `sales.create` | `POST /sales`; confirm when draft has no session |
| Sale draft | Edit | `sales.update` | **No back-office line URL in 05** |
| Sale draft | Cancel | `sales.cancel` | **No cancel URL in 05** |
| Completed sale | Void | `sales.void` | `POST /sales/{id}/void` |
| Returns | Open | `sales_returns.view` | **No list URL in 05** |
| Returns | Create | `sales_returns.create` | `POST /sales/{id}/return` |
| Returns | Approve / cancel | `sales_returns.approve` / `cancel` | **No URLs in 05** |
| Returns | Refund | `sales_returns.refund` | 05 names the key and no URL (SD-21) |
| POS | Open | `pos.view` | Screen. Lookup binding is §2.2 |
| POS | Create draft, edit cart, take tender, confirm | `pos.create_sale` | Confirm frozen. Draft, lines, and POS payments are **§2.2, not in 05** |
| POS | Reprint / refund | `pos.reprint` / `pos.refund` | **No URLs in 05** |
| Register | Open | `pos.open_register` | `POST /pos/sessions` |
| Sessions | Open list | `pos.view_sessions` | **GET proposed in §2.3** |
| Sessions | Close | `pos.close_register` | `POST /pos/sessions/{id}/close` |
| Session | Cash in / out | `pos.cash_in` / `pos.cash_out` | 05 says “endpoints” and does not name them |
| Customers | Open and mutations | `customers.view/create/update/archive/restore/export` | 05 “standard” paths, not written out |
| Customers | Transactions | `customers.view_transactions` | Not implied by view. No URL |
| Products | Open | `products.view` | `GET /products`, `GET /products/{id}` |
| Products | Create / update | `products.create` / `update` | `POST /products`, `PATCH /products/{id}` |
| Products | Deactivate | `products.archive` | `POST /products/{id}/deactivate` |
| Products | Restore | `products.restore` | **URL unbound** until §2.4 |
| Products | Export / print | `products.export` / `print` | **No URLs** |
| Categories | Open and mutations | `product_categories.view/create/update/archive` | GET/POST/PATCH in 05. DELETE vs archive is **SD-03** |
| Brands | Open and mutations | `brands.*` | **No brand URLs in 05** |
| Units | Open and mutations | `units.view/create/update/archive` | GET/POST/PATCH. No archive URL |
| Stock | Open | `inventory.view` | `GET /inventory/products/{product_id}?branch_id=` |
| Movements | Open | `inventory.view_movements` | `GET /inventory/movements` |
| Adjustments | Open and post | `inventory.view` **and** `inventory.adjust` | `POST /inventory/adjustments` |
| Transfers | Open and complete | `inventory.view` **and** `inventory.transfer` | `POST /inventory/transfers`, `…/complete`. Picker blocked (§1 SD-10) |
| Inventory | Export | `inventory.export` | **No URL** |
| Suppliers | Open and mutations | `suppliers.view/create/update/archive` | 05 “standard” paths |
| PO | Open and mutations | `purchase_orders.view/create/update/approve/cancel/export` | POST, PATCH, `…/approve`, `…/cancel`. Export URL missing |
| Receipts | Open | `goods_receipts.view` | **No receipt resource URL.** 05 receive is `POST /purchase-orders/{id}/receive` (SD-22) |
| Receipts | Post | `goods_receipts.post` | Same URL, **permission not in the 05 table** (SD-22) |
| Receipts | Create / cancel | `goods_receipts.create` / `cancel` | **No URLs** |
| Purchase returns | Open and mutations | `purchase_returns.view/create/approve/cancel` | **No URLs** |
| Expenses | Open and mutations | `expenses.view/create/update/approve/cancel/export` | GET/POST, get/patch, `…/approve`. Cancel and export URLs missing |
| Accounts | Open and mutations | `finance_accounts.view/create/update/archive` | `GET /accounting/accounts` only. Writes unnamed |
| Journals | Open | `finance_transactions.view` | `GET /accounting/journal-entries` proposed in SD-23, not in the 05 table |
| Journals | Void | `finance_transactions.void` | **No URL** |
| Journals | Create / post | `finance_transactions.create` / `post` | **Controls omitted.** 00 forbids sale posting via client journal create. HTTP exposure unresolved (SD-06) |
| Back-office tender | Record on a draft | `payments.create` | `POST /sales/{id}/payments`. Permission row **proposed in §2.2** |
| Payments list | Open | `payments.view` | **No GET /payments** (SD-08) |
| Payments | Void / refund | `payments.void` / `payments.refund` | **No URLs.** Distinct from `sales_returns.refund` and `pos.refund` |
| Receivables | Open / export | `receivables.view` / `export` | **No GET** |
| Receivables | Record payment | `receivables.create_payment` | **Control omitted** (SD-07) |
| Payables | Open / export | `payables.view` / `export` | **No GET** |
| Payables | Record payment | `payables.create_payment` | **No frozen URL** (SD-09) |
| Each report | Open | `reports.<domain>.view` | 05 lists some GETs. Per-report key is SD-23 |
| Reports | Export | `reports.export` | **No URL.** Not `reports.sales.export` |
| Users | Open | `users.view` | `GET /users`, `GET /users/{id}` |
| Users | Invite | `users.create` | `POST /users`. No `users.invite` |
| Users | Update / activate / deactivate | `users.update` / `activate` / `deactivate` | PATCH, `POST /users/{id}/activate`, `…/deactivate` |
| Users | Assign roles | `users.assign_roles` | `POST /users/{id}/roles`. Cannot assign Owner |
| Users | Load role dropdown | `roles.view` **proposed** | `GET /roles` exists in 05 with **no frozen permission**. §2.5 |
| Business | View / update | `settings.business.view` / `update` | `GET /tenant`, `PATCH /tenant` |
| Branches | Open / create / update | `branches.view` / `create` / `update` | `GET|POST /branches`, `GET|PATCH /branches/{id}` |
| Branches | Archive | `branches.archive` | **No URL** |
| Branch create side effect | Provision default warehouse and terminal | `branches.create` only, **after §2.1** | Not in 05 today |
| Tax | Open and mutations | `tax.view/create/update/archive` | **No tax URLs in 05** |
| Currency | View / update | `currency.view` / `update` | **No URLs** |
| Numbering | View / update | `numbering.view` / `update` | **No URLs** |
| Audit | Open / export | `audit.view` / `export` | `GET /audit-logs`, `GET /audit-logs/{id}`. Export URL missing |

**Not mapped, because no frozen key exists:** price override, discount, stock count, warehouse CRUD, terminal CRUD, price-list CRUD, payment-method CRUD, expense-category CRUD, ownership transfer, permission catalog, platform admin.

---

## 8. Backend enforcement and denied-request tests

Status codes (00 §9, 05): 401 unauthenticated, 403 missing permission, 404 cross-tenant or out-of-branch id, 409 conflict, 422 validation. Error body uses `PERMISSION_DENIED` and does not include the permission name. Idempotency-Key on confirm, payment, receive, return/refund, and transfer complete.

Tests arrange users by assigning a Document 07 role, then assert **HTTP and permission results**. Production code does not branch on role name.

### 8.1 Frozen endpoints (implement tests only after the slice is approved)

| Operation | Allowed permission | Deny |
|---|---|---|
| `POST /auth/login` bad password | — | Generic error, no user enumeration |
| `GET /auth/me` | Session | 401 without session |
| `GET /products` | `products.view` | 401 no session; 403 without key; 404 other tenant |
| `POST /products` | `products.create` | 403 for cashier (grant has view only) |
| `PATCH /products/{id}` | `products.update` | 403 without key |
| `POST /products/{id}/deactivate` | `products.archive` | 403 without key |
| `POST /sales` | `sales.create` | **403 for cashier.** `pos.create_sale` must not allow this URL |
| `POST /sales/{id}/confirm` back-office draft | `sales.create` | 403 when the caller has only `pos.create_sale` |
| `POST /sales/{id}/confirm` POS draft | `pos.create_sale` | 403 when the caller has only `sales.create`. Origin rule waits on §2.2 |
| `POST /sales/{id}/void` | `sales.void` | 403 for cashier |
| `POST /sales/{id}/return` | `sales_returns.create` | 403 without key; qty above eligible → 422 or 409 |
| `POST /inventory/adjustments` | `inventory.adjust` | 403 without key; also hide the screen without `inventory.view` |
| `POST /inventory/transfers/{id}/complete` | `inventory.transfer` | 403 without key |
| `POST /pos/sessions` | `pos.open_register` | 403 without key |
| `POST /pos/sessions/{id}/close` | `pos.close_register` | 403 without key, including a user who has `pos.view_sessions` only |
| `POST /users` | `users.create` | 403 for cashier |
| `POST /users/{id}/roles` with Owner role id | `users.assign_roles` | Rejected for Administrator |
| `GET /sales?branch_id=` outside scope | `sales.view` | No foreign rows (05) |

Also required when those commands exist (00 §13): one idempotency replay does not double stock or payment; two cashiers and quantity 1 → one success and one `INSUFFICIENT_STOCK`; journal debits equal credits; money fields are decimal strings.

### 8.2 Denied cases that wait on §2 (do not write the tests as if the URLs existed)

| Future operation | Allow | Deny |
|---|---|---|
| `POST /pos/sales` | `pos.create_sale` | 403 for `sales.create` alone; 403 for cashier if someone maps this to `sales.create` |
| `POST /pos/sales/{id}/payments` | `pos.create_sale` | 403 for `payments.create` alone; cashier must succeed **without** `payments.create` |
| `GET /pos/sessions` | `pos.view_sessions` | 403 for `pos.close_register` alone |
| `GET /roles` | `roles.view` after §2.5 | 403 for `users.view` alone and for `users.assign_roles` alone |
| `POST /products/{id}/activate` | `products.restore` after §2.4 | 403 without `products.restore`. Do not accept `products.archive` |

### 8.3 Frontend visibility (after UI is approved)

| Permission set | Expect |
|---|---|
| Cashier grant | Nav: Dashboard, POS, Sessions, Customers, Products. No New sale, no Refund, no Users |
| Cashier on Sessions | Close visible |
| `pos.view_sessions` without `pos.close_register` | List visible, Close absent |
| `pos.close_register` without `pos.view_sessions` | Sessions route is the 403 page |
| `products.view` without `products.create` | No Create |
| `products.restore` absent | No Restore |
| `sales.view` without `sales.void` | No Void |
| `inventory.view` without `inventory.adjust` | Adjustments absent; direct route 403 |
| `users.assign_roles` without `roles.view` | No role options |
| `dashboard.view` without `reports.finance.view` | No finance widget |

---

## 9. Reusable components

Feature folders follow Document 00 §12 (`features/pos`, `features/sales`, …). Components take permissions, never a role name.

| Component | Rule |
|---|---|
| `AppShell` | Renders a nav row only when its entry rule passes |
| `RequirePermission` | Missing entry → 403 page. Adjustments and transfers use AND |
| `Can` | Children render only when every listed permission is held |
| `PermissionButton` | Hidden when unauthorized, not disabled |
| `DocumentActions` | Status and permission. Close on the session row: `pos.close_register`. Restore: `products.restore` |
| `RoleSelect` | Mounts only with `users.assign_roles` **and** `roles.view`. Empty and no request if `roles.view` is missing |
| `PosWorkspace` | Pay slot requires `pos.create_sale`. No terminal picker |
| `Money` | Decimal strings |
| `Forbidden` / `NotFound` | 403 copy vs 404 copy. 404 does not say “wrong tenant” |

Hiding is UX. The matching use case still checks the same code (07 §1, 06 Frontend).

---

## 10. Unresolved (not inferred)

| ID | Issue | Why it is still open |
|---|---|---|
| SD-03 | `DELETE /categories/{id}` (05) vs `product_categories.archive` (07) | You did not decide. UI shows Archive only as a **proposal**, not a binding map. No Delete button is designed in. |
| SD-04 | Discounts | 01 says permission-controlled. 07 has no key. 06’s “manager ≤ 20%” is not a 07 role. Inputs omitted. |
| SD-05 | Price override | 00 mentions a permission. 07 has no key. 09 Appendix A says re-price and do not invent a key. Inputs omitted. D4 in the foundation file is not applied. |
| SD-06 | `finance_transactions.create` / `post` | Keys exist. Client journal POST for a sale is forbidden. “If ever exposed” is not a contract. Buttons omitted. |
| SD-07 | `receivables.create_payment` | Key exists. 07 says unused until Starter AR. Compact matrix “Finance Full” would include it. Control omitted. Grant not decided here. |
| SD-08 | `GET /payments` | `payments.view` has no list URL. |
| SD-09 | AP payment URL | `payables.create_payment` has no frozen path. The path in the 10 October amendment set is **not** approved. |
| SD-11 | Stock counts | Domain requires them. `inventory.count` is not live. No screen. |
| SD-12 | Price lists | 00 model, no permission. |
| SD-13 | Payment-method admin | 01 nav, no 07 key. Tenders stay the fixed 00 list. |
| SD-14 | Expense categories | `category_id` in 01, no permission. |
| SD-15 | Platform UI | No 07 keys. |
| SD-16 | Ownership transfer | 06 Owner-only command, no 07 key. Button omitted. |
| SD-18 | Unenumerated “View” / “Limited” cells | Sales Manager finance and product view, Purchasing expenses, Accountant export, Viewer report views, whether Inventory Manager “Full” includes `inventory.receive`. **Do not seed those roles from “Full”.** |
| SD-20 | Half-specified URLs | Branch archive, brands, cash in/out, expense cancel, journal void, audit export, report export, customer/supplier paths, tax, currency, numbering. |
| SD-21 | `sales_returns.refund` URL | 05 maps the return POST to `sales_returns.create` and mentions refund without a path. |
| SD-22 | Receive URL vs `goods_receipts.*` | 05: `POST /purchase-orders/{id}/receive`. 07: four receipt keys plus `inventory.receive`. Which key guards that URL is not written. |
| SD-23 | Which key guards each accounting and report GET | 05 lists URLs and does not map them. |
| SD-24 | Document 06 leftovers | Manager, `users.invite`, `sales.confirm`, `sales.refund`, `reports.sales.export`. 07 wins. 06 is not edited by this package. |
| SD-25 | Document 01 nav leftovers | Roles, Counts, Pricing, Payment methods, separate Cash group. 07 wins. |

---

## 11. Cross-document consistency report

Reviewed 2026-10-10 against the frozen files. **No frozen file was modified.** `2026-10-10-revised-amendment-set.md` is **not** formally approved.

### 11.1 This design’s five decisions

| Topic | 00 | 02 | 05 | 07 | Result |
|---|---|---|---|---|---|
| Default warehouse | Resolution rule exists | No `is_default`, many rows per branch allowed | Branch create does not provision; session open requires `terminal_id`; no terminal API | No warehouse or terminal keys | **Direction fits 00. Contract gap in 02 and 05.** Amendment §2.1 not applied |
| POS vs back-office create | One sale ledger. POS does not own sales | `terminal_id` and `session_id` columns exist | Draft create is only `POST /sales` → `sales.create`. Confirm split exists. Payments URL has no permission row | Cashier has `pos.create_sale`, not `sales.create` or `payments.create` | **Permissions stay distinct. API gap.** Amendment §2.2 not applied. Cashier is not given `sales.create` |
| Close on the session list | Close stores variance | `pos_sessions` has expected, actual, variance | Close URL and `pos.close_register` exist. **No GET list** | List entry `pos.view_sessions`; close action `pos.close_register`. Cashier grant has **both** | **No matrix contradiction.** GET gap. Amendment §2.3 not applied |
| Restore | Deactivate only | `is_active` style flags, not a restore command | `POST …/activate` with **no** permission row. Deactivate → `products.archive` | `products.restore` with **no** URL | **UI word is Restore. HTTP unbound.** Amendment §2.4 not applied |
| Role dropdown | No tenant role editor | Roles tables exist | `GET /roles` with **no** permission | No `roles.view`. No Roles screen | **Screen stays forbidden. Key proposed in §2.5 with an explicit grant table.** Not seeded |

### 11.2 The 10 October amendment set — checked, not approved

Checked because you asked for `goods_receipt_id`, the Accountant list, and `roles.view` before any apply.

**`goods_receipt_id`**

- Frozen 02 defines `purchase_receipts` and then one sentence: payables come from the receipt, not the PO. It does **not** define a `payables` table or a `goods_receipt_id` column (02 around the purchasing block and the accounting one-liner).
- The amendment’s required `goods_receipt_id` → `purchase_receipts(id)` matches the **origin rule** in 00 §7 and that 02 sentence.
- The column name and the table name differ (`goods_receipt` vs `purchase_receipts`). Permission resource in 07 is `goods_receipts`. Worth an explicit alias in the amendment before apply, so the FK is not read as a second table.
- Frozen 05 has no `POST /payables/{id}/payments`. That URL exists only inside the amendment. Applying 02’s column without the 05 path still leaves SD-09 open.

**Accountant grant list**

- Frozen 07 prose: expenses and finance **full**; sales, customers, products, inventory, purchasing **view**; no POS; reports **finance**; audit view; no users or settings.
- Frozen 07 also defines Full as all atomic keys in the domain. Finance Full therefore includes `receivables.create_payment` and `finance_transactions.create` / `post`. The same section says AR create stays unused until Starter credit exists.
- The amendment’s Accountant list **matches** the prose on POS (none), users/settings (none), audit view, expense mutations, and purchasing view.
- It **does not match** current “Finance Full”, because it withholds `receivables.create_payment`. That withhold matches the AR sentence and 00 §6, and it **changes** the Full cell. It is a real 07 edit, not a restatement.
- It **interprets** unspecified “View” by adding `product_categories.view`, `brands.view`, `units.view`, and `inventory.view_movements`. Frozen 07 does not enumerate those. Treating the list as already decided would close SD-18 for the Accountant without a separate yes.
- It grants `reports.export` with `reports.finance.view`. The compact cell says “Finance”, not “Full”, so export is an interpretation.
- It includes `finance_transactions.create` and `post` while saying HTTP stays blocked. That matches 07’s “if ever exposed” only if you also accept the block. SD-06 is still open in this design package.

**`roles.view`**

- The amendment’s `GET /roles` → `roles.view`, not implied by `users.view`, matches SD-01’s direction.
- The amendment also adds `permissions.view` and `GET /permissions`, and puts both keys on Owner and Administrator. **SD-01 did not accept `permissions.view`.** Applying that file as a set would activate a second key this design left unresolved.
- The amendment’s Accountant exclusion of `roles.view` matches the grant table in §2.5.

**Apply recommendation:** do not apply `2026-10-10-revised-amendment-set.md` as one set. `goods_receipt_id` is consistent with receipt-origin payables and absent from frozen 02. The Accountant list is a proposed narrowing of Finance Full plus an interpretation of View. `roles.view` overlaps §2.5; `permissions.view` does not.

### 11.3 Category delete

Still unresolved in frozen 05 vs 07, in the 10 October amendment (explicitly left open there), and in this design (SD-03).

---

## 12. What this revision authorizes

It records design direction for SD-01, SD-02, SD-10, SD-17, and SD-19, and it writes the gaps down.

It does **not** authorize:

- edits to Documents 00–08
- seeding `roles.view` or changing any role grant
- granting Cashier `sales.create` or `payments.create`
- calling `POST /products/{id}/activate`
- frontend or backend code, migrations, or UI

Next review is the §7 mapping plus whichever amendment blocks in §2 you want applied. Implementation stays stopped.
