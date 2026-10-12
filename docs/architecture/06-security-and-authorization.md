# Ameen Retail — Security & Authorization Design v1

Independent of the old ERP. Coherent security architecture — not permissions bolted on later.

Assumptions: multi-tenant SaaS, retail first, web + API, PostgreSQL, separate frontend, owners and employees in tenant workspace, **no public tenant self-registration**, platform admins create tenants, financial/inventory ops need stronger controls than CRUD.

---

## Objectives

1. Tenant isolation  
2. Identity security  
3. Authorization (who vs what)  
4. Least privilege  
5. Operational integrity (refunds, adjustments, voids, user admin)  
6. Accountability (user, tenant, action, resource, time, outcome)

Frontend is UX. **Backend enforces.** Deny by default. Never trust client permission checks.

## Threat model

External API abuse · cross-tenant via `X-Tenant-Id` · IDOR/BOLA · privilege escalation · role PATCH to OWNER · session theft · CSRF (cookies) · XSS in names/notes · brute-force login · insider cashier refund/cash theft.

## Identity model

User → TenantMembership (role, status) → Role → Permissions.

Entities: User, Tenant, TenantMembership, Role, Permission, RolePermission, Session, LoginAttempt, PasswordResetToken, EmailVerificationToken, AuditLog.

MVP skip unless needed: MFAFactor, APIKey, TrustedDevice. **Design so MFA can be added.**

### User

id, email, password_hash (Argon2id), names, phone, status (ACTIVE|INVITED|SUSPENDED|DISABLED), email_verified_at, last_login_at. Do not casual-delete (history).

### Tenant

status ACTIVE|SUSPENDED|ARCHIVED. Suspended → deny normal ops.

### Membership

UNIQUE(tenant_id, user_id). Status ACTIVE|INVITED|SUSPENDED|REMOVED. Operate only if user + membership + tenant ACTIVE.

### Owner

Protected system role. Admins cannot assign/remove Owner. Ownership transfer = explicit confirmed command + audit.

## Roles (v1)

Canonical list and permission keys: **document 07**.

Business Owner, Administrator, Accountant, Sales Manager, Inventory Manager, Cashier, Purchasing Officer, Viewer.

No tenant role/permission editor. No generic Manager role.

## Permissions

Format `<resource>.<action>`. Actions not screens. One registry for UI, API, docs.

Users: view, invite, update, suspend, remove  
Products: view, create, update, archive  
Inventory: view, adjust, receive, transfer, count  
Sales: view, create, update, confirm, void, refund  
Purchases: view, create, update, receive, cancel  
Customers/Suppliers: view, create, update, archive  
Expenses: view, create, update (reverse posted; no silent delete)  
Reports: sales.view, inventory.view, financial.view, profit.view  
Settings: view, update  
POS: pos.view, pos.create_sale, pos.open_register, pos.close_register, pos.cash_in, pos.cash_out (full list in 07)  
Platform (separate): platform.tenants.*, platform.users.*, platform.audit.view  

Danger: LOW view · MEDIUM create/update · HIGH refund/adjust · CRITICAL suspend user / ownership.transfer / security.settings.update.

## Authorization decision

Authentication → Tenant membership → Permission → Resource scope (`tenant_id`, branch) → Domain policy (`ALLOW|DENY|REQUIRE_APPROVAL`) → Allow.

Central `authorize(user, tenant, permission, resource?)`.

RBAC is enough for MVP. No ABAC/OPA/ReBAC.

Refund/discount thresholds are **policies**, not extra roles (e.g. cashier ≤ 5%, manager ≤ 20%).

Cross-tenant: sale.tenant_id must match context. Prefer **404** for other-tenant IDs. Public IDs UUID.

`X-Tenant-Id` → parse → membership for **this user** → tenant active → context. Else 403.

Never accept `tenant_id` in JSON body. Composite FKs for tenant integrity.

## Authentication & sessions

Email + password → verify hash → **server session**. Cookie: HttpOnly, Secure, SameSite Lax/Strict.

Store **token_hash** in `sessions` (user_id, tenant_id, created, expires, last_used, revoked, ip, user_agent).

Idle ~8h, absolute ~30d (tune later). POS may later need faster switch — not a second identity stack.

Logout **revokes** server session. Password change/reset invalidates sessions.

Passwords: length over hieroglyph rules; rate-limit; optional compromised-password check.

Reset: random token, hashed, short-lived, single-use, never logged.

Invite flow: admin invites → email → employee sets password → ACTIVE. Admins do not set employee passwords.

Lockout: rate limit + progressive delay + temporary lock, not permanent after 5 tries.

Login attempts logged (no secrets). Failure message: **Invalid email or password.**

MFA recommended later for Owner/Admin/Accountant; optional in MVP.

## POS / cash / inventory / finance

Cashier must not access users, roles, business/financial settings. POS surface: products, customers, cart, payments, sales, receipts, cash drawer.

Cash in/out/adjust: reason + audit.

Stock only via inventory transactions. Posted financials: reverse, don’t DELETE.

## Audit vs security events

Audit: business actions (sale.refunded, inventory.adjusted) — immutable for tenants.  
Security events: login.failure, permission.denied, session.revoked.

No passwords, tokens, PAN in metadata.

## API security

Every endpoint declares a permission. Mass-assignment allow-lists (`is_owner` never bindable). Input validation. File uploads: MIME, size, normalize name, object storage, signed URLs; never execute uploads.

Secrets in env. Separate dev/staging/prod credentials. No production stack traces.

CORS allowlist. CSRF if cookies. Security headers: CSP, HSTS, X-Content-Type-Options, Referrer-Policy, frame ancestors. HTTPS only; Secure cookies.

Rate limit login/reset/invite harder than GET products.

DB app role least privilege; TLS to DB; don’t encrypt-everything blindly.

Exports need explicit permission (`reports.sales.export`).

## Starter role matrix

| Capability | Owner | Admin | Manager | Cashier | Inventory | Accountant |
|---|---|---|---|---|---|---|
| POS sales | ✓ | ✓ | ✓ | ✓ | — | optional |
| Refunds | ✓ | ✓ | ✓ | policy | — | — |
| Products | ✓ | ✓ | ✓ | view | ✓ | — |
| Inventory | ✓ | ✓ | ✓ | view | ✓ | — |
| Purchases | ✓ | ✓ | ✓ | — | ✓ | — |
| Customers | ✓ | ✓ | ✓ | ✓ | — | ✓ |
| Suppliers | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| Expenses | ✓ | ✓ | ✓ | — | — | ✓ |
| Financial reports | ✓ | ✓ | ✓ | — | — | ✓ |
| Users | ✓ | ✓ | limited | — | — | — |
| Settings | ✓ | ✓ | limited | — | — | — |

Admin cannot transfer ownership or remove/assign Owner. Manager cannot manage system access unless granted. Cashier cannot manage users/roles/settings.

## Platform vs tenant

Do not mix namespaces. **No impersonation in MVP.** If added later: explicit reason, temporary session, heavy audit.

## Frontend

Same permission codes. Guards: Auth → Tenant → Permission → page. Not a security boundary.

## Security module structure

```
security/  (or split identity + access + audit per module design)
  authentication/{password,sessions,reset}
  authorization/{permissions,roles,policies,service}
  tenancy/{context,membership,isolation}
  audit/
  security_events/
```

Domain must not depend on JWT/HTTP/Django request.

Central SecurityConfig: timeouts, password policy, rate limits, MFA flag, refund threshold, audit retention, allowed_origins.

## Tests (blocking production)

Auth: wrong password, expired/revoked session, disabled user.  
Authz: missing permission, wrong role, inactive membership.  
Tenant A ↛ Tenant B for products, customers, suppliers, sales, purchases, inventory, expenses, payments.  
Cashier ↛ invite, adjust, settings, refund above threshold.  
Endpoint matrix: 401 / 404-or-403 / 403 / 200.  
Every security bug → regression test.

## Transaction / races

Refund + inventory + payment + audit one transaction. Concurrent last-unit sales and double refunds need locking.

## Supply chain

CI: dependency + image CVE scan, lockfiles, secret scanning.

## MVP must / wait

**Must:** hashing, sessions, logout revoke, reset, disabled users blocked, every API authorized, permission registry, RBAC, owner protected, tenant scope + tests, membership check, authorized refunds/adjustments/cash, no silent financial delete, audit, HTTPS, secure cookies, CSRF, CORS, headers, rate limit, secrets out of git.

**Wait:** MFA, passkeys, SSO, SCIM, API keys, anomaly AI, device management, enterprise policy engine, impersonation.

## Definition of done

Login working ≠ security done. See original §113 checklist: identity, authorization, tenancy, business security, infrastructure, testing.

## Chain

Identity → Tenant → Role → Permission → Resource → Domain policy → Transaction → Audit.
