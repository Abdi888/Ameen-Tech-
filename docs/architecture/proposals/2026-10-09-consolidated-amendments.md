# Ameen Retail — Consolidated amendment proposal (00 / 05 / 07)

**Date:** 2026-10-09  
**Status:** **PROPOSAL — not applied.** Awaits explicit approval before any edit to Documents 00, 05, or 07.  
**Source decisions:** Review of the review-only report (price override, AP path B, withhold AR, 07 keys in principle, `payables.create_payment` for Owner/Admin/Accountant, block manual journals).  
**Does not authorize:** implementation, migrations, application code, or UI.

Documents **00–08 remain unchanged** until you approve **this** consolidated text.

**Inactivity rule (your decision 4):** `roles.view`, `permissions.view`, the five `platform.*` keys, and `sales.override_price` may be **listed** in Document 07 by this amendment but stay **inactive** (not seeded into live role grants, not enforced as product APIs) until the **applicable API/UI contracts in this same proposal** are treated as approved with the pack. This file **includes** the Document 05 contract slices for roles/permissions GET, override payload, and AP payment so that, if you approve this whole document, 00+05+07 can be applied together and those keys can then be **activated** for the endpoints specified here. Platform HTTP APIs stay **out of 05** (reserved keys only). Stock-count keys stay **out**.

If you want keys listed in 07 but **still inactive** after apply, say so before apply; this proposal assumes **one apply** activates D2/D4/AP payment and **does not** activate platform control-plane HTTP or stock counts.

---

## 1. Document 00 — exact changes

### 1.1 Header

**Current:** `Updated: 2026-10-08 (docs 01–07; permission matrix in 07)`

**Replace with:** `Updated: 2026-10-09 (price override; AP payment path; AR withheld)`

### 1.2 §6 — replace the `unit_price` bullet

**Delete this bullet:**

```
- Client `unit_price` is a requested override; server re-prices unless the user has price-override permission. **Server calculates** subtotal, discount, tax, total, change. Change is not revenue.
```

**Insert:**

```
- The **authoritative** unit price is the tenant’s configured selling price (price list / variant base). The server **always** calculates subtotal, discount, tax, total, and change. Change is not revenue.

- A client may send `unit_price` on a **DRAFT** sale line (including POS) only as an **explicit override**:
  - If `unit_price` is omitted, or equals the authoritative price, use the authoritative price. No override permission is required.
  - If `unit_price` **differs** from the authoritative price, the caller **must** have Document 07 permission `sales.override_price` **and** must send a **non-empty override reason**.
  - **Reject** if `unit_price` is negative (`422` / `VALIDATION_ERROR`).
  - **Reject** if an override is requested without `sales.override_price` or without a non-empty reason (`403` `PERMISSION_DENIED` when permission is missing; `422` when reason is missing/blank). **Do not** silently ignore the submitted `unit_price`. **Do not** silently accept an unauthorized override.
  - Foundation v1 does **not** impose an automatic cost floor.
  - Override applies only while the sale is `DRAFT`. Completed lines are immutable.

- **Audit** (append-only) for every applied override: `actor` (user id), `tenant_id`, transaction identity (`sale_id` and line id when present), `authoritative_unit_price`, `override_unit_price`, `reason`, `timestamp` (UTC). No secrets in metadata.
```

**Keep unchanged** the following §6 bullets (credit/AR withhold):

```
- Payment methods v1: `cash`, `card`, `mobile_money`, `bank_transfer`, `other`.
- **Store credit / AR is out of POS v1** unless a later product decision turns it on. Do not enable `credit` as a tender until AR is explicitly in Starter.
```

**Clarify** after the payment-methods bullets (new, to match your decision 3):

```
- POS completed sales must be fully settled by allowed tenders in the CompleteSale transaction (`sum(payments) >= amount_due`). Do not persist unpaid `COMPLETED` POS sales. Do not grant or use `receivables.create_payment` until Starter credit/AR is explicitly approved.
```

### 1.3 §7 — payable origin and AP payment path

**After:**

```
- Payable is created from **receipt** (or a later supplier-invoice spec). Do not invent `supplier-invoices` at implementation time without a schema addendum.
```

**Replace that bullet with:**

```
- Payable is created from **goods receipt**, not from the purchase order. Do **not** introduce a supplier-invoice resource, table, or URL.
- AP payment v1: `POST /payables/{id}/payments` where `{id}` is that **receipt-originated** payable. Permission: Document 07 `payables.create_payment`.
- Reject payment amount **greater than outstanding balance**. Overpayment is forbidden unless a **separately approved** policy says otherwise (none in v1).
```

### 1.4 §8 — manual journals blocked

**After** “Clients **GET** accounts, journals, TB, P&L. They do **not** `POST /journal-entries` to record a sale.”

**Insert:**

```
- `finance_transactions.create` and `finance_transactions.post` (Document 07) must **not** be exposed as client journal-entry commands until API, accounting, and authorization contracts are approved. Sale/purchase/expense posting remains inside those modules’ use cases.
```

### 1.5 §10 Audit (optional one-liner)

**Append to the existing audit bullet:**

```
Price overrides are auditable; metadata must include original price, overridden price, and reason (§6).
```

### 1.6 §11 mapping table — add rows

```
| GET /roles | `roles.view` |
| GET /permissions | `permissions.view` |
| Draft/POS line unit_price ≠ authoritative | `sales.override_price` (+ `pos.create_sale` or `sales.create` / `sales.update`) |
| POST /payables/{id}/payments | `payables.create_payment` |
```

**Add under §11:**

```
`users.view` does not imply `roles.view` or `permissions.view`.
`platform.*` keys are reserved for the platform control plane; never assigned to tenant roles (including Owner and Administrator).
`receivables.create_payment` remains in Document 07 but is **not granted** while Starter AR is withheld.
`inventory.count` is not added until the stock-count contract is approved.
```

### 1.7 §14 Out of v1

**Keep** “store credit/AR (until explicit decision)”. No change required beyond existing text.

---

## 2. Document 05 — exact changes

### 2.1 Sales create payload (§ Sales)

**Replace:**

```
POST /sales → DRAFT `{ branch_id, customer_id?, items[{ product_id, quantity, unit_price? }], discount? }`
```

**With:**

```
POST /sales → DRAFT
{
  "branch_id": "...",
  "customer_id": null,
  "items": [
    {
      "product_id": "...",
      "quantity": "1",
      "unit_price": "0.70",
      "override_reason": "Manager price match"
    }
  ],
  "discount": "0.00"
}
```

Rules:

- `unit_price` optional. If omitted or equal to authoritative price, no override.
- If `unit_price` differs: require `sales.override_price` and non-empty `override_reason`; else **403** (no permission) or **422** (missing reason / negative price).
- Totals remain server-calculated.
- Same override rules on draft line PATCH / POS cart APIs when those send `unit_price`.

### 2.2 Auth / users (existing `GET /roles` · `GET /permissions`)

**Replace the bare list with:**

```
GET /roles         → 200 if roles.view; 403 otherwise. Body: system roles (id, name, description). Not a role editor.
GET /permissions   → 200 if permissions.view; 403 otherwise. Body: permission catalog (code, module, name).
GET|POST /users/{id}/roles → assign uses users.assign_roles; cannot assign/remove Business Owner.
Users UI role dropdown MUST use GET /roles. Do not authorize GET /roles with users.view.
```

### 2.3 Purchasing — replace supplier-payment sentence

**Delete:**

```
- Supplier payments against **payable/receipt**, not an unspecified invoice table
```

**Insert:**

```
- POST /purchase-receipts  (and receive via POST /purchase-orders/{id}/receive as today)
- POST /payables/{id}/payments
  {
    "amount": "100.00",
    "payment_method_id": "...",
    "notes": "optional"
  }
  Payable `{id}` MUST originate from a goods receipt.
  Permission: payables.create_payment.
  If amount > outstanding balance → 409 or 422 (PAYMENT_EXCEEDS_BALANCE). No overpayment in v1.
  No supplier-invoices resource.
```

### 2.4 Accounting read — journals

**Keep GET-only.** **Insert:**

```
Do not implement POST /journal-entries or POST /accounting/journal-entries.
finance_transactions.create and finance_transactions.post are blocked as HTTP commands until a later contract.
CompleteSale / receive / expense posting still create journals internally.
```

### 2.5 Reports

**Replace** `AR/AP only if those features exist` **with:**

```
GET /reports/accounts-payable  — allowed for roles with reports.finance.view (and payables.view as applicable).
GET /reports/accounts-receivable — do not implement Starter AR reporting that implies credit sales until AR is approved.
Do not implement credit POS tender. Do not complete POS sales with unpaid remainder.
```

### 2.6 Permission mapping table — add rows

```
| GET /roles | roles.view |
| GET /permissions | permissions.view |
| POST /payables/{id}/payments | payables.create_payment |
| Draft/POS unit_price override | sales.override_price |
```

### 2.7 Payment methods

**State explicitly:** enabled tenders `cash`, `card`, `mobile_money`, `bank_transfer`, `other`. **No** `credit`.

### 2.8 Platform APIs

**Do not add** `/platform/tenants` (or similar) in this amendment. Keys exist in 07 as reserved only.

---

## 3. Document 07 — exact changes

### 3.1 After §4 Audit, insert

```
### Platform (control plane — reserved)

Not granted to tenant roles (including Business Owner and Administrator).
Not used by bootstrap. Inactive as HTTP until a platform API/UI contract is approved.

- platform.tenants.view
- platform.tenants.create
- platform.tenants.suspend
- platform.users.view
- platform.audit.view

### Registry reads

- roles.view — GET /roles (system role list). Not a role designer.
- permissions.view — GET /permissions (permission catalog).

users.view does not imply roles.view or permissions.view.

### Sales price override

- sales.override_price — DRAFT lines only; unit_price ≠ authoritative price requires this key and a non-empty reason.
  Negative prices rejected. Unauthorized override denied (403). No cost floor in foundation v1.
  Audit: actor, tenant, transaction, original price, overridden price, reason, timestamp.

### Receivables / payables (clarification)

- receivables.create_payment — remains in the registry; **not granted** to any v1 role while Starter credit/AR is withheld.
- payables.create_payment — receipt-originated payable only; POST /payables/{id}/payments (Document 05).
```

**Keep** existing Receivables/Payables key lines in §4 Finance; add the clarification above rather than deleting `receivables.create_payment`.

### 3.2 §5 Users row — add action note

Users screen **entry** remains `users.view`.  
**Add:** Role dropdown requires `roles.view` (via `GET /roles`). Without `roles.view`, fail closed; do not list roles.

### 3.3 §7 — after compact matrix, replace “Full means…” with explicit payment/registry/override notes

```
payables.create_payment: Business Owner, Administrator, Accountant only.
  Scope: POST /payables/{id}/payments on receipt-originated payables. No supplier-invoice. No overpayment.

receivables.create_payment: granted to **no** v1 role.

roles.view, permissions.view: Business Owner, Administrator only.

sales.override_price: Business Owner, Administrator, Sales Manager.
  Not Cashier unless a later amendment.

platform.*: no tenant role.

finance_transactions.create / finance_transactions.post: keys may remain in the registry
  for Owner/Admin/Accountant as finance keys; HTTP commands remain blocked (Documents 00 and 05).
  Do not treat the keys as authorization to POST journals.
```

### 3.4 §8 backend mapping — add

```
GET /api/roles                    → roles.view
GET /api/permissions              → permissions.view
POST /api/payables/{id}/payments  → payables.create_payment
Draft/POS unit_price override     → sales.override_price
```

### 3.5 Header of 07

Add: `Amendment pending apply 2026-10-09: registry reads, platform reserved keys, sales.override_price, AP payment path, AR grant withheld.`  
(Only when applied.)

---

## 4. Updated explicit role-grant lists

**Legend**

- **Live after this pack apply:** keys already in 07 today, plus `roles.view`, `permissions.view`, `sales.override_price` if you approve activation with 05.
- **Reserved, never on tenant roles:** `platform.*`
- **In registry, granted to nobody:** `receivables.create_payment`
- **In registry, HTTP blocked:** `finance_transactions.create`, `finance_transactions.post` (listed on finance roles as 07 keys; **no** journal POST)

New keys **do not** auto-expand these lists later.

### 4.1 Business Owner and Administrator (same 07 tenant keys)

All currently approved 07 keys **except**:

- `receivables.create_payment` (**withheld**)
- all `platform.*` (**never**)

**Includes:** `payables.create_payment`

**After this amendment, also includes:** `roles.view`, `permissions.view`, `sales.override_price`

Full enumerated set (Owner = Admin for keys; domain differences below):

`dashboard.view`

`sales.view` `sales.create` `sales.update` `sales.cancel` `sales.void` `sales.export` `sales.print` `sales.override_price`

`sales_returns.view` `sales_returns.create` `sales_returns.approve` `sales_returns.cancel` `sales_returns.refund`

`pos.view` `pos.create_sale` `pos.open_register` `pos.close_register` `pos.view_sessions` `pos.cash_in` `pos.cash_out` `pos.refund` `pos.reprint`

`customers.view` `customers.create` `customers.update` `customers.archive` `customers.restore` `customers.export` `customers.view_transactions`

`products.view` `products.create` `products.update` `products.archive` `products.restore` `products.export` `products.print`

`product_categories.view` `product_categories.create` `product_categories.update` `product_categories.archive`

`brands.view` `brands.create` `brands.update` `brands.archive`

`units.view` `units.create` `units.update` `units.archive`

`inventory.view` `inventory.view_movements` `inventory.adjust` `inventory.transfer` `inventory.receive` `inventory.export`

`suppliers.view` `suppliers.create` `suppliers.update` `suppliers.archive`

`purchase_orders.view` `purchase_orders.create` `purchase_orders.update` `purchase_orders.approve` `purchase_orders.cancel` `purchase_orders.export`

`goods_receipts.view` `goods_receipts.create` `goods_receipts.post` `goods_receipts.cancel`

`purchase_returns.view` `purchase_returns.create` `purchase_returns.approve` `purchase_returns.cancel`

`expenses.view` `expenses.create` `expenses.update` `expenses.approve` `expenses.cancel` `expenses.export`

`finance_accounts.view` `finance_accounts.create` `finance_accounts.update` `finance_accounts.archive`

`finance_transactions.view` `finance_transactions.create` `finance_transactions.post` `finance_transactions.void`  
(create/post = **no HTTP journal command**)

`payments.view` `payments.create` `payments.void` `payments.refund`

`receivables.view` `receivables.export`  
**not** `receivables.create_payment`

`payables.view` `payables.create_payment` `payables.export`

`reports.sales.view` `reports.inventory.view` `reports.purchasing.view` `reports.customers.view` `reports.expenses.view` `reports.finance.view` `reports.export`

`users.view` `users.create` `users.update` `users.activate` `users.deactivate` `users.assign_roles`

`roles.view` `permissions.view`

`settings.business.view` `settings.business.update`

`branches.view` `branches.create` `branches.update` `branches.archive`

`tax.view` `tax.create` `tax.update` `tax.archive`

`currency.view` `currency.update`

`numbering.view` `numbering.update`

`audit.view` `audit.export`

**Owner vs Admin (not keys):** Admin cannot assign/remove Owner; cannot run ownership-transfer command. Neither gets `platform.*`.

### 4.2 Accountant (enabled v1 role — explicit, not “Finance Full”)

This list is **only** the grants this amendment **freezes for Accountant**. It does **not** claim a complete Accountant catalog of every 07 key; remaining Accountant grants stay as in 07 compact matrix **except** where this list **overrides**.

**Overrides / explicit finance-payment grants**

| Key | Accountant |
|---|---|
| `payables.view` | yes |
| `payables.create_payment` | **yes** — receipt-originated AP only, `POST /payables/{id}/payments` |
| `payables.export` | yes (07 finance/export pattern; compact matrix Full finance) |
| `receivables.view` | yes (view only) |
| `receivables.export` | yes |
| `receivables.create_payment` | **no** |
| `payments.view` `payments.create` `payments.void` `payments.refund` | yes (07 Full finance), **except** `payments.create` must not be used to take POS credit tenders |
| `finance_accounts.*` | yes (07 Full finance) |
| `finance_transactions.view` `void` | yes |
| `finance_transactions.create` `post` | keys per 07 Full finance; **HTTP blocked** |
| `expenses.*` (view/create/update/approve/cancel/export) | yes (07 Full expenses) |
| `reports.finance.view` `reports.export` | yes |
| `roles.view` `permissions.view` | **no** |
| `sales.override_price` | **no** |
| `platform.*` | **no** |
| POS keys | **no** (07 compact: POS —) |

**07 compact matrix still implies** Accountant: `dashboard.view`; **view** on sales, customers, products, inventory, purchasing; audit **view**. Those view keys are **not** re-listed here as a full inventory; a later amendment should enumerate Accountant completely. This amendment **only** requires that Accountant **has** `payables.create_payment` and **has not** `receivables.create_payment`.

### 4.3 Sales Manager (override only)

When `sales.override_price` is activated: **yes**.  
Not `payables.create_payment` unless a later amendment (07 compact: Finance View, Purchasing —).

### 4.4 Cashier, Inventory Manager, Purchasing Officer, Viewer

**Not** granted: `payables.create_payment`, `receivables.create_payment`, `roles.view`, `permissions.view`, `sales.override_price` (except Sales Manager above), `platform.*`.

---

## 5. Cross-document conflicts remaining after this proposal

| Item | After apply | Residual |
|---|---|---|
| Price override ignore vs 403 | **Resolved** in 00/05/07 | Need UI field `override_reason` (08 does not specify layout — OK) |
| AP path / supplier-invoice | **Resolved**: `POST /payables/{id}/payments`; no invoice resource | Document 02 `payables.purchase_order_id` vs receipt origin — 02 should eventually say payable **references receipt**, not PO. **Not in this apply set** (you forbade 02 edit unless listed). **Conflict remains in 02** until a later 02 amendment. |
| AR / credit tender | **Resolved** as withhold | `receivables` table in 02 may exist unused |
| `GET /roles` authz | **Resolved** | — |
| Platform HTTP | Keys in 07 reserved | 03 still has `/platform/*` routes with no 05 API — **intentional delay** |
| Manual journals | **Resolved** as blocked HTTP | Keys still on finance roles |
| Category DELETE vs archive | **Unchanged** | Still open (05 vs 07) |
| Product activate vs `products.restore` | **Unchanged** | Still open |
| Stock counts | **Unchanged** | Blocked; no 07 count keys in this amendment |
| Document 06 Manager / `users.invite` | **Unchanged** | Stale vs 07; not in this apply set |
| Accountant compact “Finance Full” vs withheld AR create | This proposal **overrides** Full for `receivables.create_payment` | Compact matrix table in 07 still says Finance Full — **§3.3 notes must be applied** or the table remains misleading |
| `payments.create` on Accountant vs POS | Risk of using payments API as credit | 05/00: no credit tender; POS complete still requires allowed methods |

**Document 02 not in this proposal.** After apply, 02 still sketches `payables` with `purchase_order_id`. Recommend a **follow-on** 02 change: `goods_receipt_id` (or equivalent) required; do not create payable from PO. Flagged as residual, not silently “fixed.”

---

## 6. What this proposal does *not* do

- Does not edit 00–08 until you approve.  
- Does not implement bootstrap, APIs, or UI.  
- Does not add stock-count keys or platform tenant HTTP.  
- Does not enable `credit` tender or unpaid POS completion.  
- Does not grant `receivables.create_payment`.  
- Does not fully enumerate Accountant’s every view key (only payment/registry/override/platform overrides).

---

## 7. Verification

- Frozen **00–08 were not modified** in this step.  
- This file is the only new artifact: `docs/architecture/proposals/2026-10-09-consolidated-amendments.md`.  
- No application code, migrations, or UI.

**Stop.** Wait for explicit approval to **apply** these changes to Documents 00, 05, and 07. Implementation remains blocked until those applied specs (and any remaining contracts) are approved.
