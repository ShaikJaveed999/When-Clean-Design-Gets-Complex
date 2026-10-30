# When Clean Design Gets Complex — 3NF Database Normalization

## Assignment overview

This challenge redesigns the e-commerce schema in `schema/broken_schema.sql`
and updates the product queries to use the normalized schema in
`schema/normalized_schema.sql`. The SQL targets SQLite.

## Problems in the original schema

The original `products` table stores:

- `categories` and `product_tags` as comma-separated values. These repeating,
  non-atomic groups violate 1NF and make individual values difficult to query
  and constrain.
- Supplier name, phone, and email alongside each product. The supplier's
  contact details describe the supplier, not the product, so they are repeated
  for every product from that supplier.
- A warehouse location and stock quantity in the product row. This mixes
  inventory facts with product identity and cannot represent stock for a
  product at multiple warehouses.
- No declared foreign keys, uniqueness rules, or checks for valid prices and
  quantities.

These choices lead to update anomalies (supplier details must be changed on
multiple product rows), insertion anomalies (a supplier or category cannot be
stored independently), and deletion anomalies (deleting a supplier's final
product can remove its only stored contact information). The original schema
has no composite keys, so there is no declared partial dependency; supplier
contact details do, however, depend on the supplier rather than the product.

## Normalized tables

| Table | Purpose |
|---|---|
| `suppliers` | One row per supplier, with contact information stored once. |
| `products` | Product name, price, and its supplier foreign key. |
| `categories` | One row per unique category name. |
| `product_categories` | Many-to-many product/category assignments. |
| `tags` | One row per unique tag name. |
| `product_tags` | Many-to-many product/tag assignments. |
| `warehouses` | One row per unique warehouse location. |
| `inventory` | Stock quantity for one product at one warehouse. |

### Keys and relationships

- `suppliers.supplier_id` is the supplier primary key. One supplier can provide
  many products; each product has one required supplier via
  `products.supplier_id`.
- `products.product_id`, `categories.category_id`, `tags.tag_id`, and
  `warehouses.warehouse_id` are primary keys.
- `product_categories` uses `(product_id, category_id)` as a composite primary
  key. Its foreign keys connect products and categories and prevent duplicate
  assignments.
- `product_tags` uses `(product_id, tag_id)` as a composite primary key and
  connects products and tags.
- `inventory` uses `(product_id, warehouse_id)` as a composite primary key.
  Its foreign keys connect products and warehouses; the key ensures at most
  one stock row for a product at a given warehouse.
- Foreign keys cascade deletion of product-specific junction and inventory
  facts. Supplier deletion is restricted while products reference it, and
  warehouse deletion is restricted while inventory exists.

## Why the design satisfies 3NF

- **1NF:** Every stored field contains a single value. Categories, tags, and
  warehouse-specific stock are represented as rows rather than repeating
  values in product columns.
- **2NF:** Junction tables contain only their composite key columns. In
  `inventory`, `stock_quantity` depends on the full `(product_id, warehouse_id)`
  key, not on just one part.
- **3NF:** Product attributes depend on `product_id`; supplier contact
  attributes depend on `supplier_id`; category, tag, and warehouse attributes
  depend on their respective identifiers. No non-key attribute determines
  another non-key attribute within these tables.

## Updated queries

`queries/product_queries.sql` retains the four original use cases:

1. List each product once, with category, tag, and warehouse summaries plus
   total stock across warehouses.
2. Find products in categories whose names contain `Electronics`, joining
   `products → product_categories → categories`. `DISTINCT` avoids duplicate
   products when multiple categories match.
3. Retrieve supplier contact details by joining `products` to `suppliers`.
4. Find low-stock product/warehouse pairs by joining `products`,
   `inventory`, and `warehouses`. The location is included because stock is
   specific to a warehouse.

The first query uses correlated subqueries to summarize multi-valued
relationships without multiplying product rows. The fourth query reports
warehouse-level quantities, while the first reports their total.

### Indexing Strategy

The schema defines these explicit indexes for the query and foreign-key access
patterns. Primary keys and `UNIQUE` constraints also create SQLite indexes
automatically; the table below focuses on additional indexes.

| Index name | Table | Indexed columns | Supported query pattern | Reason |
|---|---|---|---|---|
| `idx_products_supplier_id` | `products` | `supplier_id` | Supplier-first Query 3 join plans; supplier foreign-key checks and deletes | Finds products by supplier without scanning every product when a supplier is joined, changed, or deleted. |
| `idx_products_product_name` | `products` | `product_name` | Queries 2 and 3 ordering by product name | Can provide products in name order and avoid a separate sort when SQLite's chosen join plan can use that order. |
| `idx_product_categories_category_id_product_id` | `product_categories` | `category_id`, `product_id` | Query 2 category-to-product lookup after matching category rows | The junction primary key starts with `product_id`; this reverse-order index finds matching product IDs. Query 2's leading-wildcard `LIKE` still scans category names. |
| `idx_product_tags_tag_id_product_id` | `product_tags` | `tag_id`, `product_id` | Tag-side lookups and tag foreign-key checks/deletes | The junction primary key starts with `product_id`; this reverse-order index avoids scanning all assignments when looking up or maintaining a tag. |
| `idx_inventory_warehouse_id_product_id` | `inventory` | `warehouse_id`, `product_id` | Warehouse-side inventory lookups and warehouse foreign-key checks/deletes | The inventory primary key starts with `product_id`; this index supports the opposite lookup direction. |
| `idx_inventory_stock_quantity_product_warehouse` | `inventory` | `stock_quantity`, `product_id`, `warehouse_id` | Query 4 low-stock range filter and inventory-to-product/warehouse joins | Supports `stock_quantity < 10` and contains the inventory identifiers and quantity needed by the query. |

Indexes let SQLite find matching rows or join keys without repeatedly scanning
whole tables. The composite indexes put the column used to start a lookup first;
their following columns can then help return matching identifiers or cover a
query. The low-stock index starts with the filtered range column and includes
both foreign keys used by Query 4. SQLite's planner still chooses whether an
index is beneficial for a particular data size and distribution.

Indexes consume disk space and make inserts, updates, and deletes more
expensive because each affected index must also be maintained. Adding an index
for every column is therefore not beneficial: it increases storage and write
cost without necessarily improving reads. Unique constraints and primary keys
already create indexes, so duplicating those indexes would be redundant.

Normalization reduces repeated facts and improves integrity, but retrieving a
complete product view now needs joins through supplier, category, tag, and
inventory relationships. Indexes on foreign keys and both sides of junction
tables help those joins locate matching rows efficiently; the query-specific
indexes also support filtering and ordering. Indexes reduce lookup work, but
they do not remove the inherent cost of joining multiple normalized tables.

The video walkthrough and screen-share sequence are in
[`VIDEO_EXPLANATION.md`](VIDEO_EXPLANATION.md).

## Setup and execution

SQLite is used for both the schema and queries. To run them with the SQLite
command-line tool from this directory:

```text
sqlite3 catalog.db
.read schema/normalized_schema.sql
.read queries/product_queries.sql
.quit
```

Foreign-key enforcement is enabled by the schema for the current SQLite
connection. Enable it on each additional SQLite connection as well:

```sql
PRAGMA foreign_keys = ON;
```

The query file uses SQLite's `group_concat` for the display summaries.

## Testing

Python 3's standard library includes SQLite support; no third-party packages
are required. Run the automated tests from this directory:

```text
python -m unittest discover -s tests -v
```

The tests load the schema into an in-memory database, add representative
products, suppliers, categories, tags, warehouses, and inventory, execute all
four updated queries, and verify expected results and key/constraint behavior.

Validation completed with Python 3.13.7 and SQLite 3.50.4:

```text
Ran 8 tests
OK
```

The suite also attempts invalid inserts to verify primary keys, foreign keys,
uniqueness, required (`NOT NULL`) columns, non-empty names, and non-negative
prices and quantities. It checks index names and column order and verifies with
`EXPLAIN QUERY PLAN` that SQLite uses the product-name ordering index and the
low-stock range index for their corresponding queries.
