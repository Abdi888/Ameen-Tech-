# Ameen Retail ERP — Platform and Role-Template Amendments

**Document:** `docs/architecture/proposals/2026-10-11-platform-and-role-template-amendments.md`  
**Status:** Draft for review — not approved for implementation  
**Prepared:** 2026-10-12  
**Scope:** Consolidates the 2026-10-11 product handoff with the repository findings.  
**Authority:** Documents 00–08 remain frozen. This proposal does not amend them.

---

## 1. Purpose and change control

The repository currently contains the architecture pack (Documents 00–09), proposal files, and IDE/agent rules, but no application code, migrations, frontend, Docker Compose configuration, or tests. The 2026-10-11 product handoff is not yet persisted in the repository.

This proposal records the intended platform administration, tenant role-template, navigation, and tenant lifecycle design; identifies conflicts with frozen contracts; and presents decisions that must be approved before implementation.

### Non-negotiable boundaries

1. This is a greenfield project. Do not reuse code from Kinetic ERP or the older Ameen ERP.
2. Do not create application code, migrations, frontend screens, or infrastructure files until implementation is explicitly authorized.
3. Do not edit Documents 00–08 until the relevant amendment is explicitly approved.
4. Document 07 remains the authority for tenant permission identifiers and screen-to-permission mappings until formally amended.
5. Proposed permission keys remain inactive and must not be seeded, referenced by active route guards, or treated as authorized API contracts until Documents 05 and 07 are amended together.
6. Keep platform authorization separate from tenant authorization. No `platform.*` permission may be assigned to a tenant role.
7. Preserve the approved UI tokens: primary `#147D78`, Material 3 foundations, Inter typography, light mode by default, 12px default radius and 16px for large dialogs/panels.
8. The bootstrap command is an operator-controlled one-time operation, not public signup and not a substitute for a future platform provisioning workflow.

---

## 2. Proposed platform administration scope

The platform administration application is organized into seven areas:

1. Dashboard
2. Tenant Management
3. Plans & Billing
4. Tenant Provisioning
5. Platform Users
6. Roles & Permissions
7. Audit & Security

These are product areas, not yet a complete route, permission, API, or data-model contract. Each requires explicit screen definitions and platform-only authorization rules before implementation.

### 2.1 Dashboard and alerts

The platform dashboard may show operational metrics and alerts, subject to platform permissions. Proposed alert lifecycle:

`Triggered → Active → Acknowledged → Resolved`

Rules proposed for review:

- Acknowledging an alert does not resolve it.
- Identical unresolved alerts use a deduplication key and increase an occurrence count rather than creating unbounded duplicates.
- Critical alerts remain visible until acknowledged.
- Alert state transitions and their actors/timestamps are auditable.
- Email notification failure must not delete or suppress the in-system alert.
- Dashboard cards and their backing APIs must independently enforce authorization.
- Proposed freshness target: metrics updated within 60 seconds, where the metric's data source supports it.
- Subscription overdue must not automatically suspend a tenant unless a separate, explicit policy is approved.

**Not yet specified:** exact metrics, severity thresholds, alert triggers, notification retry policy, retention, and the platform permission keys for viewing, acknowledging, and resolving alerts.

### 2.2 Tenant Management and lifecycle

Tenant creation, provisioning, activation, suspension, billing status, archival, and ownership transfer are distinct operations.

Proposed lifecycle states to validate:

- `DRAFT`
- `PROVISIONING`
- `ACTIVE`
- `SUSPENDED`
- `ARCHIVED`
- `PROVISIONING_FAILED` (or an equivalent failed provisioning state)

The final state machine must define allowed transitions, actors, side effects, recovery behavior, and audit events. Do not conflate subscription delinquency with tenant suspension. Permanent deletion must not be a casual tenant-list action.

The approved bootstrap design remains separate: a controlled operator command creates a platform administrator, an initial tenant, and a separate Business Owner identity. It is not a public endpoint and does not use an HTTP permission key. Subsequent requests use normal API authorization.

### 2.3 Plans & Billing

Plans and billing are a platform concern, separate from the tenant's operational status. The minimum schema, plan lifecycle, billing status, payment recording/reconciliation, and suspension policy are not yet defined by Documents 00–09. Do not implement billing behavior until its API, data model, permissions, and failure cases are specified.

### 2.4 Tenant Provisioning

Provisioning must be distinct from tenant creation and bootstrap. Proposed requirements:

- Provisioning is an explicit, auditable operation.
- Retrying with the same idempotency key must not create duplicate tenants, Owners, memberships, or roles.
- A tenant must not become active/ready until all required provisioning steps succeed.
- Partial failures must be visible and recoverable by an authorized operator.
- Provisioning runs record status, timestamps, attempted steps, and failure information without leaking secrets.
- Provisioning must copy selected global role templates into tenant-owned role records.

**Not yet specified:** provisioning API routes, idempotency-key scope/retention, retry policy, operator permissions, and the exact required provisioning steps.

### 2.5 Platform Users, Roles & Permissions, Audit & Security

Platform identities and platform roles must be modeled separately from tenant users and tenant roles. Platform role membership must not be inferred from a tenant membership or a tenant role.

The platform permission catalogue must cover at least:
- tenant lifecycle actions;
- provisioning actions and retries;
- plan and billing administration;
- platform user administration;
- global role-template administration;
- platform dashboard and alert access;
- platform audit access.

The complete permission identifiers and screen/API mappings are unresolved. The currently proposed `platform.*` keys are proposals only and are not active permissions.

Platform audit events should include tenant suspension/reactivation, provisioning start/success/failure/retry, global template creation/edit/version changes, platform role/permission changes, billing actions, and alert acknowledgement/resolution.

---

## 3. Tenant role-template architecture

### 3.1 Proposed ownership model

Use four distinct concepts:

1. **Platform users and platform roles** — authorize operations on the platform control plane.
2. **Global role templates** — centrally maintained blueprints, not directly assignable to tenant users.
3. **Tenant-owned role copies** — independent role records created during provisioning.
4. **Tenant users and tenant memberships** — users assigned tenant-owned roles only.

At provisioning time, each selected global template is copied into a tenant-owned role with a snapshot of its permission assignments. A tenant role must not remain dynamically linked to the live permission set of the global template.

Required invariants:

- A tenant cannot assign a global template directly to a user.
- Editing a global template does not silently alter existing tenant role copies.
- Editing a tenant role does not change the global template or any other tenant's role.
- Template lineage/version metadata may be retained for traceability, but lineage must not imply live inheritance.
- Platform operators are the only actors allowed to create/edit global templates and their permission assignments.
- Tenant users may assign users to existing tenant-owned roles only if the applicable Document 07 permissions authorize that action.
- The Business Owner identity is protected and cannot be assigned through ordinary role assignment.

### 3.2 Template defaults versus optional templates — decision required

The handoff names four default roles:
- Business Owner
- Cashier
- Salesperson
- Accountant

The frozen pack defines eight system roles, including Administrator, Sales Manager, Inventory Manager, Purchasing Officer, and Viewer. The repository findings do not establish whether all eight should remain provisioned by default or become a larger optional global-template catalogue.

**Recommended decision for approval:** retain the eight existing role concepts as the initial global template catalogue, but provision only an explicitly selected default set per tenant. The default set must be finalized in a separate approved table. This preserves useful role templates without forcing every tenant to receive every role.

The following must be explicitly resolved before finalizing the table:
- Is Administrator a default tenant role, a platform role, or both as two distinct concepts? It must never be conflated across the two authorization domains.
- Should Salesperson replace Sales Manager, coexist with it, or be a renamed template with a new permission set?
- Should Inventory Manager, Purchasing Officer, and Viewer remain optional templates?
- Is Business Owner a protected tenant identity/role, and is it excluded from ordinary role assignment as already specified by Document 07?

### 3.3 Template changes and upgrades

A global template change affects future copies by default. Existing tenant copies remain unchanged.

If existing tenants are to receive a later template revision, that must be a separate, explicit migration operation with:
- a documented source and target template version;
- a preview/diff of permission changes;
- an authorized operator;
- tenant selection and a clear scope;
- audit records;
- failure handling and retry behavior;
- a rule for preserving tenant-specific edits.

No silent overwrite or automatic permission expansion is permitted.

### 3.4 Explicit permission lists

Permission assignments must be expressed as explicit permission-key lists in the authoritative contract. Labels such as `Full`, `View`, or `Limited` are not sufficient as implementation inputs unless Document 07 defines their exact expansion and guarantees the expansion cannot change unexpectedly.

Role names must never grant permissions by implication. Every permission must be listed and checked against the canonical registry.

The frozen matrix grants Business Owner broad access, including Full POS, while the handoff says Business Owner POS should be off by default. This is a contract conflict and must be resolved before seeds or route guards are implemented.

---

## 4. Tenant navigation proposal

The proposed tenant navigation has five top-level groups:

1. **Home** — dashboard, alerts, recent activity, and key metrics.
2. **Sales** — POS (only when authorized), sales history, receipts, returns, and customer-facing sales workflows.
3. **Inventory** — products, categories, stock levels, and stock adjustments.
4. **Finance** — expenses, finance/accounting workflows, and finance-related reporting where authorized.
5. **Business** — users, settings, suppliers/purchasing administration, general reports, and audit where authorized.

This is a navigation grouping only. It does not grant permission and must not change the authorization boundary of any screen or API.

**Provisional placements requiring review:** Purchasing, Expenses, Reports, Audit, and Users may not fit neatly into the five groups. Record each screen's final placement in Document 07 and retain every authorized screen even if its placement is not obvious. The final route-to-screen-to-view-permission matrix must be approved before UI implementation.

Navigation must be derived from the user's effective permissions and relevant product capabilities. Hiding a navigation item is not a substitute for server-side authorization.

---

## 5. Tenant lifecycle and ownership safeguards

Before implementation, define the tenant state machine and the API behavior for:
- create tenant;
- begin provisioning;
- retry or recover provisioning;
- activate after successful provisioning;
- suspend and reactivate;
- archive;
- transfer or recover ownership;
- inspect operational health.

Ownership transfer requires a dedicated, auditable flow. The frozen pack references ownership-transfer behavior, but the relevant permission identifier is not in the canonical Document 07 registry. Do not invent or activate a key without amending the permission and API contracts together.

The tenant list's operational-health indicator must have explicit, testable criteria; it must not be a vague composite status.

---

## 6. Proposed schema additions — not approved for implementation

The following are candidate concepts only. Exact table names, columns, foreign keys, constraints, and migration strategy belong in Document 02 after approval:

- platform user/membership and platform role/permission assignments;
- global role templates and template versions;
- tenant role copy lineage, such as `copied_from_template_id` and source version;
- provisioning runs and step-level status;
- subscriptions and billing state;
- platform alerts, deduplication identifiers, occurrence counts, acknowledgements, and resolution metadata;
- platform audit events or a clearly separated platform event scope.

The design must enforce tenant ownership at the database and application layers. A nullable `roles.tenant_id` plus `is_system_role` is not by itself a complete specification of the distinction between global templates and tenant-owned role copies.

---

## 7. Proposed API contract additions — not approved for implementation

Document 05 must define platform API routes and authorization before any corresponding endpoint is implemented. Required route families include:

- platform tenant listing/detail and lifecycle actions;
- provisioning start/status/retry;
- platform users and platform role assignments;
- global role-template listing/detail/create/edit/versioning;
- plan and billing administration;
- platform dashboard metrics;
- alert listing, acknowledgement, and resolution;
- platform audit search.

For each endpoint, Document 05 must specify request/response schemas, status codes, validation, authorization, idempotency, transaction boundaries, audit behavior, and tenant/platform scoping. Tenant-facing `GET /roles` must return only the current tenant's assignable tenant-owned roles.

Do not activate a permission key until its matching route and screen behavior are specified in Document 05 and its identifier/grant rules are approved in Document 07.

---

## 8. Permission-key proposals and safeguards

The following keys have been proposed but are **inactive** until the required contract amendments are approved:

- `roles.view`
- `permissions.view` (decision required: include it or use `roles.view` only for the relevant catalogue UI)
- `platform.tenants.view`
- `platform.tenants.create`
- `platform.tenants.suspend`
- `platform.users.view`
- `platform.audit.view`

Additional platform permissions will be required for provisioning, plans/billing, global templates, platform roles, dashboard metrics, and alert lifecycle actions. Their names and grants are not yet specified; do not infer them from this list.

Other safeguards:
- `sales.override_price` remains inactive until Documents 00, 05, and 07 are amended together.
- `receivables.create_payment` remains ungranted unless explicitly approved in the authoritative role matrix.
- `payables.create_payment` already exists in Document 07, but the intended grants for Business Owner, Administrator, and Accountant must be made explicit in the amended role matrix before implementation.
- Resolve the supplier-invoice versus goods-receipt origin conflict for payables before implementing AP payments.

---

## 9. Conflicts that must be resolved

| ID | Conflict | Required decision |
|---|---|---|
| C1 | Handoff names Salesperson; frozen pack names Sales Manager | Rename, replace, or retain both with explicit grants |
| C2 | Handoff describes four default roles; frozen pack defines eight system roles | Decide catalogue versus default-provisioned set |
| C3 | Platform role/template administration is not fully modeled | Define platform roles and separation from tenant roles |
| C4 | Business Owner POS off by default versus frozen POS Full | Approve one rule and update the seed/grant matrix |
| C5 | Five navigation groups versus existing flat screen map | Approve a complete screen-to-group mapping in Document 07 |
| C6 | Platform dashboard and alert engine are unspecified | Define metrics, triggers, lifecycle, permissions, and data model |
| C7 | Tenant lifecycle and subscription/billing lifecycle are not separated in the schema | Define states and transitions independently |
| C8 | “No automatic extra grants” conflicts with broad `Full` matrix labels | Replace shorthand with explicit permission-key lists |
| C9 | Several existing role grants and permission references are inconsistent across Documents 06, 07, and 09 | Reconcile the canonical registry and examples before seeding |

Additional frozen-pack tensions remain:
- Finance `Full` conflicts with notes that `receivables.create_payment` is unused until a future Starter-credit feature.
- Examples in Document 06 include permission identifiers not in Document 07's canonical registry.
- Ownership-transfer/danger-key examples are not all represented in Document 07.
- The payables payment origin/receipt endpoint contract remains unresolved.

---

## 10. Acceptance criteria

### Tenant isolation and authorization
- Cross-tenant access to tenant-scoped resources returns the contractually specified not-found response and does not disclose resource existence.
- Tenant users cannot access platform APIs or global-template administration, regardless of tenant role.
- Direct URL access without the required view permission is denied by the server.
- Cashier, Salesperson, and Accountant cannot invite users, adjust stock, create roles, or edit role permissions unless an explicit approved grant permits the operation.
- Business Owner cannot be assigned through ordinary role assignment or removed outside the approved ownership-transfer flow.
- If Business Owner POS is approved as off by default, both the POS route and sale-creation API deny access without the required POS keys.

### Role templates and provisioning
- Provisioning copies selected templates into independent tenant roles with the permission snapshot that existed at copy time.
- Editing a global template does not alter an existing tenant copy.
- Editing a role for tenant A does not affect tenant B or the global template.
- Retrying provisioning with the same idempotency key creates no duplicates.
- Partial provisioning failure does not mark the tenant active/ready and is recoverable and auditable.
- Template upgrades are explicit, reviewable, and auditable.

### Platform dashboard and alerts
- Each metric and alert API enforces platform authorization independently of UI visibility.
- Alert acknowledgement does not resolve the alert; each transition is audited.
- Duplicate unresolved alerts merge occurrence counts according to the approved deduplication policy.
- Critical-alert visibility follows the approved acknowledgement/resolution rules.
- Notification delivery failure leaves the in-system alert intact.
- Overdue subscription does not suspend a tenant unless an independently approved policy requires it.

### Navigation
- Navigation is permission-derived and shows only authorized screens.
- Navigation groups do not grant permissions.
- Every authorized screen remains reachable even if its group placement is unusual.
- API authorization remains effective when requests bypass the UI.

### Bootstrap and audit
- The controlled bootstrap creates a platform administrator, an initial tenant, and a separate Business Owner identity.
- Bootstrap is not exposed as public signup or a public provisioning endpoint.
- Platform lifecycle, template, permission, billing, alert, and provisioning actions are auditable.
- Tenant user-role assignment, invitations, and ownership-transfer attempts are audited according to the approved contract.

---

## 11. Recommended approval sequence

1. Resolve the six product/contract questions below.
2. Approve this proposal as the source for the handoff decisions, with any edits recorded explicitly.
3. Amend Documents 00–08 only with explicit authorization, prioritizing Documents 02, 05, 06, and 07 where schema, API, security, and permission contracts intersect.
4. Reconcile the stale references and grant ambiguities across Documents 01, 06, 07, and 09.
5. Run a contract consistency review. Do not scaffold permission seeds until the registry, explicit role grants, routes, and screen mappings agree.
6. Only after the contract is approved and implementation is separately authorized, begin the greenfield scaffold and staged implementation.

---

## 12. Decisions requested

Please confirm or revise each recommendation. No recommendation below is considered approved merely because it appears in this draft.

### D1 — Salesperson versus Sales Manager
**Recommendation:** Keep Salesperson as the standard selling-floor template and retain Sales Manager only if a separately defined supervisory grant set is required. Do not silently rename the existing role without reviewing its permission set.

### D2 — Global template catalogue versus default roles
**Recommendation:** Keep the eight existing role concepts as the initial global template catalogue, while making the per-tenant default-provisioned set explicit. Do not automatically provision every template. Decide whether the four handoff roles plus Administrator are the default set, and define Administrator as a tenant role distinct from any platform role.

### D3 — Business Owner POS default
**Recommendation:** Set Business Owner POS access to **off by default**, with POS granted only through an explicit, approved role/permission configuration. This requires an amendment to the frozen Document 07 matrix and seed rules; it must not be implemented before approval.

### D4 — `permissions.view`
**Recommendation:** Start with `roles.view` for role management screens and omit `permissions.view` unless the product requires a separate permission-catalogue screen. If that screen is required, define its exact platform/tenant scope and grant rules before adding the key.

### D5 — Persistence
**Recommendation:** Persist this as `docs/architecture/proposals/2026-10-11-platform-and-role-template-amendments.md` as a non-frozen review proposal. Keep Documents 00–08 unchanged until amendment approval.

### D6 — Prior amendment package
**Recommendation:** Review `2026-10-10-revised-amendment-set.md` selectively, not wholesale. Consider explicit finance/role grant lists and `roles.view`, but do not activate `permissions.view`, `platform.*`, or any other proposed key until the relevant Documents 05 and 07 amendments are approved together.

---

## 13. Implementation gate

**Current status: NOT AUTHORIZED TO IMPLEMENT.**

This proposal does not authorize:
- edits to Documents 00–08;
- application code, migrations, UI, or infrastructure scaffolding;
- permission seeding or route-guard activation for proposed keys;
- global role-template or provisioning implementation.

Implementation requires explicit approval of the relevant contract changes and a separate instruction to begin coding.
