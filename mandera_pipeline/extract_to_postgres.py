"""
Orchestrates extraction from MongoDB Atlas into PostgreSQL raw schema.

Pulls customers, products and orders from MongoDB and inserts them
into PostgreSQL raw tables. Designed to be called by the Airflow DAG
or run manually for testing.

USAGE:
    python -m mandera_pipeline.extract_to_postgres
"""

import os
from datetime import datetime, timezone

# load_dotenv() reads the .env file and makes all variables
# available to os.getenv() — must be called before anything else
from dotenv import load_dotenv

# Each import below is a focused module with a single responsibility
# This keeps extract_to_postgres.py clean — it only orchestrates
from mandera_pipeline.postgres.connection import get_pg_connection, get_mongo_client
from mandera_pipeline.postgres.schema import create_raw_schema
from mandera_pipeline.postgres.extract_customers import extract_customers
from mandera_pipeline.postgres.extract_products import extract_products
from mandera_pipeline.postgres.extract_orders import extract_orders

# Load .env variables into the environment
load_dotenv()


def main() -> None:
    """Orchestrate the full MongoDB -> PostgreSQL raw extraction."""

    # Log the start time so we can track how long the extraction takes
    print(f"Starting extraction: {datetime.now(timezone.utc).isoformat()}\n")

    # ── Open connections ───────────────────────────────────────────────────────

    # Connect to MongoDB Atlas using the MONGO_URL from .env
    mongo_client = get_mongo_client()

    # Select the specific database inside MongoDB
    # os.getenv("MONGO_DB_NAME") returns "mandera_db" from .env
    mongo_db = mongo_client[os.getenv("MONGO_DB_NAME")]

    # Connect to PostgreSQL running in Docker
    # Uses POSTGRES_HOST, PORT, DB, USER, PASSWORD from .env
    pg_conn = get_pg_connection()

    # A cursor is the object we use to send SQL commands to PostgreSQL
    # Think of it like a pen — pg_conn is the notebook, cursor is the pen
    pg_cursor = pg_conn.cursor()

    try:
        # ── Step 1: Create schema and tables ──────────────────────────────────
        # Creates the raw schema and all 3 tables if they don't exist yet
        # Safe to run multiple times — IF NOT EXISTS handles that
        create_raw_schema(pg_cursor)
        print("  Raw schema and tables ready.")

        # ── Step 2: Extract each collection ───────────────────────────────────
        # Each function pulls from MongoDB and inserts into PostgreSQL
        # ON CONFLICT DO NOTHING means duplicate records are silently skipped
        # so re-running this script never causes duplicate key errors

        n_customers = extract_customers(mongo_db, pg_cursor)
        print(f"  Inserted {n_customers} customers into raw.customers")

        n_products = extract_products(mongo_db, pg_cursor)
        print(f"  Inserted {n_products} products into raw.products")

        n_orders = extract_orders(mongo_db, pg_cursor)
        print(f"  Inserted {n_orders} orders into raw.orders")

        # ── Step 3: Commit the transaction ────────────────────────────────────
        # Nothing is actually saved to PostgreSQL until commit() is called
        # If commit() is never reached (e.g. an error above), nothing is saved
        pg_conn.commit()
        print("\nExtraction complete. All changes committed.")

    except Exception as e:
        # If anything goes wrong, rollback() undoes all changes
        # This prevents partial data from landing in the raw tables
        pg_conn.rollback()
        print(f"  Extraction failed: {e}")
        raise

    finally:
        # Always runs — whether extraction succeeded or failed
        # Closes all connections to free up resources
        pg_cursor.close()
        pg_conn.close()
        mongo_client.close()
        print("  Connections closed.")


# This block only runs when the file is executed directly
# e.g. python extract_to_postgres.py
# It does NOT run when the file is imported by another module
if __name__ == "__main__":
    main()