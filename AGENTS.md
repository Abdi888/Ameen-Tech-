# Ameen Retail — Agent instructions

This repository is **Ameen Retail**, a retail-only SaaS ERP (modular monolith).

## Before writing code

1. Read `docs/architecture/00-frozen-decisions.md`.
2. Read the relevant numbered design in `docs/architecture/` (01–08). Screens/RBAC: also read `07-permission-matrix-and-screens.md`. UI color/type/radius: `08-ui-design-tokens.md`.
3. If documents conflict, **frozen decisions win**.
4. Do not copy the old ERP. Do not add other industries. Do not start microservices.

## Non-negotiables

- Modular monolith: API → application use case → domain → infrastructure.
- No cross-module table writes. Use module contracts.
- Tenant isolation on every query. Never trust `X-Tenant-Id` or `tenant_id` in the body.
- Completed financial/stock documents are not deleted (void / return / reverse / adjust).
- Money: `Decimal` / `NUMERIC(19,4)`; API amounts as strings.
- Sale completion is one DB transaction including inventory and accounting.
- POS does not own sales, stock, or journals.
- Server-side permissions; frontend hiding a button is not security.

Full pack: `docs/architecture/README.md`.
