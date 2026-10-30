# System Context and Schema Findings

This database supports a simple e-commerce backend that stores products,
categories, suppliers, tags, and warehouse inventory.

## Findings in `schema/broken_schema.sql`

- `categories` and `product_tags` are comma-separated multi-valued attributes.
  Their individual values cannot be constrained or joined reliably, violating
  first normal form.
- Supplier name, phone, and email are repeated on every product supplied by
  the same supplier. Supplier contact facts depend on the supplier, not on the
  product key, creating update and deletion anomalies.
- `warehouse_location` and `stock_quantity` are stored directly on a product.
  This supports only one location per product and cannot represent a separate
  quantity for each product/warehouse pair.
- Category membership, tag assignment, and product/warehouse stock have
  independent relationships that cannot be represented as atomic values in
  the original product row.
- The original DDL declares no `NOT NULL`, uniqueness, check, or foreign-key
  constraints, so it cannot prevent blank names, negative stock/prices, or
  inconsistent references.
- There are no composite keys in the original design, so it has no direct
  partial dependency; however, the normalized relationship tables use full
  composite keys for each product/category, product/tag, and
  product/warehouse fact.

Repeating supplier contact details causes update anomalies; adding a supplier
without a product or a category without a product is awkward; deleting the
last product that mentions a supplier or category can erase the only stored
copy of that entity. Keeping inventory in a product row also overwrites or
loses the stock record when a product is held at multiple warehouses.

The normalized design stores supplier facts once, represents category and tag
membership in junction tables, and stores each stock quantity against the
product and warehouse that determine it. See the root `README.md` for the
table-by-table design, 3NF reasoning, query behavior, and test instructions.
