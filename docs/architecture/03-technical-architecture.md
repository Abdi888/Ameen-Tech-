# Ameen Retail — Technical Architecture Design v1

**Style:** Modular monolith with strict domain boundaries.  
**Not:** one giant Django app dump, and not microservices.

Only Retail exists. Shared platform (identity, tenancy, RBAC, catalog, inventory, accounting) must stay clean so future verticals can plug in later. Do not scaffold empty Wholesale/Travel modules.

---

## Goals

Retail first, SaaS multi-tenancy, domain boundaries, fast MVP, easy deploy, safe financial transactions, future business-type expansion, API/mobile readiness, authorization, auditing, testability, scale without premature complexity.

## High-level runtime

```
Browser (React / TS / Vite)
    HTTPS/JSON
Nginx (TLS)
    Django + DRF (modular monolith)
    ├── PostgreSQL
    ├── Redis (cache, broker, rate limit, locks) — not system of record
    ├── Celery (email, PDF, exports, analytics) — not POS completion
    └── S3-compatible object storage (images, PDFs, attachments)
```

Hosting: DigitalOcean. CI: GitHub Actions.

## Layers

1. **Presentation/API** — REST, auth, serialization, HTTP, pagination, request validation. No accounting logic in views.  
2. **Application** — use cases: CompleteSale, ReceiveStock, OpenRegister, …  
3. **Domain** — entities and rules (sale cannot complete without lines; journals balance; register must be open for POS cash).  
4. **Infrastructure** — ORM, Redis, Celery, storage, email. Domain does not depend on these.

## Backend layout

```
backend/
  manage.py
  pyproject.toml
  config/settings/{base,development,test,production}.py
  config/{urls,asgi,wsgi}.py
  shared/{api,database,exceptions,pagination,money,datetime,events}
  modules/
    identity/  tenants/  branches/  access/
    catalog/  inventory/  customers/  suppliers/
    sales/  pos/  purchasing/  payments/
    expenses/  accounting/  reporting/  audit/  configuration/
  tests/
```

Each module: `domain/`, `application/`, `infrastructure/`, `api/`.

## Module ownership (short)

| Module | Owns | Must not own |
|---|---|---|
| Identity | User, password, sessions, reset | Tenant RBAC, sales |
| Tenant | Tenant, profile, settings, status | Inventory |
| Branches | Branch, store/warehouse relationship | Products |
| Access | Role, permission, assignments | Business operations |
| Catalog | Product, variant, category, UOM, barcode, price list, tax assignment | Stock qty |
| Inventory | Warehouse, balance, movement, adjustment, transfer, count | Product definition |
| Customers | Customer (thin) | Invoices/payments |
| Suppliers | Supplier, terms | POs |
| Purchasing | PO, receipt, purchase return | Inventory tables |
| Sales | Sale, lines, returns | Ledger, POS session |
| POS | Terminal, session, cash drawer/movements, receipt sequence | Separate sale model |
| Payments | Payment, method, refund/allocation | Provider-specific Zaad/eDahab inside core model (adapters later) |
| Accounting | COA, journal, period | POS UI |
| Reporting | Read models | Mutations |
| Audit | Immutable logs | Transaction ownership |
| Expenses | Expense | Sales |

## Cross-domain rule

Allowed: Sales application → Inventory public interface.  
Forbidden: `from inventory.models import InventoryBalance` then decrement.

Contracts:

- Inventory: `get_availability`, `issue_stock`, `receive_stock`, `transfer_stock`, `adjust_stock`
- Accounting: `post_sale`, `post_purchase`, `post_payment`, `reverse_posting`
- Payments: `record_payment`, `refund_payment`

No `ERPService` / `GenericRepository[T]` dumping ground. Named use cases.

## API

Versioned REST `/api/v1/`. Envelope `{success, data, meta/pagination, errors}`. Command URLs. See doc 05.

## Multi-tenancy

Shared DB. RequestContext: user_id, tenant_id, branch_id, permissions, request_id. Never trust tenant in body.

## Frontend

```
frontend/src/
  app/{router,providers,layout}
  features/{auth,dashboard,products,inventory,customers,suppliers,sales,pos,purchasing,accounting,reports,settings}
  shared/{api,components,hooks,validation,formatters,types}
```

Server state: TanStack Query. Forms: RHF + Zod. Routes: `/login`, `/app/*`, `/platform/*`.

## Auth (see also 06)

Who vs what vs which company — separate. Web: HttpOnly session cookies. Pipeline: request id → auth → tenant → membership → branch → permission → use case → audit.

## Transactions, concurrency, idempotency, outbox

Complete sale: one DB transaction including inventory + journals + audit + outbox row. Worker after COMMIT for email/PDF.

Inventory: `SELECT FOR UPDATE` or equivalent.

Idempotency-Key on payments, confirm, receive, refund.

Events internally OK; **do not** make stock/accounting async.

## Redis / Celery / files

Redis: broker, cache, rate limit, locks.  
Celery: not on the POS hot path.  
Files: object storage; DB stores key/metadata.

## Money, time, IDs

Decimal + currency. UTC in DB. UUID + document sequences (tenant + type + number).

## Status machines

Explicit enums and allowed transitions. Never COMPLETED → DRAFT. Never delete posted journals; reverse.

## Exceptions

Domain errors (InsufficientStock, RegisterNotOpen, …) mapped to HTTP + machine codes.

## Observability

Structured logs with request_id, tenant_id, user_id. Never log secrets.

## Testing / CI

Domain → application → API integration → frontend unit → limited Playwright E2E.

Critical E2E: login, product, stock, open register, sell, cash, inventory down, journal, receipt, return, close register, **cross-tenant deny**.

CI: lint, pytest, migration check, frontend lint/tsc/unit, build, integration. Deploy after gates.

## Docker / production

Compose: postgres, redis, backend, celery, frontend. Production: Nginx + Gunicorn + managed PG + Redis + object storage. **No Kubernetes at this stage.**

## Security (summary)

HTTPS, hashed passwords, HttpOnly cookies, CSRF, rate limit, RBAC, tenant isolation, audit, backups, least privilege, env secrets, validation, secure uploads.

Deployment config via env (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, …). Business config in DB.

## Dependency direction

API → Application → Domain → infrastructure abstractions.  
Avoid sales → inventory → sales cycles.

## ADRs (when coding starts)

Maintain `docs/architecture/adr/` (modular monolith, shared-DB tenancy, PostgreSQL, REST, module boundaries, RBAC, inventory ledger).

## Coding rules

No cross-domain ORM writes; tenant_id everywhere; no delete of completed financial docs; Decimal money; use-case mutations; thin APIs; server-side permission; explicit transitions; stock via movements; accounting via journals; explicit transactions; platform ≠ tenant admin.

## Do not build now

Microservices, Kafka, K8s, event sourcing, CQRS everywhere, GraphQL, service mesh, multiple DBs, AI layer, plugin marketplace, workflow engine, generic metadata ERP, all future industries.

## Roadmap after this pack

API contract (done) → UI/UX → remaining security matrix / testing / deploy docs → **implementation module-by-module**, vertical slice first.
