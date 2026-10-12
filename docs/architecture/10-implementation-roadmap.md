# Ameen Retail — Implementation Roadmap v1

**Status:** Proposed engineering plan. **Not** implementation authorization.  
**Date:** 2026-10-12  
**Authority:** Documents 00–08 remain frozen. Document 09 operationalizes them. This file does not amend, supersede, or implement any of them.

If this roadmap and a frozen design disagree, **`00-frozen-decisions.md` wins**, except **permission identifiers**, which **Document 07** owns.

---

## A. Purpose and boundaries

This document translates the architecture pack into an ordered, approval-gated engineering plan: phases, dependencies, deliverables, tests, acceptance criteria, and release gates.

It is **planning only**. Creating this file does **not** authorize:

- application code, migrations, frontend screens, backend modules, infrastructure files, or tests
- dependency installation or repository scaffolding
- edits to Documents 00–08
- edits to Document 09 unless separately authorized
- activation of proposed permission keys
- invention of endpoints, schema fields, roles, or business rules

The product is a **greenfield** retail-only modular monolith. Do not reuse, copy, migrate, or depend on Kinetic ERP or any previous Ameen ERP.

**Stack (binding, Documents 00 §2 and 03):** React + TypeScript + Vite + React Router + TanStack Query + React Hook Form + Zod; Python + Django + DRF; PostgreSQL; Redis; Celery; Nginx; Docker; S3-compatible storage; GitHub Actions; DigitalOcean. Visual tokens: Document 08 and `tokens.css`. Do not introduce GraphQL, microservices, Kafka, Kubernetes, event sourcing, or CQRS-everywhere.

---

## B. Current architecture baseline

### B.1 Actual repository state (verified 2026-10-12)

Present:

| Path | Role |
|---|---|
| [00-frozen-decisions.md](./00-frozen-decisions.md) | Binding when numbered docs conflict |
| [01-system-requirements-and-domain.md](./01-system-requirements-and-domain.md) | Domain / requirements |
| [02-database-schema.md](./02-database-schema.md) | Schema design |
| [03-technical-architecture.md](./03-technical-architecture.md) | Runtime, layers, modules |
| [04-application-module-design.md](./04-application-module-design.md) | Module ownership and use cases |
| [05-api-contract.md](./05-api-contract.md) | HTTP contract |
| [06-security-and-authorization.md](./06-security-and-authorization.md) | Security design |
| [07-permission-matrix-and-screens.md](./07-permission-matrix-and-screens.md) | Canonical permission keys, roles, screens |
| [08-ui-design-tokens.md](./08-ui-design-tokens.md) + [tokens.css](./tokens.css) | Visual tokens |
| [09-implementation-specification.md](./09-implementation-specification.md) | Binding engineering rules; does not replace 00–08 |
| [README.md](./README.md) | Pack index |
| [../AGENTS.md](../../AGENTS.md) and `.cursor/rules/` | Agent / IDE rules |
| Proposals under [proposals/](./proposals/) (see B.4) | Non-frozen |
| [2026-10-11-platform-and-role-template-amendments.md](./2026-10-11-platform-and-role-template-amendments.md) | Draft amendment proposal (not under `proposals/`) |
| [ameen-retail-consolidated-decision-amendment-register.md](./ameen-retail-consolidated-decision-amendment-register.md) | Decision/amendment register (draft) |

Absent (do not invent replacements):

- `backend/`, `frontend/`, `infrastructure/`, `docker-compose.yml`, application tests
- Git repository
- OpenAPI (`openapi.yaml`)
- Requirement → API → permission → test traceability matrix (README lists this as not yet in the pack)
- Screen layouts / UX wireframes (tokens only in 08)
- `docs/architecture/proposals/2026-10-11-platform-and-role-template-amendments.md` — **header path is wrong**; the file lives one directory up

### B.2 Frozen / binding requirements

Treat as approved architecture unless a later **explicit** amendment is applied:

- Retail-only modular monolith; shared DB; `tenant_id` on tenant-owned rows; layers API → use case → domain → infrastructure
- Online POS only; weighted average cost; no POS store credit/AR unless frozen decisions change
- CompleteSale is one DB transaction (sale, payments, stock, balanced journals, audit, outbox)
- Eight **system roles** in Documents 00 §11 and 07 §6: Business Owner, Administrator, Accountant, Sales Manager, Inventory Manager, Cashier, Purchasing Officer, Viewer
- Document 07 permission registry and screen entry keys
- Owner is a protected system role; ordinary `users.assign_roles` cannot assign or remove it
- No tenant role-designer UI; tenants assign from the system-role list
- Routes: `/login`, `/app/*`, `/platform/*` never mixed
- First **code** slice when coding starts: Document 00 §15 (identity/tenant/RBAC → branch/warehouse/terminal → product → opening/adjust stock → open register → sell → pay → confirm → stock + journal + report). Purchasing is slice 2. Document 04’s purchasing-before-POS sequence **yields** to 00.

### B.3 User selections for review (not frozen)

Recorded in the [decision register](./ameen-retail-consolidated-decision-amendment-register.md) §2. They **do not** amend Documents 00–08:

| ID | Selection |
|---|---|
| U-01 | Standard selling-floor role: **Salesperson** |
| U-02 | Global role-template catalogue: retain **eight** template concepts |
| U-03 | Business Owner POS: **off by default** |
| U-04 | Permission catalogue: **`roles.view` only**; do not introduce `permissions.view` at this stage |
| U-05 | Platform Administrator and tenant Administrator are **separate** concepts |
| U-06 | Proposed default tenant-owned copies: Business Owner, Administrator, Cashier, Salesperson, Accountant |

**Catalogue-count discrepancy (must not be silently “fixed”):** if Business Owner, Administrator, Cashier, Salesperson, Accountant, Sales Manager, Inventory Manager, Purchasing Officer, and Viewer are all included, that is **nine** names. Document 00/07 currently name **exactly eight**, using Sales Manager not Salesperson. Do not drop a name to force a count of eight.

**Owner identity vs Business Owner role:** do not conflate the protected Owner identity/account with the Business Owner **role**. Protection and recovery remain as specified by Documents 00 §10, 06, and 07 until those contracts are amended together.

### B.4 Proposals (non-authoritative)

| File | Notes |
|---|---|
| [proposals/2026-10-09-foundation-decisions.md](./proposals/2026-10-09-foundation-decisions.md) | Bootstrap D1; reserved `platform.*` keys |
| [proposals/2026-10-09-consolidated-amendments.md](./proposals/2026-10-09-consolidated-amendments.md) | Broader 07/05 draft; includes keys later marked inactive |
| [proposals/2026-10-10-amendment-proposal-r2.md](./proposals/2026-10-10-amendment-proposal-r2.md) | Screen/SD items; `roles.view` proposed; `permissions.view` out of that file |
| [proposals/2026-10-10-revised-amendment-set.md](./proposals/2026-10-10-revised-amendment-set.md) | Explicit grant lists; finance Restricted†; review selectively (register D-18) |
| [proposals/2026-10-10-shared-screen-design.md](./proposals/2026-10-10-shared-screen-design.md) | Shared-screen design; not frozen |
| [2026-10-11-platform-and-role-template-amendments.md](./2026-10-11-platform-and-role-template-amendments.md) | Platform areas, templates, lifecycle; draft; §13 not authorized to implement |

Proposed keys remain **inactive** (handoff + 09 Appendix A): `roles.view`, `permissions.view`, `platform.tenants.view|create|suspend`, `platform.users.view`, `platform.audit.view`, `sales.override_price`.

### B.5 Unresolved conflicts

See §C.3. None of U-01–U-06 is incorporated into frozen Documents 00–08.

---

## C. Preconditions and blockers

Product decisions are distinct from engineering tasks. A later feature being unresolved must not stall unrelated foundation work **except** where that feature’s contract is required to seed or authorize the earlier phase.

### C.1 Must resolve before identity / RBAC / bootstrap / provisioning (Phases 1, 4–6)

These block **correct** first-slice authorization seeds. Until they are closed **or explicitly deferred** (“implement against current Document 07 eight roles and POS Full for Owner”), do not seed roles, template copies, or platform membership.

| ID | Topic | Why it blocks early phases |
|---|---|---|
| D-01 | Sales Manager disposition | Seeds, `GET /roles`, Cashier vs Salesperson vs Sales Manager grants |
| D-02 | Exact eight catalogue names vs nine listed names | Cannot seed templates or Document 07 roles until the set is enumerated |
| U-01 / C1 | Salesperson vs frozen Sales Manager | Document 07 has no Salesperson |
| U-02 / C3 | Global templates vs fixed system roles | Schema (`roles.tenant_id` NULLABLE) is not a complete template-copy model |
| U-03 / C4 | Owner POS off vs 07 POS Full | Wrong POS keys on Owner would ship a security/product defect |
| U-05 / D-03 | Platform vs tenant Administrator | Distinct identities, routes, permissions; no `platform.*` on tenant roles |
| D-04 | Template lifecycle | Who edits global templates vs tenant copies; no silent overwrite |
| D-05 | Role-assignment authority | Who assigns roles; who may edit permission assignments; Owner protection |
| D-06 | Explicit grants for the five default copies | Full/Limited is not an executable seed list except Cashier’s explicit list in 07 §7 |
| D-08 / D-09 | Tenant lifecycle and provisioning | Bootstrap vs create vs provision; ready/failed states; idempotency |
| U-04 / C9 | `roles.view` vs 05 `GET /permissions` vs 09 “do not add `roles.view`” | Cannot implement role listing without a chosen contract |
| Owner protection | Owner identity ≠ Business Owner role | Assignment, transfer, recovery must be written before user-admin APIs |

**Allowed deferral path (must be an explicit product decision, not assumed):** implement Phases 4–6 against **current** Document 07 (eight system roles, Owner POS Full, `GET /roles` mapped to `users.view` per 09 Appendix B item 6, no `roles.view`, no template copy). Record U-01–U-06 as **deferred amendments**. Mixing frozen seeds with unamended selections is forbidden.

### C.2 Must resolve before the named later phase (not before scaffold)

| Topic | First affected phase | Notes |
|---|---|---|
| Five-group navigation vs 07 flat screen map (C5, D-15) | Phase 7 (shell) | Shell can ship Document 07 areas until a nav amendment is approved |
| Platform permission catalogue (C12, D-07) | Phases 5–6 platform APIs; Phase 14 UI | 09 Appendix A: do not invent `platform.*` keys |
| Dashboard metrics / alerts / 60s freshness (C6, D-11, D-17) | Phase 14 | Tenant `GET /dashboard` (05) can exist earlier as a thin read model gated by `dashboard.view` |
| Plans / billing / subscription vs tenant status (C7, D-10) | Phase 14 | 09 §13: do not implement plan gating until a frozen plan model exists |
| Finance payment grants (C14, D-12) | Phase 10 AP payments; Phase 13 finance UI | `payables.create_payment` exists in 07; grants not explicit. `receivables.create_payment` ungranted |
| Payable origin: receipt vs supplier invoice (D-13) | Phase 10 receive/pay | 00 §7: payable from receipt unless a later supplier-invoice spec; 05: pay against payable/receipt |
| Journal HTTP create/post (D-14) | Phase 13 | 00/05: no client `POST /journal-entries` for sales; keys may exist without HTTP |
| `sales.override_price` | Phase 11 | Until 07 adds it, server re-prices (09 Appendix A) |
| Returns/refunds | Phase 12 | Domain/API already specified in 00/04/05; still needs explicit cashier/salesperson grant lists |
| Stock counts / `inventory.count` | After Phase 9 | 07: add key when screens exist; do not seed now |
| Stale 01/06 role and permission examples (D-16) | Phase 1 contract hygiene | Informational for coding if 00/07 are followed; still requires amendment to stop implementer confusion |

### C.3 Conflict register (labels)

| ID | Conflict | Label |
|---|---|---|
| C1 | Salesperson vs Sales Manager | **Must resolve before Phases 4–6** unless Document 07 path is explicitly deferred. **Requires formal amendment** of 00 §11 and 07 §6–§7. |
| C2 | Eight catalogue concepts vs nine names | **Must resolve before Phases 4–6** (or before template seed). **Requires formal amendment**. Do not drop a name arbitrarily. |
| C3 | Global templates vs fixed system roles | **Must resolve before Phases 5–6**. **Requires formal amendment** of 00 §11/§14, 02 roles, 07. |
| C4 | Business Owner POS off vs 07 POS Full | **Must resolve before Phases 4 and 11**. **Requires formal amendment** of 07 §7. |
| C5 | Five nav groups vs 07 flat map | **Can be deferred** to Phase 7. **Requires formal amendment** of 07 §3–§5 if groups become the IA contract. |
| C6 | Platform dashboard/alerts unspecified | **Can be deferred** to Phase 14. **Requires formal amendment** of 02/05/06/07 before that phase. |
| C7 | Tenant lifecycle vs 02 ACTIVE\|SUSPENDED\|ARCHIVED | **Must resolve before Phase 5** if provisioning states are implemented; otherwise implement only 02 statuses. **Requires formal amendment** to add DRAFT/PROVISIONING/FAILED. |
| C8 | Full/Limited vs explicit grants | **Must resolve before Phases 4–6** for any role that will be seeded besides Cashier’s explicit list. **Requires formal amendment** of 07 §7. |
| C9 | `roles.view` / `GET /permissions` / 09 Appendix B | **Must resolve before Phase 6**. **Requires formal amendment** of 05+07 together if `roles.view` is activated. Do not add `permissions.view` (U-04). |
| C10 | Platform template admin vs no tenant role editor | **Must resolve before Phase 6**. **Requires formal amendment**. 00 §14 still lists custom role designer as out of v1 (system roles first). |
| C11 | Salesperson in acceptance tests but not 07 | Same as C1. Informational until 07 is amended. |
| C12 | Missing platform permission catalogue | **Must resolve before** any platform HTTP beyond bootstrap command. **Can be deferred** if first slice uses operator bootstrap only (foundation D1). **Requires formal amendment**. |
| C13 | 2026-10-11 proposal header vs actual path | **Informational/non-blocking**. Correct path only with file-edit authorization. |
| C14 | Finance Full vs ungranted AR; unclear AP grants | **Must resolve before Phases 10 and 13**. **Requires formal amendment** of 07 explicit lists. |
| C15 | 04 purchasing-before-POS vs 00 §15 | **Informational**. This roadmap follows **00**. Non-blocking if phases below are used. |
| C16 | 06 Starter matrix (Manager, optional Accountant POS) vs 07 | **Informational** for implementers who follow 07; **requires amendment** of 06 to stop drift. |
| C17 | 01 roles (Manager, Inventory Clerk) and Settings Roles screen vs 07 | **Informational**; 07 wins. **Requires amendment** of 01. |
| C18 | 05 `GET /permissions` vs U-04 no `permissions.view` | **Must resolve before Phase 6**. Either remove/defer the endpoint or map it to an approved key (not invented). |

---

## D. Ordered implementation phases

**Sequence rationale.** Document 04 lists Purchasing before POS. Document 00 §15 and Document 04’s own note (“First **code** slice: see frozen decisions (POS before full purchasing)”) require **catalog → inventory → POS/CompleteSale** before full purchasing. Accounting **posting primitives** (not finance UI) are required **inside** CompleteSale. Platform Admin seven-area UI and billing wait until their contracts exist.

```
P1 Architecture contract
 → P2 Repo / engineering foundation
 → P3 Persistence, migrations, audit primitives
 → P4 Auth, tenant context, platform/tenant boundary, authorize()
 → P5 Bootstrap (+ provisioning only if contract approved)
 → P6 Users / roles / assignments (approved scope only)
 → P7 App shell, tokens, nav, UI states
 → P8 Catalog (product + default variant + barcode + category)
 → P9 Inventory visibility + opening/adjust integrity
 → P10 POS + sales + tenders + receipt + sales history   [first vertical slice]
 → P11 Returns/refunds
 → P12 Purchasing / receiving (+ AP only if origin/grants approved)
 → P13 Finance read models and reports (where 05/07 complete)
 → P14 Platform dashboard/alerts/ops/billing (if approved)
 → P15 Hardening, security review, backup, staging, deploy
```

Branch + warehouse + POS terminal belong with P4–P5 organization setup and are **entry criteria** for P9–P10 (Document 00 §15 steps 2–5).

---

## E. Phase specifications

Permissions cited below are **Document 07 canonical keys** unless marked **proposed/inactive**.

### Phase 1 — Architecture baseline and implementation contract

**Goal.** Make the written contracts internally consistent for the first slice, or record an explicit deferral of U-01–U-06.

**In scope.** Decision register close-out for D-01–D-06, D-08–D-09, and C9 as they affect seeds; authorize specific frozen-doc edits; consistency pass. Update this roadmap only if phase boundaries change.

**Exclusions.** Application code; silent edits to 00–08; activating proposed keys; wholesale adoption of `2026-10-10-revised-amendment-set.md` (register D-18).

**Dependencies / entry.** None (documentation).

**Deliverables.** Approved decision record; if authorized, amended 07 then 00/02/05/06 (register Gate 2–3); consistency checklist signed.

**Tests.** Document-only: every seed role, API, and screen in the first-slice plan traces to 07 keys.

**Acceptance.** No first-slice permission exists in a seed plan without a 07 definition; platform keys cannot be granted to tenant roles; deferred items are listed as deferred.

**Exit gate.** Written approval of (a) amendment set **or** (b) “implement frozen 07 as-is and defer U-01–U-06.”

**Blocks this phase.** Unwillingness to choose (a) or (b). Catalogue nine-vs-eight left implicit.

---

### Phase 2 — Repository and engineering foundation

**Goal.** Empty greenfield scaffold matching Documents 00 §1, 03, and 09 §3.

**In scope.** `backend/` (Django/DRF layout, `config/settings/{base,development,test,production}`, `shared/`, `modules/` packages **as empty bounded modules**, `tests/`), `frontend/` (Vite/React/TS, feature folders), `infrastructure/` placeholders, `docker-compose.yml` (postgres, redis, backend, celery, frontend per 03), GitHub Actions lint/type/test stubs, lockfiles, `.env.example` without secrets.

**Exclusions.** Business use cases; production deploy; copying Kinetic/old ERP; empty Wholesale/Travel packages; Kubernetes.

**Dependencies / entry.** Phase 1 exit **or** a separate explicit “scaffold only” authorization that still forbids seeding unresolved roles.

**Deliverables.** Runnable empty API health endpoint and empty frontend shell using Document 08 tokens; CI that fails on lint/type errors; Compose brings up postgres/redis.

**Tests.** CI pipeline exists; settings do not load production secrets in test; no second Python `src/` tree.

**Acceptance.** Layout matches 09 §3; Document 08 CSS variables imported; light mode default.

**Exit gate.** Scaffold review against 03/09; no invented modules.

**Blocks this phase.** Lack of implementation authorization (Approval Gate 3).

---

### Phase 3 — Persistence, migrations, transaction conventions, audit primitives

**Goal.** PostgreSQL schemas and cross-cutting persistence rules without product APIs.

**In scope.** Django migrations for Document 02 tables required by later phases, introduced **incrementally** (identity/organization/access/audit/system first; catalog/inventory/sales as those phases start is acceptable). `NUMERIC(19,4)`; `TIMESTAMPTZ`; UUID PKs; `tenant_id` NOT NULL on tenant-owned tables; composite FK preference; idempotency table `UNIQUE(tenant_id, key)`; append-only audit table; outbox table shape; money helpers; no FLOAT.

**Exclusions.** Platform alert/subscription tables until 02 is amended; `supplier-invoices` (00 §7); lot/serial tables; seeding `inventory.count`.

**Dependencies / entry.** Phase 2.

**Deliverables.** Initial migrations; documented transaction decorator/pattern; audit writer primitive (no business events yet).

**Tests.** Migration apply/rollback on empty DB; money columns are numeric; tenant_id null rejected; audit insert cannot be updated/deleted by ordinary ORM update (or equivalent enforcement test).

**Acceptance.** Matches 02 as constrained by 00; 09 §7 composite-FK / NULL `branch_id` trap handled.

**Exit gate.** Migration review; no data migration that scans all tenants unsafely.

**Blocks this phase.** Attempting to persist unapproved template/billing/alert schemas.

---

### Phase 4 — Authentication, tenant context, platform/tenant boundaries, authorization

**Goal.** Login, session cookies, tenant membership, `authorize()`, deny by default.

**In scope.** Identity use cases (04): LoginUser, LogoutUser, ChangePassword, ResetPassword, GetCurrentUser. Argon2id. HttpOnly + Secure + SameSite cookie; CSRF; hashed session token; rate-limited login. `GET /auth/me`. Request context: user, tenant, branch, permissions, request_id. `X-Tenant-Id` as hint. Central `authorize(user, tenant, permission, …)`. Platform vs tenant namespaces in routing (`/platform/*` vs `/app/*`) even if platform APIs are stubs that 403.

**Exclusions.** MFA/SSO/API keys; impersonation; Bearer as the web strategy; `platform.*` enforcement using invented keys; role-designer UI.

**Dependencies / entry.** Phase 3; Phase 1 decision on which role set to seed (frozen 07 vs amended).

**Deliverables.** Auth APIs per 05; membership ACTIVE + tenant ACTIVE required; permission registry **rows** = Document 07 keys only.

**Tests.** Wrong password generic error; revoked session 401; disabled/suspended user blocked; missing permission 403; cross-tenant resource 404; CSRF on cookie POST; cashier (or equivalent seeded role) cannot call `users.create`.

**Acceptance.** 00 §10 and 06 web auth; 09 §12–§13 pipeline; no tokens in localStorage.

**Exit gate.** Security checklist for identity (06 “Must” subset: hashing, sessions, logout revoke, rate limit).

**Blocks this phase.** Seeding Salesperson / Owner POS-off / templates without 07 amendment; granting `platform.*` to tenant roles.

---

### Phase 5 — Bootstrap and tenant provisioning

**Goal.** Controlled first tenant and identities; later, provisioning **only** if contracted.

**In scope (bootstrap — foundation proposal D1, not a frozen schema):** operator management command creating (1) initial platform administrator identity, (2) initial tenant, (3) separate tenant Owner identity. Not public signup. Not an HTTP permission. Subsequent HTTP uses normal authz.

**In scope (provisioning):** only after D-08/D-09 and 02/05/06/07 amendments: idempotent provision job, template copy snapshot, ready vs failed, retry without duplicates.

**Exclusions.** Public registration; using bootstrap as the future provision API; marking tenant ready after partial failure; silent template sync; automatic suspension for overdue billing.

**Dependencies / entry.** Phase 4. Provisioning APIs also need C12 platform keys in 07 + 05 routes.

**Deliverables.** Documented bootstrap command; audit of bootstrap outcomes; if contracted, provision run records.

**Tests.** Bootstrap idempotence or documented one-time guard; platform admin ≠ tenant Owner; tenant B cannot read tenant A; provision retry same key does not duplicate Owner/roles (when that API exists).

**Acceptance.** 00 “platform admins create tenants”; 09: bootstrap is not a substitute for Document 07 on later HTTP.

**Exit gate.** Operator runbook for local/dev bootstrap; production bootstrap policy recorded (still not a public API).

**Blocks this phase.** Implementing multi-tenant provisioning HTTP without platform permission catalogue and lifecycle states.

---

### Phase 6 — User, role, and permission administration (approved scope)

**Goal.** Tenant user invite/activate/assign **existing** roles; no tenant permission editor.

**In scope.** 05 user APIs; invite → employee sets password; `users.assign_roles` cannot assign/remove Owner; list assignable roles.

**Role listing contract (until amended):** 09 Appendix B item 6 maps `GET /roles` to `users.view` and **forbids adding `roles.view`**. U-04 wants `roles.view` activated only after 05+07 amendment. **Do not implement `GET /permissions` as a live product API** until C18 is resolved; U-04 forbids `permissions.view`.

**Exclusions.** Tenant role-permission mapping UI; custom tenant roles; platform Roles & Permissions seven-area product until C10/C12; activating `roles.view` without amendment.

**Dependencies / entry.** Phases 4–5; D-05/D-06 or explicit frozen-07 deferral.

**Deliverables.** Users screens under `/app/settings/users` (`users.view`); assign-roles command; audit of invite/activate/role assign.

**Tests.** Administrator cannot assign Owner; Cashier 403 on invite; listing roles does not leak other tenants; mass assignment cannot bind `is_owner`.

**Acceptance.** 07 §3 no tenant Roles screen; 00 §11.

**Exit gate.** Authz matrix for user APIs 401/403/404/200.

**Blocks this phase.** C9/C18 unresolved if the implementation tries to add `roles.view` or `GET /permissions` as authorized product behavior.

---

### Phase 7 — Application shell, responsive navigation, UI states, tokens

**Goal.** Tenant app chrome that is permission-derived and token-compliant.

**In scope.** `/login`, `/app/*` shell; loading/empty/error/403 states (09 §23); nav from **effective Document 07 permissions**; Inter, `#147D78` via CSS variables, 12px default radius, 16px large surfaces, pills only for avatars/switches/badges; light default.

**Navigation:** use 07 §3 areas until D-15/C5 is approved. Five groups (Home/Sales/Inventory/Finance/Business) are a **proposal**; do not hide a 07 screen solely because grouping is undecided—record unplaced screens as design issues.

**Exclusions.** Invented layouts as a second design system; dark mode as shipping default; pixel-frozen wireframes (08 excludes them).

**Dependencies / entry.** Phase 4 (`/auth/me`); Document 08.

**Deliverables.** Shared layout, guards Auth → Tenant → Permission → page; token usage in buttons/fields/cards.

**Tests.** Vitest/RTL: nav hides items without view permission; direct route without view shows access denied; Playwright smoke: login → dashboard 403-or-allow per seed. Responsive checks for login and shell at desktop and a mobile viewport. Accessibility: focus ring 2px primary (08); labelled controls on login.

**Acceptance.** UI checks are UX only; APIs still authorize.

**Exit gate.** Token review; no second brand hue/font.

**Blocks this phase.** None for frozen 07 nav. Five-group IA blocked on D-15 if treated as required for this phase.

---

### Phase 8 — Product / category catalogue vertical slice

**Goal.** Product with default variant, SKU, barcode, category; no stock quantity on product.

**In scope.** Catalog module; `POST /products` facade (05); tax_rate_id not raw percent; activate/deactivate; `GET /products/lookup?barcode=` (needed by POS); categories. Permissions: `products.*`, `product_categories.*` as used.

**Exclusions.** Full UOM conversion engine (00); lot/serial tracking enabled; price-list admin UI unless 07 keys exist (07 has no price-list CRUD keys—do not invent); `sales.override_price`.

**Dependencies / entry.** Phases 4–7; tax rates referenced per 00 (tax module/schema owns rates).

**Deliverables.** Products and categories screens; OpenAPI slice; tenant-scoped queries.

**Tests.** Duplicate SKU 409/422 per contract; deactivate referenced product conflict; cross-tenant product 404; amounts as strings; `products.view` without `products.create` hides create and API 403.

**Acceptance.** Product ≠ inventory; every product ≥1 variant; `UNIQUE(tenant_id, sku)` and barcode unique per tenant.

**Exit gate.** Catalog slice demo on one tenant.

**Blocks this phase.** Missing tax-rate assignment model if implementation tries raw percent.

---

### Phase 9 — Inventory visibility and stock integrity

**Goal.** Balances materialized from immutable movements; opening/adjust-in for the first slice.

**In scope.** Warehouses (branch default warehouse resolution per 00 §3); `inventory_balances`; `inventory_movements`; adjustment header + reasons; `GET /inventory/products/{id}`; `GET /inventory/movements`; `POST /inventory/adjustments`. WAC on movement and balance. `reserved = 0`. Negative stock forbidden. `SELECT … FOR UPDATE` on concurrent issues (used in P10). Permissions: `inventory.view`, `inventory.view_movements`, `inventory.adjust`. Screen: adjustments require view **and** adjust.

**Exclusions.** Stock-count screens (`inventory.count` not in registry); transfers unless this phase is extended (transfer is in 00/05—may follow opening/adjust but is **not** required for first POS slice); faked reservations.

**Dependencies / entry.** Phase 8; branch + warehouse exist (00 §15 step 2).

**Deliverables.** Inventory screens listed in 07; Inventory application contract `get_availability`, `adjust_stock` (and `issue_stock` interface stub for P10).

**Tests.** Adjustment writes movement + balance in one transaction; cashier without `inventory.adjust` 403; quantity never FLOAT; opening balance movement type used as specified.

**Acceptance.** Source of truth = movements; no `product.quantity`.

**Exit gate.** Stock on-hand visible and consistent after adjust.

**Blocks this phase.** None beyond missing warehouse/branch.

---

### Phase 10 — POS, sales, payments/tenders, receipt, sales history

**Goal.** Complete the Document 00 §15 vertical slice: open register → draft sale → pay → confirm → stock down, payment recorded, journal posted, sale on report/history.

**In scope.** Sales DRAFT/COMPLETED; `POST /sales`, `POST /sales/{id}/payments`, `POST /sales/{id}/confirm`; POS sessions open/close; one open session per register; tenders `cash`, `card`, `mobile_money`, `bank_transfer`, `other` only; server totals; client `unit_price` ignored until override key exists; cash change is not revenue; POS does not write inventory/journals; CompleteSale steps 00 §6; Idempotency-Key on confirm and payment; `pos.create_sale` vs `sales.create` per 07; walk-in customer optional.

**Accounting:** implement `accounting.post_sale` inside the same DB transaction (balanced). Do **not** wait for Phase 13 UI. Minimal COA/seed sufficient to post a retail sale.

**Reporting:** at least sale visible on `GET /sales` and a sales report or dashboard widget gated by `sales.view` / `reports.sales.view` as applicable (07: `sales.view` does not imply `reports.sales.view`).

**Exclusions.** Credit tender; AR; `sales.override_price`; offline POS; Celery on CompleteSale path; Owner POS if U-03 is approved and 07 amended—otherwise follow frozen Full until amended.

**Dependencies / entry.** Phases 8–9; POS terminal; open-session rules; payment methods seeded without `credit`.

**Deliverables.** POS feature, sales history screens, receipt UX (POS-owned); journals created only via accounting contract.

**Tests (mandatory, 00 §13 / 09 §31):** CompleteSale atomic; same Idempotency-Key no double stock/payment; two cashiers stock=1 → one `INSUFFICIENT_STOCK`; journal balances; no float JSON; register not open → domain error; forced failure rolls back sale+stock+payment+journal; tenant isolation; default cashier has no `pos.refund`.

**Browser:** Playwright journey login → product → stock → open register → sell → pay → confirm → stock down → sale visible.

**Acceptance.** Status after confirm is **COMPLETED** not lingering CONFIRMED/PAID.

**Exit gate.** Vertical slice demo; CI includes the tests above.

**Blocks this phase.** C4 if shipping Owner POS contrary to an approved-but-unamended selection; missing accounting post contract; credit tender.

---

### Phase 11 — Returns and refunds

**Goal.** New return documents; original sale immutable; stock and finance reverse in one transaction.

**In scope.** `POST /sales/{id}/return`; `sales_returns.*`; qty ≤ eligible; COMPLETED → PARTIALLY_REFUNDED → REFUNDED; `payments.refund_payment` / accounting reverse via contract; audit.

**Exclusions.** Editing completed sale lines; cashier `pos.refund` / `sales_returns.refund` unless explicit grant (07 default cashier: no `pos.refund`); double-refund races (must lock).

**Dependencies / entry.** Phase 10; reversal semantics already in 00/04/05 (this phase is implementation, not invention).

**Deliverables.** Returns screen (`sales_returns.view`); refund command with Idempotency-Key.

**Tests.** Return qty > eligible rejected; concurrent double refund; cashier without refund permission 403; stock increases per return rules; journal reverse balances; original sale lines unchanged.

**Browser:** return path from 03 E2E list.

**Acceptance.** Returns are new documents.

**Exit gate.** Return journey green in CI.

**Blocks this phase.** Unclear salesperson/cashier refund grants if those roles are seeded without explicit lists (C8).

---

### Phase 12 — Suppliers, purchasing, receiving (slice 2)

**Goal.** PO does not change stock; receipt does; partial receive; payable from **receipt** unless a later invoice spec is approved.

**In scope.** Suppliers master; PO DRAFT → CONFIRMED → PARTIALLY_RECEIVED → RECEIVED; `POST /purchase-orders/{id}/approve` maps to CONFIRMED; receive with Idempotency-Key; `inventory.receive_stock`; `accounting.post_purchase`; purchase returns after RECEIVED (cannot cancel RECEIVED).

**AP payments:** only if D-12/D-13 closed. Until then, **receive and post purchase** without `payables.create_payment` HTTP. 05: supplier payments against payable/receipt, not an unspecified invoice table. 00 §7: do not invent `supplier-invoices` at implementation time.

**Exclusions.** Supplier-invoice module; treating overdue AP as tenant suspension; Inventory Manager / Purchasing Officer seeds unless catalogue decision includes them.

**Dependencies / entry.** Phases 9–10 (inventory + accounting contracts); D-13 before payment-against-payable APIs.

**Deliverables.** Purchasing screens per 07; ReceivePurchase one COMMIT (02/04).

**Tests.** PO confirm does not move stock; partial receive; receive rollback; RECEIVED cannot cancel; cross-tenant PO 404; `purchase_orders.approve` permission.

**Acceptance.** Purchasing never writes inventory tables.

**Exit gate.** Slice-2 demo: PO → receive → stock up → journal.

**Blocks this phase.** D-13 if the work item is AP **payment**; not blocked for receive-only if payable row is created from receipt without payment API.

---

### Phase 13 — Finance and reporting (where contracts are complete)

**Goal.** Read-only accounting and reports already implied by posting; expenses if in v1 (00 §8).

**In scope.** `GET /accounting/accounts`, journal-entries, trial-balance, P&amp;L as in 05; `reports.finance.view` / domain report keys; expenses create/approve/cancel without posted DELETE. Widgets require domain view (cashier must not see finance).

**Exclusions.** Client `POST /journal-entries` for sales (00); HTTP `finance_transactions.create`/`post` until D-14; `receivables.create_payment` until granted; plan-based report gating.

**Dependencies / entry.** Phase 10 postings exist; D-12/D-14 for payment/journal write APIs; explicit Accountant/Owner finance key lists before seeding those buttons.

**Deliverables.** Finance screens that 07 already maps (`finance_accounts.view`, etc.) **only** for operations that 05 names.

**Tests.** Posted journal debit=credit; expense posted cannot DELETE; `reports.sales.view` not implied by `sales.view`; cashier dashboard has no finance widget.

**Acceptance.** 07 screen entry; 05 accounting is read for sales path.

**Exit gate.** Report matches a completed sale’s journal.

**Blocks this phase.** C14/D-12/D-14 for write APIs; otherwise read-only reports can ship.

---

### Phase 14 — Dashboard, alerts, platform operations, billing (if approved)

**Goal.** Platform Admin seven areas and tenant dashboard **only** after contracts exist.

**In scope (tenant):** `GET /dashboard` + `dashboard.view`; widgets gated by domain view (07 §4).

**In scope (platform):** seven areas from the 2026-10-11 proposal **after** 02/05/06/07 amendments: metrics, alerts lifecycle, tenant management, provisioning UI, platform users, global templates, audit. Billing/plans only if D-10 approved. Freshness 60s is a **target to validate**, not a frozen SLA.

**Exclusions.** Invented `platform.*` keys; auto-suspend on overdue; treating acknowledgement as resolution; email failure deleting alerts; mixing `/platform` and `/app`.

**Dependencies / entry.** C6, C7, C12, D-07, D-10, D-11, D-17 closed **or** this phase is skipped in first release.

**Deliverables.** OpenAPI for platform routes; alert state machine tests; tenant list does not offer ordinary permanent delete.

**Tests.** Platform API 403 for tenant users including Owner; metric APIs enforce permissions; alert ack ≠ resolve; provisioning retry idempotent; overdue ≠ suspend.

**Acceptance.** Matches approved amendments, not the draft proposal alone.

**Exit gate.** Separate product approval that platform v1 is in the release.

**Blocks this phase.** Any missing platform permission/API/schema. **Non-blocking for first retail slice.**

---

### Phase 15 — Release hardening, security review, backup/recovery, staging, deployment

**Goal.** Production-capable operations for whatever slice was authorized.

**In scope.** HTTPS/HSTS, CORS allowlist, security headers, secret scanning, dependency/image CVE scan, backups of PostgreSQL, restore drill, DigitalOcean + Nginx + Gunicorn + managed PG + Redis + object storage (03); staging environment; 09 Definition of Done; 06 blocking tests; Playwright critical E2E; OpenAPI complete for shipped endpoints.

**Exclusions.** Kubernetes; claiming deferred features exist; production deploy without Approval Gate 4.

**Dependencies / entry.** All in-release phases’ exit gates.

**Deliverables.** Runbook (README listed this as not yet in the pack—create only when authorized as ops docs); backup/restore evidence; signed security review.

**Tests.** Full 00 §13 set; 06 tenant matrix; secret not in git; CI green.

**Acceptance.** Login working ≠ security done (06).

**Exit gate.** Staging sign-off; then **separate** production authorization.

**Blocks this phase.** Open P0 security gaps; unresolved first-slice authz seeds; missing backups.

---

## F. Cross-cutting engineering gates

Apply to every in-scope phase after P2. Fail the merge if any shipped endpoint violates them (09 §38).

| Gate | Rule | Evidence |
|---|---|---|
| API contract | `/api/v1`, envelope, `meta.pagination`, decimal strings, UTC `Z`, command URLs | Contract tests vs OpenAPI |
| Tenant isolation | Body must not set `tenant_id`; `X-Tenant-Id` hint; cross-tenant **404** | Per-resource tests |
| Object-level authz | Branch scope ≠ permission (07 §1) | Branch-restricted user cannot `?branch_id=` another branch |
| Deny by default | Missing 07 key → 403; no `if role ==` | Authz tests |
| Platform/tenant split | No `platform.*` on tenant roles; routes never mixed | Negative tests |
| Transactions | CompleteSale / receive / return one COMMIT; rollback on failure | Forced-failure tests |
| Idempotency | Confirm, payment, receive, return/refund, transfer complete | Same key → same result |
| Audit | Append-only; no secrets/PAN; login, role assign, stock, sale, payments | Audit row assertions |
| Schema safety | NUMERIC(19,4); TIMESTAMPTZ; migrations reviewed | Migration tests |
| Money/time | No float JSON; tenant TZ for “today” reports | API fixtures |
| CI | Lint, pytest, tsc, frontend unit, migration check, build | GitHub Actions |
| Security scans | Lockfiles, secret scan, image CVE | CI jobs |
| UX | Document 08 tokens; loading/empty/error/403; responsive + a11y on login, POS, checkout | RTL + Playwright + token review |

---

## G. First-release recommendation

**Essential (narrow, coherent retail loop — Document 00 §15 plus returns from 03 E2E):**

1. Identity, tenant membership, RBAC (frozen 07 **or** amended grants—never a mix)
2. Branch, warehouse, POS terminal
3. Product + default variant + barcode + category
4. Opening/adjust-in stock
5. Open register → POS sale → tender → CompleteSale → stock + payment + balanced journal
6. Sales history / receipt reprint as granted
7. Sales return/refund with permissions as granted
8. Tenant dashboard **without** finance widgets for cashier
9. Operator bootstrap (not public signup)

**Defer (do not imply they exist in the first release):**

- Full purchasing/receiving/AP (slice 2) — unless product explicitly pulls slice 2 into the same release after D-13
- Expenses, full COA admin, client journal posting
- Platform Admin seven areas, alerts engine, plans/billing
- Global template editor and template migration
- Stock counts, transfers, price-list CRUD, ownership-transfer UI
- `sales.override_price`, credit/AR, `permissions.view`
- Five-group navigation as a frozen IA (use 07 map)
- MFA, SSO, offline POS, impersonation

Purchasing may be the **second** release immediately after the POS loop, matching 00 “Purchasing receive is slice 2.”

---

## H. Traceability template

Copy one row per work item. Do not invent keys or routes; leave cells **blocked** if the pack has no entry.

| Field | Value |
|---|---|
| Work item ID | |
| Summary | |
| Requirement / doc | e.g. `00` §15, `07` §5 POS, `05` Sales |
| Domain module | e.g. `sales` (03/04/09 `backend/modules/sales`) |
| Screen / route | e.g. `/app/pos` — enter `pos.view` |
| API operation | e.g. `POST /api/v1/sales/{id}/confirm` |
| Permission key | Document 07 string only (or **inactive/proposed — do not implement**) |
| Database entities | e.g. `sales.sales_orders`, `inventory_movements`, `journal_entries` |
| Tests | unit / API / integration / Playwright / migration / security |
| Acceptance criteria | measurable |
| Explicit exclusions | e.g. no credit tender; no Celery on this path |

---

## I. Approval gates

These gates are sequential and **separate**. Passing one does not pass the next.

| Gate | Approves | Does not approve |
|---|---|---|
| **1. Architecture amendments** | Specific edits to named frozen documents after D-01–D-18 (or recorded deferrals) | Coding, scaffolding, seeding proposed keys |
| **2. This implementation roadmap** | Phase order, first-release cut, test/gate expectations | Coding; frozen-doc edits |
| **3. Begin repository/application implementation** | Named scope (e.g. “Phases 2–10 only, frozen 07 seeds”) | Staging/production; platform UI; unlisted phases |
| **4. Staging and production deployment** | Staging first, then production, with backup/restore and 06 blocking tests | Features not in the authorized slice |

**This roadmap does not authorize implementation.**

---

## J. Document map (relative)

- Frozen: [00](./00-frozen-decisions.md) · [01](./01-system-requirements-and-domain.md) · [02](./02-database-schema.md) · [03](./03-technical-architecture.md) · [04](./04-application-module-design.md) · [05](./05-api-contract.md) · [06](./06-security-and-authorization.md) · [07](./07-permission-matrix-and-screens.md) · [08](./08-ui-design-tokens.md) · [tokens.css](./tokens.css)
- Engineering rules: [09](./09-implementation-specification.md)
- Decisions: [ameen-retail-consolidated-decision-amendment-register.md](./ameen-retail-consolidated-decision-amendment-register.md)
- Index: [README.md](./README.md)

---

## K. Stop line

No application code, migrations, UI, infrastructure, or tests are authorized by this document. The next engineering action is **Approval Gate 1 and/or 2**, then a **separate** instruction naming the permitted implementation scope.
