# Ameen Retail — Accounting Design and Controls

**Status:** Proposal. Not an implementation authorization. Not an amendment to Documents 00–09, the roadmap, or the decision register.
**Date:** 2026-10-14
**Path:** `docs/architecture/proposals/2026-10-14-accounting-design-and-controls.md`

This document designs the accounting subsystem so inventory, POS completion, returns, purchasing, and financial reporting can post correctly inside the phases that already exist. It does not add a roadmap phase, seed a chart of accounts, or treat any unresolved policy as approved.

**Decision labels used below**

| Label | Meaning |
|---|---|
| Established | Already binding in Documents 00–09, the accepted foundation, or the current code. |
| Proposed | A design default in this file. Safe to implement only after the owner approves it. |
| Requires owner approval | The pack is silent or in conflict. Coding must wait. |

Where this file recommends an account, a tax treatment, or a new permission, that recommendation is **requires owner approval**. Illustrative journal tables use **account roles**. They are not an approved chart of accounts.

---

## 0. What was inspected

### 0.1 Documents and registers

| Source | What it already decides |
|---|---|
| `00-frozen-decisions.md` | Double-entry; balanced post or no post; `accounting.post_*`; no client journal command for a sale; expenses in product v1; `NUMERIC(19,4)`; UTC storage and tenant-local business dates; weighted average; CompleteSale steps; payable from receipt; no POS store credit. |
| `01-system-requirements-and-domain.md` | Accounting records journals for other modules. COGS is quantity times inventory cost. Gross-profit wording still needs a policy. Returns change stock only for sellable condition. |
| `02-database-schema.md` | Sketches `accounts`, `accounting_periods`, `journal_entries`, `journal_lines`, `tax_rates`, `expenses`, `currencies`. No account-role seed. No `account_balances` table. |
| `03-technical-architecture.md` | Journals are synchronous. Posted journals are reversed, never deleted. |
| `04-application-module-design.md` | Accounting owns the chart, journals, and periods. Named operations include `post_sale`, `post_purchase`, `post_expense`. |
| `05-api-contract.md` | Read paths for accounts, journal entries, general ledger, and trial balance. `GET /reports/profit-loss`. Error code `ACCOUNTING_ENTRY_UNBALANCED`. One approved amendment: `METHOD_NOT_ALLOWED` at HTTP 405. |
| `06-security-and-authorization.md` | Posted financial records are reversed. Refund, stock, payment, and audit share one transaction. |
| `07-permission-matrix-and-screens.md` | Finance, expense, payable, receivable, tax, currency, and report keys. Sale posting stays inside CompleteSale. |
| `08-ui-design-tokens.md` | Visual tokens only. No accounting rules. |
| `09-implementation-specification.md` | Required contracts: `post_sale`, `post_purchase`, `post_payment`, `reverse_posting`. CompleteSale rollback includes the journal. |
| Decision register | §9.4 leaves the sale chart, payment timing, and missing idempotency status open. §10–§12 accept foundation work through roadmap Phase 3 only. |
| `10-implementation-roadmap.md` | Posting is inside Phase 10, reversal inside Phase 11, purchase posting inside Phase 12, finance screens inside Phase 13. |

### 0.2 What is implemented

Accepted through roadmap Phase 3. Roadmap Phase 4 and later are not authorized.

| Present | Absent |
|---|---|
| Empty PostgreSQL schema `accounting` | `accounts`, `accounting_periods`, `journal_entries`, `journal_lines` |
| `MoneyField` / `money()`: `NUMERIC(19,4)`; float rejected; more than four decimal places rejected | A rounding policy for tax or weighted-average division |
| `system.idempotency_keys`, unique `(tenant_id, key)` | A unique key from a business document to its journal |
| `run_in_transaction` | `post_sale` and the other accounting contracts |
| Append-only `audit.audit_logs` | Journal immutability enforcement |
| Permission catalogue rows for finance, expenses, payables, and `reports.finance.view` | Accounting screens, routes, and seeds |
| `ACCOUNTING_ENTRY_UNBALANCED` mapped to HTTP 500 in the foundation error table | Currencies table; `tenants.default_currency_id` is a nullable UUID with no foreign key |
| | Outbox table (register §12.3). `document_sequences` (register §12.4) |

No application module posts a journal today. A design file does not make the subsystem complete or production-ready.

### 0.3 Minimum capability and what waits

The roadmap already puts the posting engine in Phase 10. Phase 13 is the read model and the expense workflow. This proposal keeps that split.

| Needed before the first completed sale | Fits the later phase already named | Outside the current contracts |
|---|---|---|
| Chart roles required by a sale, opening stock, and adjustments | Expense approval and `post_expense` (Phase 13) | Client `POST /journal-entries` (D-14) |
| Balanced compound journal, source link, idempotency, immutability | Purchase receipt, purchase return, payable (Phase 12) | Supplier payment API until D-12 and D-13 |
| `post_sale` in the CompleteSale transaction | Return and void reversal (Phase 11) | POS store credit and receivables |
| Opening and adjustment journals so inventory value matches the ledger | `GET` accounts, journals, general ledger, trial balance, profit and loss (Phase 13) | Formal cash-flow statement, year-end close, foreign exchange |
| One open accounting period and a posted-only trial balance check | Full chart administration UI (Phase 13; roadmap section G defers it from the first release) | Period close UI until a permission amendment exists |

---

## 1. Accounting principles

### 1.1 Double-entry bookkeeping

**Established.** Every posted journal balances: the sum of debit amounts equals the sum of credit amounts. An unbalanced journal does not post. Sales, purchasing, expenses, payments, and inventory call an accounting contract. They do not update ledger balances themselves.

**Proposed.** Each business event creates one compound journal inside the same database transaction as the business document. Revenue and cost of goods sold for one sale are lines of that same journal, so a failure cannot leave revenue posted without cost.

Document 02 does not define an `account_balances` table. **Proposed:** posted `journal_lines` are the general ledger. Reports sum those lines. If a materialized balance is added later, only the accounting module may write it, in the same transaction as the journal.

### 1.2 Debit and credit conventions

**Established.** Account type is `ASSET`, `LIABILITY`, `EQUITY`, `REVENUE`, or `EXPENSE`. The `accounts` sketch includes `normal_balance`.

**Proposed.** Normal balances follow the type. A contra account keeps its statement type and uses the opposite normal balance.

| Type | Normal balance | Increases by | Decreases by |
|---|---|---|---|
| Asset | Debit | Debit | Credit |
| Expense | Debit | Debit | Credit |
| Liability | Credit | Credit | Debit |
| Equity | Credit | Credit | Debit |
| Revenue | Credit | Credit | Debit |

A journal line carries a non-negative debit or a non-negative credit, never both, and never a negative amount. A reversal is a new journal that swaps the sides. It is not a negative line on the original.

### 1.3 Accrual accounting and revenue recognition

**Established.** A draft sale is not revenue. CompleteSale is the moment stock, payment, and the journal commit together. Cash change is not revenue. A purchase order does not create inventory or a payable. The goods receipt does. Store credit and accounts receivable are outside POS v1.

**Proposed.** Ameen Retail uses accrual accounting.

| Event | Recognition |
|---|---|
| Completed POS or back-office sale | Revenue, tax liability, discount, tender, and cost of goods sold at completion, when control of the goods passes at the register |
| Card, mobile-money, and bank-transfer tenders | Revenue at completion. Settlement of the processor or bank is a later cash movement, not the revenue event |
| Draft sale, draft return, unapproved expense | No journal |
| Goods receipt | Inventory and supplier liability at receipt |
| Supplier payment | Reduces the liability when the payment use case exists. It does not recognize the purchase |
| Sellable sales return or void | Reverses the earned portion in the return or void transaction |
| Operating expense | When the expense is approved (Phase 13), for the approved amount |

Accounting posts the sale snapshot. It does not run a second price, discount, or tax calculation. If the snapshot cannot produce a balanced journal, CompleteSale rolls back.

### 1.4 Monetary precision, currency, and rounding

**Established.**

- Stored money and the API use `NUMERIC(19,4)` and decimal strings.
- `money()` rejects floats, non-finite values, and scales beyond four decimal places. It does not round extra scale away.
- A sale stores `currency`. A payment sketch stores `currency_id`. The currencies table is not implemented.
- Document 09 names `USD`, `SOS`, and `EUR` as currency-seed examples, not as permission to run three currencies in one tenant.

**Proposed, and required before Phase 10 posts money.**

| Rule | Default |
|---|---|
| Books of account | One currency per tenant, the tenant default. Journals reject any other currency |
| Journal amounts | Exactly four decimal places before they reach `money()` |
| Tax and extended cost | Quantize with half-up to four places in the sales or inventory calculation. Accounting posts those quantized amounts and does not quantize them differently |
| Weighted-average remainder | `stock_value` is authoritative. The last unit issued from a balance takes the remaining value so the subledger can reach zero. Section 5 states the steps |
| Balance tolerance | None. A difference of `0.0001` is unbalanced |
| Foreign exchange | Deferred. No gain or loss accounts until a later decision |

Changing `money()` so that it rounds, instead of rejecting extra scale, is a change to accepted Phase 3 behavior. This proposal does not ask for that change.

### 1.5 Accounting dates, timestamps, and fiscal periods

**Established.** Database timestamps are `timestamptz` UTC. “Today” for a business report is the tenant’s local calendar day. Journal sketches include `entry_date`, `posted_at`, and `accounting_periods` (`name`, `start_date`, `end_date`, `status`). Period status values are not defined.

**Proposed.**

| Field | Rule |
|---|---|
| `entry_date` | A date. For a system posting it is the tenant-local calendar date of the business event (`order_date`, receipt date, return date, expense date). The client does not choose it |
| `posted_at` | UTC timestamp of the successful post |
| Period | `entry_date` must fall inside a period with status `OPEN` |
| First release | Seed monthly periods for the current local year, all `OPEN`. No close command until section 7’s permission amendment is approved |
| Fiscal year | Profit and loss uses `date_from` and `date_to`. A fiscal-year start month can wait |
| Backdating | A system document uses its event date. A closed period rejects the post. Section 7 covers corrections |

---

## 2. Chart of accounts

### 2.1 Accounts

**Established sketch.** `id`, `tenant_id`, `parent_id`, `code`, `name`, `account_type`, `normal_balance`, `is_active`.

**Proposed constraints**, to be written into Document 02 when an amendment is authorized:

| Rule | Purpose |
|---|---|
| `UNIQUE (tenant_id, code)` | Stable codes |
| Posting only to an active account with no children | Headers group reports; lines hit leaves |
| `normal_balance` is `DEBIT` or `CREDIT` | Enforces section 1.2 |
| Inactive accounts reject new lines | History stays readable |
| Code and type do not change after a line has been posted | Corrections use a new account and a mapping change, not a rewrite |

### 2.2 Control accounts and direct posting

**Established.** Clients do not post a sale by creating a journal. `finance_transactions.create` and `finance_transactions.post` exist in Document 07 and have no approved HTTP command (decision D-14).

**Proposed.** Seeded roles below are control accounts. `allows_manual_posting = false`. Operational modules post them only through accounting contracts. A future manual journal, if D-14 is approved, cannot use those accounts. That flag is not in Document 02; section 12 lists the amendment.

Roles are stable identifiers inside accounting. Display codes are data. Neither the codes nor the role list is approved.

### 2.3 Tenant accounts and default mappings

**Established.** Every account belongs to one tenant. Register §9.4 requires the exact accounts used by `post_sale` before that contract is finalized. No seed exists.

**Proposed default chart.** Codes are illustrative so reviewers can see a minimal retail ledger. Approval of this table is approval of register §9.4’s accounting item. Until then, do not seed it.

| Code | Role key | Name | Type | Normal balance | Manual posting |
|---|---|---|---|---|---|
| 1000 | `cash_on_hand` | Cash on hand | Asset | Debit | No |
| 1010 | `card_clearing` | Card clearing | Asset | Debit | No |
| 1020 | `mobile_money_clearing` | Mobile-money clearing | Asset | Debit | No |
| 1030 | `bank` | Bank | Asset | Debit | No |
| 1090 | `other_tender_clearing` | Other tender clearing | Asset | Debit | No |
| 1200 | `inventory` | Inventory | Asset | Debit | No |
| 2000 | `accounts_payable` | Accounts payable | Liability | Credit | No |
| 2100 | `sales_tax_payable` | Sales tax payable | Liability | Credit | No |
| 3000 | `opening_balance_equity` | Opening balance equity | Equity | Credit | No |
| 4000 | `sales_revenue` | Sales revenue | Revenue | Credit | No |
| 4010 | `sales_discounts` | Sales discounts | Revenue | Debit | No |
| 4020 | `sales_returns` | Sales returns | Revenue | Debit | No |
| 5000 | `cogs` | Cost of goods sold | Expense | Debit | No |
| 5100 | `inventory_shrinkage` | Inventory shrinkage | Expense | Debit | No |
| 6000 | `operating_expense` | Operating expense | Expense | Debit | No |

`sales_discounts` and `sales_returns` are contra-revenue: type `REVENUE`, normal balance `DEBIT`.

**Proposed mapping rules.**

- A required role used by an active feature points at exactly one active leaf account.
- Expense categories may later point at their own expense leaves. Until category mapping is approved, approved expenses use `operating_expense`.
- Changing a mapping affects later postings only. Posted lines keep the account they used.
- A mapping cannot be pointed at an inactive account, a header, or an account of the wrong normal balance.
- The `other` tender uses `other_tender_clearing` so an unmapped method cannot be posted to cash or revenue.

Tenant-created accounts, once `finance_accounts.create` is exposed in Phase 13, are additional leaves. They do not replace a control role unless an authorized user changes the mapping.

### 2.4 Opening balances and configuration governance

**Established.** Inventory opening stock is a movement of type `OPENING_BALANCE`, with a cost. There is no general-ledger opening-balance document in the pack.

**Proposed.**

| Opening item | Treatment | When |
|---|---|---|
| Opening inventory value | Debit `inventory`, credit `opening_balance_equity`, for the movement’s extended cost | Same transaction as the movement once accounting exists; catch-up before the first sale if Phase 9 wrote movements earlier (section 5) |
| Opening cash in the drawer | Remains a POS session figure until a cash-variance policy is approved (section 6) | Not a journal in the first posting slice |
| Opening payables, receivables, loans, and owner capital | Deferred | No document supports them |
| Chart edits | `finance_accounts.view`, `create`, `update`, `archive` | Phase 13 UI. Archive means `is_active = false`, not a delete |
| Who may edit | Document 07 gives Finance “Full” to Owner, Administrator, and Accountant | Explicit key lists remain register D-06. Register §10.1 says later identity work uses the frozen matrix. This proposal does not expand grants |

---

## 3. Journal and general ledger

### 3.1 Headers and lines

**Established sketch.**

- Header: `entry_number`, `entry_date`, `description`, `reference_type`, `reference_id`, `status`, `posted_by`, `posted_at`, `created_at`, `tenant_id`.
- Line: `journal_entry_id`, `account_id`, `debit`, `credit`, `description`.
- Human numbers are unique per `(tenant_id, document_type, number)` and come from `document_sequences`. That table is specified and not yet built.

**Proposed header and line rules.**

| Item | Rule |
|---|---|
| Identity | UUID primary key. Public number from `document_sequences`, document type `JOURNAL`, prefix `JE` |
| Lines | At least two. Each line has exactly one of debit or credit greater than zero |
| Currency | Header stores the tenant currency. Every line is in that currency |
| Branch | Header stores `branch_id` when the source document has a branch, so a branch-scoped user can be filtered without joining every source type |
| Tenant on lines | `journal_lines.tenant_id` is required, matching Document 00’s rule for every tenant-owned row |
| Actor | `posted_by` is the authenticated user of the business command. System catch-up records that user as well. The client does not send it |
| Description | Server-built from the document type and human number |

`branch_id`, line `tenant_id`, and header currency are not in the Document 02 sketch. Section 12 lists them as amendments. They are not permission to add the columns now.

### 3.2 Draft, posted, and reversed

**Established.** Status exists on the header. Posted financial documents are not deleted. Document 03: reverse a posted journal. Expense lifecycle is `DRAFT → APPROVED → PAID`.

**Proposed status set:** `DRAFT`, `POSTED`.

| Origin | Status behavior |
|---|---|
| CompleteSale, receipt, return, void, opening stock, adjustment, approved expense | Inserted as `POSTED` in the business transaction. These flows do not leave a draft journal |
| Expense before approval | No journal |
| Future manual journal (D-14) | May exist as `DRAFT` until `finance_transactions.post`. Out of scope until that decision |

A reversal does not change the original amounts or accounts. The original stays `POSTED`. The new header stores `reversal_of_id`. Reports and duplicate checks treat a journal that has a reversal as reversed. `finance_transactions.void` means “create the reversing journal,” once that command is specified. It does not mean SQL `DELETE` or an update of the amounts.

### 3.3 Balance validation

**Established.** The application checks the sums before post. The code `ACCOUNTING_ENTRY_UNBALANCED` exists. The foundation maps it to HTTP 500.

**Proposed check, in order, inside the posting transaction:**

1. Resolve roles through the tenant mapping. Missing, inactive, or header accounts fail.
2. Reject a line with both sides set, neither side set, or a negative amount.
3. Compare debit and credit sums as `NUMERIC(19,4)` with no tolerance.
4. Reject an `entry_date` outside an `OPEN` period.
5. Insert header and lines as `POSTED` only when all checks pass.
6. On failure, roll back the business transaction.

For a system-generated journal, imbalance is a defect in the server calculation. HTTP 500 matches the current foundation mapping and is appropriate there. A future manual draft should return 422 `VALIDATION_ERROR` and remain unposted. That split needs a Document 05 note when manual journals are specified.

### 3.4 Source documents and traceability

**Proposed.** Every system journal stores:

| Field | Example |
|---|---|
| `reference_type` | `sales_order`, `sales_return`, `purchase_receipt`, `purchase_return`, `inventory_movement`, `expense`, `supplier_payment` |
| `reference_id` | UUID of that document or movement |
| `posting_event` | `SALE`, `SALE_VOID`, `SALE_RETURN`, `PURCHASE_RECEIPT`, `PURCHASE_RETURN`, `OPENING`, `ADJUSTMENT`, `EXPENSE`, `SUPPLIER_PAYMENT` |

The general-ledger read model returns these fields so an authorized user can open the source document. Drill-down also requires the source module’s view permission. A finance view does not bypass branch scope.

### 3.5 Immutability

**Established.** No delete of completed sales, payments, journals, or movements. Audit rows are append-only in the current code.

**Proposed.** Posted headers and lines reject update and delete in the application, and a database rule rejects both for `POSTED` rows. Allowed later writes on a posted header are limited to the reversal link, set in the same transaction that inserts the reversing journal. Corrections are new journals. Audit history records `accounting.journal_posted` and `accounting.journal_reversed` with the journal id, source reference, and entry number. Audit payloads omit card numbers and tokens.

### 3.6 Corrections

| Situation | Mechanism | Permission |
|---|---|---|
| Sale recorded in error and still fully outstanding | `POST /sales/{id}/void`. `reverse_posting` swaps every line | `sales.void` |
| Goods come back, or a partial commercial reversal | New return document and a new journal for the returned amounts | `sales_returns.*` as granted |
| Purchase receipt that is `RECEIVED` | Purchase return. The receipt is not cancelled | Purchasing return permissions |
| Posted expense | `expenses.cancel` creates a reversing journal | `expenses.cancel` |
| Wrong account on a posted line | Reversing journal plus a replacement journal. The original line stays | Business command, or a future finance void |
| Closed period | Section 7. The period is not reopened by the cashier | No key exists yet |

`reverse_posting` is the full swap of one existing journal. A partial return is a new posting calculated from the return snapshot and the original movement cost. It is not a partial edit of the sale journal.

### 3.7 Idempotency and duplicate posting

**Established.** `Idempotency-Key` is required on confirm, payment, receive, return/refund, and transfer complete. The same tenant and key return the original response and do not create a second movement or payment. Uniqueness is `(tenant_id, key)`. The HTTP status for a missing key is still register §9.4.

**Proposed.**

| Layer | Rule |
|---|---|
| HTTP idempotency | The business command stores its response under the existing idempotency table. Replaying the key does not call `post_*` again |
| Accounting uniqueness | `UNIQUE (tenant_id, reference_type, reference_id, posting_event)` |
| Second confirm of a completed sale | `SALE_ALREADY_COMPLETED`, even with a new idempotency key |
| Second void | `SALE_ALREADY_VOIDED` |
| Concurrent duplicate | The unique index makes one transaction succeed. The other rolls back |

**Proposed default for the missing key:** HTTP 422, code `VALIDATION_ERROR`, field `Idempotency-Key`. This remains owner approval because §9.4 is open. Void is not in the frozen idempotency list. The state machine and the unique posting key still stop a double void. Adding the header requirement for void is a Document 00/05 amendment, listed in section 12.

---

## 4. Automatic accounting rules

### 4.1 How to read the tables

**Established inputs the journal must trust**

- Server-calculated subtotal, discount, tax, total, paid amount, and change.
- Tender types `cash`, `card`, `mobile_money`, `bank_transfer`, and `other`.
- Inventory movement cost. Cost of goods sold is never the selling price.
- Sale line snapshots. Completed sale lines stay as they were.
- Return quantity at or below the eligible remainder. Condition `GOOD` can return to sellable stock. `DAMAGED` / `UNSELLABLE` cannot.

**Assumptions used in every table until the owner decides otherwise**

| Topic | Assumption in the table | If the owner chooses differently |
|---|---|---|
| Account codes | Role names from section 2.3 | Remap roles. Do not change posted journals |
| Discount | Contra-revenue `sales_discounts` | Net method: credit `sales_revenue` for the amount after discount and omit the discount line |
| Sales tax | Credit `sales_tax_payable` for the snapshot `tax_amount` | A jurisdiction with no tax omits the line when the amount is zero |
| Tax base, inclusive versus exclusive | Whatever the tax module stored on the sale. Accounting does not reinterpret `is_inclusive` | A tax amendment may change the snapshot. It should not add a second computation in accounting |
| Input tax on purchases | Receipt `unit_cost` is the capitalized inventory amount. Accounts payable equals that amount | A recoverable-tax decision adds a debit to a tax-receivable role and includes tax in the payable. That role is not in section 2.3 |
| Card, mobile money, bank | Debit a clearing role, not `cash_on_hand` | Immediate deposit to `bank` is a possible simpler mapping and loses processor reconciliation |
| Cash change | The cash debit is the cash tender minus change | Change is never credited to revenue |
| `other` | Debit `other_tender_clearing` | Block the tender until a mapping exists |
| Cost | Extended cost from section 5 | A different costing method requires a frozen-decision change. FIFO is outside v1 |
| One event | One compound journal | Separate journals are acceptable only if they share the transaction and the same idempotency key |

Dependencies that are already open, and which these tables do not close: register §9.4 chart and payment timing, D-12, D-13, D-14, tax URLs, and the outbox schema.

### 4.2 Cash sale

Customer pays cash, possibly more than the amount due. Change reduces the cash debit.

Illustrative sale, tax exclusive, 5 percent of the discounted amount: gross `100.0000`, discount `10.0000`, tax `4.5000`, total due `94.5000`, cash tender `100.0000`, change `5.5000`, quantity `2`, unit cost `20.0000`.

| Role | Debit | Credit |
|---|---:|---:|
| `cash_on_hand` | 94.5000 | |
| `sales_discounts` | 10.0000 | |
| `sales_revenue` | | 100.0000 |
| `sales_tax_payable` | | 4.5000 |
| `cogs` | 40.0000 | |
| `inventory` | | 40.0000 |

Debits and credits both equal `144.5000`. Net cash equals the amount due. The `5.5000` handed back is not a line.

### 4.3 Card sale

Same commercial amounts, tender `card` for `94.5000`, no change.

| Role | Debit | Credit |
|---|---:|---:|
| `card_clearing` | 94.5000 | |
| `sales_discounts` | 10.0000 | |
| `sales_revenue` | | 100.0000 |
| `sales_tax_payable` | | 4.5000 |
| `cogs` | 40.0000 | |
| `inventory` | | 40.0000 |

Processor fees and the later deposit into `bank` are not part of CompleteSale. No fee account is proposed.

### 4.4 Mobile-money sale

Same pattern as the card sale. Debit `mobile_money_clearing` for the applied tender. Credit revenue, tax, and inventory, and debit discounts and cost, as in section 4.3.

### 4.5 Bank-transfer sale

Same pattern. Debit `bank` for the applied tender. This treats a bank-transfer tender as already in the tenant bank account when the sale completes. If the business later needs an uncleared-transfer account, add a role at that time. Do not overload `card_clearing`.

### 4.6 Split tender

**Established.** Split tenders are allowed. The sum applied must cover the amount due. Cash may produce change.

**Proposed.** One debit line per tender role for the amount of that tender that settles the sale. Cash uses tender minus change. Non-cash tenders do not produce change.

Example: amount due `94.5000`, cash applied `50.0000`, card applied `44.5000`. Commercial and cost lines match section 4.2.

| Role | Debit | Credit |
|---|---:|---:|
| `cash_on_hand` | 50.0000 | |
| `card_clearing` | 44.5000 | |
| `sales_discounts` | 10.0000 | |
| `sales_revenue` | | 100.0000 |
| `sales_tax_payable` | | 4.5000 |
| `cogs` | 40.0000 | |
| `inventory` | | 40.0000 |

### 4.7 Discounts, tax, and a zero-tender sale

Discount and tax are lines inside the sale journal, not separate documents.

When `tax_amount` is zero, omit `sales_tax_payable`. When `discount_amount` is zero, omit `sales_discounts`.

A fully discounted sale with no cash still posts, if the sales rules allow the discount:

| Role | Debit | Credit |
|---|---:|---:|
| `sales_discounts` | 100.0000 | |
| `sales_revenue` | | 100.0000 |
| `cogs` | 40.0000 | |
| `inventory` | | 40.0000 |

Document 01 describes gross profit as revenue minus cost of goods sold, discounts, and relevant returns. The contra accounts above keep those amounts visible. The net method would shrink revenue and make that sentence count discounts twice. The contra presentation is the recommended default and still requires approval.

### 4.8 Cost of goods sold

**Established.** Weighted average. Cost of goods sold equals quantity times inventory cost.

**Proposed.** The credit to `inventory` and the debit to `cogs` use the extended cost calculated in section 5 at the moment the sale movement is created. Both lines carry that same amount. A zero cost omits both lines and still posts the commercial lines.

### 4.9 Sales return — sellable

**Established.** The return is a new document. The original sale lines stay unchanged. Stock increases only when the condition is sellable.

**Proposed.** `posting_event = SALE_RETURN`. Amounts are the server’s return snapshot, proportional to the returned quantity. Inventory and cost use the **original sale movement’s unit cost**, not the current average. Section 5 then recomputes the average because value comes back at that historical cost.

Return half of the section 4.2 sale, condition `GOOD`: revenue `50.0000`, discount `5.0000`, tax `2.2500`, refund `47.2500`, cost `20.0000`. Refund tender follows section 4.11.

| Role | Debit | Credit |
|---|---:|---:|
| `sales_revenue` | 50.0000 | |
| `sales_tax_payable` | 2.2500 | |
| `sales_discounts` | | 5.0000 |
| `cash_on_hand` | | 47.2500 |
| `inventory` | 20.0000 | |
| `cogs` | | 20.0000 |

Both sides equal `72.2500`.

### 4.10 Sales return — damaged or unsellable

**Proposed.** Reverse revenue, tax, discount, and the refund. Do not debit `inventory` and do not credit `cogs`. No sellable movement is created. The original cost stays in cost of goods sold, which is the result of goods that cannot be resold.

| Role | Debit | Credit |
|---|---:|---:|
| `sales_revenue` | 50.0000 | |
| `sales_tax_payable` | 2.2500 | |
| `sales_discounts` | | 5.0000 |
| `cash_on_hand` | | 47.2500 |

This is an owner decision. The alternative, a non-sellable stock bucket plus a shrinkage journal, needs locations and accounts the v1 schema does not require.

### 4.11 Refunds

**Established.** `payments.refund_payment` runs inside the return transaction. `payments.refund` is a different key from `sales_returns.refund` and `pos.refund`.

**Proposed.**

| Case | Credit (the cash or clearing leaving the business) |
|---|---|
| Original sale had one tender | The same role as the original tender |
| Original sale was split | Refund in the original tender proportions unless a return tender is explicitly chosen by an approved rule |
| Refund amount | The return document’s `refund_amount`. Accounting does not accept a client refund total |

A refund without a return, or a refund above the unrefunded sale total, is rejected by the sales and payments rules before posting.

### 4.12 Void

**Established.** Void is allowed from `COMPLETED`, with `sales.void`, a reason, and an audit record. It is a different command from a return.

**Proposed.** `reverse_posting` of the sale’s `SALE` journal. `posting_event = SALE_VOID`. Stock comes back at the original movement costs through `SALE_RETURN`-typed movements or the void’s own movements, using those same costs, and the inventory lines of the reversal match them. A sale that already has a return is not voided; further quantities use returns. That restriction is proposed because the pack does not say whether void is allowed after a partial refund.

### 4.13 Inventory receipt and supplier liability

**Established.** `accounting.post_purchase` runs in the receipt transaction after `inventory.receive_stock`. The payable comes from the receipt. Partial receipt posts only the received quantities. `RECEIVED` is not cancelled.

**Proposed**, under the capitalized `unit_cost` assumption:

Receipt of quantity `10` at `20.0000`.

| Role | Debit | Credit |
|---|---:|---:|
| `inventory` | 200.0000 | |
| `accounts_payable` | | 200.0000 |

The payable’s open balance is a purchasing/payments fact. The ledger balance for `accounts_payable` must equal the sum of open receipt payables. A purchase order alone posts nothing.

### 4.14 Supplier payment

**Established.** The payment HTTP API waits on D-12 and D-13. Phase 12 can receive and post without that API. Payments, when they exist, target the payable or the receipt.

**Proposed, only after those decisions.** `post_payment` in the same transaction as the payment row.

| Role | Debit | Credit |
|---|---:|---:|
| `accounts_payable` | payment amount | |
| `bank` or `cash_on_hand` | | payment amount |

The credit role follows the payment method. Overpayment is rejected with `PAYMENT_EXCEEDS_BALANCE`. The payment does not change inventory.

### 4.15 Purchase return

**Established.** A purchase return reduces inventory and creates a supplier-side financial effect. It is the correction path for a received order.

**Proposed.** Reduce `accounts_payable` by the vendor credit on the return document. Reduce `inventory` by the extended cost from section 5 (current average, because weighted average has no purchase layers). Post any difference to `inventory_shrinkage`.

Example: vendor credit `20.0000`, current average extended cost `18.0000`.

| Role | Debit | Credit |
|---|---:|---:|
| `accounts_payable` | 20.0000 | |
| `inventory` | | 18.0000 |
| `inventory_shrinkage` | | 2.0000 |

If the average cost exceeds the vendor credit, `inventory_shrinkage` is debited for the difference. A cash refund from the supplier, once payments exist, debits `bank` or `cash_on_hand` instead of accounts payable for the cash portion.

### 4.16 Opening stock and adjustments

Opening movement, extended cost `200.0000`:

| Role | Debit | Credit |
|---|---:|---:|
| `inventory` | 200.0000 | |
| `opening_balance_equity` | | 200.0000 |

Adjustment out for damage, loss, expiry, theft, count correction, or other, extended cost `15.0000`:

| Role | Debit | Credit |
|---|---:|---:|
| `inventory_shrinkage` | 15.0000 | |
| `inventory` | | 15.0000 |

Adjustment in uses the opposite sides. One shrinkage account is the default. Splitting theft from expiry can wait.

`posting_event` is `OPENING` or `ADJUSTMENT`. `reference_id` is the inventory movement id so each movement posts once.

### 4.17 Warehouse transfer

**Proposed.** `TRANSFER_OUT` and `TRANSFER_IN` move the same extended cost between warehouses. The tenant-level `inventory` account does not change, so there is no journal. Section 5 keeps the subledger values equal and opposite. A future branch balance sheet would require a different decision and an amendment.

### 4.18 Operating expenses

**Established.** Expenses are in product v1. Posted expenses are cancelled or reversed, never deleted. Lifecycle `DRAFT → APPROVED → PAID`. Phase 13 owns the workflow. Roadmap section G defers expenses from the first release.

**Proposed.** `post_expense` runs when approval succeeds, not when the draft is saved.

| Role | Debit | Credit |
|---|---:|---:|
| `operating_expense` | approved amount | |
| `cash_on_hand`, `bank`, or `accounts_payable` | | approved amount |

The credit is `accounts_payable` when no settlement method is recorded. It is the cash or bank role when the expense is paid at approval. `PAID` then records settlement of a payable with `post_payment` and does not post the expense a second time. Cancel of a posted expense uses `reverse_posting`.

### 4.19 Register variance and cash in/out

**Established.** Close stores expected cash, actual cash, and variance. Sales figures stay as they were. Cash in and cash out require a reason and an audit record.

**Proposed default.** Those session events do not create journals in Phases 10 or 11. General-ledger cash will not equal the counted drawer, because the drawer includes opening float and paid-in/paid-out amounts. A reconciliation report must show both figures. Posting variance to `inventory_shrinkage` or to equity without a reason-to-account map would misstate profit. A later policy can add `cash_over_short` and map each cash-movement reason. That policy is Phase 13 work and needs an owner decision.

---

## 5. Inventory accounting

### 5.1 Weighted average and the ledger

**Established.**

- Balances are unique on `(warehouse_id, product_variant_id)`.
- Movements are immutable and store `unit_cost`.
- The balance stores unit cost and stock value.
- Average cost is per stock balance, which means per warehouse and variant.
- Negative stock is denied unless a later setting enables it.
- Movement types are `PURCHASE_RECEIPT`, `SALE`, `SALE_RETURN`, `PURCHASE_RETURN`, `ADJUSTMENT_IN`, `ADJUSTMENT_OUT`, `TRANSFER_IN`, `TRANSFER_OUT`, `OPENING_BALANCE`, and `STOCK_COUNT`.
- Quantity on hand is `NUMERIC(19,4)`.

**Proposed calculation.** `stock_value` and `quantity_on_hand` are the source of truth. `unit_cost` is the working average.

1. Inbound extended cost is quantized half-up to four decimal places before it is added. Opening, receipt, adjustment in, and transfer in use the document cost. A sellable customer return uses the original sale movement’s unit cost times quantity.
2. `stock_value = stock_value + inbound extended cost`. `quantity_on_hand` increases. `unit_cost = half-up(stock_value / quantity_on_hand, 4)`.
3. Outbound extended cost for a partial issue is `half-up(quantity * unit_cost, 4)`, and it cannot exceed `stock_value`.
4. An outbound that takes the entire remaining quantity uses the entire remaining `stock_value`, so the residual cents leave with the last unit.
5. After an outbound, subtract that extended cost from `stock_value`. Leave `unit_cost` unchanged. At zero quantity, set value and unit cost to zero.
6. The journal amount for that movement equals the extended cost applied to `stock_value`, except transfers, which post no journal.

Example. Opening value `10.0000` for quantity `3`. Working unit cost `3.3333`.

| Issue | Extended cost | Value remaining |
|---|---:|---:|
| 1 | 3.3333 | 6.6667 |
| 1 | 3.3333 | 3.3334 |
| 1 (clears the balance) | 3.3334 | 0.0000 |

Total cost issued is `10.0000`.

A sellable return of one unit that originally cost `3.3333` adds `3.3333` to `stock_value` and divides the new value by the new quantity to reset `unit_cost`.

### 5.2 Which movements post

| Movement | Ledger effect | Contract |
|---|---|---|
| `OPENING_BALANCE` | Debit inventory, credit opening-balance equity | Proposed `post_inventory`. Not in the Document 09 contract list |
| `ADJUSTMENT_IN` / `ADJUSTMENT_OUT` | Inventory and shrinkage | Proposed `post_inventory` |
| `SALE` | Credit inventory, debit cost of goods sold, inside `post_sale` | Established name |
| `SALE_RETURN` for `GOOD` | Debit inventory, credit cost of goods sold, at original cost | New return journal |
| Damaged return | No movement and no inventory lines | Section 4.10 |
| `PURCHASE_RECEIPT` | Debit inventory, credit accounts payable | `post_purchase` |
| `PURCHASE_RETURN` | Section 4.15 | Proposed extension of `post_purchase` or a named return operation |
| `TRANSFER_IN` / `TRANSFER_OUT` | Subledger only | No journal under section 4.17 |
| `STOCK_COUNT` | Same as an adjustment once `inventory.count` exists | Deferred with stock-count screens |

Inventory use cases call these contracts. Accounting does not import inventory tables and does not compute a second average.

### 5.3 Phase order and catch-up

Roadmap Phase 9 writes movements and weighted-average balances. Roadmap Phase 10 writes the first journals. Phase 9 must not insert into accounting tables to close that gap.

**Proposed gate before the first CompleteSale.**

- Accounting reads unposted opening and adjustment movements through an inventory application query.
- It posts one journal per movement, idempotent on the movement id, locking the balance row.
- New adjustments after that point call `post_inventory` inside the adjustment transaction.
- CompleteSale fails closed when a variant it is about to issue still has an unposted value movement.

The failure needs an error code. Reusing `RESOURCE_CONFLICT` is possible. A dedicated code is clearer and is a Document 05 amendment (section 12). Do not add the code in application code until that amendment exists.

### 5.4 Duplicate posting

A movement id can appear on one inventory journal. A sale id can appear on one `SALE` journal and, later, one `SALE_VOID` journal. A return id can appear on one `SALE_RETURN` journal. Replay of the business idempotency key returns the stored response. The database unique key stops a second insert if the application check is skipped.

### 5.5 Reconciliation and valuation tests

These tests become mandatory in the phase that first has both movements and journals.

| Test | Expected |
|---|---|
| Sum of `stock_value` across warehouses | Equals the posted `inventory` account |
| One sale | Inventory credit equals the movement’s extended cost and the cost-of-goods debit |
| Last unit | Balance value is `0.0000` and the cumulative cost of goods sold equals the value that had been received |
| Concurrent sales of the last units | One sale posts a journal. The other gets `INSUFFICIENT_STOCK` and posts nothing |
| Sellable return | Inventory increases by the original cost. The average may change. The journal matches the new movement |
| Damaged return | `stock_value` unchanged. Inventory account unchanged |
| Transfer | Both warehouses change by equal and opposite value. Inventory account unchanged |
| Receipt | Inventory account and stock value increase by the same amount. Accounts payable increases by that amount |
| Tenant B | Cannot read Tenant A’s balances or journals |

---

## 6. Financial reporting

Reporting reads posted journals and the inventory subledger. It does not keep a second set of business totals.

### 6.1 Reports already named in the contract

| Report | Contract | Phase | First release (roadmap G) |
|---|---|---|---|
| Sale on `GET /sales` and a sales report | Document 05 sales and `/reports/sales` | 10 | Yes, as granted. `sales.view` does not grant `reports.sales.view` |
| Account list | `GET /accounting/accounts` | 13 | Deferred with the finance UI |
| Journal inquiry | `GET /accounting/journal-entries` | 13 | Deferred as a screen. The rows exist from Phase 10 |
| General ledger and source drill-down | `GET /accounting/general-ledger` | 13 | Deferred as a screen |
| Trial balance | `GET /accounting/trial-balance` | 13 | Deferred as a screen. Phase 10 tests still assert debit equals credit |
| Profit and loss | `GET /reports/profit-loss` | 13 | Deferred as a screen |
| Inventory on hand | Inventory GET | 9 | Yes |
| Inventory valuation | `GET /reports/inventory` plus `reports.inventory.view` | With that report, after journals exist | Valuation versus the ledger is a Phase 10 test and a Phase 13 screen |

**Proposed query behavior for the Phase 13 reads**, to be copied into Document 05 when that phase is authorized:

| Read | Behavior |
|---|---|
| General ledger | Filter by account, `date_from`, `date_to`, and branch. Posted lines only. Running balance from the account’s normal balance. Each row includes `reference_type` and `reference_id` |
| Journal inquiry | Header plus lines. Branch scope enforced |
| Trial balance | As of a tenant-local date. One row per account with posted activity or a non-zero balance. Debit column total equals credit column total |
| Profit and loss | Accounts of type `REVENUE` and `EXPENSE` with `entry_date` in the range. Contra-revenue appears as a reduction of sales. Net profit is the difference |
| Drill-down | Resolve the source only when the user also has the source view permission and the branch |

Dates in these filters are tenant-local dates. Response timestamps stay UTC.

### 6.2 Balance sheet

Document 05 does not list a balance-sheet route. **Proposed for Phase 13, after a Document 05 amendment:** assets, liabilities, and equity as of a date, plus current earnings. Current earnings are revenue minus expenses for all posted lines up to that date. No year-end closing journal is required for the statement to balance.

Until that route is approved, the trial balance is the completeness report. Do not add `GET /accounting/balance-sheet` in code ahead of the amendment.

### 6.3 Cash-flow reporting

Document 01 asks for cash and payment-method figures. Document 05 does not define a statement of cash flows.

| Need | Placement |
|---|---|
| Sales by payment method | Sales report. Phase 10 / reports as granted |
| Drawer expected, actual, and variance | Session close. Phase 10. Operational, not a journal, under section 4.19 |
| Formal statement of cash flows | Deferred. It needs a cash-classification flag on accounts and a new route |

### 6.4 Inventory valuation and financial reconciliation

**Proposed Phase 13 report, with the equality tested in Phase 10.**

| Figure | Source |
|---|---|
| Inventory units and value by warehouse and variant | `inventory_balances` |
| Inventory general-ledger balance | Posted lines on the `inventory` role |
| Difference | Must be zero, or the report shows the unmatched movement ids |
| Gross profit | Sales revenue minus sales discounts, sales returns, and cost of goods sold, for the same date range |

A dashboard widget that shows profit requires `reports.finance.view` or the domain view Document 07 already requires. A cashier dashboard does not show it.

---

## 7. Financial governance

### 7.1 Posting and reversal permissions

**Established.**

| Action | Who can cause it | Key |
|---|---|---|
| Post a sale journal | The CompleteSale actor | `pos.create_sale` or `sales.create`. Not `finance_transactions.post` |
| Read finance | Finance roles per Document 07 | `finance_accounts.view`, `finance_transactions.view`, `reports.finance.view` |
| Cashier | POS sale only | Default cashier has no finance keys and no `pos.refund` |
| Accountant | Finance and expenses. Sales view. No POS | Document 07 compact matrix |
| Void a completed sale | Granted void users | `sales.void` |
| Return | Granted return users | `sales_returns.*` |
| Manual journal HTTP | Nobody, until D-14 | Keys may exist without a route |

**Proposed.** `finance_transactions.void`, when a route is eventually approved, creates a reversing journal for a journal that has no business document command. It is not an override of sale void rules, and it is not granted to the cashier.

### 7.2 Period close and reopening

**Proposed policy, not implementable as a screen until keys exist.**

| Rule | Detail |
|---|---|
| Close | Sets one period to `CLOSED`. Rejects a close when an earlier period is still `OPEN` |
| Effect | Posting with `entry_date` in that period fails and rolls back |
| Reopen | Sets it back to `OPEN`, writes an audit row with the reason, and is a separate permission from close |
| First release | Periods stay open. No close button |

There is no Document 07 key for close or reopen. Section 12 proposes `accounting_periods.close` and `accounting_periods.reopen`. Do not invent them in the catalogue as part of this proposal.

### 7.3 Audit and approval

**Established.** Audit is append-only. Sale confirm, void, return, payment, stock adjustment, and expense approval are audited. Refunds may require approval once numeric thresholds exist. Those thresholds are Document 09 Appendix B and are not set.

**Proposed audit rows for accounting:** journal posted, journal reversed, period closed, period reopened, account archived, mapping changed. Each row stores actor, tenant, entity id, and the before/after status. Original journals are not edited to record the audit.

Approval gates that already exist stay where they are: expense `approve` before `post_expense`; stock-count approve before a `STOCK_COUNT` movement, when that feature is built. Inventory adjustments post with reason and audit in the existing adjustment command. This proposal does not add a second approval step.

### 7.4 Separation of duties

| Duty | Proposed separation |
|---|---|
| Sell | Cashier can cause a system journal and cannot open the ledger, change the chart, or void, under the default grant |
| Void or refund | A different permission from `pos.create_sale`. Default cashier has neither |
| Chart and mappings | Owner, Administrator, Accountant, when finance keys are granted. A cashier cannot point cash at revenue |
| Expense | Creator and approver can be the same user in v1 because no rule forbids it. A two-person rule would be a new decision |
| Period reopen | Different key from day-to-day posting, so a reopen is visible and rare |
| Branch | A branch-scoped user posts and reads only that branch’s documents and journals |

Document 07 is the grant source. This table does not add roles.

### 7.5 Tenant and branch authorization

**Established.** Membership is proven. `X-Tenant-Id` is a hint. Bodies cannot set `tenant_id`. Another tenant’s id returns 404. Branch scope is independent of the permission key.

**Proposed.** Journal queries filter `tenant_id` and, for a branch-scoped user, `branch_id`. A journal whose source is outside the user’s branches is a 404. Account mappings are tenant-wide in v1. Branch-specific charts are out of scope.

### 7.6 Corrections, backdating, and closed periods

| Case | Rule |
|---|---|
| Open period, business correction | Void, return, purchase return, or expense cancel. New journal, old journal unchanged |
| Event date still inside an open period | `entry_date` is that event date even if the user submits the command later the same period |
| Closed period | Reject the post. The user corrects in the current open period with a replacement journal whose `entry_date` is the current local date, and the description cites the original document |
| Reopen | Only with the future reopen permission, a reason, and an audit row. Then the business command may post into the reopened period |
| Client-supplied accounting date | Ignored on sale, return, receipt, and adjustment commands |

---

## 8. API and data integrity

### 8.1 Contract alignment

**Established.**

- Base path `/api/v1`, JSON envelope, decimal strings, UTC timestamps.
- Status families in Document 05, including 405 `METHOD_NOT_ALLOWED`.
- Accounting reads listed in section 6.
- No client `POST /journal-entries` for a sale.
- Commands: confirm, void, return, receive, expense approve. Status is not changed by a free-form PATCH.
- Permission keys are the Document 07 strings only.

**Proposed HTTP shape for system posting.** There is no new public posting route. The existing business commands call the accounting module inside the use case.

| Command | Accounting call |
|---|---|
| `POST /sales/{id}/confirm` | `post_sale` |
| `POST /sales/{id}/void` | `reverse_posting` |
| `POST /sales/{id}/return` | Return posting in section 4.9 or 4.10 |
| `POST /purchase-orders/{id}/receive` | `post_purchase` |
| Purchase return command, when its URL is specified | Section 4.15 |
| `POST /inventory/adjustments` and opening stock | `post_inventory` after the contract name is added |
| `POST /expenses/{id}/approve` | `post_expense` |
| Supplier payment, after D-12 and D-13 | `post_payment` |

Document 04 names `post_expense`. Document 09’s required-contract list names `post_payment` and `reverse_posting` and does not name `post_expense`, `post_inventory`, or a return-specific method. Section 12 records that gap. Implementation should not invent a fifth public style of posting while skipping the amendment.

### 8.2 Atomicity

**Established.** CompleteSale, receipt, and return each commit once. The journal is synchronous. Celery runs only after commit. A failure rolls back sale, stock, payment, and journal together. The outbox row is part of that commit once its schema exists. This proposal does not define outbox columns.

**Proposed.** Opening stock, adjustment, expense approval, expense cancel, void, purchase return, and supplier payment follow the same pattern: business rows, inventory contract, accounting contract, audit, then commit.

Payment timing remains register §9.4. The accounting rule that stays valid under either reading: `post_sale` reads the tenders the confirm transaction treats as settling the sale, and it runs only inside that transaction. A draft with a saved tender and no successful confirm has no revenue journal.

### 8.3 Idempotency, isolation, concurrency, rollback

| Concern | Rule |
|---|---|
| Idempotency | Section 3.7. Replay returns the stored command response |
| Isolation | PostgreSQL read committed, plus `SELECT … FOR UPDATE` on the inventory balance rows and on the sale or receipt header |
| Weighted average | The lock is held across the cost calculation, the movement insert, and the journal insert |
| Unique keys | Idempotency `(tenant_id, key)` and the proposed journal source key |
| Rollback | Any exception, including an unbalanced journal or a locked-period rejection, rolls back the transaction. No compensation journal is required for a failed attempt |
| After commit | Workers may send receipts or refresh analytics. They do not post |

### 8.4 Client journal data

The confirm, return, receive, adjust, and expense payloads cannot supply account ids, debit and credit lines, posted status, `tenant_id`, or authoritative totals. The serializer allow-list omits them. If a client sends them, the use case ignores them and calculates the journal on the server. A future manual-journal command, under D-14, would be a different route with `finance_transactions.create` and `finance_transactions.post`, and it would still reject control accounts, closed periods, unbalanced drafts, and a client-set `posted_by`.

### 8.5 Amendments required before new surface area

This proposal does not add the following. Each one needs the document named in section 12 first.

- Balance-sheet route
- Period close and reopen routes
- Dedicated error codes for a closed period or an inventory/ledger mismatch
- `accounting_periods.close` and `accounting_periods.reopen`
- HTTP journal create, post, or void
- Payable payment route

---

## 9. Testing and acceptance criteria

Tests below are acceptance criteria for the phase that introduces the behavior. They do not authorize that phase.

### 9.1 Journals

| Case | Expect |
|---|---|
| Balanced sale fixture from section 4.2 | Posted journal. Debit sum equals credit sum. Amounts are decimal strings with four places |
| Force the debits to differ by `0.0001` | No journal, no completed sale, no movement. `ACCOUNTING_ENTRY_UNBALANCED` |
| Both debit and credit on one line, or a negative amount | Rejected before insert |
| Inactive account or header account in a mapping | Rejected. Sale rolls back |
| `entry_date` in a closed period | Rejected. Sale rolls back |
| `entry_date` with no period | Rejected |

### 9.2 Idempotency and duplicates

| Case | Expect |
|---|---|
| Same `Idempotency-Key` on confirm | One movement, one payment effect, one `SALE` journal. Second response matches the first |
| New key on an already completed sale | `SALE_ALREADY_COMPLETED`. Still one journal |
| Two concurrent confirms | One success. The unique keys and the sale lock keep a single journal |
| Missing `Idempotency-Key` | The status chosen when §9.4 is approved. Recommended default: 422 `VALIDATION_ERROR` |

### 9.3 Rollback

| Case | Expect |
|---|---|
| Journal insert fails after the sale row is staged | Sale not `COMPLETED`, stock unchanged, no payment side effect beyond what the frozen payment-timing decision allows, no journal |
| Inventory lock fails | No journal |
| Process crash before commit | No partial post after restart |

### 9.4 Concurrency and costing

| Case | Expect |
|---|---|
| Two cashiers, one unit | One `INSUFFICIENT_STOCK`. One journal |
| The section 5 three-unit example | Cumulative cost of goods sold equals `10.0000`. Ending `stock_value` is `0.0000` |
| Receipt then sale | Sale cost uses the average after the receipt, not the catalog selling price |
| Transfer | No journal. Warehouse values move by equal amounts |

### 9.5 Returns, refunds, and reversals

| Case | Expect |
|---|---|
| Return quantity above the eligible remainder | Rejected. No journal |
| Concurrent double return of the last eligible unit | One success |
| Sellable return | New return document. Original sale lines unchanged. Inventory and cost lines use the original unit cost. Journal balances |
| Damaged return | No increase in `quantity_on_hand`. No inventory journal lines |
| Void of a completed sale with no return | Reversing journal. Original lines still stored. Stock restored at original cost |
| Cashier without the refund grant | 403. No journal |
| Posted journal update or delete | Rejected by the application and by the database rule |

### 9.6 Statements and reconciliation

| Case | Expect |
|---|---|
| Trial balance after a mix of sales, returns, receipts, and adjustments | Debit total equals credit total |
| Profit and loss for the section 4.2 sale and the section 4.9 return | Revenue, discount, tax, and cost match the remaining journal lines |
| Inventory account versus sum of `stock_value` | Equal |
| Cashier `GET /accounting/trial-balance` | 403 |
| `reports.sales.view` absent | Sales report denied even when `sales.view` is present |

### 9.7 Tenant, permission, and audit

| Case | Expect |
|---|---|
| Tenant A journal id requested by Tenant B | 404 |
| Branch-scoped user and another branch’s journal | 404 |
| Cashier CompleteSale | Succeeds without `finance_transactions.post` |
| Accountant | Can view finance when granted. Cannot open POS |
| Posted journal | Audit row exists. A later reversal adds a new audit row and a new journal. The first journal’s amounts stay |

---

## 10. Open decisions and dependencies

Nothing in this section is approved by the existence of this file.

| ID | Decision | Consequence | Recommended default | Status | Roadmap phase that needs it |
|---|---|---|---|---|---|
| A-01 | Exact accounts for `post_sale` and the other roles in section 2.3 | Register §9.4. Without it, Phase 10 cannot seed a ledger | Adopt the role table in section 2.3 | Requires owner approval | 10, before the first post |
| A-02 | Contra-revenue discounts versus net revenue | Changes gross profit and the profit-and-loss layout. Document 01’s sentence matches contra-revenue | Contra accounts `sales_discounts` and `sales_returns` | Requires owner approval | 10 |
| A-03 | Tax inclusive or exclusive, and the tax base | Sales must compute the snapshot accounting will post. Accounting will not invent the rule | Keep today’s rule: post the snapshot. Tax policy stays a sales/tax decision | Requires owner approval | 8 for tax assignment, 10 for the first taxed sale |
| A-04 | Input tax capitalized or recoverable | Changes the receipt journal and may add a tax-receivable role | Capitalize receipt `unit_cost`. No tax-receivable role yet | Requires owner approval | 12 |
| A-05 | Card, mobile money, and bank as clearing accounts or as immediate cash | Changes cash reconciliation | Clearing roles in section 2.3. Bank-transfer tender debits `bank` | Requires owner approval | 10 |
| A-06 | `other` tender | An unmapped tender could hit the wrong asset | `other_tender_clearing` | Requires owner approval | 10 |
| A-07 | Weighted-average rounding and the last-unit residual | `money()` will reject unquantized division results | Section 5. Half-up. `stock_value` authoritative. Last unit clears the value | Requires owner approval | 9 for the average, 10 for the journal amount |
| A-08 | Sellable return cost | Current average would misstate the original sale’s margin | Original sale movement cost | Requires owner approval | 11 |
| A-09 | Damaged return stock and cost | Determines whether cost of goods sold is reversed | No sellable stock and no cost reversal | Requires owner approval | 11 |
| A-10 | Split-tender refund allocation | Which asset is credited | Same proportions as the original tenders | Requires owner approval | 11 |
| A-11 | Void after a partial return | Two corrections could overlap | Reject void when any return exists | Requires owner approval | 11 |
| A-12 | Payment recorded before confirm, or inside confirm | Register §9.4. A journal still exists only after a successful confirm | Keep `post_sale` inside the confirm transaction only | Requires owner approval | 10 |
| A-13 | HTTP status when `Idempotency-Key` is missing | Register §9.4 | 422 `VALIDATION_ERROR` | Requires owner approval | 10 |
| A-14 | Journal HTTP create and post | D-14. Keys exist. Routes do not | Keep system posting only | Established as blocked. Any exposure requires owner approval | 13 |
| A-15 | Who receives `payables.create_payment` and `receivables.create_payment` | D-12 | Do not grant from this document. Phase 12 can post receipts without the payment API | Requires owner approval | 12 for payments, not for receipt posting |
| A-16 | Payable document: receipt or supplier invoice | D-13. Frozen text says receipt unless a later spec exists | Keep the receipt. Do not add `supplier-invoices` here | Established direction. A change requires owner approval | 12 |
| A-17 | Drawer float, cash in/out, and variance journals | General-ledger cash will differ from the drawer if they are omitted | Omit those journals until a reason map exists. Show both cash figures | Requires owner approval | 10 for the limitation, 13 for a later journal policy |
| A-18 | Single currency per tenant | The currencies table is not built. Sale `currency` and payment `currency_id` differ | One tenant currency. Reject others. No foreign exchange | Requires owner approval | 10 |
| A-19 | Period close and reopen keys | A close button would invent permissions | Periods stay open in the first release | Requires owner approval before any close UI | 13 |
| A-20 | Year-end closing journals | Affects equity and profit-and-loss cutoffs | No closing entries. Profit and loss is a date-range query. Balance sheet uses current earnings | Requires owner approval | 13 |
| A-21 | Balance-sheet and cash-flow routes | Not in Document 05 | Add a balance sheet in Phase 13 by amendment. Defer the cash-flow statement | Requires owner approval | 13 for the balance sheet |
| A-22 | Expense credit: cash or accounts payable | Double posting if both approval and `PAID` recognize the expense | Recognize on approval. `PAID` only settles a payable | Requires owner approval | 13 |
| A-23 | Purchase-return price difference | Vendor credit and average cost often differ | Difference to `inventory_shrinkage` | Requires owner approval | 12 |
| A-24 | Transfer journals | Branch balance sheets would need them | No journal while inventory is one tenant account | Requires owner approval | When transfers are implemented |
| A-25 | Outbox columns | CompleteSale cannot meet Document 00 until the table exists | Accounting does not invent the columns. Same commit as the journal once specified | Unresolved in register §12.3 | 10 |
| A-26 | `document_sequences` | Journal human numbers need it | Use the Document 02 table, type `JOURNAL`. It was deferred from Phase 3, not redesigned here | Specified, not built | 10 |
| A-27 | Return workflow: Document 01 `DRAFT → APPROVED → COMPLETED` versus one `POST` | The journal must wait until stock and refund actually happen | Post only on the completion that issues stock and refund. Do not post on a draft return | Requires owner approval to reconcile 01 and 05 | 11 |
| A-28 | Explicit Accountant and Owner finance grant lists | D-06. “Full” is not a seed list | Follow Document 07 and register §10.1. Ask where a cell is still ambiguous | Requires owner approval | 6 for seeds, 13 for finance buttons |
| A-29 | Dedicated error code when inventory value and the ledger differ | Operators need a clear failure | Amend Document 05 before adding a code. Until then do not invent one in the handler | Requires owner approval | 10 |

---

## 11. Roadmap placement

No phase is added or reordered. Document 00 and the roadmap already require the posting engine inside CompleteSale. Document 04’s later “Accounting” build step and Document 05’s “accounting after purchasing” implementation order yield to that. Phase 13 remains the finance read model.

| Phase | Accounting work inside it |
|---|---|
| 3 (accepted) | Money type, idempotency table, transaction helper, append-only audit, empty `accounting` schema. Done |
| 4–8 | No journals. Tax assignment in the catalogue must store a rate id so Phase 10 can post a snapshot |
| 9 | Movements, locks, and weighted average. No writes to accounting tables |
| 10 | Accounting module, approved chart seed, open periods, `post_sale`, catch-up of opening and adjustment journals, immutability, source unique key. Sale visible on sales reads. Finance screens still wait |
| 11 | Return and void journals, refund tender, original-cost restoration |
| 12 | `post_purchase`, purchase-return journal, payable from the receipt. Supplier payment only after D-12 and D-13 |
| 13 | Account, journal, general-ledger, trial-balance, and profit-and-loss reads. Expenses. Chart UI. Optional balance sheet after an API amendment. Cash-flow statement stays deferred |
| 14–15 | No new accounting scope. Hardening uses the section 9 tests |

The first release described in roadmap section G includes the Phase 10 and Phase 11 engine: a completed sale and a return produce balanced journals. It does not include expense administration, full chart UI, or client journal posting.

---

## 12. Amendments this proposal does not apply

These are identified so a later edit can be authorized precisely. None of them is made by this file.

| Document | Section | Why it would change | Proposed amendment |
|---|---|---|---|
| 02 Database schema | Accounting | Lines have no `tenant_id`. Header has no branch, currency, `posting_event`, or `reversal_of_id`. Status values are unnamed. No unique source key. No `allows_manual_posting` | Add those columns and enums after A-01 is approved. Money columns stay `NUMERIC(19,4)` |
| 02 Database schema | Inventory balances | Cost fields are prose (“unit_cost / stock_value”) | Declare both `NUMERIC(19,4)` and state that `stock_value` is authoritative |
| 04 Module design and 09 §5 | Accounting contracts | The lists disagree, and opening, adjustment, and partial return have no name | Name `post_expense`, `post_inventory`, and the return posting beside the existing four contracts |
| 05 API contract | Confirm pipeline and headers | Register §9.4 payment timing and missing idempotency status | Record the chosen timing and the 422 default if A-12 and A-13 are approved |
| 05 API contract | Accounting reads | No balance sheet. No closed-period or inventory-mismatch code | Add the route and codes only with A-21 and A-29 |
| 05 API contract | Error catalogue | System imbalance is HTTP 500 in the foundation, and Document 05 does not state the status | State 500 for a system-generated imbalance |
| 07 Permission matrix | Finance | Period close would otherwise invent keys | Add `accounting_periods.close` and `accounting_periods.reopen` only with A-19 |
| 00 §6 and 05 headers | Idempotency list | Void is unprotected by the header requirement | Add void to the required-key list |
| 01 §18 | Gross profit | The sentence is ambiguous once discounts reduce revenue | State that discounts and returns are contra-revenue if A-02 is approved |
| 01 §28 and 05 Sales | Return lifecycle | Journal timing depends on which workflow is real | Choose one completion path in A-27 |
| Decision register §9.4 | Accounting row | The chart is still unresolved | Point that row at the approved version of section 2.3. Do not edit the register from this proposal |
| Decision register §12.3 | Outbox | CompleteSale’s commit is incomplete without it | Specify columns in Document 02 before Phase 10. Accounting does not own that table |

---

## 13. Conflicts with frozen requirements

| Topic | What the pack says | How this proposal treats it |
|---|---|---|
| When the engine exists | Document 04 and Document 01 place accounting after POS and purchasing. Document 00 §15, Document 09, and roadmap Phase 10 place a balanced journal inside CompleteSale | Follow Document 00 and the roadmap. Phase 13 stays the UI |
| Manual journals | Document 07 lists create and post. Document 00 and Document 05 forbid a client sale post. Consolidated amendments block the HTTP command | System contracts only, until D-14 |
| `ACCOUNTING_ENTRY_UNBALANCED` | Document 05 names the code and does not give it a status. The foundation uses 500 | Keep 500 for a broken system journal. Do not use it as a client validation error |
| Gross profit | Document 01 subtracts discounts from revenue | Recommend contra accounts so the subtraction happens once. Unapproved |
| Return states | Document 01 has draft, approved, and completed. Document 05 publishes one return command | Post only when stock and refund commit. Workflow choice is A-27 |
| Payment step | Document 00 lists record-payments inside CompleteSale. Document 05 describes tenders already recorded, then journals | Journal stays inside the confirm commit. The earlier insert is A-12 |
| Journal line tenancy | Document 00 requires `tenant_id` on every tenant-owned row. The line sketch omits it | Amendment in section 12. Do not ship lines without it |
| `account_balance` | Document 00 says other modules must not update it. Document 02 does not define the table | Derive balances from posted lines |
| Cash variance | Document 00 requires the variance to be kept and forbids rewriting sales | Keep the session figures. Do not force the ledger to the drawer count |
| Starter role matrix in Document 06 | Generic manager and optional accountant POS | Document 07 is the role source |
| FIFO, store credit, client-posted sales journals | Forbidden or deferred by Document 00 | Not proposed |

No frozen file was edited to remove these tensions.

---

## 14. Implementation boundary

This proposal does not authorize schema changes, seeds, routes, permission keys, or UI. Phase 10 remains blocked until the owner approves the chart (A-01) and the posting defaults Phase 10 cannot imply on its own, and until the outbox schema exists. The accounting subsystem is not complete and is not production-ready.
