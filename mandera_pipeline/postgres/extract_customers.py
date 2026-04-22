"""
Extracts customer documents from MongoDB into raw.customers in PostgreSQL.

Responsibility: one collection, one table, one function.
This module only handles customers — products and orders have their own modules.
"""

import psycopg2
import psycopg2.extras

# Database is the type hint for a pymongo database instance
# Using type hints makes the function signature self-documenting
from pymongo.database import Database


def extract_customers(mongo_db: Database, cursor: psycopg2.extensions.cursor) -> int:
    """Pull all customer documents from MongoDB and insert into raw.customers.

    Uses execute_values() for bulk insertion — far more efficient than
    inserting one row at a time in a loop. ON CONFLICT DO NOTHING means
    this is safe to re-run — existing records are silently skipped.

    Args:
        mongo_db: Active MongoDB database instance.
        cursor: Active PostgreSQL cursor — part of an open transaction.

    Returns:
        Number of customer records inserted.
    """

    # .find() returns a lazy cursor — it doesn't load data until iterated
    # list() forces it to load all documents into memory at once
    # This is fine for the volumes we expect (15-25 customers per batch)
    customers = list(mongo_db["customers"].find())

    # Guard clause — exit early if the collection is empty
    if not customers:
        print("  No customers found in MongoDB.")
        return 0

    # Build a list of tuples — one tuple per customer document
    # doc.get() is safer than doc[] because it returns None instead of
    # raising a KeyError if a field is missing from a document
    # The order of fields must match the INSERT statement below exactly
    rows = [
        (
            doc.get("customer_id"),
            doc.get("name"),
            doc.get("email"),
            doc.get("phone"),
            doc.get("city"),
            doc.get("batch_id"),
            doc.get("created_at") or doc.get("creatred_at"),
        )
        for doc in customers
    ]

    # execute_values() sends all rows in a single SQL INSERT statement
    # Much faster than calling cursor.execute() in a loop
    # %s is the placeholder — psycopg2 safely escapes all values
    # preventing SQL injection attacks
    psycopg2.extras.execute_values(
        cursor,
        """
        INSERT INTO raw.customers
            (customer_id, name, email, phone, city, batch_id, created_at)
        VALUES %s
        ON CONFLICT (customer_id) DO NOTHING;
        """,
        rows,
    )

    # Return the count so the orchestrator can log how many were inserted
    return len(rows)