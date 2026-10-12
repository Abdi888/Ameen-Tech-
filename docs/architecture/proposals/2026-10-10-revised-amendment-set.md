# Ameen Retail — Revised document-only amendment set

**Date:** 2026-10-10  
**Status:** **WITHDRAWN for review.** Do not apply this file as a set.  
**Replaced by:** `2026-10-10-amendment-proposal-r2.md`.  
**Why:** the Accountant list in §2.2 adds view keys and `reports.export` that Document 07 does not explicitly assign, and this file includes `permissions.view`. Those are not approved. r2 lists any extra grant as a separate decision and leaves `permissions.view` out.  
**Supersedes (for review):** `2026-10-09-consolidated-amendments.md` where this file is more specific.  
**Does not authorize:** edits to Documents 00–08, implementation, migrations, or UI.

Wait for **explicit approval** before applying any frozen-pack change.

---

## Approved decisions preserved

| Decision | Status in this set |
|---|---|
| AP endpoint `POST /payables/{id}/payments` | Include in 00 + 05 |
| Payables originate from **goods receipts** only | Include in 00 + **02** + 05 |
| No supplier-invoice resource | Include |
| No overpayment (unless a later policy) | Include |
| Starter credit / AR **disabled** | Include |
| `receivables.create_payment` **registered, ungranted** | Include in 07 |
| `platform.*` **never** on tenant roles | Include |
| `sales.override_price` **registered, inactive** until API + UI + audit + **test** contracts are approved | **Listed in 07, granted to nobody, 05 contract marked inactive** |
| Manual `finance_transactions.create` / `post` **HTTP blocked** | Include |
| Stock counts **unimplemented**; no count keys in this apply | Include |
| Category DELETE vs archive | **Unresolved — out of this set** |
| Product activate vs restore | **Unresolved — out of this set** |

**Price-override 00 business rules** may be written into Document 00 so the ignore-vs-403 conflict is resolved on paper. **Do not grant** `sales.override_price` and **do not implement** override APIs/UI until those contracts are separately approved. Document 05 override payload in §2.2 is the **draft contract**, not an implementation permit.

---

## 1. Exact proposed changes by document

### 1.1 Document 00 (`00-frozen-decisions.md`)

**§6 — replace the current `unit_price` bullet** with the approved D4 rules (authoritative price; `sales.override_price` + non-empty reason; 403 unauthorized; 422 negative/blank reason; draft-only; audit; no cost floor). **Add:** override **implementation and grants remain inactive** until API, UI, audit, and test contracts are approved.

**§6 — keep** tenders without `credit`. **Add:** no unpaid `COMPLETED` POS sales; do not grant `receivables.create_payment` while AR is withheld.

**§7 — replace** the payable/supplier-invoice bullet with:

```
- A payable is created only from a **posted goods receipt**, never from a purchase order alone.
- Do not introduce a supplier-invoice resource, table, or URL.
- AP payment: POST /payables/{id}/payments. {id} is the receipt-originated payable.
- Permission: payables.create_payment (Owner, Administrator, Accountant only — Document 07).
- Reject amount > outstanding balance. No overpayment in v1.
- purchase_orders.id may appear on the payable only as a denormalized copy from the receipt, not as the payable’s origin (Document 02).
```

**§8 — add:** `finance_transactions.create` / `post` are not HTTP journal commands until a later approved contract.

**§11 — add mapping rows** for `GET /roles` → `roles.view`, `GET /permissions` → `permissions.view`, `POST /payables/{id}/payments` → `payables.create_payment`.  
Add override mapping **marked inactive** until contracts approved.  
State: `users.view` ≠ `roles.view`; `platform.*` never on tenant roles; `receivables.create_payment` ungranted.

**§14 — keep** store credit/AR out until explicit decision.

---

### 1.2 Document 02 (`02-database-schema.md`)

**Problem:** The original schema sketch used `payables.purchase_order_id` (nullable). Prose already says “Payables from receipt (frozen), not from PO,” but the column name implies PO origin. The expanded `payables` column list is not fully specified in the current 02 file (only a pointer at § Accounting).

**Proposed: add an explicit `payables` (and `receivables`) definition under Accounting**, and a purchasing cross-rule.

**Insert after** “Receipt completion generates movements. Payables from receipt (frozen), not from PO.”:

```
AP payable origin (v1)
----------------------
A payable row is created when a goods receipt is posted (same receive transaction).
It is not created when a purchase order is confirmed.

purchase_receipts.purchase_order_id may be NULL (receipt without PO) or set
(receipt against a PO). That is a property of the receipt, not of payable origin.
```

**Replace the one-liner**  
`receivables` / `payables` exist in the original schema sketch…  
**with:**

```
receivables
-----------
id UUID PK
tenant_id UUID NOT NULL
customer_id UUID NOT NULL
sales_order_id UUID NULL          -- unused for POS credit while AR withheld
amount, paid_amount, balance NUMERIC(19,4)
due_date DATE NULL
status VARCHAR
created_at TIMESTAMPTZ

v1: table may exist for schema completeness. Do not create receivable rows from
POS CompleteSale. Do not grant receivables.create_payment.

payables
--------
id UUID PK
tenant_id UUID NOT NULL
supplier_id UUID NOT NULL
goods_receipt_id UUID NOT NULL    -- ORIGIN (required)
purchase_order_id UUID NULL       -- OPTIONAL COPY from purchase_receipts.purchase_order_id
                                  -- for reporting only. NOT a second origin.
                                  -- MUST NOT be set unless the receipt has that PO.
                                  -- MUST NOT be used to create or pay a payable
                                  -- without goods_receipt_id.
amount NUMERIC(19,4)              -- original payable
paid_amount NUMERIC(19,4)
balance NUMERIC(19,4)             -- amount - paid_amount
due_date DATE NULL
status VARCHAR                    -- e.g. OPEN, PARTIAL, PAID
created_at TIMESTAMPTZ

Constraints:
  UNIQUE(tenant_id, goods_receipt_id)  -- one payable per receipt in v1
  goods_receipt_id NOT NULL
  FK goods_receipt_id → purchase_receipts(id)
  FK purchase_order_id → purchase_orders(id)  -- nullable
  CHECK (balance = amount - paid_amount)     -- or maintain in application + tests
  CHECK (paid_amount >= 0 AND amount >= 0)
  CHECK (paid_amount <= amount)              -- no overpayment v1

Payment: POST /payables/{id}/payments (Document 05).
reference on payments: reference_type = payable, reference_id = payables.id
```

**Do not** add a `supplier_invoices` table.

**`payments.reference_type`:** allow `payable` (and existing sale/expense). Do not use `supplier_invoice`.

---

### 1.3 Document 05 (`05-api-contract.md`)

**Users / roles**

```
GET /roles        → requires roles.view; 403 otherwise. Not authorized by users.view.
GET /permissions  → requires permissions.view; 403 otherwise.
Users role dropdown MUST call GET /roles; fail closed without roles.view.
POST /users/{id}/roles → users.assign_roles; cannot assign/remove Business Owner.
Employee invite is the users.create flow (email invite, user sets password).
There is no users.invite permission key.
```

**Purchasing — AP payment (active contract once this pack is applied)**

```
POST /payables/{id}/payments
Permission: payables.create_payment
Body: { "amount": "…", "payment_method_id": "…", "notes": "optional" }
Payable must have goods_receipt_id (receipt-originated).
No /supplier-invoices resource.
amount > outstanding balance → PAYMENT_EXCEEDS_BALANCE (409 or 422).
```

**Tenders:** `cash` | `card` | `mobile_money` | `bank_transfer` | `other`. No `credit`.  
CompleteSale: `sum(payments) >= amount_due`. No unpaid COMPLETED POS sale.

**Accounting:** GET journals/accounts/TB only. No `POST /journal-entries`.  
`finance_transactions.create` / `post` HTTP **blocked**.

**AR reports:** do not ship credit-sale AR flows.

**Price override (DRAFT CONTRACT — inactive for implementation)**

Document the payload (`unit_price`, `override_reason`) and 403/422 rules **as the future API contract**. Header this subsection:

```
INACTIVE — do not implement until API, UI, audit, and test contracts are explicitly approved.
```

Do **not** treat applying Document 05’s *other* sections as permission to build override.

**Mapping table add:** `GET /roles`, `GET /permissions`, `POST /payables/{id}/payments`. Override row marked **inactive**.

**Unresolved (do not “fix” in this set):** `DELETE /categories/{id}` vs `product_categories.archive`; `POST /products/{id}/activate` vs `products.restore`.

---

### 1.4 Document 06 (`06-security-and-authorization.md`)

**Why Manager / `users.invite` are not valid as-is**

- Document 07 + 00 §11: eight roles; **no generic Manager**.
- Document 07: invite/create employee is **`users.create`**, not `users.invite`.
- Document 06 § Roles already lists the eight roles and says “No generic Manager role,” but **§ Permissions** and **§ Starter role matrix** still contradict that.

They do **not** remain valid. They are stale leftovers. **Invite as a process** remains valid (admin invites → user sets password); that is not a permission code.

**Proposed replacements (exact)**

**§ Permissions — Users line**

Delete: `Users: view, invite, update, suspend, remove`  
Insert: `Users: see Document 07 (users.view, users.create, users.update, users.activate, users.deactivate, users.assign_roles). There is no users.invite key. Invitation is the users.create flow.`

**§ Permissions — other resource lists**

Replace inline stale names (`sales.confirm`, `sales.refund` as sales.*, `reports.financial.view`, `reports.profit.view`, `reports.sales.export`, `inventory.count` as if live, `platform.tenants.*` wildcard) with:

```
Permission identifiers: Document 07 is authoritative.
Do not use: users.invite, sales.confirm, sales.refund (use sales_returns.*),
reports.financial.view, reports.sales.export (use reports.export / reports.finance.view),
or a generic Manager role.

Platform keys (reserved, not granted to tenant roles):
platform.tenants.view, platform.tenants.create, platform.tenants.suspend,
platform.users.view, platform.audit.view
(inactive as HTTP until a platform API/UI contract is approved).
```

**§ Authorization — discount example**

Delete: `cashier ≤ 5%, manager ≤ 20%` as if **role name Manager**.  
Insert: `Numeric discount/refund thresholds are domain policies (ALLOW / REQUIRE_APPROVAL), not extra permission keys and not a Manager role. Map policy bands to Document 07 roles when those numbers are approved (e.g. Cashier vs Sales Manager). Threshold values remain unspecified.`

**§ Starter role matrix — replace entire table and following sentence**

```
Canonical roles and grants: Document 07 (explicit lists, not this table).

Capability columns must not use “Manager”. Use:
Business Owner | Administrator | Sales Manager | Inventory Manager |
Cashier | Purchasing Officer | Accountant | Viewer

This document does not duplicate the 07 grant lists. If this section and
Document 07 diverge, Document 07 wins on keys and grants; Document 00 wins
on cookies, sale lifecycle, and AR withhold.

Admin cannot transfer ownership or assign/remove Owner.
Cashier cannot manage users, roles, or settings.
There is no generic Manager; “limited settings” is not granted to Sales Manager
unless Document 07 says so (it does not).
```

**§ Tests:** `Cashier ↛ invite` → `Cashier ↛ users.create / users.assign_roles`.

**§ Danger keys:** `ownership.transfer` is a **domain command**, not a 07 permission; do not seed it. `security.settings.update` is not in 07; do not seed it.

---

### 1.5 Document 07 (`07-permission-matrix-and-screens.md`)

**§4 Finance — after existing receivable/payable keys, insert:**

```
receivables.create_payment — registered; granted to no v1 role (Starter AR withheld).
payables.create_payment — POST /payables/{id}/payments on a payable whose
  goods_receipt_id is NOT NULL. Not payable-from-PO. No supplier-invoice.
  Granted only to Business Owner, Administrator, Accountant.
```

**§4 — insert registry reads, reserved platform keys, inactive override** (same keys as previously approved). Mark `sales.override_price` **registered, granted to nobody until override contracts are approved**.

**§5 Users:** entry `users.view`; role dropdown requires `roles.view` (inactive until 07+05 apply for those keys, then active with GET /roles).

**§7 Compact matrix — replace the Finance row and the “Full =” definition:**

**Replace**

`Full = all atomic permissions for that domain.`

**with**

```
Full = all Document 07 keys for that domain EXCEPT keys this document
explicitly withholds or restricts. Compact cells are subordinate to the
explicit grant lists and to the notes below.
```

**Replace Finance row:**

| Module | Owner | Admin | Accountant | Sales Mgr | Inv Mgr | Cashier | Purchasing | Viewer |
|---|---|---|---|---|---|---|---|---|
| Finance | Restricted† | Restricted† | Restricted† | View‡ | — | — | — | View‡ |

```
† Restricted finance (Owner, Administrator, Accountant):
  Includes: finance_accounts.*, finance_transactions.view, finance_transactions.void,
  payments.view/create/void/refund (not credit tender), payables.view,
  payables.create_payment (receipt-originated only), payables.export,
  receivables.view, receivables.export.
  Excludes: receivables.create_payment.
  finance_transactions.create and finance_transactions.post remain in the
  registry for these roles as 07 keys but MUST NOT be used as HTTP journal
  commands until a later contract (Documents 00, 05).

‡ View = finance_accounts.view, finance_transactions.view, payments.view,
  payables.view, receivables.view only — no create_payment keys.
```

**Do not** leave Accountant / Owner / Admin Finance = `Full`.

**§7 notes — add** the grant table in §3 of this proposal (Owner/Admin/Accountant). State new keys never auto-expand roles. `platform.*` never on tenant roles. `sales.override_price` ungranted until contracts approved (then Owner, Admin, Sales Manager only — **not in the live grant list in §3 until then**).

**§8 — add** GET /roles, GET /permissions, POST /payables/{id}/payments. Override mapping marked inactive.

**Unresolved in 07 (leave as notes, do not pick):** category DELETE vs archive; product activate vs restore.

---

### 1.6 Documents 01, 03, 04, 08, 09

No required edits in this set. 08 unchanged. 01/03 still mention stock counts (requirements; unimplemented).

---

## 2. Explicit Owner / Administrator / Accountant grant lists

**After this amendment is applied**, live **granted** keys are as follows.  
**Not granted:** `receivables.create_payment`, `platform.*`, `sales.override_price` (until override contracts approved), `inventory.count` / `inventory.count_approve` (not in registry).

`finance_transactions.create` / `post`: **listed** on finance roles as 07 keys; **HTTP forbidden**.

### 2.1 Business Owner and Administrator (identical key sets)

`dashboard.view`

`sales.view` `sales.create` `sales.update` `sales.cancel` `sales.void` `sales.export` `sales.print`

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

`payments.view` `payments.create` `payments.void` `payments.refund`

`receivables.view` `receivables.export`

`payables.view` `payables.create_payment` `payables.export`

`reports.sales.view` `reports.inventory.view` `reports.purchasing.view` `reports.customers.view` `reports.expenses.view` `reports.finance.view` `reports.export`

`users.view` `users.create` `users.update` `users.activate` `users.deactivate` `users.assign_roles`

`roles.view` `permissions.view`  
(only after this 07+05 amendment is applied; until then these keys do not exist)

`settings.business.view` `settings.business.update`

`branches.view` `branches.create` `branches.update` `branches.archive`

`tax.view` `tax.create` `tax.update` `tax.archive`

`currency.view` `currency.update`

`numbering.view` `numbering.update`

`audit.view` `audit.export`

**Not in this list:** `sales.override_price`, `receivables.create_payment`, `platform.*`

**Owner vs Admin:** same keys. Admin cannot assign/remove Owner; cannot ownership-transfer.

### 2.2 Accountant (explicit; compact matrix must match)

`dashboard.view`

`sales.view`  
`sales_returns.view`

`customers.view`  
`products.view`  
`product_categories.view` `brands.view` `units.view`  
`inventory.view` `inventory.view_movements`  
`suppliers.view`  
`purchase_orders.view` `goods_receipts.view` `purchase_returns.view`

`expenses.view` `expenses.create` `expenses.update` `expenses.approve` `expenses.cancel` `expenses.export`

`finance_accounts.view` `finance_accounts.create` `finance_accounts.update` `finance_accounts.archive`

`finance_transactions.view` `finance_transactions.create` `finance_transactions.post` `finance_transactions.void`

`payments.view` `payments.create` `payments.void` `payments.refund`

`receivables.view` `receivables.export`

`payables.view` `payables.create_payment` `payables.export`

`reports.finance.view` `reports.export`

`audit.view`

**Accountant does not get:** POS keys; `sales.create` / update / void / export / print / `sales.override_price`; purchasing mutations; inventory adjust/transfer/receive; users/settings; `roles.view`; `permissions.view`; `receivables.create_payment`; `platform.*`; `reports.sales.view` (07 compact: reports = Finance only).

This **is** the Accountant list this amendment freezes. Compact Finance cell = **Restricted†**, not Full.

---

## 3. Cross-document consistency report

| Topic | 00 | 02 | 05 | 06 | 07 | After this set |
|---|---|---|---|---|---|---|
| Payable origin | Receipt | **`goods_receipt_id` required; `purchase_order_id` optional copy** | `POST /payables/{id}/payments` | — | `payables.create_payment` scoped | **Consistent** |
| Supplier invoice | Forbidden | No table | No resource | — | — | **Consistent** |
| Overpayment | Forbidden | CHECK `paid_amount <= amount` | `PAYMENT_EXCEEDS_BALANCE` | — | — | **Consistent** |
| AR / credit tender | Withheld | receivables unused | No credit; no unpaid POS | — | key ungranted | **Consistent** |
| Manager role | Eight roles | — | — | **Matrix still Manager** → replace | Eight roles | **Consistent if 06 replaced** |
| `users.invite` | — | — | invite **flow** | **Stale key** → `users.create` | `users.create` | **Consistent if 06 replaced** |
| `roles.view` | Mapping | — | GET /roles | Point to 07 | New key | **Consistent** |
| Price override | Rules in 00; impl inactive | line snapshot `unit_price` | Draft contract inactive | — | Key registered, **ungranted** | **Consistent** (impl still blocked) |
| Manual journals | HTTP blocked | journal tables exist | GET only | — | keys exist, HTTP blocked | **Consistent** |
| Platform keys | Never on tenant | — | No platform HTTP in this set | Exact five keys, reserved | Same | **Consistent** |
| Stock counts | Later | tables sketched | “when built” | `inventory.count` in old list → defer | No live count key | **Consistent** (unimplemented) |
| Category DELETE vs archive | Unresolved | `is_active` | DELETE if unused | — | archive only | **Explicitly unresolved** |
| Product activate vs restore | Unresolved | `is_active` | POST activate | — | `products.restore` | **Explicitly unresolved** |
| 02 payable vs PO id | Receipt origin | **Was implied PO FK** | Path B | — | AP create | **Resolved by 02 text in this set** |
| 07 “Finance Full” vs ungranted AR create | Withhold AR | — | — | — | **Matrix Full contradicted grants** | **Resolved by Restricted† + Accountant list** |
| `reports.sales.export` (06) vs `reports.export` (07) | 07 wins | — | — | Stale | `reports.export` | **Resolved if 06 points at 07** |
| Discount “manager 20%” | Policy not frozen numbers | — | — | Role name clash | No Manager | **Reword 06 to policy + 07 role names** |

**Not in this set:** bootstrap command (approved operationally, not a frozen-doc schema); platform HTTP APIs; stock-count contract; override implementation/tests/UI.

---

## 4. Apply order (when you approve)

1. Document 07 (keys, Restricted† finance, explicit lists)  
2. Document 00 (payable path, override rules, AR withhold)  
3. Document 02 (payables columns)  
4. Document 05 (AP + roles GET; override subsection **inactive**)  
5. Document 06 (Manager / invite / matrix)

Implementation, migrations, and UI remain **blocked** until you approve **apply** and then separately approve implementation.

---

## 5. Verification

- Documents **00–08 were not modified**.  
- New file only: `docs/architecture/proposals/2026-10-10-revised-amendment-set.md`.  
- No application code, migrations, or UI.  
- Category DELETE vs archive and product activate vs restore **not decided**.  
- `sales.override_price` and stock counts **not** implementation-ready.

**Stop.** Wait for explicit approval before applying amendments to the frozen pack.
