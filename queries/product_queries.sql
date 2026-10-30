-- PRODUCT QUERIES
-- These SQLite queries preserve the original product, supplier, category,
-- tag, and stock use cases against the normalized schema.

-- Query 1
-- Get one row per product, with its independent multi-valued attributes
-- summarized for display. Inventory stock_quantity is the total across
-- warehouses; Query 4 reports stock at each warehouse.
SELECT
    p.product_id,
    p.product_name,
    (
        SELECT group_concat(category_name, ', ')
        FROM (
            SELECT c.category_name
            FROM product_categories AS pc
            JOIN categories AS c ON c.category_id = pc.category_id
            WHERE pc.product_id = p.product_id
            ORDER BY c.category_name
        )
    ) AS categories,
    s.supplier_name,
    s.supplier_phone,
    s.supplier_email,
    (
        SELECT group_concat(tag_name, ', ')
        FROM (
            SELECT t.tag_name
            FROM product_tags AS pt
            JOIN tags AS t ON t.tag_id = pt.tag_id
            WHERE pt.product_id = p.product_id
            ORDER BY t.tag_name
        )
    ) AS product_tags,
    p.price,
    (
        SELECT group_concat(location, ', ')
        FROM (
            SELECT w.location
            FROM inventory AS i
            JOIN warehouses AS w ON w.warehouse_id = i.warehouse_id
            WHERE i.product_id = p.product_id
            ORDER BY w.location
        )
    ) AS warehouse_location,
    (
        SELECT COALESCE(SUM(i.stock_quantity), 0)
        FROM inventory AS i
        WHERE i.product_id = p.product_id
    ) AS stock_quantity
FROM products AS p
JOIN suppliers AS s ON s.supplier_id = p.supplier_id
ORDER BY p.product_id;

-- Query 2
-- Find products in categories whose names contain the requested term.
-- DISTINCT keeps a product from appearing more than once if it has several
-- matching categories.
SELECT DISTINCT p.product_id, p.product_name, p.price
FROM products AS p
JOIN product_categories AS pc ON pc.product_id = p.product_id
JOIN categories AS c ON c.category_id = pc.category_id
WHERE c.category_name LIKE '%Electronics%'
ORDER BY p.product_name;

-- Query 3
-- Supplier attributes are stored once and reached through the product FK.
SELECT p.product_name, s.supplier_name, s.supplier_phone
FROM products AS p
JOIN suppliers AS s ON s.supplier_id = p.supplier_id
ORDER BY p.product_name;

-- Query 4
-- Inventory is warehouse-specific, so include the location with each low-stock
-- result rather than treating stock as a product-wide attribute.
SELECT p.product_name, w.location AS warehouse_location, i.stock_quantity
FROM products AS p
JOIN inventory AS i ON i.product_id = p.product_id
JOIN warehouses AS w ON w.warehouse_id = i.warehouse_id
WHERE i.stock_quantity < 10
ORDER BY i.stock_quantity, p.product_name, w.location;
