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

    def test_all_updated_queries_execute_with_expected_results(self):
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
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO product_categories VALUES (100, 1)"
            )

        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO product_categories VALUES (999, 1)"
            )

        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO categories (category_name) VALUES ('Electronics')"
            )

        self.assertEqual(
            self.connection.execute("PRAGMA foreign_key_check").fetchall(), []
        )

    def test_non_negative_constraints(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO products (product_name, supplier_id, price) "
                "VALUES ('Invalid price', 1, -0.01)"
            )

        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO inventory (product_id, warehouse_id, stock_quantity) "
                "VALUES (101, 2, -1)"
            )

    def test_product_deletion_cascades_to_product_facts(self):
        self.connection.execute("DELETE FROM products WHERE product_id = 100")
        for table in ("product_categories", "product_tags", "inventory"):
            with self.subTest(table=table):
                count = self.connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE product_id = 100"
                ).fetchone()[0]
                self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
