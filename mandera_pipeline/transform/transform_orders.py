"""
Validate and transform raw order records into staging.orders.

Reads from raw.orders in PostgreSQL, validates each record against
data quality rules, applies cleaning transformations, then loads clean
records into staging.orders.

Failed records are logged and skipped — the pipeline continues with
valid data only.

NOTE: Orders depend on staging.customers and staging.products existing
and being populated first, due to foreign key constraints.

USAGE:
    python -m mandera_pipeline.transform_orders
"""

from datetime import datetime, timezone  # datetime for timestamps; timezone to make them UTC-aware

import psycopg2.extras  # Provides execute_values for efficient bulk inserts

from mandera_pipeline.transform.db_utils import (  # Import all shared utilities from the central helper module
    create_staging_schema,  # Ensures the staging schema and tables exist before writing
    fetch_raw,              # Pulls all rows from a given raw table as a list of dicts
    get_pg_connection,      # Opens and returns an authenticated PostgreSQL connection
)


def transform_orders(rows: list, cursor, loaded_at: datetime) -> int:
    """Validate, clean and load order records into staging.orders."""
    valid    = []  # Accumulates tuples that have passed all validation checks
    rejected = 0   # Counts records that failed validation and were skipped

    for row in rows:  # Iterate over every raw order record
        if not row.get("order_id") or not row.get("customer_id") or not row.get("product_id"):  # Check that the three required ID fields are present and non-empty
            print(f"  [REJECTED] Order missing required field: {row.get('order_id')}")  # Log which order_id (or None) triggered the rejection
            rejected += 1  # Increment the rejection counter
            continue  # Skip to the next row — do not add this record to valid

        quantity   = row.get("quantity")    # Extract the raw quantity value (may be None or a string)
        unit_price = row.get("unit_price")  # Extract the raw unit price value (may be None or a string)

        if quantity is None or int(quantity) <= 0:  # Reject the record if quantity is missing or not a positive integer
            print(f"  [REJECTED] Order {row.get('order_id')} invalid quantity: {quantity}")  # Log the specific order and the bad quantity
            rejected += 1  # Increment the rejection counter
            continue  # Skip to the next row

        if unit_price is None or float(unit_price) <= 0:  # Reject the record if unit_price is missing or not a positive number
            print(f"  [REJECTED] Order {row.get('order_id')} invalid unit_price: {unit_price}")  # Log the specific order and the bad price
            rejected += 1  # Increment the rejection counter
            continue  # Skip to the next row

        qty   = int(quantity)              # Cast quantity to int now that it has been validated
        price = round(float(unit_price), 2)  # Cast unit_price to float and round to two decimal places

        valid.append((  # Build a cleaned tuple in the exact column order expected by the INSERT statement
            row.get("order_id"),    # order_id — kept as-is; already validated above
            row.get("customer_id"), # customer_id — FK to staging.customers; validated as non-empty above
            row.get("product_id"),  # product_id — FK to staging.products; validated as non-empty above
            qty,                    # quantity — cleaned positive integer
            price,                  # unit_price — cleaned positive float rounded to 2 d.p.
            round(qty * price, 2),  # total_price — derived as quantity × unit_price, rounded to 2 d.p.
            row.get("status", "").strip().lower() if row.get("status") else None,  # status — strip whitespace and lowercase (e.g. "Shipped" → "shipped"); None if absent
            row.get("payment_method"),   # payment_method — optional; carried over unchanged
            row.get("shipping_method"),  # shipping_method — optional; carried over unchanged
            row.get("batch_id"),         # batch_id — carried over unchanged to track source ingestion batch
            row.get("created_at"),       # created_at — carried over as-is (order timestamps are reliable)
            loaded_at,                   # loaded_at — the UTC timestamp captured at the start of this pipeline run
        ))

    if valid:  # Only attempt a database write if there is at least one valid record
        psycopg2.extras.execute_values(  # Bulk-insert all valid tuples in a single round-trip to the database
            cursor,  # The open database cursor to execute the statement on
            """
            INSERT INTO staging.orders
                (order_id, customer_id, product_id, quantity, unit_price,
                 total_price, status, payment_method, shipping_method,
                 batch_id, created_at, loaded_at)
            VALUES %s
            ON CONFLICT (order_id) DO NOTHING;
            """,  # Skip duplicate order_ids that are already present in staging
            valid,  # The list of cleaned tuples to insert
        )

    print(f"  Orders: {len(valid)} loaded, {rejected} rejected")  # Summary log line for this table
    return len(valid)  # Return the count of successfully loaded records to the caller


def main():
    """Run the orders-only raw -> staging validate and transform pipeline."""
    print(f"Starting order transform: {datetime.now(timezone.utc).isoformat()}\n")  # Log the UTC start time

    pg_conn   = get_pg_connection()   # Open a connection to the PostgreSQL database
    pg_cursor = pg_conn.cursor()      # Create a cursor for executing SQL statements
    loaded_at = datetime.now(timezone.utc)  # Capture the pipeline start time; used as loaded_at on every row

    try:
        create_staging_schema(pg_cursor)  # Ensure the staging schema and orders table exist
        print("  Staging schema ready.\n")  # Confirm schema initialisation to the console

        raw_orders = fetch_raw(pg_cursor, "orders")  # Pull all rows from raw.orders into memory
        n_orders   = transform_orders(raw_orders, pg_cursor, loaded_at)  # Validate, clean, and load the order records

        pg_conn.commit()  # Persist all inserts to the database in a single atomic commit
        print(f"\nTransform complete — {n_orders} orders loaded.")  # Final summary line

    except Exception as e:
        pg_conn.rollback()  # Roll back all changes so the staging table is not left in a partial state
        print(f"  Transform failed: {e}")  # Log the error message before re-raising
        raise  # Re-raise so the calling process receives a non-zero exit code

    finally:
        pg_cursor.close()  # Release the cursor regardless of success or failure
        pg_conn.close()    # Close the database connection to free the server-side resource
        print("  Connection closed.")  # Confirm clean teardown to the console


if __name__ == "__main__":
    main()  # Entry point — run the orders pipeline when the script is executed directly
