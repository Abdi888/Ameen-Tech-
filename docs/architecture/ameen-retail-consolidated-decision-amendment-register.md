# Ameen Retail ERP — Consolidated Decision and Amendment Register

**Status:** Choice (b) recorded 2026-10-12. Gate 1 resolutions remain recorded proposals and are not applied to Documents 00 or 07.  
**Date:** 2026-10-12. Identity and access acceptance added 2026-10-13 (§11). Roadmap Phase 3 acceptance added 2026-10-13 (§12). Tax configuration decision recorded 2026-10-14 (§13). Accounting-engine review record added 2026-10-14 (§14). Roadmap Phase 4 acceptance added 2026-10-14 (§15).  
**Scope:** Greenfield Ameen Retail ERP architecture amendment  
**Implementation status:** Foundation corrections in §10. Identity and access accepted in §11. Roadmap Phase 3 accepted in §12. Roadmap Phase 4 is accepted in §15. Phase 5 is not authorized. §13 and the approved parts of §14 are for decision review only and do not authorize implementation. §15 does not accept §13, §14, or the accounting proposal.  
**Frozen-document status:** Documents 00–04 and 06–08 remain unchanged and frozen. Document 05 has one approved amendment: `METHOD_NOT_ALLOWED` at HTTP 405 (§10.2). The password endpoints in §11.2 are not a Document 05 amendment.  
**Document 09:** Code list includes `METHOD_NOT_ALLOWED`. Appendix B item 6 remains the implementer rule until Documents 05 and 07 are amended together for role listing. `roles.view` stays inactive.

**Source of recorded Gate 1 text:** user record 2026-10-12; proposal `docs/architecture/proposals/2026-10-12-gate-1-amendment-set.md`. Those resolutions do not supersede Documents 00–04, 06–08, or Document 07. Choice (b) defers U-01–U-06 (§10.1). The Document 05 amendment in §10.2 is a separate approved correction.

## 1. Purpose and boundaries

This register consolidates the user's six selections, remaining decisions identified in the Cursor review, proposed document impacts, and approval gates.

This is a review artifact. It does not amend Documents 00–04 or 06–08. Sections 9 and 10 are the 2026-10-12 record. Section 11 records the 2026-10-13 acceptance of the identity and access implementation. Section 12 records the 2026-10-13 acceptance of Roadmap Phase 3. Section 13 records the 2026-10-14 tax-configuration decision for review. Section 14 records the 2026-10-14 accounting-engine review. Neither §13 nor §14 authorizes implementation. Section 15 records the 2026-10-14 acceptance of Roadmap Phase 4. It does not authorize Phase 5.

The project is greenfield and must not reuse code from the legacy ERP.

## 2. User selections recorded for review

| ID | Decision | Selected value | Current status |
|---|---|---|---|
| U-01 | Standard selling-floor role | `Salesperson` | Recorded Gate 1; replaces Sales Manager in the eight-template catalogue. Frozen 07 still names Sales Manager until amended. |
| U-02 | Global role-template catalogue | Eight names in §9.1 | Recorded Gate 1. Nine-name alternative not selected. |
| U-03 | Business Owner POS access | Off by default; no `pos.*` | Recorded Gate 1; conflicts with Document 07 POS Full until amended. |
| U-04 | Permission-catalogue approach | `roles.view` for `GET /roles`; no `permissions.view`; `GET /permissions` deferred | Recorded Gate 1; inactive until 05 and 07 are amended together. |
| U-05 | Administrator model | Platform Administrator ≠ tenant Administrator | Recorded Gate 1. `platform.*` inactive in this amendment wave. |
| U-06 | Default tenant role copies | Business Owner, Administrator, Cashier, Salesperson, Accountant | Recorded Gate 1. Independent copies; no silent template overwrite. |

### 2.1 Catalogue and defaults are different

The eight-template catalogue is not a requirement to copy all eight roles into every tenant. The recorded default tenant-owned role copies are the five listed in U-06.

**Recorded catalogue (eight):** Business Owner, Administrator, Cashier, Salesperson, Accountant, Inventory Manager, Purchasing Officer, Viewer. Sales Manager is **not** in this catalogue. The nine-name alternative (retain both Salesperson and Sales Manager) is documented in the Gate 1 proposal and is **not selected**.

Inventory Manager, Purchasing Officer, and Viewer are catalogue-only until explicit permission lists exist. They are not default copies.

### 2.2 Owner identity protection

The Owner identity/account and the Business Owner role must not be conflated. The Owner must remain protected from ordinary assignment, removal, or privilege reduction according to the approved security contract. The exact invariants and recovery procedure must be written into the relevant contracts before implementation.

## 3. Cursor-review conflicts and current disposition

| Review item | Conflict or gap | Disposition after current selections |
|---|---|---|
| C1 | Salesperson vs. Sales Manager | **Recorded:** Salesperson replaces Sales Manager in the eight-template catalogue. Nine-name alternative not selected. Frozen 07 still lists Sales Manager until amended. Salesperson must not inherit Sales Manager Full; explicit selling-floor list still required. |
| C2 | Four-role proposal vs. eight system-role concepts | **Recorded:** eight templates in §9.1; five default copies. Catalogue membership ≠ automatic provisioning. |
| C3 | Global templates vs. fixed system-role model | Template-copy model selected in principle; schema, ownership, versioning, and edit rules remain open. |
| C4 | Business Owner POS Full vs. POS off | POS off selected for proposed amendment; current Document 07 remains authoritative until approved amendment. |
| C5 | Five navigation groups vs. flat screen map | Five groups are a navigation proposal; every screen still needs an approved group, route, and permission mapping. |
| C6 | Dashboard/alerts lack complete schema/API/permission contracts | Define only after scope and required metrics, events, permissions, and APIs are agreed. |
| C7 | Proposed lifecycle states vs. current tenant statuses | Resolve lifecycle state machine and compatibility with current schema before amending. |
| C8 | “No automatic extra grants” vs. Full/Limited shorthand | Replace shorthand with explicit permission-key grants; document inheritance and defaulting rules. |
| C9 | Permission/API inconsistencies | `roles.view` selected; reconcile Document 05's permission endpoint and Document 09's restrictions with Document 07 before activation. |
| C10 | Platform role/template administration vs. deferred tenant role editor | Decide who may manage global templates, tenant role copies, and tenant role assignments; keep platform and tenant scopes separate. |
| C11 | Salesperson in acceptance criteria but not canonical registry | Add only through approved Document 07 amendment and align acceptance criteria afterward. |
| C12 | Platform permission catalogue missing | Define an explicit platform-only permission catalogue and API contracts; do not invent active keys in code. |
| C13 | Proposal path differs from header | Correct the proposal's canonical path only after explicit file-edit authorization. Cursor reported the file in `docs/architecture/2026-10-11-platform-and-role-template-amendments.md`, while its header points to `docs/architecture/proposals/...`. |
| C14 | Finance Full includes `receivables.create_payment`; payables grants unclear | Decide exact role grants and payment semantics. Do not activate or grant withheld permissions by implication. |

## 4. Remaining decisions requiring approval

Gate 1 catalogue and boundary resolutions are recorded in §9. The following still need approval or explicit deferral before, or in parallel with, frozen-document edits. D-01 and D-02 are recorded; they are not live in Documents 00–07 until authorized edits.

| ID | Decision required | Recommended review question / acceptance condition |
|---|---|---|
| D-01 | Sales Manager disposition | **Recorded:** not retained in the eight-template catalogue. Salesperson is the selling-floor template. A future Sales Manager template would be a new catalogue entry with its own grants. |
| D-02 | Eight catalogue names | **Recorded:** the eight names in §9.1. Nine-name alternative documented, not selected. |
| D-03 | Tenant Administrator meaning | Define tenant Administrator's authority and explicit limits. Confirm it is not a platform role and receives no `platform.*` permissions. |
| D-04 | Template lifecycle | Decide who can create/edit/deactivate global templates; whether tenant role copies are editable; whether template changes propagate; how versioning, audit history, and rollback work. Default recommendation: copied tenant roles are independent and global template edits do not silently alter existing tenants. |
| D-05 | Role assignment authority | Define who can assign roles, edit tenant role grants, create custom tenant roles, and protect the Owner account. State any deferred capabilities explicitly. |
| D-06 | Explicit role grants | Approve a permission-key list for each default role. Do not rely on `Full`, `Limited`, or implicit inheritance as executable authorization rules. |
| D-07 | Platform permission catalogue | Define each platform permission, the platform role allowed to hold it, the endpoint/screen it controls, and its audit behavior. Keep platform permissions unavailable to tenant roles. |
| D-08 | Tenant lifecycle | Decide allowed states, transitions, actors, guards, audit events, and recovery paths. Reconcile proposed states with the current `ACTIVE`, `SUSPENDED`, and `ARCHIVED` model. |
| D-09 | Provisioning contract | Specify steps, transaction boundaries, idempotency key, retry behavior, partial-failure recovery, default role copies, Owner creation, and readiness criteria. |
| D-10 | Plans and billing | Decide whether subscriptions, plan assignments, billing status, and enforcement are in this amendment wave or explicitly deferred. |
| D-11 | Dashboard and alerts | Define required dashboard metrics and alert events, data sources, refresh/retention expectations, authorization, and API response contract—or explicitly defer them. |
| D-12 | Finance payment grants | Explicitly decide which roles, if any, receive `receivables.create_payment` and `payables.create_payment`. Do not infer grants from a broad finance label. |
| D-13 | Payables origin and endpoint | Resolve whether a payment is linked to a supplier invoice, a goods receipt, or another payable record; then specify the canonical endpoint and relationship. |
| D-14 | Journal HTTP exposure | Decide whether finance transaction create/post operations are exposed over HTTP, which permissions guard them, and the required posting/audit invariants. |
| D-15 | Navigation map | Map each approved screen to one of Home, Sales, Inventory, Finance, or Business; separately map route access to permissions and plan/business capability rules. |
| D-16 | Stale permission examples | Reconcile examples such as `ownership.transfer` and `security.settings.update` against the canonical registry; either approve and add them coherently or remove them from examples. |
| D-17 | Operational health | Define what platform dashboard “health” means, which checks are in scope, and what data may be exposed to which platform roles. |
| D-18 | Amendment scope | Decide whether to include the proposed `2026-10-10-revised-amendment-set.md` changes. Review each proposal individually; do not adopt the file wholesale by implication. |
| D-19 | Default tax-rate effective date | **Unresolved.** Decide whether a changed tenant default tax rate takes effect immediately or from a specified future date. No rule is approved. See §13.7. |
| D-20 | Opening Balance Equity clearing | **Unresolved.** How and when Opening Balance Equity is cleared or reconciled is not decided. The opening-stock journal in §14.2 does not decide it. |

## 5. Proposed amendment sequence

This sequence is a plan for approval, not permission to edit files.

### Gate 1 — Approve the decision baseline

Approve the six user selections as the intended direction for contract amendments, while acknowledging that the current frozen documents remain authoritative until formally amended. Close D-01 through D-06, or explicitly defer any item that is not needed for the first vertical slice.

**Exit criteria**
- The exact eight catalogue concepts are enumerated.
- The five default tenant role copies are confirmed.
- Sales Manager disposition is explicit.
- Platform Administrator and tenant Administrator are distinct in scope.
- Owner protection and role-template edit rules are defined.
- Explicit grants are approved for the five default role copies.

### Gate 2 — Amend Document 07 first

After explicit authorization to edit frozen documents, update the canonical role catalogue, explicit grants, Business Owner POS default, permission registry, screen list, and screen-to-navigation mapping.

**Exit criteria**
- Every permission key is canonical and unique.
- Each role has explicit grants; no executable meaning depends on Full/Limited shorthand.
- Business Owner POS is off by default in the approved grant list.
- Platform permissions cannot be assigned to tenant roles.
- No new key is activated before its corresponding API/security contracts are approved.

### Gate 3 — Align architecture contracts

After Document 07 is approved, update only the necessary contracts, in this proposed order:

1. **Document 00:** role/template invariants, platform/tenant boundary, bootstrap and provisioning boundaries.
2. **Document 02:** role ownership and copies, platform identity model, and any approved lifecycle/billing/alert data.
3. **Document 05:** platform APIs, role/permission APIs, provisioning behavior, and the canonical payables/payment contract.
4. **Document 06:** platform RBAC, tenant role assignment rules, Owner protection, lifecycle guards, and audit events.
5. **Document 04:** module ownership and cross-module responsibilities.
6. **Document 03:** update only if the approved design changes technical boundaries or deployment architecture.
7. **Document 01:** reconcile requirements and remove stale role/screen definitions.
8. **Document 09:** align seeds, plan gates, acceptance tests, and implementation sequencing to the approved contracts.

Document 08 remains unchanged unless a separate, explicit design-token change is approved.

### Gate 4 — Consistency review

Run a document-only consistency pass. Check role names, permission identifiers, route/API guards, database fields, lifecycle states, template ownership, and acceptance criteria across all amended documents.

**Exit criteria**
- No permission exists in an API, screen, example, seed plan, or test without a canonical definition.
- No platform permission can be granted to a tenant role.
- Template edits do not silently change existing tenant roles.
- Owner protection and bootstrap behavior are unambiguous.
- The five default role copies and their grants agree across schema, security, API, and tests.
- Deferred capabilities are explicitly marked deferred, not left ambiguous.

### Gate 5 — Separate implementation authorization

Architecture approval does not authorize implementation. A separate user approval must specify the permitted implementation scope, such as repository scaffolding, migrations, backend, frontend, or a named vertical slice.

## 6. Proposed change-impact map

| Document | Expected impact if approved |
|---|---|
| 00 — Frozen Decisions | Role/template rules, Administrator scope, platform/tenant boundary, provisioning invariants |
| 01 — System Requirements and Domain | Stale role names/screens, approved role and navigation requirements |
| 02 — Database Schema | Template catalogue/copies, role ownership, platform identity, and approved lifecycle/billing/alert entities |
| 03 — Technical Architecture | Only if platform/tenant or provisioning changes affect technical boundaries |
| 04 — Application/Module Design | Role/template administration, provisioning responsibilities, dashboard/alerts if included |
| 05 — API Contract | Role/permission APIs, platform APIs, provisioning, payment/payables semantics |
| 06 — Security and Authorization | Explicit grants, Owner protection, platform-vs-tenant RBAC, lifecycle and audit enforcement |
| 07 — Permission Matrix and Screens | Canonical registry, role catalogue, explicit grants, Business Owner POS, screen map and navigation groups |
| 08 — UI Design Tokens | No change expected |
| 09 — Implementation Specification | Seeds, permission/role setup, acceptance tests, scope and sequencing |

## 7. Non-negotiable guardrails

- Do not reuse legacy ERP code; this project remains greenfield.
- Do not edit Documents 00–08 without explicit authorization.
- Do not code, create migrations, scaffold UI, or change infrastructure under this review-only authorization.
- Do not activate proposed permissions or invent missing permission keys.
- Do not grant platform permissions to tenant roles.
- Do not treat navigation visibility as authorization.
- Do not treat template catalogue membership as automatic tenant provisioning.
- Do not let global template edits silently change existing tenant role copies.
- Do not treat architecture approval as implementation approval.
- Do not treat recorded Gate 1 resolutions as applied amendments until named frozen documents are explicitly authorized and edited.

## 8. Approval checklist

Use this checklist at the next review. Partial approval is acceptable; any deferred item must be recorded explicitly.

**Resolved** means an owner decision is recorded in §10. **Deferred** means choice (b) postponed it. A deferred item is not approved. **Unresolved** means no owner decision is recorded.

- [x] **Resolved — recorded; frozen-document edit deferred under choice (b).** Eight-template catalogue and Sales Manager disposition (Salesperson replaces Sales Manager; nine-name alternative not selected). Not applied to Documents 00 or 07.
- [x] **Resolved — recorded; application deferred under choice (b).** Five default tenant-owned copies and no-silent-overwrite rule. Not applied to Documents 00 or 07.
- [x] **Resolved — recorded; activation deferred under choice (b).** Owner POS off, platform vs tenant Administrator, `roles.view`, and deferred `GET /permissions`. Proposed keys stay inactive until Documents 05 and 07 are amended together.
- [ ] **Deferred under choice (b).** Explicit key-by-key grants for Business Owner, Administrator, Salesperson, and Accountant. When identity work is authorized, use the frozen Document 07 matrix, including the Cashier list already in Document 07.
- [ ] **Unresolved.** Template lifecycle and who may edit tenant role copies.
- [ ] **Deferred — proposed keys stay inactive.** Platform permission catalogue and platform API contracts are not approved. `platform.*` stays inactive.
- [ ] **Unresolved.** Lifecycle/provisioning, finance/payables, and dashboard/alert scope.
- [ ] **Unresolved.** Phase 10 addendum: `post_sale` accounts, Document 00 vs 05 payment timing, and the missing `Idempotency-Key` HTTP contract. See §9.4.
- [x] **Resolved for one edit.** Document 05 amendment: `METHOD_NOT_ALLOWED` at HTTP 405 (§10.2). No other frozen-document edit is authorized.
- [ ] **Unresolved.** Consistency review of amended documents. This checklist does not sign off Phase 1.
- [x] **Resolved for foundation corrections only.** As of §10 (2026-10-12), identity implementation was not yet authorized.
- [x] **Accepted 2026-10-13.** Identity and access implementation (§11). Outstanding contract items in §11.2 are recorded and are not frozen-document edits. At that acceptance, Roadmap Phase 3 was not yet authorized; it is accepted in §12.
- [x] **Accepted 2026-10-13.** Roadmap Phase 3 (§12). `MoneyField` rejects Python floats; `NUMERIC(19,4)` is unchanged; no new migration. The outbox schema remains unresolved and blocks CompleteSale. At that acceptance, Roadmap Phase 4 was not yet authorized; it is accepted in §15.
- [x] **Accepted 2026-10-14.** Roadmap Phase 4 (§15), with branch selection, Phase 7 frontend routes, and `REQUIRE_APPROVAL` left deferred. Phase 5 is not authorized. §13, §14, and the accounting proposal are not part of this acceptance.
- [x] **Approved for decision review only.** Tenant default tax rate, tax-inclusive calculation, sale snapshot, and historical-rate protection (§13). Not an implementation authorization. Documents 00–08 are unchanged.
- [ ] **Unresolved.** Effective date of a changed default tax rate: immediate or a specified future date (D-19, §13.7).
- [x] **Approved for decision review only.** Opening stock debits Inventory Asset and credits Opening Balance Equity (§14.2). Not an implementation authorization.
- [ ] **Unresolved.** Minimal first-sale chart of accounts and tender-account map. Not verified as an owner-approved list (§14.1, §9.4).
- [ ] **Unresolved.** Clearing and reconciliation of Opening Balance Equity (D-20, §14.3).
- [ ] **Unresolved.** Which tax rule a discount must follow. §14.4 records the requirement and does not select a discount base (§13.3).

## 9. Recorded Gate 1 resolutions (2026-10-12)

Recorded proposals, not applied to Documents 00 or 07. Document 05 has one approved amendment, `METHOD_NOT_ALLOWED` at HTTP 405 (§10.2). Documents 00–04 and 06–08 remain frozen. Foundation corrections are the only authorized implementation. Identity implementation is not authorized.

Proposal detail: `docs/architecture/proposals/2026-10-12-gate-1-amendment-set.md`.

### 9.1 Role-template catalogue

Eight templates:

1. Business Owner
2. Administrator
3. Cashier
4. Salesperson
5. Accountant
6. Inventory Manager
7. Purchasing Officer
8. Viewer

**Not selected:** retain both Salesperson and Sales Manager (nine templates). That alternative remains documented in the Gate 1 proposal only.

**Default tenant-owned copies:** Business Owner, Administrator, Cashier, Salesperson, Accountant.

Each tenant receives independent copies. Later global template changes must not silently change existing tenant roles.

### 9.2 Authorization boundaries

- **Business Owner:** POS disabled by default; no `pos.*` grants. Owner identity is distinct from the Business Owner role.
- **Cashier:** retain the existing Document 07 grant list unchanged.
- **Salesperson:** requires an explicit selling-floor permission list; must not inherit the full Sales Manager permission set. The list in Gate 1 proposal §3.4 remains proposed until key-by-key approval.
- **Accountant and Administrator:** require explicit, key-by-key grants consistent with Document 07. Gate 1 proposal §3.2 and §3.5 remain proposed until approved.
- **Inventory Manager, Purchasing Officer, Viewer:** catalogue entries only until their permission lists are explicitly defined.
- **Platform Administrator:** separate from tenant Administrator. `platform.*` remains inactive in this amendment wave.
- **Role and permission APIs:** `roles.view` authorizes `GET /roles`. No `permissions.view` key. `GET /permissions` is deferred.

The endpoint decision supersedes Document 09 Appendix B item 6 **only after** Documents 05 and 07 are amended together.

### 9.3 CompleteSale transaction contract (verified in 00/04/05/09)

Completion path: `POST /sales/{id}/confirm` → status **COMPLETED**.

Single synchronous database transaction:

1. Calculate and validate totals.
2. Lock and validate stock.
3. Complete the sale.
4. Record payments.
5. Issue stock through `issue_stock`.
6. Post accounting through `accounting.post_sale`; the journal must balance.
7. Write the audit record and outbox event.
8. Commit.

Any critical failure → **ROLLBACK**. Journals are synchronous. Celery starts only after commit.

Idempotency: the same `Idempotency-Key` within the same tenant must return the original result without creating another stock movement or journal.

### 9.4 Outstanding Phase 10 addendum items

These remain unresolved and must be settled before the relevant contract is finalized. They do not close Gate 1 by themselves.

| Item | Required resolution |
|---|---|
| Accounting | Identify the exact chart-of-accounts accounts used by `accounting.post_sale`. |
| Payment timing | Reconcile conflicting payment-timing wording between Documents 00 and 05. |
| Missing idempotency header | Specify the HTTP status and error contract when `Idempotency-Key` is absent. |

### 9.5 Change-control status

| Artifact | Status |
|---|---|
| Documents 00–04 and 06–08 | Frozen; unchanged |
| Document 05 | One approved amendment, 2026-10-12: `METHOD_NOT_ALLOWED` at HTTP 405. See §10 |
| Document 09 | Code list updated to include that same code. Appendix B item 6 remains the implementer rule until 05 and 07 are amended together for role listing |
| Gate 1 resolutions | Recorded; not applied to Documents 00/07 |
| Implementation | Foundation corrections only. Identity implementation is not authorized |

## 10. Approved foundation decisions (2026-10-12)

The owner approved two corrections. Neither one starts identity implementation.

### 10.1 Permission scope — roadmap choice (b)

When identity implementation is later authorized, implement the frozen Document 07 permission matrix as-is. U-01 through U-06 stay deferred. Proposed permission keys stay inactive. Role grants are not changed. Roles are not seeded.

Rationale: the roadmap exit required an explicit choice between amending the role catalogue and deferring it. The owner chose deferral. Gate 1 selections in §9 remain recorded proposals. They are not edits to Documents 00 or 07.

### 10.2 Document 05 — `METHOD_NOT_ALLOWED`

Unsupported HTTP methods return **405** with code `METHOD_NOT_ALLOWED` and the standard error envelope. `INVALID_VALUE` remains **422** and is not used for this case.

Rationale: Document 05 had no 405 status and no dedicated code, so the handler used `INVALID_VALUE` at 405 while the catalogue mapped that code to 422. The owner approved a narrow Document 05 amendment rather than overloading a validation code. Documents 00–04 and 06–08 were not edited. Document 09’s code list was updated so it still matches Document 05.

## 11. Identity and access acceptance (2026-10-13)

The owner accepted the identity and access implementation. In the owner’s phase label this work was “Phase 2.” The implementation roadmap still calls repository setup Phase 2 and authentication Phase 4. This section does not renumber or edit that roadmap.

Documents 00–08 were not edited for this acceptance.

### 11.1 Verification recorded with acceptance

From `backend/`, after the CSRF, token, and concurrency checks:

| Check | Result |
|---|---|
| `ruff check .` | Passed |
| `ruff format --check .` | Passed (96 files already formatted) |
| `mypy` | Passed (89 source files) |
| `pytest --tb=line -q` | **71 passed** in 23.42s |

### 11.2 Outstanding items

These are recorded only. They are not silent edits to frozen documents, and they are not authorization to implement them.

1. **Document 05 password routes.** `POST /api/v1/auth/password/change`, `/auth/password/reset`, and `/auth/password/reset/confirm` are not in Document 05. They need an approved amendment through the same path as §10.2 before they are frozen contract routes. Until then they are the HTTP shape of the Document 06 change, reset, and invite-set-password use cases.
2. **Currency foreign key.** Document 02 declares `tenants.default_currency_id` as a foreign key to `currencies`. The currencies table is not implemented. The column stays a nullable UUID with no foreign key until that table exists.
3. **Invite rate limit.** Document 06 requires rate limiting for invite. No threshold is frozen. The limit stays unimplemented until an explicit number is chosen.

### 11.3 Not authorized

§11 did not authorize Roadmap Phase 3. That phase was accepted later in §12. §11 and §12 did not authorize Roadmap Phase 4. That phase was accepted later in §15. §15 does not authorize Phase 5.

## 12. Roadmap Phase 3 acceptance (2026-10-13)

The owner accepted Roadmap Phase 3: persistence, migrations, transaction conventions, and audit primitives. This section does not renumber or edit `docs/architecture/10-implementation-roadmap.md`. It did not authorize Roadmap Phase 4. That phase was accepted later in §15. This section does not authorize Phase 5 or any later phase.

Documents 00–09 were not edited for this acceptance.

### 12.1 Verification recorded with acceptance

From `backend/`, after the `MoneyField` float rejection was fixed:

| Check | Result |
|---|---|
| `ruff check .` | Passed |
| `ruff format --check .` | Passed (101 files formatted) |
| `mypy` | Passed (94 source files) |
| `pytest --tb=line -q` | **77 passed** in 21.35s |

### 12.2 MoneyField

The review blocker is resolved. `MoneyField.to_python` rejects a Python `float` before `DecimalField.to_python` can convert it. `NUMERIC(19,4)` is unchanged. No new migration was required.

### 12.3 Unresolved dependency — outbox

Document 00 and Document 09 require an outbox row in the same commit as CompleteSale. Document 02 does not define that table. The outbox schema remains unresolved and must be approved before CompleteSale is implemented. This section does not invent its columns.

### 12.4 Deferrals preserved

These stay deferred. This acceptance does not implement them.

- `tenant_settings`
- `documents`
- `document_sequences`
- The currencies table and the foreign key from `tenants.default_currency_id` (§11.2)
- The invite rate-limit threshold (§11.2)
- The Document 05 password-route amendment (§11.2)

### 12.5 Not authorized

§12 did not authorize Roadmap Phase 4. That phase was accepted later in §15. Phase 5 and every later phase remain unauthorized. No further application code or migrations are authorized by this section.

## 13. Tax configuration decision (2026-10-14)

**Status:** Approved for decision review. This is not implementation authorization.

The owner approved the rules in §13.1 through §13.6 for review. This section does not authorize application code, tests, schema changes, migrations, API routes, permission changes, or edits to Documents 00–08, Document 09, or the roadmap. Those documents stay as they are. This section does not withdraw their existing tax sketches.

### 13.1 Authorized roles

Business Owner and an authorized Administrator may configure the tenant's default tax rate. Existing permission checks still apply. This decision does not add permission keys and does not change Document 07 grants.

### 13.2 Configuration model

One configurable default tax rate per tenant.

Multiple tax rates and product-specific tax categories are not part of this decision. Their absence here is a scope limit of §13. It is not an approved change to Documents 00–08.

### 13.3 Tax calculation

The previously approved tax-inclusive calculation is preserved:

- Tax amount = gross price × tax rate / (100 + tax rate).
- Taxable base = gross price − tax amount.

This register had no earlier section that stated the formula. §13.3 is the record of that preserved calculation. It does not define how the rate is stored, and it does not define a discount interaction.

### 13.4 Sale snapshot

The finalized sale snapshot preserves the gross price, taxable base, tax rate, tax amount, and pricing mode. The accounting engine must use this snapshot. It must not recalculate tax, and it must not post tax twice.

### 13.5 Historical transactions

Changing the default rate must not alter or recalculate completed sales or their accounting records.

### 13.6 Auditability

A rate change must be attributable to the authorized user, and the time of the change must be recorded. This is a requirement for future design. It does not authorize implementation of audit storage or an audit screen.

### 13.7 Unresolved — effective date

**Open decision D-19.** Whether a changed default tax rate takes effect immediately or from a specified future date is not decided. Neither behavior is an approved rule.

### 13.8 Not authorized

§13 does not authorize implementation. Roadmap Phase 4 and every later phase remain unauthorized. No tax configuration behavior is approved to be built from this section alone.

## 14. Accounting-engine review record (2026-10-14)

**Status:** Mixed. Approved items are for decision review only. This section does not authorize implementation.

This section records only decisions that can be verified. It does not adopt the unapproved role table in `docs/architecture/proposals/2026-10-14-accounting-design-and-controls.md`. Documents 00–08, Document 09, and the roadmap are unchanged.

### 14.1 Minimal chart and tender accounts — not verified

The owner asked to record an approved minimal chart of accounts and the tender-account treatment for the first sale.

No owner-approved account list or tender-to-account map is in this register or in an approved decision record. Register §9.4 still requires the exact accounts used by `accounting.post_sale`. The accounting proposal's role table, including card, mobile-money, and bank clearing names, is marked there as not approved. The later review recommended one asset account per tender and also marked that recommendation as not approved.

§14 does not convert either source into an approved chart. §9.4 stays unresolved.

Document 00 §6 already lists the v1 tenders and states that cash change is not revenue. That is existing frozen text. It is not a new chart decision.

### 14.2 Opening stock — approved for decision review

**Approved for decision review. Not implementation authorization.**

Opening stock is recorded as:

| Account | Debit | Credit |
|---|---|---|
| Inventory Asset | opening stock value | |
| Opening Balance Equity | | opening stock value |

This entry does not approve account codes, a full chart, adjustment journals, or a catch-up posting procedure.

### 14.3 Unresolved — Opening Balance Equity

**Open decision D-20.** Clearing and reconciliation of Opening Balance Equity are not decided. No method, date, or destination account is approved.

### 14.4 Tax-inclusive sale snapshot

The tax-inclusive calculation, the finalized sale snapshot, and the rule against calculating or posting tax twice are already approved for decision review in §13.3 and §13.4. §14 does not restate them as a second decision.

The owner also requires that discounts follow the applicable tax rules, and that the accounting engine use the finalized snapshot without recalculating tax. The snapshot rule is §13.4.

**Unresolved.** This register does not state which discount-tax rule is the applicable one. §13.3 does not define a discount interaction. Contra-revenue, net revenue, and whether the gross price in the §13.3 formula is before or after discount are not approved here.

## 15. Roadmap Phase 4 acceptance (2026-10-14)

The owner accepted Roadmap Phase 4: authentication, tenant context, the platform/tenant boundary, and authorization. This section does not renumber or edit `docs/architecture/10-implementation-roadmap.md`. It does not authorize Roadmap Phase 5 or any later phase.

Documents 00–09 were not edited for this acceptance.

The accepted baseline is the identity and access implementation in §11, the persistence implementation in §12, and the limited request-context permission change accepted on 2026-10-14. After one membership is proven, the request context stores the permission codes computed on the server for that membership. Client headers, query parameters, and request bodies do not supply those codes.

### 15.1 Verification recorded with acceptance

The request-context review accepted that change. The implementation run reported before that review, and not repeated for this acceptance, was:

| Check | Result |
|---|---|
| `ruff check .` | Passed |
| `mypy` | Passed (95 source files) |
| `makemigrations --check --dry-run` | No changes detected |
| `migrate --noinput` | Existing migrations applied; no new migration |
| `pytest tests/test_request_context.py` | **4 passed** |
| `pytest --tb=line -q` | **81 passed** in 23.10s |

### 15.2 Deferrals preserved

These stay deferred. This acceptance does not implement them.

- Current branch selection. `branch_id` stays unset. No branch header, stored default branch, or branch, warehouse, or terminal models.
- Frontend routes `/login`, `/app/*`, and `/platform/*`, including platform API stubs. Deferred to Phase 7. No `platform.*` keys.
- `REQUIRE_APPROVAL`. Authorization stays `ALLOW` or `DENY` until refund and discount thresholds are approved.
- The Document 05 password-route amendment (§11.2).
- The invite rate-limit threshold (§11.2).
- U-01 through U-06, including Salesperson, Owner POS off, and tenant role-template copies (choice (b), §10.1).
- The deferrals already listed in §12.4, including the unresolved outbox schema. The outbox schema still blocks CompleteSale.

### 15.3 Not authorized

Phase 5 and every later phase remain unauthorized. A separate explicit approval is required before that work starts. This acceptance does not include §13, §14, or `docs/architecture/proposals/2026-10-14-accounting-design-and-controls.md`.
