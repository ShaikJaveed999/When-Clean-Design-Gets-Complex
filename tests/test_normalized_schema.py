import re
import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NormalizedSchemaTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(
            (ROOT / "schema" / "normalized_schema.sql").read_text(
                encoding="utf-8"
            )
        )
        self._insert_sample_data()

    def tearDown(self):
        self.connection.close()

    def _insert_sample_data(self):
        self.connection.executescript(
            """
            INSERT INTO suppliers
                (supplier_id, supplier_name, supplier_phone, supplier_email)
            VALUES
                (1, 'Acme Electronics', '555-0101', 'sales@acme.example'),
                (2, 'Northwind Furnishings', '555-0202', 'orders@northwind.example');

            INSERT INTO products (product_id, product_name, supplier_id, price)
            VALUES
                (100, 'Wireless Headphones', 1, 79.99),
                (101, 'USB-C Charger', 1, 19.95),
                (102, 'Ergonomic Chair', 2, 249.00);

            INSERT INTO categories (category_id, category_name)
            VALUES
                (1, 'Electronics'),
                (2, 'Audio'),
                (3, 'Furniture');

            INSERT INTO product_categories (product_id, category_id)
            VALUES
                (100, 1),
                (100, 2),
                (101, 1),
                (102, 3);

            INSERT INTO tags (tag_id, tag_name)
            VALUES
                (1, 'Bluetooth'),
                (2, 'Audio'),
                (3, 'Charging'),
                (4, 'Office'),
                (5, 'Ergonomic');

            INSERT INTO product_tags (product_id, tag_id)
            VALUES
                (100, 1),
                (100, 2),
                (101, 3),
                (102, 4),
                (102, 5);

            INSERT INTO warehouses (warehouse_id, location)
            VALUES (1, 'Central'), (2, 'North');

            INSERT INTO inventory (product_id, warehouse_id, stock_quantity)
            VALUES
                (100, 1, 8),
                (100, 2, 15),
                (101, 1, 4),
                (102, 2, 12);
            """
        )

    def _query_blocks(self):
        script = (ROOT / "queries" / "product_queries.sql").read_text(
            encoding="utf-8"
        )
        blocks = re.split(r"(?=-- Query \d+)", script)
        return [
            block.strip()
            for block in blocks
            if re.match(r"-- Query \d+", block.strip())
        ]

    def test_all_queries_execute_with_expected_results(self):
        blocks = self._query_blocks()
        self.assertEqual(len(blocks), 4)

        results = [self.connection.execute(block).fetchall() for block in blocks]

        self.assertEqual(len(results[0]), 3)
        headphones = results[0][0]
        self.assertEqual(headphones[1], "Wireless Headphones")
        self.assertEqual(headphones[2], "Audio, Electronics")
        self.assertEqual(headphones[6], "Audio, Bluetooth")
        self.assertEqual(headphones[8], "Central, North")
        self.assertEqual(headphones[9], 23)

        self.assertEqual(
            [(row[1], row[2]) for row in results[1]],
            [("USB-C Charger", 19.95), ("Wireless Headphones", 79.99)],
        )
        self.assertEqual(len(results[2]), 3)
        self.assertEqual(
            [(row[0], row[1]) for row in results[3]],
            [("USB-C Charger", "Central"), ("Wireless Headphones", "Central")],
        )

    def test_primary_keys_foreign_keys_and_uniqueness(self):
        invalid_rows = (
            "INSERT INTO suppliers VALUES (1, 'Duplicate ID', NULL, NULL)",
            "INSERT INTO products VALUES (100, 'Duplicate ID', 1, 1)",
            "INSERT INTO categories VALUES (1, 'Duplicate ID')",
            "INSERT INTO tags VALUES (1, 'Duplicate ID')",
            "INSERT INTO warehouses VALUES (1, 'Duplicate ID')",
            "INSERT INTO product_categories VALUES (100, 1)",
            "INSERT INTO product_categories VALUES (999, 1)",
            "INSERT INTO product_categories VALUES (100, 999)",
            "INSERT INTO product_tags VALUES (100, 1)",
            "INSERT INTO product_tags VALUES (999, 1)",
            "INSERT INTO product_tags VALUES (100, 999)",
            "INSERT INTO inventory VALUES (100, 1, 3)",
            "INSERT INTO inventory VALUES (999, 1, 3)",
            "INSERT INTO inventory VALUES (100, 999, 3)",
            "INSERT INTO products VALUES (200, 'Unknown supplier', 999, 1)",
            "INSERT INTO categories (category_name) VALUES ('Electronics')",
            "INSERT INTO tags (tag_name) VALUES ('Bluetooth')",
            (
                "INSERT INTO suppliers "
                "(supplier_name, supplier_email) "
                "VALUES ('Duplicate email', 'sales@acme.example')"
            ),
        )
        for statement in invalid_rows:
            with self.subTest(statement=statement):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.connection.execute(statement)

        self.assertEqual(
            self.connection.execute("PRAGMA foreign_key_check").fetchall(), []
        )

    def test_explicit_indexes_have_expected_columns_and_order(self):
        expected_indexes = {
            "idx_products_supplier_id": ("products", ("supplier_id",)),
            "idx_products_product_name": ("products", ("product_name",)),
            "idx_product_categories_category_id_product_id": (
                "product_categories",
                ("category_id", "product_id"),
            ),
            "idx_product_tags_tag_id_product_id": (
                "product_tags",
                ("tag_id", "product_id"),
            ),
            "idx_inventory_warehouse_id_product_id": (
                "inventory",
                ("warehouse_id", "product_id"),
            ),
            "idx_inventory_stock_quantity_product_warehouse": (
                "inventory",
                ("stock_quantity", "product_id", "warehouse_id"),
            ),
        }

        for index_name, (table_name, expected_columns) in expected_indexes.items():
            with self.subTest(index=index_name):
                index_list = self.connection.execute(
                    f"PRAGMA index_list('{table_name}')"
                ).fetchall()
                self.assertIn(index_name, {row[1] for row in index_list})

                actual_columns = tuple(
                    row[2]
                    for row in self.connection.execute(
                        f"PRAGMA index_info('{index_name}')"
                    ).fetchall()
                )
                self.assertEqual(actual_columns, expected_columns)

    def test_query_plans_use_ordering_and_low_stock_indexes(self):
        blocks = self._query_blocks()

        product_listing_plan = " ".join(
            row[3]
            for row in self.connection.execute(
                f"EXPLAIN QUERY PLAN {blocks[2]}"
            ).fetchall()
        )
        self.assertIn("idx_products_product_name", product_listing_plan)

        low_stock_plan = " ".join(
            row[3]
            for row in self.connection.execute(
                f"EXPLAIN QUERY PLAN {blocks[3]}"
            ).fetchall()
        )
        self.assertIn(
            "idx_inventory_stock_quantity_product_warehouse",
            low_stock_plan,
        )

    def test_non_negative_and_non_empty_checks(self):
        invalid_rows = (
            (
                "INSERT INTO products (product_name, supplier_id, price) "
                "VALUES ('Invalid price', 1, -0.01)"
            ),
            (
                "INSERT INTO inventory (product_id, warehouse_id, stock_quantity) "
                "VALUES (101, 2, -1)"
            ),
            (
                "INSERT INTO products (product_name, supplier_id, price) "
                "VALUES ('   ', 1, 1)"
            ),
        )
        for statement in invalid_rows:
            with self.subTest(statement=statement):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.connection.execute(statement)

    def test_required_columns_reject_null_values(self):
        invalid_rows = (
            "INSERT INTO suppliers (supplier_name) VALUES (NULL)",
            "INSERT INTO products (product_name, supplier_id, price) "
            "VALUES (NULL, 1, 1)",
            "INSERT INTO products (product_name, supplier_id, price) "
            "VALUES ('Missing supplier', NULL, 1)",
            "INSERT INTO products (product_name, supplier_id, price) "
            "VALUES ('Missing price', 1, NULL)",
            "INSERT INTO categories (category_name) VALUES (NULL)",
            "INSERT INTO product_categories VALUES (NULL, 1)",
            "INSERT INTO product_categories VALUES (100, NULL)",
            "INSERT INTO tags (tag_name) VALUES (NULL)",
            "INSERT INTO product_tags VALUES (NULL, 1)",
            "INSERT INTO product_tags VALUES (100, NULL)",
            "INSERT INTO warehouses (location) VALUES (NULL)",
            "INSERT INTO inventory VALUES (NULL, 1, 0)",
            "INSERT INTO inventory VALUES (100, NULL, 0)",
            "INSERT INTO inventory VALUES (100, 1, NULL)",
        )
        for statement in invalid_rows:
            with self.subTest(statement=statement):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.connection.execute(statement)

    def test_product_deletion_cascades_to_product_facts(self):
        self.connection.execute("DELETE FROM products WHERE product_id = 100")
        for table in ("product_categories", "product_tags", "inventory"):
            with self.subTest(table=table):
                count = self.connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE product_id = 100"
                ).fetchone()[0]
                self.assertEqual(count, 0)

    def test_supplier_and_warehouse_deletion_is_restricted(self):
        for statement in (
            "DELETE FROM suppliers WHERE supplier_id = 1",
            "DELETE FROM warehouses WHERE warehouse_id = 1",
        ):
            with self.subTest(statement=statement):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.connection.execute(statement)


if __name__ == "__main__":
    unittest.main()
