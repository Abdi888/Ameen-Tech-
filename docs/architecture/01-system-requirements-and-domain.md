# Ameen Retail — System Requirements & Domain Design v1

**Document:** System Requirements & Domain Design  
**Product:** Ameen Retail  
**Version:** 1.0  
**Status:** Foundation / Engineering Baseline  
**Architecture style:** Modular monolith initially  
**Primary business:** Retail stores  
**Deployment:** SaaS / multi-tenant  
**Initial vertical:** Retail only  

Where this conflicts with `00-frozen-decisions.md`, follow frozen decisions.

---

## 1. Product definition

Ameen Retail is a business management system for small and growing retail businesses.

Operational cycle: Products → Purchasing → Receiving → Inventory → Pricing → Point of Sale → Payments → Returns → Accounting → Reports.

The system must answer:

1. What do I sell?
2. How much stock do I have?
3. What did I buy and from whom?
4. What did I sell and how was it paid?
5. How much money and profit did the business make?

## 2. Product philosophy

v1 is deliberately narrow. Excellent at retail, not mediocre at ten industries.

**v1 focuses on:** retail products, suppliers, customers, purchasing, receiving, inventory, stock adjustments, stock counts, pricing, POS, payments, sales returns, purchase returns, expenses, basic accounting, cash management, retail reports, users/permissions, business/branch configuration.

**v1 does not focus on:** manufacturing, construction, hospitals, universities, travel, field service, professional services, payroll, CRM automation, project management, advanced HR, complex WMS, e-commerce marketplace, BOM/MRP, advanced subscription billing.

## 3. Target customer

Grocery, clothing, electronics, cosmetics, pharmacy-like general retail where legally appropriate, household goods, hardware, mini-market, convenience, small supermarket.

Support single-store simply. Multi-branch later must not make single-store hard. Domain must not assume every customer has multiple branches.

## 4. Core distinctions (never collapse)

- Product is not Inventory.
- Sale is not Payment.
- Purchase Order is not Inventory Receipt.
- Cart is not a completed Sale.

## 5. High-level domain

Tenant/Business → Locations, Users, Settings.  
Locations → Products and Inventory (movements, counts).  
Products → categories, brands, units, barcodes, prices.  
Purchasing: PO → Receiving → Supplier invoice → Inventory.  
POS: Sale → Payments and Returns → Treasury → Accounting → Reporting.

## 6. Bounded contexts (v1 domain map)

1. Identity  
2. Tenant / Business  
3. Locations  
4. Catalog  
5. Inventory  
6. Purchasing  
7. Sales / POS  
8. Payments  
9. Cash Management (implemented under POS module)  
10. Customers  
11. Suppliers  
12. Expenses  
13. Accounting  
14. Reporting  
15. Audit  

Identity must not contain retail business logic.

## 7. Tenant / Business

Entity **Business** (table `tenants`): id, name, legal_name, business_type, currency, timezone, country, address, phone, email, logo, status, timestamps.

`business_type` for this product: **RETAIL** only.

## 8. Location

Physical place where inventory can exist.

Types: **STORE**, **WAREHOUSE**.

A store may have POS terminals.

Fields: id, business_id, name, code, type, address, phone, status.

Implementation split: `branches` + `warehouses` (see frozen decisions).

## 9. Catalog

### Product

Sellable item. Attributes include: id, business_id, sku/name/description via variant facade, category_id, brand_id, unit_id, cost/selling on variant, tax category/rate, track_inventory, track_batch, track_expiry, track_serial, is_active, timestamps.

SKU is the retailer's internal id. SKU ≠ barcode.

A product may have multiple barcodes. Types: EAN, UPC, GTIN, INTERNAL, OTHER. Leave room for GS1 batch/expiry/weight as extra data, not as product identity.

### Variants

Use Product + ProductVariant. Simple products have one default variant. Do not build a huge variant engine in v1.

### Category

Hierarchical: id, business_id, parent_id, name, code, is_active.

### Brand

Optional. Zero or one brand per product.

### Units

Piece, box, carton, kg, gram, liter, meter. Distinguish purchase / selling / stock units when conversions exist (e.g. 1 carton = 24 pieces). See frozen decisions for v1 UOM scope.

## 10. Inventory

Owns stock state, not product definitions.

**InventoryBalance:** product (variant) + location (warehouse): on_hand, reserved, available.  
`available = on_hand - reserved`. v1 reserved = 0 until real reservations.

Stock changes only via **InventoryMovement**: id, business_id, location/warehouse, product, quantity, movement_type, reference_type, reference_id, unit_cost, occurred_at, created_by.

Types: PURCHASE_RECEIPT, SALE, SALE_RETURN, PURCHASE_RETURN, ADJUSTMENT_IN, ADJUSTMENT_OUT, TRANSFER_IN, TRANSFER_OUT, STOCK_COUNT, OPENING_BALANCE.

Ledger is source of truth; balance is transactional materialized state.

### Adjustment

Never silently overwrite stock. Reasons: DAMAGED, LOST, EXPIRED, THEFT, COUNT_CORRECTION, OTHER.

### Stock count

Create → select location → count → variance → review → approve → create adjustments.

## 11. Purchasing

Entities: Supplier, PurchaseOrder, PurchaseOrderLine, GoodsReceipt, GoodsReceiptLine, SupplierInvoice (optional later), PurchaseReturn.

PO statuses: DRAFT, CONFIRMED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED.

PO must not modify inventory. Receiving does. Partial receiving required.

Purchase return decreases inventory and creates supplier-side financial effect.

## 12. Sales and POS

Entities: Sale, SaleLine, SalePayment, SaleReturn, SaleReturnLine.

POS is a transaction workflow, not CRUD: scan → identify → line → price → discount → tax → total → pay → complete → inventory → accounting → receipt.

Cart is temporary. Completed sale is effectively immutable.

Sale fields include: id, business_id, location_id, terminal_id, cashier_id, customer_id (nullable), sale_number, status, subtotal, discount, tax, total, paid_amount, change_amount, currency, occurred_at.

Sale lines **snapshot** product_name, sku, quantity, unit_price, discount, tax, line_total.

Pricing is a domain: product, location, effective period. Start with base selling price; allow retail/wholesale/branch/promo later.

Discounts: LINE or ORDER; FIXED or PERCENTAGE; permission-controlled.

Tax: TaxCategory + TaxRate; configurable, not hard-coded in sales logic.

## 13. Payments

Separate from sales. Methods: CASH, CARD, MOBILE_MONEY, BANK_TRANSFER, OTHER.

Multiple payments per sale. Fully paid: sum(payments) >= amount_due. Cash change = amount_paid - amount_due. Change is not revenue.

## 14. Customers

Optional on POS. Walk-in: `customer_id` null.

Fields: id, business_id, name, phone, email, address, credit_limit, status.

Credit/AR is a deliberate feature — **out of POS v1** per frozen decisions.

## 15. Returns

Own workflow. Do not edit original sale.

Return qty cannot exceed eligible remaining qty. Conditions: GOOD (sellable +1), DAMAGED/UNSELLABLE (do not auto-return to sellable stock).

Effects on complete: inventory + refund/credit according to policy.

## 16. Cash management (POS module)

CashRegister, CashSession, CashMovement.

Session: open with opening cash → sales/cash in-out → close → count → variance. One open session per register. Preserve variance; do not rewrite sales totals.

## 17. Expenses

Operational expenses: rent, electricity, transport, etc.

Fields: id, business_id, location_id, category_id, amount, payment_method, description, expense_date, created_by.

## 18. Accounting

Integration domain. Retail modules produce effects; accounting records journals.

Entities: Account, JournalEntry, JournalLine, Period.

Invariant: posted entry debits = credits.

Valuation v1: **weighted average**. COGS = qty × inventory cost, never selling price.

Gross profit = sales revenue − COGS − discounts − relevant returns (formalize with accounting policy).

## 19. Reporting and dashboard

Reporting is read-only. No second business-logic system. Dashboard numbers from authoritative sources, not drift counters.

Core reports: sales (daily, product, category, cashier, branch, payment method), inventory (on hand, low stock, valuation, movement, adjustment, count variance), purchasing, financial (revenue, COGS, GP, expenses, cash, payment methods).

“Today” = completed sales in **business-local calendar day**.

KPIs: Revenue, Transactions, Units Sold, ATV, Gross Profit, Gross Margin, Inventory Turnover (per costing policy).

## 20. Users and permissions

Roles (domain list; v1 security set is in frozen decisions): Owner, Administrator, Manager, Cashier, Inventory Clerk, Purchasing Officer, Accountant, Viewer.

Permissions are actions (`sales.view`, `sales.create`, …). Server-side: authenticated → membership → permission → location scope → operation.

Cashier: open register, create/complete sale, payment, receipt, authorized return, close register. Not: product cost, delete products, accounting, tax config, users.

Every mutation checked server-side.

## 21. Multi-tenancy and location scope

Every business-owned row has tenant/business id. Never `get(id)` without tenant. Cashier on Store A must not operate Store B.

## 22. Transaction boundaries

Completed sale, receiving, and return are atomic. No partial completion. Core sync; analytics/email async via outbox.

Domain events (SaleCompleted, GoodsReceived, …) for secondary effects only.

## 23. Module ownership (data)

See document 04. Catalog owns products/SKU/barcodes/categories/brands/units. Inventory owns stock/movements/counts/adjustments. Sales owns sales/returns. Accounting owns journals/accounts. No blurring.

## 24. Audit, numbering, money, time

AuditLog: who, what, when, where, why. Sensitive mutations audited.

Human numbers: SALE-000001, PO-000001, GRN-000001, RET-000001, EXP-000001, SC-000001.

Money: Decimal + currency. Time: UTC storage + business timezone display.

## 25. POS performance and idempotency

Barcode scan must feel immediate. Final complete still validates server state.

Idempotency keys on complete sale, payment, receive, return.

## 26. API style (see also 05)

Commands for business transactions: complete/confirm sale, receive, return, open/close register, approve count.

Validation at UI, API, and domain.

## 27. Invariants (must be tests)

- Stock cannot go negative unless explicitly configured.
- Payment amount > 0.
- Return qty ≤ eligible.
- Debits = credits.
- No cross-tenant access.
- No unauthorized location.

## 28. Lifecycles (domain)

Product: DRAFT → ACTIVE → INACTIVE (no delete with history).  
Supplier: ACTIVE / INACTIVE.  
Purchase: DRAFT → CONFIRMED → PARTIALLY_RECEIVED → RECEIVED; cancel from draft/confirmed.  
Sale (implementation freeze): DRAFT → COMPLETED then void/return states.  
Return: DRAFT → APPROVED → COMPLETED; stock/finance on complete.

## 29. Functional requirements (FR)

FR-001 Business setup  
FR-002 Locations  
FR-003 Products create/update/activate/deactivate  
FR-004 SKU and barcode  
FR-005 Hierarchical categories  
FR-006 Stock per product and location  
FR-007 Immutable movement history  
FR-008 Purchase orders  
FR-009 Full and partial receiving  
FR-010 Suppliers  
FR-011 POS create/complete sales  
FR-012 Payment methods  
FR-013 Split payments  
FR-014 Sales returns against completed sales  
FR-015 Cash sessions  
FR-016 Expenses  
FR-017 Accounting effects  
FR-018 Reports  
FR-019 Multiple users per business  
FR-020 RBAC  
FR-021 Tenant isolation  
FR-022 Audit  
FR-023 Idempotency  
FR-024 Atomic critical transactions  

## 30. Non-functional (NFR)

Security, tenant isolation, reliability (atomic financial/stock), auditability, POS latency, scale by adding tenants/locations without redesigning boundaries, maintainability (logic in domain/application), testability without frontend, observability (request/correlation ids), data integrity (no silent overwrite).

## 31. Testing strategy (domain)

Unit: calculations, eligibility, inventory, cash variance, journal balance.  
Integration: complete sale, receive, return, close register, adjust.  
API: authz, tenant, validation, idempotency.  
E2E: product → purchase → receive → sell → pay → stock/report; sell → return; open register → cash sale → close → variance.

## 32. Build order (original)

Phase 0 architecture → Identity/Tenant → Catalog → Inventory → Purchasing → POS/Sales → Payments/Cash → Returns → Accounting → Reports → hardening.

First vertical slice (refined in frozen decisions): identity/product/inventory/POS/pay first; purchasing as slice 2.

## 33. What must never happen

Giant god models/services; direct cross-module DB writes; frontend-only auth; edit completed transactions; stock without movements; payment embedded as the only payment model inside Sale with no payment domain; accounting inside POS; product = inventory entity; everything async; microservices day one.

## 34. MVP navigation (target UI)

Dashboard; Sales (POS, Sales, Returns); Products (Products, Categories, Brands, Pricing); Inventory (Stock, Movements, Counts, Adjustments); Purchasing (Suppliers, POs, Receiving, Purchase returns); Customers; Expenses; Cash (Registers, Sessions); Reports; Settings (Business, Locations, Users, Roles, Taxes, Payment methods).

POS UI is scanner/keyboard/touch first: search/scan, product grid, cart, totals, PAY.

## 35. Data ownership matrix

| Domain | Owns | Does not own |
|---|---|---|
| Identity | Users/Auth | Sales |
| Tenant | Business | Inventory |
| Locations | Stores/warehouses | Products |
| Catalog | Products/SKU/barcodes | Stock |
| Inventory | Stock/movements | Product definition |
| Purchasing | POs/receipts | Sales |
| Sales | Sales/returns | Accounting ledger |
| Payments | Payments | Product |
| Cash/POS | Registers/sessions | Product |
| Customers | Customer data | Sales ledger |
| Suppliers | Supplier data | Inventory |
| Expenses | Expenses | Sales |
| Accounting | Journals/accounts | POS UI |
| Reporting | Read models | Transaction ownership |
| Audit | Audit records | Business transactions |
