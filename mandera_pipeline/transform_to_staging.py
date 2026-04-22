"""
Orchestrates the validate and transform pipeline for MANDERA_ANALYTICS.

Reads from raw schema in PostgreSQL, validates each record against
data quality rules, applies cleaning transformations, then loads
clean records into the staging schema.

Failed records are logged and skipped — the pipeline continues
with valid data only.

Pipeline order:
  1. Customers  — no dependencies
  2. Products   — no dependencies
  3. Orders     — depends on customers and products (FK constraints)

USAGE:
    python -m mandera_pipeline.transform_to_staging
"""

import os
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


# Sentinel timestamp for null created_at from early batches with the typo
UNKNOWN_TIMESTAMP = datetime(1970, 1, 1, tzinfo=timezone.utc)


def get_pg_connection():
    """Create and return a PostgreSQL connection using env credentials."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def create_staging_schema(cursor):
    """Create staging schema and tables if they don't already exist."""
    cursor.execute("CREATE SCHEMA IF NOT EXISTS staging;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.customers (
            customer_id     VARCHAR PRIMARY KEY,
            name            VARCHAR NOT NULL,
            email           VARCHAR NOT NULL,
            phone           VARCHAR,
            city            VARCHAR,
            batch_id        INTEGER,
            created_at      TIMESTAMP WITH TIME ZONE,
            loaded_at       TIMESTAMP WITH TIME ZONE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.products (
            product_id      VARCHAR PRIMARY KEY,
            product_name    VARCHAR NOT NULL,
            category        VARCHAR NOT NULL,
            price           NUMERIC(10, 2),
            batch_id        INTEGER,
            created_at      TIMESTAMP WITH TIME ZONE,
            loaded_at       TIMESTAMP WITH TIME ZONE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.orders (
            order_id        VARCHAR PRIMARY KEY,
            customer_id     VARCHAR NOT NULL,
            product_id      VARCHAR NOT NULL,
            quantity        SMALLINT NOT NULL,
            unit_price      NUMERIC(10, 2) NOT NULL,
            total_price     NUMERIC(10, 2) NOT NULL,
            status          VARCHAR NOT NULL,
            payment_method  VARCHAR,
            shipping_method VARCHAR,
            batch_id        INTEGER,
            created_at      TIMESTAMP WITH TIME ZONE,
            loaded_at       TIMESTAMP WITH TIME ZONE
        );
    """)


def fetch_raw(cursor, table: str) -> list:
    """Fetch all records from a raw schema table as a list of dicts."""
    cursor.execute(f"SELECT * FROM raw.{table};")
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def transform_customers(rows: list, cursor, loaded_at: datetime) -> int:
    """Validate, clean and load customer records into staging.customers."""
    valid    = []
    rejected = 0

    for row in rows:
        if not row.get("customer_id") or not row.get("name") or not row.get("email"):
            print(f"  [REJECTED] Customer missing required field: {row.get('customer_id')}")
            rejected += 1
            continue

        valid.append((
            row.get("customer_id"),
            row.get("name", "").strip().title(),
            row.get("email", "").strip().lower(),
            row.get("phone", "").strip().replace("-", "").replace(".", "").replace(" ", "") if row.get("phone") else None,
            row.get("city", "").strip() if row.get("city") else None,
            row.get("batch_id"),
            row.get("created_at") or UNKNOWN_TIMESTAMP,
            loaded_at,
        ))

    if valid:
        psycopg2.extras.execute_values(
            cursor,
            """
            INSERT INTO staging.customers
                (customer_id, name, email, phone, city, batch_id, created_at, loaded_at)
            VALUES %s
            ON CONFLICT (customer_id) DO NOTHING;
            """,
            valid,
        )

    print(f"  Customers: {len(valid)} loaded, {rejected} rejected")
    return len(valid)


def transform_products(rows: list, cursor, loaded_at: datetime) -> int:
    """Validate, clean and load product records into staging.products."""
    valid    = []
    rejected = 0

    for row in rows:
        if not row.get("product_id") or not row.get("product_name") or not row.get("category"):
            print(f"  [REJECTED] Product missing required field: {row.get('product_id')}")
            rejected += 1
            continue

        price = row.get("price")
        if price is None or float(price) <= 0:
            print(f"  [REJECTED] Product {row.get('product_id')} invalid price: {price}")
            rejected += 1
            continue

        valid.append((
            row.get("product_id"),
            row.get("product_name", "").strip().title(),
            row.get("category", "").strip().title(),
            round(float(price), 2),
            row.get("batch_id") or row.get("batch-id"),
            row.get("created_at"),
            loaded_at,
        ))

    if valid:
        psycopg2.extras.execute_values(
            cursor,
            """
            INSERT INTO staging.products
                (product_id, product_name, category, price, batch_id, created_at, loaded_at)
            VALUES %s
            ON CONFLICT (product_id) DO NOTHING;
            """,
            valid,
        )

    print(f"  Products: {len(valid)} loaded, {rejected} rejected")
    return len(valid)


def transform_orders(rows: list, cursor, loaded_at: datetime) -> int:
    """Validate, clean and load order records into staging.orders."""
    valid    = []
    rejected = 0

    for row in rows:
        if not row.get("order_id") or not row.get("customer_id") or not row.get("product_id"):
            print(f"  [REJECTED] Order missing required field: {row.get('order_id')}")
            rejected += 1
            continue

        quantity   = row.get("quantity")
        unit_price = row.get("unit_price")

        if quantity is None or int(quantity) <= 0:
            print(f"  [REJECTED] Order {row.get('order_id')} invalid quantity: {quantity}")
            rejected += 1
            continue

        if unit_price is None or float(unit_price) <= 0:
            print(f"  [REJECTED] Order {row.get('order_id')} invalid unit_price: {unit_price}")
            rejected += 1
            continue

        qty   = int(quantity)
        price = round(float(unit_price), 2)

        valid.append((
            row.get("order_id"),
            row.get("customer_id"),
            row.get("product_id"),
            qty,
            price,
            round(qty * price, 2),
            row.get("status", "").strip().lower() if row.get("status") else None,
            row.get("payment_method"),
            row.get("shipping_method"),
            row.get("batch_id"),
            row.get("created_at"),
            loaded_at,
        ))

    if valid:
        psycopg2.extras.execute_values(
            cursor,
            """
            INSERT INTO staging.orders
                (order_id, customer_id, product_id, quantity, unit_price,
                 total_price, status, payment_method, shipping_method,
                 batch_id, created_at, loaded_at)
            VALUES %s
            ON CONFLICT (order_id) DO NOTHING;
            """,
            valid,
        )

    print(f"  Orders: {len(valid)} loaded, {rejected} rejected")
    return len(valid)


def main():
    """Orchestrate the full raw -> staging validate and transform pipeline."""
    print(f"Starting transform: {datetime.now(timezone.utc).isoformat()}\n")

    pg_conn   = get_pg_connection()
    pg_cursor = pg_conn.cursor()
    loaded_at = datetime.now(timezone.utc)

    try:
        create_staging_schema(pg_cursor)
        print("  Staging schema ready.\n")

        raw_customers = fetch_raw(pg_cursor, "customers")
        raw_products  = fetch_raw(pg_cursor, "products")
        raw_orders    = fetch_raw(pg_cursor, "orders")

        n_customers = transform_customers(raw_customers, pg_cursor, loaded_at)
        n_products  = transform_products(raw_products, pg_cursor, loaded_at)
        n_orders    = transform_orders(raw_orders, pg_cursor, loaded_at)

        pg_conn.commit()
        print(f"\nTransform complete — {n_customers} customers, {n_products} products, {n_orders} orders.")

    except Exception as e:
        pg_conn.rollback()
        print(f"  Transform failed: {e}")
        raise

    finally:
        pg_cursor.close()
        pg_conn.close()
        print("  Connection closed.")


if __name__ == "__main__":
    main()