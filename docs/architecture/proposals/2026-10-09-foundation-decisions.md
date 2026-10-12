# Ameen Retail — Foundation decision record v1.1

**Date:** 2026-10-09  
**Supersedes:** v1.0 of this file  
**Status:** Direction **approved** (Review Decision — Foundation Decisions v1).  
**Not frozen.** Documents **00–08 are unchanged**. Proposed 07 text in §3 is **not applied**.  
**Does not authorize:** implementation, migrations, application code, UI/API features, or edits to 00–08.

Wait for **explicit approval of the document amendments** before any of those.

---

## 1. Decisions and approval status

| ID | Decision | Approval status | Active in product? |
|---|---|---|---|
| D1 | One-time bootstrap: platform admin **and** tenant **and** **separate** Owner | **Approved** | No (not implemented) |
| D2 | `roles.view` / `permissions.view` for `GET /roles` / `GET /permissions` | **Approved as proposed keys** | **No** until 07 amendment |
| D3 | Platform keys for future control plane | **Approved as proposed keys** | **No** until 07 + API/UI contracts |
| D4 | `sales.override_price` + override rules | **Approved as proposed key + rules** | **No** until 07 + API + UI |
| D5 | Stock counts: keep in requirements; do not implement | **Approved** | **Blocked** pending full contract + 07 |
| D6 | Explicit Owner/Admin grants from **current** 07 only | **Approved** | Grant **list** approved for planning; seed only after 07 amendment if new keys are added |
| D7 | This revision of the proposal only | **Approved as the required next step** | — |

### D1 — Bootstrap and first users (approved)

The operator-controlled, one-time bootstrap command **must** create three distinct outcomes:

1. The **initial platform administrator** account (platform authorization boundary).  
2. The **initial tenant**.  
3. A **separate Owner account** for that tenant (tenant Business Owner). Platform admin and tenant Owner are **different identities**.

Rules:

- Do **not** grant `platform.*` to tenant roles (including Owner).  
- Secure, documented, idempotent; refuse accidental/unauthorized reuse.  
- Not public signup. Does **not** replace the future platform tenant-provisioning API.  
- Bootstrap uses **no** application permission key. That does **not** exempt normal HTTP operations from Document 07 authorization.

### D2 — Registry endpoints (approved as proposed keys)

- `GET /roles` requires **`roles.view`**.  
- `GET /permissions` requires **`permissions.view`**.  
- Do **not** use `users.view` for either.  
- Users screen role dropdown may load options **only** through an authorized `GET /roles`. If the user lacks `roles.view`, **fail closed** (no registry leak).  
- Add to Document 07 **only** via the amendment in §3 after you approve that amendment.

Suggested grants once 07 is amended: Owner and Administrator **yes**; other tenant roles **no**.

### D3 — Future platform API (approved as proposed keys; reserved)

Approved candidates (must stay consistent with Document 06 platform namespace):

- `platform.tenants.view`  
- `platform.tenants.create`  
- `platform.tenants.suspend`  
- `platform.users.view`  
- `platform.audit.view`  

Reserved for the **future** platform control plane. **Not active** until the 07 amendment **and** the platform API/UI contracts are approved. Not used by bootstrap.

### D4 — Sales price override (approved as proposed key + rules)

Proposed key: **`sales.override_price`**.

Approved rules (inactive until 07 + API + UI contracts):

- Configured selling price remains authoritative unless an **authorized** override is **explicitly** supplied.  
- **Reject** negative selling prices.  
- Require a **non-empty override reason**.  
- Audit: actor, tenant, transaction, original price, overridden price, reason, timestamp.  
- **No** automatic cost floor in this foundation version.  
- Do **not** silently ignore `unit_price`.  
- Do **not** silently accept an unauthorized override (deny).

Suggested grants once active: Owner, Administrator, Sales Manager **yes**; Cashier and other roles **no** (unless you later amend 07).

### D5 — Inventory stock counts (approved deferral)

Remain in requirements (01/02/03/00). **Do not implement.**  
Proposed keys `inventory.count` and `inventory.count_approve` stay **proposals** until a complete count contract **and** Document 07 are approved. See §5.

### D6 — Owner and Administrator grants (approved method)

Use **explicit** lists from the **currently approved** Document 07 registry only (§4).  
New permissions must **not** silently expand these roles.  
`platform.*` excluded from tenant roles.

`receivables.create_payment` / `payables.create_payment`: see §4.2 and §5. Keys **exist** in 07; inclusion depends on documented business authorization, not on “Full.”

---

## 2. Proposed keys vs currently approved keys

### Currently approved (Document 07 today — live registry)

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

`receivables.view` `receivables.create_payment` `receivables.export`

`payables.view` `payables.create_payment` `payables.export`

`reports.sales.view` `reports.inventory.view` `reports.purchasing.view` `reports.customers.view` `reports.expenses.view` `reports.finance.view` `reports.export`

`users.view` `users.create` `users.update` `users.activate` `users.deactivate` `users.assign_roles`

`settings.business.view` `settings.business.update`

`branches.view` `branches.create` `branches.update` `branches.archive`

`tax.view` `tax.create` `tax.update` `tax.archive`

`currency.view` `currency.update`

`numbering.view` `numbering.update`

`audit.view` `audit.export`

Document 07 **foreshadows** `inventory.count` (“add when the screen is built”) but it is **not** an approved live key.

### Proposed (not in 07 until amendment)

| Key | Decision | Status |
|---|---|---|
| `roles.view` | D2 | Approved proposal; inactive |
| `permissions.view` | D2 | Approved proposal; inactive |
| `platform.tenants.view` | D3 | Approved proposal; reserved |
| `platform.tenants.create` | D3 | Approved proposal; reserved |
| `platform.tenants.suspend` | D3 | Approved proposal; reserved |
| `platform.users.view` | D3 | Approved proposal; reserved |
| `platform.audit.view` | D3 | Approved proposal; reserved |
| `sales.override_price` | D4 | Approved proposal; inactive |
| `inventory.count` | D5 | Proposal only; count contract incomplete |
| `inventory.count_approve` | D5 | Proposal only; count contract incomplete |

**Do not seed or check** proposed keys in code until the 07 amendment is approved (and, for D3/D4/D5, the related contracts).

---

## 3. Exact proposed Document 07 amendment (not applied)

The following is the **verbatim amendment** to apply to `07-permission-matrix-and-screens.md` **only after you explicitly approve this amendment**. It does **not** add stock-count keys (D5 still incomplete). It does **not** add `sales.override_price` until API/UI contracts exist — **wait**: you approved the key as proposed, inactive until 07 **and** API/UI. This amendment **includes** D2, D3, and D4 keys so 07 can list them as **reserved/inactive** or we split.

**Consistency with your D4/D3 wording:** keys remain inactive until 07 **and** applicable contracts. Recommendation: add D2+D3+D4 to 07 in **one** amendment, marked “inactive until API/UI as cited”; **omit** D5 keys until the count contract exists.

### 3.1 Insert in Document 07 §4 (registry), after Audit

```markdown
### Platform (control plane — reserved)

These keys are not granted to tenant roles. They are inactive until the platform
API and UI contracts are approved. Bootstrap does not evaluate them.

- platform.tenants.view
- platform.tenants.create
- platform.tenants.suspend
- platform.users.view
- platform.audit.view

### Registry reads

- roles.view — GET /roles (system role list). Not a role designer.
- permissions.view — GET /permissions (permission catalog).

users.view does not imply roles.view or permissions.view.

### Sales price override (inactive until API and UI contracts)

- sales.override_price — accept a draft-line unit_price different from the
  authoritative selling price, with a non-empty reason. Reject negative prices.
  Unauthorized or silent ignore is forbidden. No cost floor in foundation v1.
```

### 3.2 Insert in Document 07 §5 (screens) and §8 (API)

```markdown
Users role dropdown data: GET /roles requires roles.view. Fail closed.

GET /roles        → roles.view
GET /permissions  → permissions.view
POST /users/{id}/roles → users.assign_roles (unchanged; cannot assign Owner)

Draft sale / POS line with unit_price ≠ authoritative price
  → sales.override_price (plus existing sales.create or pos.create_sale)
  → 403 if unauthorized; do not apply catalog price silently when an
     override was requested without permission
```

### 3.3 Insert in Document 07 §7 (role matrix notes)

```markdown
When activated: roles.view and permissions.view → Business Owner, Administrator only.

When activated: sales.override_price → Business Owner, Administrator, Sales Manager.

Never: platform.* on Owner, Administrator, or any other tenant role.
```

### 3.4 Document 00 / 05 / 06 (after 07, if you approve a pack sync)

Not part of this file’s apply step. After 07 is amended, **recommended** follow-ups (still require your approval):

| Doc | Change |
|---|---|
| 00 §6 | Reference `sales.override_price`; require reason; 403 if unauthorized override requested |
| 00 §11 | Add GET /roles, GET /permissions, override mapping |
| 05 | `unit_price` + `override_reason`; 403 unauthorized override; GET /roles authz |
| 06 | Align platform key list with 07; drop stale Manager / `users.invite` when you choose to sync |

**Document 08:** no amendment required.

---

## 4. Explicit Owner and Administrator grant lists

**Source:** currently approved Document 07 keys only.  
**Identical tenant key sets** except domain rules below.  
**Not included:** any §2 proposed key; any `platform.*`.

### 4.1 Granted to Business Owner and to Administrator

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

`payables.view` `payables.export`

`payables.create_payment` — **included** (see §4.2)

`reports.sales.view` `reports.inventory.view` `reports.purchasing.view` `reports.customers.view` `reports.expenses.view` `reports.finance.view` `reports.export`

`users.view` `users.create` `users.update` `users.activate` `users.deactivate` `users.assign_roles`

`settings.business.view` `settings.business.update`

`branches.view` `branches.create` `branches.update` `branches.archive`

`tax.view` `tax.create` `tax.update` `tax.archive`

`currency.view` `currency.update`

`numbering.view` `numbering.update`

`audit.view` `audit.export`

### 4.2 Payment keys — include vs hold

| Key | In 07 registry? | Business authorization documented? | In §4.1? |
|---|---|---|---|
| `payables.create_payment` | Yes | **Partial.** 00: payable from **receipt**; 05: pay outstanding (path still says `supplier-invoices`, which 00 forbids inventing). Paying a receipt-based payable is an intended purchasing/finance operation. | **Yes** — so Owner/Admin can authorize AP payment **once** the pay-against-receipt API is specified without a new key. |
| `receivables.create_payment` | Yes | **No for Starter POS.** 00: no store credit/AR in POS; 07: `receivables.create_payment` unused in POS until credit sales are an explicit Starter feature. | **No** — not silently granted. Not a new key; **withheld** until AR is explicitly authorized. |

This does **not** omit receipt/AP payment (`payables.create_payment`). It does **not** enable POS credit.

### 4.3 Owner vs Administrator (not extra 07 keys)

| Rule | Owner | Administrator |
|---|---|---|
| Keys in §4.1 | yes | yes |
| Assign/remove Business Owner | no | no |
| Ownership transfer (06 command; **no** 07 key) | yes | no |
| `platform.*` | no | no |
| Proposed keys in §2 | no, until 07 amendment + grants | no, until 07 amendment + grants |

After a **future** 07 amendment, **do not** auto-add new keys to these lists. Update §4.1 in this record (or 07) by explicit review.

---

## 5. Unresolved stock-count and payment-authorization questions

### Stock counts (block implementation)

Prepare and approve a **complete contract** before any count code or 07 count keys. That contract must define:

1. Count document lifecycle and statuses.  
2. Create, submit, review, approve, **reject**, cancel rules.  
3. Permissions and **segregation of duties** (whether creator may approve).  
4. Expected qty, counted qty, variance, **valuation** (WAC).  
5. Concurrency / movements **during** counting (freeze, allow sales, or snapshot expected).  
6. How approved variances become **auditable** stock changes.  
7. Whether `STOCK_COUNT` is a distinct document vs posting `ADJUSTMENT_*` (00 lists both `STOCK_COUNT` movement type and count → adjustments).  
8. Database (02 sketches `stock_counts`), API, UI, audit.

Until then: `inventory.count` / `inventory.count_approve` remain proposals only.

### Payment authorization

| Question | Why it matters |
|---|---|
| Exact AP payment endpoint (`POST /purchase-receipts/{id}/payments` vs 05 `supplier-invoices`) | 00 vs 05 contradiction; `payables.create_payment` is the 07 key either way |
| When `receivables.create_payment` is granted | Requires explicit Starter **credit sales / AR** decision |
| Whether Owner/Admin may **POST** `finance_transactions` | 07 has create/post; 05 is GET-only for journals except sale posting inside CompleteSale. Manual journals **blocked** until 05 adds a command |
| Split tender / `payments.create` vs sale confirm | Already in 00/05/07; not blocked |

---

## 6. Conflicts with Documents 00–06 or 08

| Topic | Conflict | Handling in this record |
|---|---|---|
| 00 §6 override without reason | 00 does not require override **reason**; D4 does | D4 is an **approved product rule** awaiting 00/05/07 sync. Until 07 is amended, do not implement override. |
| 00 §6 “re-price unless permitted” vs D4 “do not silently ignore” | If unauthorized client sends `unit_price`, 00 could be read as ignore; D4 requires **reject** | **D4 wins** for future implementation: 403, do not apply a hidden catalog price when override was requested. Needs 00 wording update when you allow pack edits. |
| 06 `platform.tenants.*` wildcard vs five exact keys | 06 is not an exhaustive API list | D3 keys are the **only** platform identifiers proposed; no extra `platform.tenants.update` |
| 06 `ownership.transfer` as permission-like code | Not in 07 | Still a **domain command**, not a grant in §4.1 |
| 06 Manager role / `users.invite` | 07/00 use eight roles and `users.create` | No change; stale 06 |
| 05 `GET /roles` with no permission | D2 supplies keys | Blocked until 07 amendment |
| 05 `supplier-invoices` vs 00 no invoice table | AP payment path | Key `payables.create_payment` kept; path unresolved |
| 05/07 category DELETE vs archive | Unrelated to D1–D7 | Still open; not resolved here |
| 05 activate vs `products.restore` | Same | Not resolved here |
| 01/03 counts vs 07 incomplete key | D5 | Defer implementation |
| 08 UI tokens | None | No change |
| Bootstrap three identities vs 06 “platform creates tenants” | Compatible: command is the operator stand-in for platform | Separate Owner identity is **new operational detail**, not a 00 contradiction |

---

## 7. Feature readiness (unchanged authorization to code)

| Item | Status |
|---|---|
| Amend Documents 00–08 | **Not authorized** |
| Seed live 07 keys / Owner-Admin §4.1 | Plan-only until you authorize implementation |
| Bootstrap command | Design approved; **implementation not authorized** |
| `GET /roles` / `GET /permissions` | **Blocked** on 07 amendment |
| Platform HTTP APIs | **Blocked** |
| Price override | **Blocked** on 07 + API + UI |
| Stock counts | **Blocked** on full contract + 07 |
| AR `receivables.create_payment` | **Blocked** on Starter credit decision |
| Manual journal POST | **Blocked** on 05 command |
| Application / migrations / frontend | **Not authorized** |

---

## 8. Verification

- Documents **00–08 were not modified**.  
- Document **09 was not modified**.  
- **No** application code, migrations, or UI/API features were created.  
- Proposed keys are recorded here only; they are **not** in the live Document 07 registry.  
- No legacy ERP was referenced.  
- No unrelated modules were redesigned.

**Stop.** Wait for explicit approval of the **Document 07 (and follow-on 00/05) amendments** before implementation.
