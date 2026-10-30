# Video Explanation Script (3–5 minutes)

**Target length:** about 4 minutes  
**Recording note:** This is a script and screen-share plan. No video has been
recorded or uploaded.

## 0:00–0:35 — Introduce the original schema

**Show:** `schema/broken_schema.sql`

“This challenge models a simple e-commerce catalog. The original `products`
table puts comma-separated categories and tags in single columns, repeats
supplier contact details on each product, and stores one warehouse location
and stock quantity alongside product data. These choices cause update,
insertion, and deletion anomalies. The single inventory fields also cannot
represent the same product at more than one warehouse.”

## 0:35–1:35 — Explain the normalized design

**Show:** `schema/normalized_schema.sql`, scrolling through the table
definitions.

“The normalized schema gives each independent fact its own table: suppliers,
products, categories, tags, and warehouses. Products and categories are
many-to-many, represented by `product_categories`; products and tags use
`product_tags`. Inventory records a quantity for one product at one warehouse,
using the pair of IDs as its composite primary key.

“Foreign keys enforce the relationships. Unique and check constraints guard
names, prices, and stock values. Each descriptive attribute belongs to the key
that determines it. Inventory quantity depends on the full product/warehouse
key, so the design avoids partial and transitive dependencies.”

## 1:35–2:30 — Demonstrate the queries

**Show:** `queries/product_queries.sql`; point to each `-- Query` heading.

“Query 1 returns one row per product and uses correlated lookups to summarize
categories, tags, and warehouse locations without multiplying product rows.
It also totals stock across warehouses.

“Query 2 joins products through `product_categories` to categories to find
matching category names. Query 3 joins products to suppliers for contact
details. Query 4 joins products, inventory, and warehouses to show each
low-stock product at its specific location.”

## 2:30–3:25 — Explain indexes

**Show:** the index definitions near the bottom of
`schema/normalized_schema.sql`, then the “Indexing Strategy” table in
`README.md`.

“The category junction’s primary key starts with product ID, which supports
product-first reads. A second index begins with category ID for category-to-
product lookups in Query 2 after category names are matched. The query's
leading-wildcard `LIKE` still scans category names. Similar reverse-order
indexes support tag and warehouse lookups and foreign-key maintenance.

“The supplier index supports Query 3's supplier join. The stock-quantity
composite index supports Query 4's low-stock range and includes the product and
warehouse IDs. Product name indexing can help the ordered results. SQLite's
query planner decides which indexes help for the current data.”

## 3:25–4:00 — Trade-offs and test results

**Show:** `README.md` indexing and testing sections; optionally run
`python -B -m unittest discover -s tests -v`.

“Normalization improves consistency but means a product view needs more
joins. Foreign-key and junction indexes help those lookups, while indexes
consume storage and make writes more expensive. We avoid duplicate indexes
already created by primary keys and unique constraints.

“The test suite loads realistic sample data into in-memory SQLite, runs all
four queries, checks constraints and relationships, verifies the explicit
index definitions, and inspects query plans for the product-name and low-stock
indexes. The current run passes all eight tests.”

## Recording checklist

- [ ] Show the original schema and identify the multi-valued and mixed facts.
- [ ] Show all entity and junction tables and explain their keys/relationships.
- [ ] Run or point to all four updated queries and explain their joins.
- [ ] Show each explicit index and match it to its query pattern in the README.
- [ ] Explain index storage/write overhead and the joins introduced by normalization.
- [ ] Run the test command or show its real output.
- [ ] Keep the final recording between 3 and 5 minutes.
- [ ] Upload the video yourself and add its URL to the assignment/PR if requested.
