import json
import sqlite3
from pathlib import Path
from datetime import datetime


# Project folders
PROJECT_ROOT = Path(__file__).parent.parent

DATABASE_FILE = PROJECT_ROOT / "database" / "grocery_prices.db"
DATA_FILE = PROJECT_ROOT / "data" / "products.json"


def import_data():

    # Connect to database
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # Read JSON file
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        products = json.load(file)

    for item in products:

        # -------------------------
        # Add retailer
        # -------------------------

        cursor.execute(
            """
            INSERT OR IGNORE INTO retailers (name)
            VALUES (?)
            """,
            (item["platform"],)
        )

        cursor.execute(
            """
            SELECT id
            FROM retailers
            WHERE name = ?
            """,
            (item["platform"],)
        )

        retailer_id = cursor.fetchone()[0]

        # -------------------------
        # Add product
        # -------------------------

        cursor.execute(
            """
            SELECT id
            FROM products
            WHERE name = ?
            AND brand = ?
            AND quantity = ?
            AND unit = ?
            """,
            (
                item["product"],
                item["brand"],
                item["quantity"],
                item["unit"]
            )
        )

        existing_product = cursor.fetchone()

        if existing_product:

            product_id = existing_product[0]

        else:

            cursor.execute(
                """
                INSERT INTO products
                (name, brand, quantity, unit)
                VALUES (?, ?, ?, ?)
                """,
                (
                    item["product"],
                    item["brand"],
                    item["quantity"],
                    item["unit"]
                )
            )

            product_id = cursor.lastrowid

        # -------------------------
        # Add price
        # -------------------------

        checked_at = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO prices
            (product_id, retailer_id, price, checked_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                product_id,
                retailer_id,
                item["price"],
                checked_at
            )
        )

    connection.commit()
    connection.close()

    print("✅ Grocery data imported successfully!")


if __name__ == "__main__":
    import_data()