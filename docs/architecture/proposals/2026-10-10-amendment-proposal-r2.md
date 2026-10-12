# Ameen Retail — Document-only amendment proposal (r2)

**Date:** 2026-10-10  
**Status:** **PROPOSAL — not applied.** Not an approval to edit Documents 00–08 or to write application code.  
**Supersedes for review:** `2026-10-10-revised-amendment-set.md` (Accountant grant expansion and `permissions.view` in that file are **withdrawn**).  
**Screen design:** direction stays in `2026-10-10-shared-screen-design.md`. This file is the architecture text. Approving a section here is still required before that section is implemented.

Nothing below is seeded, migrated, or wired.

---

## 1. Decision register

| Item | Decision recorded here | Your status | This file |
|---|---|---|---|
| SD-10 | One default warehouse and one default terminal per branch. No new permissions. No management screens. | Conditional | §3 writes the schema, provisioning, branch link, and session resolution. Implementation waits on approval of §3. |
| SD-19 | Dedicated POS workflow authorized by `pos.create_sale`. Cashier does not gain `sales.create`. | Proposed | §4 is the API contract. Do not implement until §4 is approved. |
| SD-17 | Close Register on the sessions list. `pos.view_sessions` lists. `pos.close_register` closes. No new permission. | Approve (design) | §5 adds the missing `GET` contract only. Close URL and both keys already exist. |
| SD-02 | UI action is Restore under `products.restore`. | Conditional | §6 maps the existing activate URL and states that the verbs are not fully identical. Unwired until §6 is approved. |
| SD-01 | Propose `roles.view` for `GET /roles` in user assignment. Grants: Business Owner and Administrator only. | Proposed | §7. Do not activate or seed. `permissions.view` is **not** in this amendment. |
| Payables | Receipt origin. `goods_receipt_id` required. `purchase_order_id` optional reporting copy. One payable per receipt. | Approve in principle | §8 is the 02 + 05 contract. Not applied. |
| Accountant | Do not treat compact “Finance Full” as the grant list. Do not add view keys or `reports.export` by assumption. | Correction required | §9. Each extra grant is a separate yes/no. |

Still unresolved, and **not decided** in this file: category DELETE vs archive, discounts, price override, journal create/post HTTP, AR record-payment, and every unenumerated View/Limited cell (Sales Manager, Inventory Manager, Purchasing Officer, Viewer, and Accountant cells that §9 does not explicitly propose).

---

## 2. What would change, only after you approve that section

| If you approve | Documents touched later | Not touched |
|---|---|---|
| §3 | 02 (default flags and uniques), 05 (branch create side effect, session resolution) | New permission keys, new screens |
| §4 | 05 (POS sale, lines, tenders, confirm split) | Cashier grant, `sales.create` |
| §5 | 05 (`GET /pos/sessions`) | 07 permissions |
| §6 | 05 (permission row and status rule for activate) | New permission key |
| §7 | 07 (`roles.view` text and the grant table in §7.2) | `permissions.view`, Roles screen, seeding before a second approval |
| §8 | 02 (payables columns), 05 (payment command) | Supplier-invoice resource |
| §9 only where you mark Yes | 07 (those grant lines, and the compact-label sentence) | Any row you leave as No |

`permissions.view` and `GET /permissions` are unchanged and unresolved.

---

## 3. SD-10 — Default warehouse and terminal (conditional)

**Design direction:** one active default warehouse and one active default POS terminal per branch. Provision them inside branch creation. No warehouse screen, no terminal screen, no `warehouses.*` or `pos.terminals.*` key.

**Why this is not already true**

- Document 00 §3 requires callers to resolve a **branch default warehouse** and forbids picking a warehouse by accident. It does not say how the default is stored.
- Document 02 `warehouses` is `id, tenant_id, branch_id, name, code, is_active`. Several rows per branch are valid. There is no default flag.
- Document 02 `pos_terminals` is `id, tenant_id, branch_id, name, code, status, is_active`. Same gap.
- Document 05 `POST /branches` creates a branch only. `POST /pos/sessions` requires a client `terminal_id`. There is no terminal list endpoint.

### 3.1 Proposed Document 02 constraints

Add to `warehouses` and to `pos_terminals`:

```
is_default BOOLEAN NOT NULL

Branch association:
  branch_id UUID NOT NULL
  FK (branch_id, tenant_id) → branches(id, tenant_id)

Active default, one per branch:
  UNIQUE (tenant_id, branch_id) WHERE is_default = true AND is_active = true

Codes:
  UNIQUE (tenant_id, code)
```

A branch may not have two active default warehouses or two active default terminals. MVP does not provide a way to insert a second row. The tables stay separate from `branches` (Tenant ≠ Branch ≠ Warehouse ≠ Terminal, Document 00 §3).

### 3.2 Proposed provisioning (Document 05)

`POST /branches`, permission **`branches.create`** (already the branch-create key). One database transaction:

1. Insert the branch.
2. Insert one warehouse: `branch_id` = that branch, `is_default = true`, `is_active = true`, `name` = branch name, `code` = branch `code` + `-WH`.
3. Insert one POS terminal: `branch_id` = that branch, `is_default = true`, `is_active = true`, `status = ACTIVE`, `name` = branch name + ` Register`, `code` = branch `code` + `-POS`.
4. If any insert fails, roll back the branch. The response includes `default_warehouse_id` and `default_terminal_id`.

No other endpoint in this proposal creates a warehouse or a terminal. The client does not send warehouse or terminal fields. Archive of a branch (`branches.archive`, URL still unnamed in Document 05) is out of scope here; do not invent an archive side effect in this section.

### 3.3 How a POS session resolves the terminal

`POST /pos/sessions`, permission **`pos.open_register`** (unchanged).

Body:

```
{ "branch_id": "<uuid>", "opening_cash": "0.0000", "terminal_id": "<uuid, optional>" }
```

Server:

1. Prove membership and branch scope. Out of scope → **404**.
2. Load active `pos_terminals` where `tenant_id`, `branch_id`, `is_default = true`, `is_active = true`.
3. Zero rows or more than one row → **409** `RESOURCE_CONFLICT`. Do not pick an arbitrary terminal.
4. If `terminal_id` is present and is not that row → **409** if it belongs to this branch, **404** if it belongs to another tenant or branch.
5. If this terminal already has a session in `OPEN` → **409** (one open session per register, Document 00 §6).
6. Insert `pos_sessions` with that `terminal_id`, the caller as `cashier_id`, and `opening_cash`.

Inventory `GET /inventory/products/{product_id}?branch_id=` uses the same rule for the default **warehouse**. Zero or many active defaults → **409**. The client does not send `warehouse_id`.

---

## 4. SD-19 — POS sale contract (proposed, not approved)

**Direction:** POS creates and tenders a draft through POS URLs authorized only by `pos.create_sale`. Back-office `POST /sales` stays `sales.create`. The row is still `sales_orders`. POS does not write inventory or journal tables. Cashier is not granted `sales.create` or `payments.create`.

**Gap this contract fills:** Document 05 maps `POST /sales` to `sales.create` and maps only **confirm** to `pos.create_sale`. The cashier grant has `pos.create_sale` and not `sales.create`. There is no POS draft URL, no POS line URL, and no permission on `POST /sales/{id}/payments`.

### 4.1 Relationship to `sales_orders`

`POST /pos/sales` calls the Sales create-draft use case. It inserts `sales.sales_orders` and `sales_order_lines` (Document 02). It is not a second sale table, cart table, or ledger.

Columns set by the server on a POS draft:

| Column | Value |
|---|---|
| `status` | `DRAFT` |
| `branch_id` | Branch of the resolved default terminal |
| `terminal_id` | That terminal |
| `session_id` | The open session for that terminal |
| `warehouse_id` | That branch’s active default warehouse |
| `cashier_id` | Authenticated user |
| `customer_id` | Request value or null |

A back-office `POST /sales` leaves `terminal_id` and `session_id` null. That null `session_id` is how confirm chooses the permission (see §4.6).

### 4.2 `POST /pos/sales`

Permission: **`pos.create_sale`**. `sales.create` does not authorize this URL. `pos.create_sale` does not authorize `POST /sales`.

```
{
  "terminal_id": "<optional; must be the branch default if sent>",
  "branch_id": "<required when terminal_id is omitted>",
  "customer_id": null,
  "items": [{ "product_id": "<uuid>", "quantity": "1.0000" }]
}
```

**Reject, do not ignore,** if the body contains `unit_price`, `discount`, `tenant_id`, `warehouse_id`, `session_id`, or client totals → **422** `VALIDATION_ERROR`. Price override and discounts stay unresolved and are not accepted on this URL.

Header: **`Idempotency-Key` required.** Replay of the same key, tenant, and body returns the original draft and does not insert another sale. Approving §4 adds this command to the idempotency set. Document 00’s current list names confirm and payment, not draft create.

**Validation**

- Caller is authenticated, a member of the tenant, and holds `pos.create_sale`.
- Terminal resolution is §3.3. The session for that terminal is `OPEN`. Else **409** `REGISTER_NOT_OPEN`.
- Default warehouse resolution is §3.3. Else **409**.
- `customer_id`, when present, is that tenant’s customer. Else **404**.
- Each product is that tenant’s, and **ACTIVE**. Else **404** or **409**.
- `quantity` is a decimal string `> 0`. Else **422**.
- At least one item. Else **422**.

**Transaction:** one database transaction that inserts the draft header, the lines, the server-calculated draft totals, and the idempotency row. It does **not** lock stock, write movements, write payments, or post journals. Failure rolls back the draft.

**Response:** the sale id, `DRAFT`, and server totals as decimal strings.

### 4.3 POS line editing

Permission: **`pos.create_sale`**. `sales.update` does not authorize these URLs.

```
POST /pos/sales/{id}/lines
{ "product_id": "<uuid>", "quantity": "1.0000" }

PATCH /pos/sales/{id}/lines/{line_id}
{ "quantity": "2.0000" }
```

`quantity` of `0` on PATCH removes that **draft** line. This is not a delete of a completed sale.

**Preconditions:** sale exists in this tenant (**404** otherwise); `status = DRAFT`; `session_id` is the caller’s open session on the default terminal. Otherwise **409** `INVALID_STATUS_TRANSITION` or `REGISTER_NOT_OPEN`.

Same field rejections as §4.2 for price and discount.

**Transaction:** one short transaction per call. Replace draft line quantities and recompute draft totals. No stock lock, no movement, no journal. **`Idempotency-Key` required.**

### 4.4 POS tenders

Permission: **`pos.create_sale`**. `payments.create` does not authorize this URL. This URL does not authorize back-office `POST /sales/{id}/payments`.

```
POST /pos/sales/{id}/payments
Idempotency-Key: required
{ "payment_method": "cash|card|mobile_money|bank_transfer|other", "amount": "10.0000" }
```

No `credit`. Amount must be `> 0` (**422**). Method outside the list → **422**.

The server resolves `payment_methods.id` for this tenant and that `type`, then inserts `payments` with `reference_type = sale` and `reference_id = sales_orders.id`. If the tenant has no active method of that type → **422**.

**Preconditions:** same as §4.3 (this tenant, `DRAFT`, open session).

**Transaction:** one transaction for the payment row and the idempotency row. Draft `paid_amount` is updated. Stock and sale journals are **not** written here. A tender may be less than the amount due; confirm enforces `sum >= amount due`.

**Boundary versus Document 00 §6.** Document 00 lists “record payments” inside CompleteSale. Document 05 already attaches tenders to the draft before confirm. This proposal keeps that split: the tender transaction commits the payment on the draft; the confirm transaction re-reads those payments and is the only transaction that issues stock and posts the sale journal. If confirm rolls back, the sale stays `DRAFT` and the tender rows remain so the cashier can confirm again. Confirm must not insert a second payment for the same idempotency key.

### 4.5 Back-office, unchanged except the permission row

`POST /sales` → `sales.create`. Body stays the Document 05 draft body. It must not set `terminal_id` or `session_id`.

`POST /sales/{id}/payments` → **`payments.create`**. Only when `session_id` is null. A POS draft rejected here with **409**.

### 4.6 Confirm

`POST /sales/{id}/confirm`, **`Idempotency-Key` required**. This is the Document 00 §6 CompleteSale transaction (stock, journals, audit, commit or full rollback).

| Draft | Permission | The other permission |
|---|---|---|
| `session_id` is set | `pos.create_sale` | `sales.create` does not authorize it |
| `session_id` is null | `sales.create` | `pos.create_sale` does not authorize it |

Also for a POS draft: session still `OPEN`, terminal is that branch’s default, branch in scope (Document 07 §7 extra checks). `sum(payments) >= amount_due`, else **409**. Cash may produce change. Change is not revenue.

### 4.7 Lookup

`GET /products/lookup?barcode=` is allowed when the caller has **`pos.view` or `products.view`**. The cashier grant already includes `products.view`. This does not grant `sales.create`.

### 4.8 Denied-request tests (after §4 is approved, not before)

| Call | Caller | Result |
|---|---|---|
| `POST /pos/sales` | `pos.create_sale` only | 201 draft |
| `POST /pos/sales` | `sales.create` only | 403 |
| `POST /sales` | cashier grant (`pos.create_sale`, no `sales.create`) | 403 |
| `POST /pos/sales/{id}/payments` | `payments.create` only | 403 |
| `POST /pos/sales/{id}/payments` | `pos.create_sale` | 201, no stock movement |
| `POST /sales/{id}/confirm` on a POS draft | `sales.create` only | 403 |
| `POST /sales/{id}/confirm` on a POS draft | `pos.create_sale` | Completes, or rolls back entirely |
| Same Idempotency-Key on confirm | `pos.create_sale` | One stock issue, one journal |
| Body includes `unit_price` or `discount` | `pos.create_sale` | 422 |

---

## 5. SD-17 — Sessions list and close (design approved)

**Accepted without a new permission.**

- Screen `/app/pos/sessions` enters with **`pos.view_sessions`**.
- Close Register on that list renders only with **`pos.close_register`**.
- `POST /pos/sessions/{id}/close` stays **`pos.close_register`** (Document 05 and Document 07 §8). Body `{ "actual_cash": "0.0000" }`. Expected, actual, and variance are stored. Sales are not rewritten (Document 00 §6).
- The cashier grant already contains both keys. No role grant changes.

**Missing contract, proposed for Document 05:**

```
GET /pos/sessions
  Permission: pos.view_sessions
  Query: branch_id, status, date_from, date_to, page, page_size
  Returns sessions for branches in the caller's scope.
  pos.close_register is not required and does not authorize this GET.

GET /pos/sessions/{id}
  Permission: pos.view_sessions
  Other tenant or out-of-scope branch → 404.
```

Cash in and cash out stay on the session detail route and still require `pos.cash_in` or `pos.cash_out`. Their URLs remain **unnamed** in Document 05 (unresolved, not invented here).

A user with `pos.close_register` and without `pos.view_sessions` does not see the list. This amendment does not add a grant to change that.

---

## 6. SD-02 — Restore and `POST /products/{id}/activate` (conditional)

**UI:** the control is labeled **Restore** and requires **`products.restore`**. No Activate button. Unwired until this section is approved.

**Are activation and restoration the same?**

**No, not for every transition.**

| Transition | Document 00 lifecycle | Permission already in 07 | HTTP in 05 |
|---|---|---|---|
| `ACTIVE` → `INACTIVE` | Deactivate | `products.archive` | `POST /products/{id}/deactivate` (05 already maps this) |
| `INACTIVE` → `ACTIVE` | Return to sellable. 07’s verb is restore | `products.restore` | **Not stated.** 05 only names the activate URL |
| `DRAFT` → `ACTIVE` | First activation of a draft | **No key named** | The same URL might be read this way. 05 does not say |

So the HTTP name `activate` is not, by itself, proof that the command is `products.restore`. Publishing a draft and restoring an inactive product are different transitions. This proposal binds the URL to **only** the restore transition.

**Proposed Document 05 mapping:**

```
POST /products/{id}/deactivate
  Permission: products.archive
  Allowed only from ACTIVE → INACTIVE.
  Any other status → 409 INVALID_STATUS_TRANSITION.

POST /products/{id}/activate
  Permission: products.restore
  Allowed only from INACTIVE → ACTIVE.
  DRAFT → ACTIVE is not this command → 409 INVALID_STATUS_TRANSITION.
  UI label for this call: Restore.
  products.archive does not authorize it.
  There is no products.activate key.
```

`DRAFT → ACTIVE` stays **unresolved**. Do not use `products.restore` for it.

---

## 7. SD-01 — `roles.view` (proposed, not activated)

**Not in this amendment:** `permissions.view`, any change to `GET /permissions`, a Roles screen, seeding, or a grant to any role except the two named below.

### 7.1 Proposed Document 07 text

Insert after the Users keys:

```
### Role catalog (read-only)

roles.view — GET /roles. Returns the eight system roles (id and name) so the
user-assignment dropdown can load them.

Does not create, edit, or delete roles or permissions.
Does not open a Roles, Permissions, or role-permission screen.

users.view does not imply roles.view.
users.assign_roles does not imply roles.view.
The compact word Full does not add roles.view to any role other than the
explicit grant list for this key.
```

Insert in §8: `GET /roles` → `roles.view`. Otherwise **403** `PERMISSION_DENIED`.

`POST /users/{id}/roles` stays `users.assign_roles` and still cannot assign or remove Business Owner.

`GET /roles` may include Business Owner in the payload so the current assignment can be displayed. The assignment command still rejects that role id.

### 7.2 Proposed grants (separate, not seeded)

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

The dropdown renders only when the user has **both** `users.assign_roles` and `roles.view`. Owner and Administrator already have `users.assign_roles` in Document 07. That key does not start allowing `GET /roles` until this section is approved **and** you separately allow seeding.

---

## 8. Payables (in principle; contract below is the approval text)

Frozen Document 02 has `purchase_receipts` and the sentence “Payables from receipt (frozen), not from PO.” It does **not** define `payables` columns. Frozen Document 05 has no `POST /payables/{id}/payments`. Permission `payables.create_payment` already exists in Document 07. This section does not add a key.

### 8.1 Proposed Document 02

There is no `goods_receipts` table. The foreign key uses the column name `goods_receipt_id` and references **`purchase_receipts`**.

```
payables
  id UUID PK
  tenant_id UUID NOT NULL
  supplier_id UUID NOT NULL
  goods_receipt_id UUID NOT NULL
  purchase_order_id UUID NULL
  amount NUMERIC(19,4) NOT NULL
  paid_amount NUMERIC(19,4) NOT NULL
  balance NUMERIC(19,4) NOT NULL
  due_date DATE NULL
  status VARCHAR NOT NULL          -- OPEN | PARTIAL | PAID
  created_at TIMESTAMPTZ NOT NULL

  FK (goods_receipt_id, tenant_id) → purchase_receipts(id, tenant_id)
  FK (purchase_order_id, tenant_id) → purchase_orders(id, tenant_id)
  FK (supplier_id, tenant_id) → suppliers(id, tenant_id)

  UNIQUE (tenant_id, goods_receipt_id)     -- one payable per receipt

  CHECK (amount >= 0 AND paid_amount >= 0 AND paid_amount <= amount)
  CHECK (balance = amount - paid_amount)
```

`purchase_order_id` is a reporting copy:

- It is not the origin.
- It is null when `purchase_receipts.purchase_order_id` is null.
- When the receipt has a purchase order, the copy must equal that value.
- A payable is never inserted from a purchase order alone.
- Payment commands ignore this column as an origin.

No `supplier_invoices` table. `payments.reference_type` may be `payable`. `reference_id` is `payables.id`. Do not use `supplier_invoice`.

### 8.2 When the payable is created

Inside the **same transaction** as posting the goods receipt (Document 04 ReceivePurchase; Document 00: receipt changes stock, PO confirm does not):

1. Receipt becomes posted.
2. Inventory movements and balances.
3. Insert one `payables` row: `goods_receipt_id` = `purchase_receipts.id`, `amount` = receipt total, `paid_amount = 0`, `balance = amount`, `status = OPEN`, supplier from the receipt, `purchase_order_id` copied only as in §8.1.
4. Accounting post for the receipt.
5. Audit.
6. COMMIT.

If the unique key hits (a payable already exists for that receipt), the whole receipt transaction rolls back. Confirming a PO does not insert a payable.

### 8.3 Proposed Document 05 payment command

```
POST /payables/{id}/payments
Permission: payables.create_payment
Idempotency-Key: required

{
  "amount": "10.0000",
  "payment_method": "cash|card|mobile_money|bank_transfer|other",
  "notes": "optional"
}
```

Server resolves `payment_methods.id` for that tenant and type (Document 02). Client totals and `tenant_id` are rejected.

**Rules**

- Unknown payable or other tenant → **404**.
- `goods_receipt_id` null → **409** (should be unreachable if §8.1 is applied).
- `amount <= 0` → **422**.
- `amount` greater than `balance` → **409** `PAYMENT_EXCEEDS_BALANCE`. No overpayment.
- No `credit` tender.

**Transaction:** insert `payments` (`reference_type = payable`), increase `paid_amount`, set `balance`, set status `PARTIAL` or `PAID`, call accounting, audit, commit. Any failure rolls back the payment and the balance change. Idempotency replay returns the original payment and does not apply the amount twice.

### 8.4 Who may call it (explicit grant, not “Full”)

`payables.create_payment` is an existing key. This proposal grants it only if you approve this line:

| Role | Grant `payables.create_payment` |
|---|---|
| Business Owner | Proposed yes |
| Administrator | Proposed yes |
| Accountant | Proposed yes |
| Everyone else | No |

Until you approve this table, the key stays ungranted. Compact “Finance Full” does not grant it by itself (see §9.1).

---

## 9. Accountant permissions (corrected)

Document 07 does **not** publish an explicit key list for the Accountant. It says: expenses + finance **full**; sales, customers, products, inventory, and purchasing **view**; POS none; reports **finance**; audit **view**; no users or settings. §7 defines Full as all atomic keys in the domain, and View as view-only.

That wording does **not** explicitly assign:

- `product_categories.view`, `brands.view`, `units.view` (separate resources from `products.view`)
- `inventory.view_movements` (Document 07 §5 gives movements its own entry key)
- `reports.export` (the cell says Finance, not Full)
- `permissions.view` (not in Document 07)
- `sales_returns.view`, `customers.view_transactions`
- `suppliers.view`, `purchase_orders.view`, `purchase_returns.view`

This amendment **does not grant those**. They are not harmless clarifications.

### 9.1 Finance Full does not override the detailed list

Document 07 §4 says `receivables.create_payment` stays unused until Starter credit sales exist. §7 still labels Accountant finance as Full, which would include that key and also `finance_transactions.create` / `post`.

**Proposed sentence for Document 07 §7**, if you approve §9.1:

```
A compact cell does not grant a key that the detailed list or the prose
withholds. For Finance, the detailed list is authoritative.
"Full" does not grant receivables.create_payment while Starter AR is withheld.
"Full" does not grant finance_transactions.create or finance_transactions.post
for an HTTP journal command. Those two keys stay in the registry and stay
ungranted until a journal HTTP contract is approved (screen-design SD-06,
still unresolved).
```

This applies to Owner and Administrator as well as Accountant, so the Owner/Admin “Full” cell cannot silently grant AR payment or manual journal HTTP. Approving §9.1 is that rule. It is not an extra screen.

### 9.2 Keys already fixed by a 1:1 reading (not new grants)

These are the Accountant keys this proposal treats as already assigned. No new key is introduced.

| Key | Why it is already assigned |
|---|---|
| `dashboard.view` | Matrix check for every role, including Accountant |
| `sales.view` | “sales … view”, and View means the view key only |
| `customers.view` | “customers … view” |
| `products.view` | “products … view”. Not categories, brands, or units |
| `inventory.view` | “inventory … view”. Not movements |
| `goods_receipts.view` | §4: “Accountant may still view AP from receipts.” |
| `expenses.view` `expenses.create` `expenses.update` `expenses.approve` `expenses.cancel` `expenses.export` | Expenses cell is Full, and §4 lists exactly these keys for that one resource |
| `reports.finance.view` | Reports cell is Finance, which is this key |
| `audit.view` | “audit view”. Not `audit.export` |

Explicitly **absent** for Accountant, already, and left absent:

- Every `pos.*` key
- Every `users.*` key, and `roles.view`
- Every settings key (`settings.business.*`, `branches.*`, `tax.*`, `currency.*`, `numbering.*`)
- `sales.create`, `sales.update`, `sales.cancel`, `sales.void`, `sales.export`, `sales.print`
- `products.create`, `products.update`, `products.archive`, `products.restore`, `products.export`, `products.print`
- `inventory.adjust`, `inventory.transfer`, `inventory.receive`, `inventory.export`

### 9.3 Finance keys — separate yes/no (not assumed from Full)

Approve each row on its own. **No** means the Accountant does not receive it in this amendment.

| Proposed Accountant grant | Recommendation in this file | Your decision |
|---|---|---|
| `finance_accounts.view` | Yes | Pending |
| `finance_accounts.create` | Yes | Pending |
| `finance_accounts.update` | Yes | Pending |
| `finance_accounts.archive` | Yes | Pending |
| `finance_transactions.view` | Yes | Pending |
| `finance_transactions.void` | Yes | Pending |
| `finance_transactions.create` | **No** until SD-06 | Pending |
| `finance_transactions.post` | **No** until SD-06 | Pending |
| `payments.view` | Yes | Pending |
| `payments.create` | Yes | Pending |
| `payments.void` | Yes | Pending |
| `payments.refund` | Yes | Pending |
| `receivables.view` | Yes | Pending |
| `receivables.export` | Yes. This is the receivables export key, not `reports.export` | Pending |
| `receivables.create_payment` | **No** while AR is withheld | Pending |
| `payables.view` | Yes | Pending |
| `payables.export` | Yes. Not `reports.export` | Pending |
| `payables.create_payment` | Yes, only if you also approve §8.4 | Pending |

`reports.export` is **not** in this table.

### 9.4 Additional view grants — separate yes/no

These exist in Document 07 and are **not** assigned to the Accountant by §9.2. Default here is **No**.

| Key | This amendment grants it to Accountant? |
|---|---|
| `product_categories.view` | No, unless you mark Yes |
| `brands.view` | No, unless you mark Yes |
| `units.view` | No, unless you mark Yes |
| `inventory.view_movements` | No, unless you mark Yes |
| `reports.export` | No, unless you mark Yes |
| `sales_returns.view` | No, unless you mark Yes |
| `customers.view_transactions` | No, unless you mark Yes |
| `suppliers.view` | No, unless you mark Yes |
| `purchase_orders.view` | No, unless you mark Yes |
| `purchase_returns.view` | No, unless you mark Yes |
| `permissions.view` | **Out of this amendment.** Not available to mark Yes here |

No other role receives these keys from this section.

---

## 10. Still unresolved

Do not infer these.

| Topic | Status |
|---|---|
| Category `DELETE` vs `product_categories.archive` | Unresolved |
| Discounts | No permission key. Unresolved |
| Price override / `sales.override_price` | Not in Document 07. Unresolved. POS and back-office bodies in §4 reject `unit_price` until a later contract |
| `finance_transactions.create` / `post` HTTP | Unresolved (SD-06). §9.1 keeps them ungranted |
| `receivables.create_payment` | Registered. Ungranted. Unresolved as a product feature |
| Sales Manager, Inventory Manager, Purchasing Officer, Viewer “View” / “Limited” cells | Unresolved. Not expanded |
| `GET /permissions` | Unresolved. No `permissions.view` in this file |
| `DRAFT → ACTIVE` | Unresolved (§6) |
| Cash in/out URLs | Unresolved (§5) |
| Transfer UI with a single warehouse per branch | Unresolved. No warehouse picker added |

---

## 11. Cross-document consistency

Frozen Documents 00–08 were not modified.

| Topic | Frozen pack | This proposal | Consistent if the section is approved | Still inconsistent until then |
|---|---|---|---|---|
| Default warehouse | 00 requires resolution. 02 has no flag. 05 does not provision | §3 `is_default`, one active per branch, created with the branch | 00’s resolution has a row to resolve | 02 and 05 as they stand |
| POS draft | 05 draft is `sales.create`. 07 cashier has `pos.create_sale` only. 02 already has `terminal_id` and `session_id` | §4 POS URLs, same `sales_orders` | Cashier need not receive `sales.create` | A cashier cannot legally create a draft today |
| Payment timing | 00 records payments inside CompleteSale. 05 attaches them to the draft first | §4.4 states both and keeps stock/journals inside confirm only | Only after you accept that split | The two frozen sentences still disagree |
| Close register | 07 splits list and close. Cashier has both. 05 has close and no list GET | §5 GET only | No new permission | List screen has no frozen GET |
| Restore | 07 `products.restore`. 05 activate URL with no permission. 00 deactivate and DRAFT → ACTIVE → INACTIVE | §6 binds activate to INACTIVE → ACTIVE only | UI word Restore matches 07 | Draft publish still has no key |
| Roles | 05 has `GET /roles` and no permission. 07 has no Roles screen and no `roles.view` | §7 key, dropdown only, two grants, not seeded | No Roles admin UI | Endpoint remains unauthorized in the frozen pack |
| `permissions.view` | Absent from 07 | Omitted | This file does not widen the registry | `GET /permissions` still has no key |
| Payables origin | 00 and 02 prose: from the receipt, not the PO. No payable columns. No payment URL | §8 FK to `purchase_receipts`, unique, optional PO copy, payment command | Origin matches the prose | Columns and URL are not in 00–08 yet |
| Accountant views | 07 says “view” and “Finance”, and also “Full” | §9.2 is the 1:1 set. §9.3–§9.4 are opt-in | No silent `product_categories.view`, `brands.view`, `units.view`, `inventory.view_movements`, or `reports.export` | Compact Full still contradicts the AR sentence inside 07 |
| Previous amendment set | Withdrew nothing in the frozen pack | Accountant expansion and `permissions.view` in `2026-10-10-revised-amendment-set.md` are withdrawn for review | Use this file, not that grant list | That file must not be applied as a set |

---

## 12. Stop

Approve sections individually if you want them. Implementation stays stopped until you approve the relevant section **and** the screen design package. Documents 00–08 stay unchanged until you explicitly allow those edits.
