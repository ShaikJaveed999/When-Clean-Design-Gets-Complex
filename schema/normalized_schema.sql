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
