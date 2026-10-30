# When Clean Design Gets Complex — 3NF Database Normalization

## Assignment overview

This project repairs the e-commerce schema supplied in `schema/broken_schema.sql`
and updates the product queries for the normalized design in
`schema/normalized_schema.sql`. The schema and queries target SQLite.

## Problems identified

The original `products` table stores:

- `categories` as a comma-separated string and `product_tags` as a multi-value
  string. These are non-atomic repeating groups, break 1NF, and prevent
  dependable constraints and joins.
- Supplier name, phone, and email alongside each product. A supplier's contact
  details depend on the supplier, not on the product, so they are duplicated
  whenever a supplier provides multiple products.
- A single warehouse location and stock quantity in the product row. This
  mixes inventory with product identity and cannot represent stock at multiple
  warehouses.
- No declared foreign keys, `NOT NULL`, uniqueness, or non-negative checks.

These choices create update anomalies (supplier details must be updated on
every product row), insertion anomalies (a supplier or category cannot be
stored independently), and deletion anomalies (deleting a supplier's last
product can remove its only contact details). They also prevent consistent
product/category/tag assignments and warehouse-specific stock.

There are no explicit composite keys in the broken schema, so no partial
dependency is declared there. In the new junction tables, every non-key
attribute depends on the complete composite key.

## Normalized structure

| Table | Purpose and key facts |
|---|---|
| `products` | Product identity, name, price, and required supplier FK. |
| `suppliers` | One row per supplier; contact fields are stored once. |
| `categories` | One row per unique category name. |
| `product_categories` | Product/category many-to-many junction with a composite PK. |
| `tags` | One row per unique tag name. |
| `product_tags` | Product/tag many-to-many junction with a composite PK. |
| `warehouses` | One row per unique warehouse location. |
| `inventory` | Stock quantity per product and warehouse; composite PK `(product_id, warehouse_id)`. |

### Relationships

- One supplier can provide many products; each product references one supplier
  through `products.supplier_id`.
- Products and categories are many-to-many through `product_categories`.
- Products and tags are many-to-many through `product_tags`.
- Products and warehouses are many-to-many through `inventory`, whose quantity
  describes the stock fact for that exact pair.
- Junction-table foreign keys enforce referential integrity; composite primary
  keys prevent duplicate assignments or stock rows.

## Why the design satisfies 3NF

- **1NF:** All stored attributes are atomic. Categories, tags, and warehouse
  stock are represented by rows, not comma-separated or repeating fields.
- **2NF:** The junction tables contain no non-key attributes. In `inventory`,
  `stock_quantity` depends on the full `(product_id, warehouse_id)` key; it
  does not depend on only one side.
- **3NF:** Supplier contact details depend only on `supplier_id` in
  `suppliers`; product attributes depend only on `product_id` in `products`;
  category and tag names depend only on their own identifiers. No non-key
  attribute in those tables determines another non-key attribute.

## Updated queries

`queries/product_queries.sql` contains all four original use cases:

1. List each product once, using correlated joins to produce display-friendly
   category/tag/location summaries and total stock across its warehouses.
2. Find products in a category whose name contains `Electronics`, joining
   products through `product_categories` to `categories`. `DISTINCT` prevents
   duplicates if more than one matching category is assigned.
3. Retrieve product and supplier contact details by joining `products` to
   `suppliers`.
4. Find low-stock product/warehouse pairs by joining `products`, `inventory`,
   and `warehouses`. Location is included because stock is warehouse-specific.

For example, the category lookup follows
`products → product_categories → categories`; the low-stock lookup follows
`products → inventory → warehouses`.

## Setup and execution

Install SQLite with its command-line tool, then run these commands from the
project root:

```text
sqlite3 catalog.db
.read schema/normalized_schema.sql
.read queries/product_queries.sql
.quit
```

The schema enables SQLite foreign-key enforcement. When executing statements
through another SQLite connection, enable it for that connection as well:

```sql
PRAGMA foreign_keys = ON;
```

The queries use SQLite's `group_concat` for the display summaries.

## Tests

Python 3's standard library is sufficient; no third-party package is needed.
Run the reproducible schema, integrity, sample-data, and query tests with:

```text
python -m unittest discover -s tests -v
```

The test suite creates an in-memory SQLite database, loads the schema and
representative data, executes each updated query, and checks primary keys,
foreign keys, unique constraints, non-negative checks, and expected results.
