import sqlite3
from pathlib import Path


# Location of our database
DATABASE_FILE = Path(__file__).parent / "grocery_prices.db"


def create_database():
    """
    Create the grocery database and required tables.
    """

    connection = sqlite3.connect(DATABASE_FILE)

    cursor = connection.cursor()

    # Retailer/platform table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS retailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    # Product table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT,
            quantity REAL,
            unit TEXT
        )
    """)

    # Price table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            retailer_id INTEGER NOT NULL,
            price REAL NOT NULL,
            checked_at TEXT NOT NULL,

            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (retailer_id) REFERENCES retailers(id)
        )
    """)

    connection.commit()
    connection.close()

    print("✅ Database created successfully!")


if __name__ == "__main__":
    create_database()