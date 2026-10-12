# Ameen Retail — Database Schema Design v1

**Database:** PostgreSQL  
**Tenancy:** Shared database + shared schema, `tenant_id` on every tenant-owned table.  
**Money/qty:** `NUMERIC(19,4)` — never FLOAT/REAL/DOUBLE.  
**Time:** `TIMESTAMPTZ`.  
**IDs:** UUID PK. Human document numbers separate.

A table belongs to **one domain**. Other domains reference IDs; they do not manipulate another domain’s rows.

Apply `00-frozen-decisions.md` for barcodes, sale snapshots, stock count headers, cash movements, PO states, AR, and composite FKs.

PostgreSQL schemas: `identity`, `organization`, `catalog`, `inventory`, `sales`, `purchasing`, `customers`, `suppliers`, `payments`, `expenses`, `accounting`, `tax`, `audit`, `system`.

---

## Multi-tenancy

```
tenants
  id UUID PK
  name VARCHAR
  slug VARCHAR UNIQUE
  business_type VARCHAR          -- RETAIL
  default_currency_id UUID FK
  timezone VARCHAR
  country_code VARCHAR
  logo_url TEXT
  status VARCHAR                 -- ACTIVE | SUSPENDED | ARCHIVED
  created_at TIMESTAMPTZ
  updated_at TIMESTAMPTZ
```

Every tenant-owned table: `tenant_id UUID NOT NULL REFERENCES tenants(id)`.

Prefer composite FKs such as `(customer_id, tenant_id) → customers(id, tenant_id)` so sale tenant cannot point at another tenant’s customer.

---

## Organization

```
branches
  id, tenant_id, name, code, phone, email, address, city, country_code
  is_active BOOLEAN
  timestamps
  UNIQUE(tenant_id, code)
```

---

## Identity & access

```
users
  id UUID PK
  email VARCHAR UNIQUE           -- platform-level identity
  phone VARCHAR
  password_hash TEXT             -- Argon2id
  first_name, last_name VARCHAR
  status VARCHAR                 -- ACTIVE | INVITED | SUSPENDED | DISABLED
  email_verified_at TIMESTAMPTZ
  last_login_at TIMESTAMPTZ
  timestamps

tenant_users / tenant_memberships
  id, tenant_id, user_id, role_id (or via tenant_user_roles)
  status VARCHAR                 -- ACTIVE | INVITED | SUSPENDED | REMOVED
  is_owner BOOLEAN               -- Owner is protected; see security doc
  joined_at, timestamps
  UNIQUE(tenant_id, user_id)

roles
  id, tenant_id NULLABLE         -- NULL = system role
  name, description
  is_system_role BOOLEAN
  timestamps

permissions
  id, code UNIQUE, name, module, description, is_system, danger_level

role_permissions
  PRIMARY KEY(role_id, permission_id)

tenant_user_roles
  tenant_user_id, role_id, branch_id NULLABLE
```

**NULL `branch_id` in a composite PK is a PostgreSQL trap.** Use a sentinel, partial unique indexes, or `applies_to_all_branches BOOLEAN` — do not rely on NULL uniqueness.

Also (security design): `sessions` (token_hash, expires, revoked, ip, user_agent), `login_attempts`, `password_reset_tokens` (hashed, single-use).

---

## Catalog

```
product_categories
  id, tenant_id, parent_id NULL, name, code, description, is_active, timestamps

brands
  id, tenant_id, name, code, description, is_active, timestamps

units
  id, tenant_id NULLABLE, name, symbol, type, is_active

products
  id, tenant_id, category_id, brand_id NULL
  name, description, product_type
  track_inventory, track_serial, track_batch BOOLEAN
  is_active, timestamps

product_variants
  id, tenant_id, product_id, sku, name, unit_id
  cost_price NUMERIC(19,4), selling_price NUMERIC(19,4)
  minimum_stock, maximum_stock NUMERIC(19,4)
  is_active, timestamps
  UNIQUE(tenant_id, sku)

barcodes                          -- required (frozen)
  id, tenant_id, product_variant_id, value, type, is_primary
  UNIQUE(tenant_id, value)

price_lists
  id, tenant_id, name, currency_id, is_default, is_active, created_at

product_prices
  id, price_list_id, product_variant_id, price NUMERIC(19,4)
  minimum_quantity, valid_from NULL, valid_to NULL
```

API `POST /products` creates product + default variant + optional primary barcode.

---

## Inventory

```
warehouses
  id, tenant_id, branch_id, name, code, is_active, timestamps

stock_locations                   -- optional v1
  id, warehouse_id, name, code, is_active

inventory_balances
  id, tenant_id, warehouse_id, product_variant_id
  quantity_on_hand, quantity_reserved, quantity_available NUMERIC(19,4)
  unit_cost / stock_value for WAC (add; original sketch omitted cost on balance)
  updated_at
  UNIQUE(warehouse_id, product_variant_id)

inventory_movements               -- immutable ledger
  id, tenant_id, warehouse_id, product_variant_id
  movement_type, quantity, unit_cost
  reference_type, reference_id
  occurred_at, created_by, notes

stock_adjustments                 -- header with reason
stock_adjustment_lines

stock_counts                      -- controlled process
stock_count_lines

stock_transfers
  id, tenant_id, transfer_number, from_warehouse_id, to_warehouse_id
  status, requested_by, approved_by NULL, timestamps, notes

stock_transfer_lines
  transfer_id, product_variant_id, quantity
```

Movement types: PURCHASE_RECEIPT, SALE, SALE_RETURN, PURCHASE_RETURN, ADJUSTMENT_IN, ADJUSTMENT_OUT, TRANSFER_IN, TRANSFER_OUT, OPENING_BALANCE, STOCK_COUNT.

`quantity >= 0` on balances unless negative-stock policy enabled.

---

## Customers & suppliers

```
customers
  id, tenant_id, customer_number, name, phone, email, address
  credit_limit NUMERIC(19,4), is_active, timestamps
  -- do not unique on phone

suppliers
  id, tenant_id, supplier_number, name, phone, email, address
  payment_terms_days INTEGER, credit_limit NUMERIC(19,4), is_active, timestamps
```

---

## Purchasing

```
purchase_orders
  id, tenant_id, supplier_id, warehouse_id, order_number, status
  order_date DATE, expected_date DATE NULL
  subtotal, tax_amount, discount_amount, total_amount NUMERIC(19,4)
  created_by, timestamps

purchase_order_lines
  id, purchase_order_id, product_variant_id
  quantity, quantity_received, unit_cost, tax_amount, discount_amount, line_total

purchase_receipts
  id, tenant_id, purchase_order_id NULL, supplier_id, warehouse_id
  receipt_number, receipt_date, status, created_by, created_at

purchase_receipt_lines
  receipt_id, product_variant_id, quantity, unit_cost

purchase_returns / purchase_return_lines
```

Receipt completion generates movements. Payables from receipt (frozen), not from PO.

---

## Sales & POS

```
sales_orders                      -- exposed as Sale
  id, tenant_id, branch_id, warehouse_id, customer_id NULL
  terminal_id, cashier_id, session_id
  order_number, status, order_date TIMESTAMPTZ
  subtotal, discount_amount, tax_amount, total_amount
  paid_amount, change_amount, currency
  created_by, timestamps

sales_order_lines
  id, sales_order_id, product_variant_id
  product_name_snapshot, sku_snapshot
  quantity, unit_price, discount_amount, tax_amount, line_total

sales_returns / sales_return_lines
  original sale + sale_order_line_id, qty, unit_price, refund_amount, condition

pos_terminals
  id, tenant_id, branch_id, name, code, status, is_active

pos_sessions
  id, tenant_id, terminal_id, cashier_id
  opened_at, opening_cash, closed_at NULL, closing_cash NULL
  expected_balance, actual_balance, variance
  status OPEN | CLOSED

pos_cash_movements
  session_id, type IN/OUT, amount, reason, created_by
```

---

## Payments, expenses, tax, currency

```
payment_methods
  id, tenant_id, name, type, is_active

payments
  id, tenant_id, payment_number, payment_method_id
  amount, currency_id, status, payment_date
  reference_type, reference_id, received_by, notes, created_at

expense_categories
  id, tenant_id, name, description, is_active

expenses
  id, tenant_id, branch_id, category_id, amount, currency_id
  expense_date, payment_method_id, description, status, created_by, created_at

tax_rates
  id, tenant_id, name, code, rate NUMERIC(8,4), is_inclusive, is_active

product_tax_rates
  PRIMARY KEY(product_variant_id, tax_rate_id)

currencies
  id, code CHAR(3), name, symbol, decimal_places, is_active
```

---

## Accounting

```
accounts
  id, tenant_id, parent_id NULL, code, name
  account_type ASSET|LIABILITY|EQUITY|REVENUE|EXPENSE
  normal_balance, is_active

accounting_periods
  id, tenant_id, name, start_date, end_date, status

journal_entries
  id, tenant_id, entry_number, entry_date, description
  reference_type, reference_id, status, posted_by, posted_at, created_at

journal_lines
  id, journal_entry_id, account_id, debit, credit, description
```

Posted: SUM(debit) = SUM(credit) in application before post.

`receivables` / `payables` exist in the original schema sketch. **Do not wire credit sales until AR is an explicit Starter feature.** Tables may be added with purchasing payables from receipts.

---

## Documents, audit, settings, idempotency

```
documents
  id, tenant_id, entity_type, entity_id, file_name, file_url, mime_type
  file_size, uploaded_by, created_at
  -- files in object storage, not bytea

audit_logs
  id, tenant_id, user_id NULL, action, entity_type, entity_id
  old_values JSONB, new_values JSONB, ip INET, user_agent TEXT, created_at
  -- append-only for tenant users

tenant_settings
  id, tenant_id, key, value JSONB, UNIQUE(tenant_id, key)
  -- JSONB only for prefixes/format. Invariants stay typed columns.

idempotency_keys
  tenant_id, key, endpoint, response, created_at
  UNIQUE(tenant_id, key)

document_sequences
  tenant_id, document_type, prefix, current_number
```

---

## Constraints (mandatory)

- `tenant_id NOT NULL` on tenant-owned tables  
- `UNIQUE(tenant_id, sku)`  
- Unique barcode values per tenant  
- `UNIQUE(tenant_id, code)` on branches  
- Unique document numbers per tenant + type  
- `UNIQUE(warehouse_id, product_variant_id)` on balances  
- Quantity/money CHECKs where appropriate  

## Soft delete

Masters: `is_active`. Financial/stock: VOIDED / CANCELLED / REVERSED — never physical delete.

## Indexes (minimum)

`(tenant_id, name)` products; `(tenant_id, sku)` / barcode on variants; sales `(tenant_id, order_date)`, `(tenant_id, customer_id)`; PO date; movements `(tenant_id, product_variant_id, occurred_at)`; payments date; journals entry_date. Do not index every column.

## Transaction examples

**Sale:** create order+lines, validate inventory, movements, balances, payment, journal, audit — one COMMIT.

**Receive:** receipt+lines, movements, balances, payable, journal, PO received qty, audit — one COMMIT.

## Out of v1 schema

Manufacturing, BOM, MRP, hospital/university/construction/hotel/fleet, payroll, CRM automation, BI warehouse, marketplace, multi-company consolidation, advanced budgeting, depreciation engine.

## Architecture reminder

The database is not the architecture. Frontend must not orchestrate stock + sale + payment + accounting as separate writes. `POST /sales/{id}/confirm` coordinates one use case.
