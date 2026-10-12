# Ameen Retail — Gate 1 Amendment Set (Option A)

**Status:** Draft — Gate 1 catalogue and boundary resolutions **recorded** in the decision register; **not applied** to Documents 00–09. Does not authorize implementation.  
**Date:** 2026-10-12  
**Path:** `docs/architecture/proposals/2026-10-12-gate-1-amendment-set.md`  
**Baseline:** Frozen Documents 00–09; register `docs/architecture/ameen-retail-consolidated-decision-amendment-register.md` §9; roadmap `docs/architecture/10-implementation-roadmap.md`.

**Recorded 2026-10-12:** D1 recommended eight-template catalogue is the selected direction. The nine-name alternative (retain Sales Manager) is **not selected**. Explicit key-by-key grants for Owner, Administrator, Salesperson, and Accountant remain **proposed** until approved. Documents 00–08 stay frozen until named-file edit authorization. Document 09 Appendix B item 6 remains the implementer rule until 05 and 07 are amended together.

---

## 0. CompleteSale / accounting posting — verification (not invented)

The roadmap places accounting posting in Phase 10 with CompleteSale. Documents 00–09 **already specify** the sale-completion rules below. They are **not** open for invention at coding time. Residual gaps are listed; they do **not** block Gate 1 role/contract work, but they **do** block Phase 10 implementation until closed or explicitly deferred to a CompleteSale addendum.

### 0.1 Specified: when a sale becomes completed

| Rule | Source |
|---|---|
| `POST /sales` creates **DRAFT**. Cart is not a completed sale. | 00 §6; 05 Sales |
| `POST /sales/{id}/confirm` is **CompleteSale**. Result status is **`COMPLETED`**. Do not persist lingering `CONFIRMED` / `PAID`. | 00 §6; 09 §8; 09 Appendix A |
| Confirm from POS requires `pos.create_sale`; from back-office requires `sales.create`. | 00 §11; 07 §4 / §8; 05 Permissions table |
| POS extra checks (not extra keys): membership, branch, terminal, **register open**, allowed tender, inventory/accounting rules. | 07 §7 |

### 0.2 Specified: transactional relationship of stock, payment, and journals

CompleteSale is **one synchronous DB transaction** (00 §6; 04 CompleteSale; 09 §8):

1. Auth, tenant, permission, register open (POS cash)
2. Load sale; status must be **DRAFT**
3. Recalculate totals (server)
4. Lock inventory (`SELECT … FOR UPDATE`); check availability
5. Persist **COMPLETED** + line snapshots
6. Record/validate payments (sum ≥ amount due; cash change is not revenue)
7. `inventory.issue_stock` + balances
8. `accounting.post_sale` — journals **must balance** or the step fails
9. Audit + **outbox** row (same COMMIT)
10. **COMMIT**

POS must not write inventory or journals. Sales owns Sale. Inventory and accounting are called through public contracts (`issue_stock`, `post_sale`). Celery is **not** on this path (email/PDF/analytics **after** commit). POS must work if workers are down (09 §27).

### 0.3 Specified: failure

If any critical step fails: **ROLLBACK**. Do not leave sale completed with stock unchanged, or payment recorded with sale still draft (09 §8). Domain error `ACCOUNTING_ENTRY_UNBALANCED` exists (05; 09 §10). Concurrent last-unit: loser gets `INSUFFICIENT_STOCK` (00 §5).

### 0.4 Specified: duplicate requests

`Idempotency-Key` is **required** on confirm, payment, receive, return/refund, transfer complete (00 §6; 05 headers; 09 §9 / §26). Same key + tenant → return the original result; no second movement or payment.

### 0.5 Specified: posting is synchronous

Inventory and journals are **not** async (00 §6). Internal events after commit are allowed; stock/accounting must not be made async (03). No client `POST /journal-entries` to record a sale (00 §8; 05 Accounting).

### 0.6 Residual gaps (amend or ask before Phase 10 — do not invent in code)

| Gap | Why it matters | Suggested home |
|---|---|---|
| Confirm pipeline wording: 00 records payments **inside** confirm; 05 says payments **already recorded / remaining cash**, then mark COMPLETED | Implementers could disagree whether `POST /sales/{id}/payments` is mandatory before confirm | Align 00 §6 and 05 “Confirm sale pipeline” in the same edit wave as Phase 10, or in this set if approved here |
| HTTP status when Idempotency-Key is **missing** on confirm | 00 says required; status code not named (422 vs 400) | 05 |
| Chart of accounts / which accounts `post_sale` debits and credits | 02 has `accounts` / `journal_lines`; 04 has `post_sale`; no seed mapping | 02 or 04 addendum before Phase 10 |
| Outbox payload contents | 00/09 require an outbox row; schema of the payload is not specified | 02 / 03 |
| Confirm **without** a prior payment row vs cash remaining on confirm | Split-tender vs remaining-cash-at-confirm | 05 |

**Gate 1 conclusion:** Phase 10 accounting posting is **architecturally specified** for transaction boundary, rollback, synchrony, and idempotency. It is **not** fully specified for COA mapping and a few API edge cases. Those are Phase 10 blockers, not role-catalogue blockers.

---

## 1. Purpose of this amendment set

Close roadmap **Gate 1 (Option A)** so later document edits can be authorized as a consistent set:

1. Exact eight-template catalogue and Sales Manager disposition
2. Five default tenant-owned role copies
3. Explicit permission grants for each default role (Document 07 keys only, plus `roles.view` proposed in this set)
4. Platform Administrator vs tenant Administrator
5. Business Owner POS **off** by default
6. `roles.view` vs `GET /roles` / `GET /permissions` / Document 09 Appendix B item 6
7. Required changes to Documents 00–09, identified per document

**Not in this set (explicitly deferred):** platform HTTP permission catalogue activation; tenant lifecycle states beyond 02 `ACTIVE|SUSPENDED|ARCHIVED`; provisioning API; alerts/billing; five-group navigation; `permissions.view`; `sales.override_price`; `receivables.create_payment` grants; supplier-invoice table; journal HTTP create/post; stock-count keys; optional-template explicit lists (Inventory Manager, Purchasing Officer, Viewer) beyond “do not default-provision.”

---

## 2. Decisions proposed for approval

None of the following is live until Documents 00 and 07 (and paired 05/06/09 as listed) are edited under separate authorization.

### D1 — Eight-template catalogue and Sales Manager

**Problem:** User selections name **Salesperson** and also retain an eight-template catalogue. Frozen 00/07 name **Sales Manager**, not Salesperson. Counting Business Owner, Administrator, Cashier, Salesperson, Accountant, Sales Manager, Inventory Manager, Purchasing Officer, and Viewer yields **nine** names. Do not drop Viewer, Purchasing Officer, or Inventory Manager arbitrarily to force a count of eight.

**Proposed resolution (recommended):** **Replace** the frozen name **Sales Manager** with **Salesperson** as the selling-floor template. Do **not** retain Sales Manager in this catalogue. A later supervisory “Sales Manager” template would be a **new** catalogue entry requiring its own explicit grants and an amendment to the count.

**Catalogue of eight templates (proposed):**

| # | Template name | Default-provisioned? |
|---|---|---|
| 1 | Business Owner | Yes |
| 2 | Administrator (tenant) | Yes |
| 3 | Cashier | Yes |
| 4 | Salesperson | Yes |
| 5 | Accountant | Yes |
| 6 | Inventory Manager | No — catalogue only |
| 7 | Purchasing Officer | No — catalogue only |
| 8 | Viewer | No — catalogue only |

Platform Administrator is **not** a tenant template (see D4).

**Alternative (not selected, 2026-10-12):** Keep **both** Salesperson and Sales Manager. Amend “exactly eight” to **nine** templates. Documented only; **not** the recorded catalogue.

**Recorded selection:** D1 recommended eight-name table above. **Until frozen documents are authorized and edited, Document 07’s eight names including Sales Manager remain canonical.**

### D2 — Default tenant-owned copies

At provisioning (once that contract exists) and at bootstrap of the first tenant, copy **only** these five templates into **tenant-owned** roles:

1. Business Owner  
2. Administrator  
3. Cashier  
4. Salesperson  
5. Accountant  

Copies are snapshots. Global template edits must not silently change existing tenant roles. Tenant users are assigned **tenant-owned** roles only, never the global template row. Tenants still **cannot** create roles or edit role-permission assignments (00 §11 / 07 §3), unless a later amendment says Platform Admin may edit tenant copies — **not decided here** beyond: tenant Business Owner / tenant Administrator assign users to existing copies only (`users.assign_roles` + `roles.view`).

### D3 — Business Owner POS off by default

Amend 07 §7 so Business Owner is **not** granted any `pos.*` keys by default. POS may be added later only by an explicit, authorized, audited grant change (platform-managed template/copy edit — itself not fully contracted in this set).

This **overrides** 07 §6 “full tenant permissions” **only** for POS keys. Owner remains protected (cannot be assigned/removed via ordinary `users.assign_roles`).

**Do not conflate** the protected **Owner identity/account** with the **Business Owner role**. The identity is unique and protected; the role is the tenant-owned copy of the Business Owner template.

Tenant **Administrator** retains POS keys as in the explicit Admin list below (frozen 07 Admin POS Full), unless a later decision turns Admin POS off as well. **Not proposed here.**

### D4 — Platform Administrator vs tenant Administrator

| Concept | Scope | Holds tenant 07 keys? | Holds `platform.*`? |
|---|---|---|---|
| **Platform Administrator** | `/platform/*` control plane: tenants, future provisioning, platform users, global templates, platform audit | No (not by this role) | Only after a future 07 platform catalogue is approved. **This set does not activate `platform.*` keys.** |
| **Tenant Administrator** | `/app/*` within one tenant | Yes — explicit Admin list | **Never** |

They are different identities and different role records. Bootstrap (when implemented) must create a platform admin identity **separate** from the tenant Owner identity (foundation D1). Tenant Administrator is a **role copy**, not the platform admin.

No tenant role, including Business Owner and tenant Administrator, may receive `platform.*`.

### D5 — `roles.view`; no `permissions.view`

**Proposed new tenant key (inactive until this set is applied to 07 + 05 together):**

- `roles.view` — list the **current tenant’s** assignable tenant-owned roles (`GET /roles`).

**Grants:** Business Owner and tenant Administrator only.

**Not added:** `permissions.view`.

**`GET /permissions` (Document 05):** mark **out of v1 / deferred**. Do not implement it. Do not invent a key for it.

**Supersedes** Document 09 Appendix B item 6 (“map `GET /roles` to `users.view`; do not add `roles.view`”) **once this amendment is applied**. Until then, 09 Appendix B item 6 remains the implementer rule.

**Assignment:** `POST /users/{id}/roles` remains `users.assign_roles`. The Users assign-roles UI requires **both** `users.assign_roles` and `roles.view`. Owner role id cannot be assigned or removed. `GET /roles` may include the Owner role for display of current assignment; the assign command still rejects that id.

---

## 3. Explicit grants for the five default roles

All keys below exist in Document 07 §4 except `roles.view` (proposed in D5). **Not granted to any tenant role:** `platform.*`, `permissions.view`, `sales.override_price`, `receivables.create_payment`, `inventory.count`.

`finance_transactions.create` and `finance_transactions.post` remain in the Owner/Admin/Accountant lists as 07 keys; **HTTP journal create/post stays blocked** (00 §8; 05 Accounting; prior D-14). That is not activation of client journal posting.

Cashier list is copied from 07 §7. Owner/Admin lists expand 07 “Full” minus the withholdings and Owner POS. Accountant expands 07 §6 literally; optional extra view keys are **not** granted in this set.

### 3.1 Business Owner (POS off)

`dashboard.view`

`sales.view` `sales.create` `sales.update` `sales.cancel` `sales.void` `sales.export` `sales.print`

`sales_returns.view` `sales_returns.create` `sales_returns.approve` `sales_returns.cancel` `sales_returns.refund`

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

`roles.view` *(proposed D5)*

`settings.business.view` `settings.business.update`

`branches.view` `branches.create` `branches.update` `branches.archive`

`tax.view` `tax.create` `tax.update` `tax.archive`

`currency.view` `currency.update`

`numbering.view` `numbering.update`

`audit.view` `audit.export`

**Explicitly absent:** every `pos.*` key; `receivables.create_payment`; `platform.*`; `permissions.view`; `sales.override_price`.

Protected: cannot be assigned/removed via `users.assign_roles`; ownership transfer remains a protected command (06 / 09 Appendix A) until 07 adds a key — **this set does not add `ownership.transfer`.**

### 3.2 Tenant Administrator

Same keys as Business Owner **plus** all POS keys:

`pos.view` `pos.create_sale` `pos.open_register` `pos.close_register` `pos.view_sessions` `pos.cash_in` `pos.cash_out` `pos.refund` `pos.reprint`

Same absences except POS. **Cannot** assign/remove Business Owner; **cannot** run ownership transfer. **No** `platform.*`.

### 3.3 Cashier (unchanged 07 §7 explicit list)

`dashboard.view`

`pos.view` `pos.create_sale` `pos.open_register` `pos.close_register` `pos.view_sessions` `pos.cash_in` `pos.cash_out` `pos.reprint`

`customers.view` `customers.create`

`products.view`

**Default absent:** `pos.refund`, `sales.view`, `sales.void`, `sales.export`, `sales_returns.refund`, all inventory/purchasing/expenses/finance/reports/users/settings/audit keys, `roles.view`.

### 3.4 Salesperson (proposed selling-floor — requires approval)

This list is **not** in Document 07 today. It is **not** a silent rename of Sales Manager Full (07 §6: sales+POS+customers full; products/inventory view; finance view/limited; reports sales). Selling-floor is proposed as Cashier POS **plus** back-office draft-sale and customer update, **without** finance, inventory mutation, users, settings, audit, or reports.

`dashboard.view`

`pos.view` `pos.create_sale` `pos.open_register` `pos.close_register` `pos.view_sessions` `pos.cash_in` `pos.cash_out` `pos.reprint`

`sales.view` `sales.create` `sales.update` `sales.cancel` `sales.print`

`customers.view` `customers.create` `customers.update` `customers.view_transactions`

`products.view`

**Default absent:** `pos.refund`; `sales.void`; `sales.export`; all `sales_returns.*`; inventory/purchasing/expenses/finance; `reports.*`; users/settings/audit; `roles.view`.

**If reviewers instead want Salesperson = frozen Sales Manager compact cell,** reject §3.4 and require a Full/View expansion of 07 §7 Sales Mgr **before** seeding. Do not seed “Sales Manager Full” from shorthand.

### 3.5 Accountant (07 §6 + recorded AP grant; not Finance Full)

`dashboard.view`

`sales.view`

`customers.view`

`products.view`

`inventory.view`

`suppliers.view` `purchase_orders.view` `goods_receipts.view` `purchase_returns.view`

`expenses.view` `expenses.create` `expenses.update` `expenses.approve` `expenses.cancel` `expenses.export`

`finance_accounts.view` `finance_accounts.create` `finance_accounts.update` `finance_accounts.archive`

`finance_transactions.view` `finance_transactions.create` `finance_transactions.post` `finance_transactions.void`

`payments.view` `payments.create` `payments.void` `payments.refund`

`receivables.view` `receivables.export`

`payables.view` `payables.create_payment` `payables.export`

`reports.finance.view`

`audit.view`

**Absent:** all POS keys; sales mutations/export/print; inventory adjust/transfer/receive; purchasing mutations; users/settings; `roles.view`; `receivables.create_payment`; `platform.*`; `reports.sales.view`; `reports.export` (07 reports cell is Finance, not Full).

**Not granted in this set (optional view keys — 07 “view” does not automatically include sibling resources):** `product_categories.view`, `brands.view`, `units.view`, `inventory.view_movements`, `sales_returns.view`. Approve separately if Accountant must open those screens.

### 3.6 Catalogue-only templates (Inventory Manager, Purchasing Officer, Viewer)

**Not default-provisioned.** Do **not** seed them from Full/Limited/View shorthand (09 Appendix B item 2). Copying them is blocked until each has an approved explicit key list. That work is **out of Gate 1** except the catalogue names in D1.

---

## 4. Proposed changes by document (for later authorized edits)

No files in 00–09 are modified by creating this proposal.

### 4.1 Document 00 — `00-frozen-decisions.md`

| Section | Proposed change |
|---|---|
| §6 CompleteSale vs 05 pipeline | Optional in this wave: one sentence that confirm **validates draft tenders already attached** and records any remaining cash in the same transaction; payments on DRAFT via `POST /sales/{id}/payments` remain the normal path |
| §10 | State Platform Administrator ≠ tenant Administrator ≠ Owner identity; `platform.*` never on tenant roles; bootstrap is not public signup |
| §11 | Replace “exactly these eight” system-role names with the D1 eight **templates**; tenants receive **copies**; they assign copies, not global templates; no tenant permission editor |
| §11 | Business Owner default grants exclude `pos.*` |
| §14 Out of v1 | Keep custom tenant role designer out of v1; platform-managed global templates are **not** a tenant designer. Do not describe template copy as tenant-editable permissions |

### 4.2 Document 01 — `01-system-requirements-and-domain.md`

| Section | Proposed change |
|---|---|
| Roles list (~line 230) | Remove Manager / Inventory Clerk; align names with D1 |
| Settings screens (~line 339) | Remove tenant **Roles** admin screen; users assign existing roles only |

### 4.3 Document 02 — `02-database-schema.md`

| Section | Proposed change |
|---|---|
| Identity & access `roles` | Distinguish **global role templates** (`tenant_id` null, not assignable) from **tenant-owned copies** (`tenant_id` set, `copied_from_template_id`, source version). Lineage is not live inheritance |
| `tenant_user_roles` | May reference tenant-owned roles only |
| CompleteSale COA | **Not in Gate 1** — flag for Phase 10 addendum |

Do **not** add billing, alerts, or provisioning-run tables in Gate 1.

### 4.4 Document 03 — `03-technical-architecture.md`

| Section | Proposed change |
|---|---|
| Access / platform ≠ tenant admin | One sentence: platform Administrator and tenant Administrator are distinct |
| Else | No stack or module-layout change required for Gate 1 |

### 4.5 Document 04 — `04-application-module-design.md`

| Section | Proposed change |
|---|---|
| Authorization module | Owns global templates, tenant copies, `authorize()`; never `if role ==` |
| Tenant module | Bootstrap/create tenant does not imply provision-complete until a later provisioning spec |
| Build sequence | Already defers to 00 for first code slice — no phase reorder |

### 4.6 Document 05 — `05-api-contract.md`

| Section | Proposed change |
|---|---|
| Tenant / users / roles | `GET /roles` → `roles.view`; returns current tenant’s tenant-owned roles only |
| | `GET /permissions` → **deferred / not v1** |
| | `POST /users/{id}/roles` → `users.assign_roles`; cannot assign/remove Owner |
| Confirm sale pipeline | Align with 00 §6 (draft payments + remaining cash + stock + journals + COMPLETED, one transaction) |
| Permissions table | Add `GET /roles` → `roles.view` |
| Missing Idempotency-Key | Optional: 422 `VALIDATION_ERROR` when required header absent |

No platform HTTP routes in this set.

### 4.7 Document 06 — `06-security-and-authorization.md`

| Section | Proposed change |
|---|---|
| Roles (v1) | Replace list with D1 templates + copy model; Platform Administrator vs tenant Administrator |
| Permissions examples | Delete stale identifiers (`users.invite`, `sales.confirm`, `reports.financial.view`, `ownership.transfer` as a seeded key). Point to 07 |
| Starter role matrix | Replace Manager / optional Accountant POS with D1 names; Owner POS off |
| Platform vs tenant | No mixing; no `platform.*` on tenant roles; platform keys still **not** activated in 07 by this set |

### 4.8 Document 07 — `07-permission-matrix-and-screens.md` (primary)

| Section | Proposed change |
|---|---|
| Header | After amendment, this document still wins on keys, role **template** names, screen entry, no tenant role editor |
| §3 | No tenant Roles/Permissions screens; Users assign roles using `roles.view` + `users.assign_roles` |
| §4 Users | Add `roles.view`. Do not add `permissions.view`. Note `roles.view` inactive until 05 row exists (apply together) |
| §6 | Replace eight system roles with D1 eight templates; describe copy-on-provision; Owner POS off; Salesperson not Sales Manager |
| §7 | Replace compact Full/Limited **for the five defaults** with the explicit lists in §3 of this proposal; POS row: Owner —; Admin Full; Salesperson and Cashier as listed |
| §7 | State optional templates are not seeded from shorthand |
| §8 | `GET /roles` → `roles.view` |
| §9 | Keep “no tenant-editable designer”; platform may maintain global templates (future API) |

### 4.9 Document 08 — `08-ui-design-tokens.md` + `tokens.css`

**No change.**

### 4.10 Document 09 — `09-implementation-specification.md`

| Section | Proposed change |
|---|---|
| §13 / §14 roles | Eight templates per D1; Owner POS off; `roles.view` in registry after 07+05 apply |
| §30 Seeds | Seed 07 keys including `roles.view` only after activation; seed five default copies not eight live tenant roles; do not seed optional templates until explicit lists exist; do not seed `platform.*` or `permissions.view` |
| Appendix A | Update platform-keys row: still do not invent/activate `platform.*` in this wave |
| Appendix B item 2 | For the five defaults, explicit lists in amended 07 replace Full/Limited |
| Appendix B item 6 | **Supersede:** `GET /roles` uses `roles.view`; `GET /permissions` deferred |

---

## 5. Apply order (only after explicit edit authorization)

1. Document 07 (keys, templates, explicit grants, Owner POS, `roles.view`)  
2. Document 00 §10–§11 (and optional §6 confirm wording)  
3. Document 05 (`GET /roles`, defer `GET /permissions`, confirm pipeline)  
4. Document 06 (stale examples, Admin split, Owner POS)  
5. Document 02 (`roles` template vs copy columns only)  
6. Document 04 / 03 as needed  
7. Document 01 stale names/screens  
8. Document 09 seeds and Appendix B  
9. Cross-document consistency pass (register Gate 4)  
10. **Separate** implementation authorization (roadmap Gate 3)

`roles.view` must not appear in seeds or route guards until steps 1 and 3 are both applied.

---

## 6. Consistency checks after approved edits

- Catalogue contains **eight** names and **no** Sales Manager **or** nine names with Sales Manager explicitly retained (D1 must not stay ambiguous).
- Default copies are exactly the five listed.
- Business Owner seed has **zero** `pos.*`; POS route and `pos.create_sale` 403 for default Owner.
- Tenant Administrator has no `platform.*`.
- `GET /permissions` is not a live v1 route.
- `GET /roles` is tenant-scoped and requires `roles.view`.
- Cashier list matches 07 §7 (no extra keys).
- `receivables.create_payment` ungranted.
- CompleteSale text in 00 and 05 does not disagree on payment timing.
- Document 08 unchanged.

---

## 7. Approval checklist

- [x] D1 recommended recorded (Salesperson replaces Sales Manager; eight names as tabled). Nine-name alternative **not selected**. Frozen 07 unchanged until edit authorization.
- [x] D2 five default copies recorded
- [x] D3 Owner POS off recorded (not yet in Document 07)
- [x] D4 platform vs tenant Administrator recorded; `platform.*` inactive
- [x] D5 `roles.view` yes; `permissions.view` no; `GET /permissions` deferred — recorded; inactive until 05+07 amended together
- [ ] §3.1–§3.5 grant lists (especially Salesperson §3.4 and Accountant optional view keys)
- [ ] Phase 10 addendum: `post_sale` COA, 00 vs 05 payment timing, missing Idempotency-Key status
- [ ] Authorize **named** frozen-file edits (this file does not)
- [ ] Consistency pass
- [ ] Separate implementation authorization

---

## 8. Stop line

This proposal does **not** edit Documents 00–09, does **not** activate `roles.view` in code, and does **not** authorize scaffolding or application implementation. Catalogue and boundary resolutions are recorded in the decision register §9. Next step: approve remaining key-by-key grants, then authorize specific document edits.
