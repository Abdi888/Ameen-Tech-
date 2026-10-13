# Ameen Retail — Architecture Pack (v1)

These documents are the **engineering baseline**. Implementation must follow them.

If two design docs disagree, **`00-frozen-decisions.md` wins**.

If a behavior is not specified, **ask before inventing** a new domain, table, or API.

Do **not** copy patterns from the old ERP.

## Reading order

1. [00 — Frozen decisions](./00-frozen-decisions.md) — read this first when coding
2. [01 — System Requirements & Domain Design](./01-system-requirements-and-domain.md)
3. [02 — Database Schema Design](./02-database-schema.md)
4. [03 — Technical Architecture](./03-technical-architecture.md)
5. [04 — Application / Module Design](./04-application-module-design.md)
6. [05 — API Contract](./05-api-contract.md)
7. [06 — Security & Authorization](./06-security-and-authorization.md)
8. [07 — Permission Matrix & Screen Boundaries](./07-permission-matrix-and-screens.md) — roles, keys, screens
9. [08 — UI design tokens](./08-ui-design-tokens.md) — color, Inter, 12px corners ([`tokens.css`](./tokens.css))

## What is not in this pack yet

These were listed as later artifacts. Do not invent them as if they were already frozen:

- Requirement → API → permission → test traceability matrix
- Screen layouts / UX wireframes (colors, type, and radius **are** frozen in 08)
- Testing strategy document (beyond rules already in 01–06)
- Deployment / infrastructure runbook beyond the stack in 03

## Product

**Ameen Retail** — multi-tenant SaaS for small and growing **retail** businesses. Modular monolith. Retail only in v1. No Wholesale, Travel, HR, manufacturing, or other verticals in this codebase until an explicit product decision.

## Implementation gate

Start code only when asked. First code should be a **vertical slice**, not every CRUD screen:

Identity + Tenant → Product (default variant) → Inventory (opening/adjust) → POS sale → Payment → stock down → journal → report.

Purchasing/receiving is the next slice unless the user says otherwise.

## Running the Phase 1 foundation

The API foundation lives in `backend/`. It serves `GET /api/v1/health`, the Document 05 JSON envelope, cookie login, tenant membership checks, and Document 07 permission checks. The React app, Redis, and Celery are not part of this phase. Document 05 has one approved amendment, `METHOD_NOT_ALLOWED` at HTTP 405. Documents 00–04 and 06–08 are unchanged.

From the repository root, with Python 3.12 and Docker:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python manage.py migrate
python manage.py runserver
```

Health check: `GET http://localhost:8000/api/v1/health`.

Checks, from `backend/`:

```powershell
ruff check .
ruff format --check .
mypy
python manage.py makemigrations --check --dry-run
pytest
```

`docker compose up --build` also starts the API container against the Postgres service. The database password in `.env.example` and `docker-compose.yml` is a local placeholder. Do not use it outside a local machine. Tests refuse a non-local `DATABASE_URL`.
