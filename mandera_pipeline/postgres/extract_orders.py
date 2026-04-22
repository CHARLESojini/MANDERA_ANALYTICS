"""
Extracts order documents from MongoDB into raw.orders in PostgreSQL.

Responsibility: one collection, one table, one function.
Orders are extracted last because they reference customers and products.
Even though raw layer has no FK constraints, maintaining this order
is good practice and mirrors the dependency chain.
"""

import psycopg2
import psycopg2.extras
from pymongo.database import Database


def extract_orders(mongo_db: Database, cursor: psycopg2.extensions.cursor) -> int:
    """Pull all order documents from MongoDB and insert into raw.orders.

    Orders are the largest collection — potentially thousands of records
    per batch. execute_values() handles bulk inserts efficiently regardless
    of volume. ON CONFLICT DO NOTHING prevents duplicate key errors on re-runs.

    Args:
        mongo_db: Active MongoDB database instance.
        cursor: Active PostgreSQL cursor — part of an open transaction.

    Returns:
        Number of order records inserted.
    """

    # Fetch all order documents from MongoDB
    # For large collections this loads everything into memory at once
    # For very large datasets (millions of rows) we would use pagination
    # but for our current volumes this is acceptable
    orders = list(mongo_db["orders"].find())

    # Guard clause — exit early if the collection is empty
    if not orders:
        print("  No orders found in MongoDB.")
        return 0

    # Build a list of tuples — one tuple per order document
    # 11 fields per order — order must match the INSERT column list below
    # doc.get() safely handles any missing fields by returning None
    rows = [
        (
            doc.get("order_id"),
            doc.get("customer_id"),    # references a customer
            doc.get("product_id"),     # references a product
            doc.get("quantity"),
            doc.get("unit_price"),
            doc.get("total_price"),    # pre-calculated in fake_orders.py
            doc.get("status"),         # e.g. pending, shipped, delivered
            doc.get("payment_method"), # e.g. credit_card, paypal
            doc.get("shipping_method"),# e.g. standard, express
            doc.get("batch_id"),
            doc.get("created_at"),
        )
        for doc in orders
    ]

    # Bulk insert all orders in a single SQL statement
    # ON CONFLICT (order_id) DO NOTHING — skip duplicates silently
    # This makes the pipeline idempotent — safe to re-run without side effects
    psycopg2.extras.execute_values(
        cursor,
        """
        INSERT INTO raw.orders
            (order_id, customer_id, product_id, quantity, unit_price,
             total_price, status, payment_method, shipping_method, batch_id, created_at)
        VALUES %s
        ON CONFLICT (order_id) DO NOTHING;
        """,
        rows,
    )

    return len(rows)