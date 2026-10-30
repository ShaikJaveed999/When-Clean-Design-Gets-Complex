-- PRODUCT QUERIES
-- These SQLite queries support common product requests against
-- schema/normalized_schema.sql.

-- Query 1
-- Return one row per product, summarizing multi-valued relationships for
-- display and totaling stock across all warehouses. The junction-table
-- primary keys begin with product_id, supporting these correlated lookups.
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
-- DISTINCT prevents duplicate products if several assigned categories match.
-- idx_product_categories_category_id_product_id supports the category-side
-- lookup; it does not accelerate the leading-wildcard category-name LIKE.
-- idx_products_product_name can support the requested name ordering.
SELECT DISTINCT p.product_id, p.product_name, p.price
FROM products AS p
JOIN product_categories AS pc ON pc.product_id = p.product_id
JOIN categories AS c ON c.category_id = pc.category_id
WHERE c.category_name LIKE '%Electronics%'
ORDER BY p.product_name;

-- Query 3
-- Supplier contact attributes are reached through the product's supplier FK.
-- idx_products_supplier_id supports the join; idx_products_product_name can
-- support the result ordering.
SELECT p.product_name, s.supplier_name, s.supplier_phone
FROM products AS p
JOIN suppliers AS s ON s.supplier_id = p.supplier_id
ORDER BY p.product_name;

-- Query 4
-- Inventory is warehouse-specific, so report each low-stock product/location.
-- idx_inventory_stock_quantity_product_warehouse supports the range filter;
-- primary keys on products and warehouses support the remaining joins.
SELECT p.product_name, w.location AS warehouse_location, i.stock_quantity
FROM products AS p
JOIN inventory AS i ON i.product_id = p.product_id
JOIN warehouses AS w ON w.warehouse_id = i.warehouse_id
WHERE i.stock_quantity < 10
ORDER BY i.stock_quantity, p.product_name, w.location;
