"""
Extracts product documents from MongoDB into raw.products in PostgreSQL.

Responsibility: one collection, one table, one function.
This module only handles products — customers and orders have their own modules.
"""

import psycopg2
import psycopg2.extras
from pymongo.database import Database


def extract_products(mongo_db: Database, cursor: psycopg2.extensions.cursor) -> int:
    """Pull all product documents from MongoDB and insert into raw.products.

    Uses execute_values() for bulk insertion — far more efficient than
    inserting one row at a time in a loop. ON CONFLICT DO NOTHING means
    this is safe to re-run — existing records are silently skipped.

    Args:
        mongo_db: Active MongoDB database instance.
        cursor: Active PostgreSQL cursor — part of an open transaction.

    Returns:
        Number of product records inserted.
    """

    # .find() with no arguments returns all documents in the collection
    # list() forces the lazy cursor to load all documents into memory
    products = list(mongo_db["products"].find())

    # Guard clause — exit early if the collection is empty
    if not products:
        print("  No products found in MongoDB.")
        return 0

    # Build a list of tuples — one tuple per product document
    # Field order must exactly match the INSERT column list below
    # doc.get() returns None for missing fields instead of raising KeyError
    rows = [
        (
            doc.get("product_id"),
            doc.get("product_name"),
            doc.get("category"),
            doc.get("price"),
            doc.get("batch_id") or doc.get("batch-id"),
            doc.get("created_at"),
        )
        for doc in products
    ]

    # execute_values() inserts all rows in one SQL statement
    # ON CONFLICT (product_id) DO NOTHING — skip if product already exists
    # This makes the extract idempotent — safe to run multiple times
    psycopg2.extras.execute_values(
        cursor,
        """
        INSERT INTO raw.products
            (product_id, product_name, category, price, batch_id, created_at)
        VALUES %s
        ON CONFLICT (product_id) DO NOTHING;
        """,
        rows,
    )

    return len(rows)