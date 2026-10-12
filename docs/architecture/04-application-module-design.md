# Ameen Retail — Application / Module Design v1

Defines modules, ownership, use cases, interactions, permissions at module level, and transaction boundaries. **Not implementation code.**

Conflicts: follow `00-frozen-decisions.md` (sale states, events vs sync, first slice, AR).

---

## Purpose

Multi-tenant retail app: catalog, inventory, purchasing, sales, POS, customers, suppliers, payments, returns, expenses, basic accounting, reporting, access, configuration, audit.

Rules: isolated tenant data; module ownership; rules not in controllers/UI; financial/inventory mutations transactional; modules talk through application interfaces; future products must not contaminate Retail.

## Module classification

**Core:** Catalog, Inventory, Purchasing, Sales, POS, Customers  
**Supporting:** Suppliers, Payments, Expenses, Accounting  
**Platform:** Identity, Tenant, Users/Authorization, Configuration, Audit  
**Read:** Dashboard, Reporting  

Notifications = event handlers, not a full product module.

Reports must not own Sale/Stock/Journal.

## Internal module shape

```
module/
  domain/{entities,value_objects,services,rules,events}
  application/{commands,queries,dto,services}
  infrastructure/{repositories,persistence,integrations}
  interfaces/{api,serializers}
```

HTTP → Application → Domain → Repository interface → Infrastructure → DB.

## Modules and use cases

### Identity

Owns: credentials, sessions, password, auth state.  
Use cases: RegisterUser (platform/invite only), LoginUser, LogoutUser, RefreshSession, ChangePassword, ResetPassword, GetCurrentUser.

### Tenant / Business

Owns: tenant identity, profile, currency, timezone, status, settings.  
Use cases: CreateBusiness (platform), Get/UpdateBusiness, Activate/Suspend, UpdateBusinessSettings.

### Authorization

Owns: roles, permissions, assignments, evaluation. Does **not** own sales/inventory rules.  
`require_permission(user, "sales.void")` — never `if role == "manager"`.

### Catalog

Owns: Product, Category, Brand, Unit, Variant, Pricing, SKU, Barcode.  
Lifecycle: Draft → Active → Inactive.  
Use cases: Create/Update/Activate/Deactivate/Get/List/Search product, AssignCategory/Brand, SetPrice, UpdateBarcode.  
Does **not** own quantity.

### Inventory

Owns: stock levels, movements, adjustments, transfers, counts, valuation, availability.  
Use cases: GetStock, AdjustStock, TransferStock, GetStockMovements, GetLowStock, CheckAvailability, count create/approve (when built).  
Invariant: balance = sum(movements) or materialized + immutable history.

Purchasing/Sales call Inventory application services.

### Suppliers

Owns: supplier master. Does not own POs.

### Purchasing

Owns: PO, GoodsReceipt, PurchaseReturn.  
States: DRAFT → CONFIRMED → PARTIALLY_RECEIVED → RECEIVED; CANCELLED from draft/confirmed.  
Use cases: Create/Update/Confirm/Cancel PO, ReceivePurchase, CreatePurchaseReturn, Get/List.  
Does not write inventory tables.

### Customers

Owns: customer master (thin). Does not own sales. `GetCustomerBalance` only if AR exists.

### Sales

Owns: Sale, SaleItem, SalePayment (or via Payments module), SaleReturn.  
Use cases: CreateSale, Add/Remove items, RecordPayment, CompleteSale (`confirm`), CancelSale (draft), VoidSale, CreateSalesReturn, Get/List.

POS is **not** a second sales model.

### POS

Owns: Cart, cash/register session, receipt workflow, POS UX.  
Flow: Open session → cart → scan → checkout → Sales.CompleteSale → receipt.  
Must not mutate stock/journals.

### Payments

Owns: Payment across SALE, PURCHASE, EXPENSE, OTHER. Methods: CASH, CARD, BANK_TRANSFER, MOBILE_MONEY, OTHER.

### Expenses

Use cases: Create/Update/Approve/Cancel, RecordExpensePayment, List.  
Lifecycle: DRAFT → APPROVED → PAID. Posts via Accounting.

### Accounting

Owns: COA, journals, periods. Does not calculate sales. `post_sale` / `post_purchase` / `post_expense`. Debit = credit.

### Reporting / Dashboard

Read-only. Dashboard uses optimized queries/read models, not N+1 over all sales.

### Configuration

Typed business settings (receipt prefix, tax enabled, negative stock policy, POS). Not an untyped JSON dump for invariants.

### Audit

Append-only: actor, action, entity, id, timestamp, metadata.

## Dependency map

Identity → Authorization → Tenant.  
Catalog → Inventory.  
Customers → Sales. Suppliers → Purchasing → Inventory.  
Sales → POS, Payments, Inventory → Accounting.  
Purchasing/Expenses/Payments → Accounting.  
Operational modules → Reporting → Dashboard. All → Audit.

Arrows are application contracts, not DB coupling.

## CompleteSale (canonical)

1. Validate sale/products/register  
2. Inventory.CheckAvailability  
3. Calculate totals (domain)  
4. Persist sale  
5. Payments.Record  
6. Inventory.Deduct/issue  
7. Accounting.PostSale  
8. Audit.Record  
9. Commit  
Then events: receipt, notification, analytics.

## ReceivePurchase

Validate PO/qty → GoodsReceipt → Inventory.Receive → payable → Accounting.PostPurchase → update PO → commit.

## SalesReturn

Validate original + qty → return docs → refund → inventory (by condition) → accounting reverse → audit. Original sale immutable.

## Commands vs queries

Mutations are commands; lists/gets/reports are queries. DTOs at API boundary — do not expose domain entities.

## Communication

Allowed: application service → application service; domain event → handler (secondary); query → read model.  
Forbidden: UI → database; Sales SQL into inventory.

## Shared kernel

Money, Currency, DateTime, TenantContext, DomainError, EntityId, Pagination, DomainEvent.

## Testing per module

Domain rules, application use cases, integration across modules, API authz/tenant, E2E primary flows.

## Build sequence

Phase 1 Foundation (identity, tenant, authz, config, audit)  
Phase 2 Catalog  
Phase 3 Inventory  
Phase 4 Purchasing  
Phase 5 Customers + Sales + Payments + Returns  
Phase 6 POS  
Phase 7 Accounting  
Phase 8 Expenses  
Phase 9 Reporting  
Phase 10 Hardening  

First **code** slice: see frozen decisions (POS before full purchasing).

## Every future module spec

Name, purpose, responsibilities, entities, commands, queries, rules, events, dependencies, integrations, permissions, APIs, transactions, failure modes, tests.
