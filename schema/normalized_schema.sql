-- Normalized e-commerce catalog schema for SQLite.
PRAGMA foreign_keys = ON;

CREATE TABLE suppliers (
    supplier_id INTEGER PRIMARY KEY,
    supplier_name TEXT NOT NULL CHECK (length(trim(supplier_name)) > 0),
    supplier_phone TEXT,
    supplier_email TEXT UNIQUE
);

-- Each product has one supplier; supplier contact data is stored once.
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL CHECK (length(trim(product_name)) > 0),
    supplier_id INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- idx_products_supplier_id on products(supplier_id) supports supplier-first
-- Query 3 joins and efficient supplier FK checks/deletes without table scans.
CREATE INDEX idx_products_supplier_id ON products (supplier_id);

-- idx_products_product_name on products(product_name) supports Queries 2 and
-- 3 ORDER BY product_name and can avoid a separate sort when selected.
CREATE INDEX idx_products_product_name ON products (product_name);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
        CHECK (length(trim(category_name)) > 0)
);

-- Products and categories are many-to-many; the composite key prevents
-- assigning the same category to a product more than once.
CREATE TABLE product_categories (
    product_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (product_id, category_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories (category_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- idx_product_categories_category_id_product_id on
-- product_categories(category_id, product_id) supports Query 2's lookup from
-- matched categories to products; the PK starts with product_id instead.
-- The leading-wildcard LIKE on category_name itself still requires a scan.
CREATE INDEX idx_product_categories_category_id_product_id
    ON product_categories (category_id, product_id);

CREATE TABLE tags (
    tag_id INTEGER PRIMARY KEY,
    tag_name TEXT NOT NULL UNIQUE CHECK (length(trim(tag_name)) > 0)
);

-- Tags are independent labels and are assigned to products many-to-many.
CREATE TABLE product_tags (
    product_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (product_id, tag_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (tag_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- idx_product_tags_tag_id_product_id on product_tags(tag_id, product_id)
-- supports tag-side lookups and FK checks/deletes; its PK starts with
-- product_id for Query 1.
CREATE INDEX idx_product_tags_tag_id_product_id
    ON product_tags (tag_id, product_id);

CREATE TABLE warehouses (
    warehouse_id INTEGER PRIMARY KEY,
    location TEXT NOT NULL UNIQUE CHECK (length(trim(location)) > 0)
);

-- Quantity is a fact about one product at one warehouse, so it depends on
-- the complete composite key rather than on either identifier by itself.
CREATE TABLE inventory (
    product_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
    PRIMARY KEY (product_id, warehouse_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses (warehouse_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- idx_inventory_warehouse_id_product_id on inventory(warehouse_id, product_id)
-- supports warehouse-side lookups and FK checks/deletes; the PK starts with
-- product_id.
CREATE INDEX idx_inventory_warehouse_id_product_id
    ON inventory (warehouse_id, product_id);

-- idx_inventory_stock_quantity_product_warehouse on
-- inventory(stock_quantity, product_id, warehouse_id) supports Query 4's
-- low-stock range and covers its inventory columns for the product/warehouse joins.
CREATE INDEX idx_inventory_stock_quantity_product_warehouse
    ON inventory (stock_quantity, product_id, warehouse_id);
