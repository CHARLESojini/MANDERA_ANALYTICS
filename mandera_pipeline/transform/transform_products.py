"""
Validate and transform raw product records into staging.products.

Reads from raw.products in PostgreSQL, validates each record against
data quality rules, applies cleaning transformations, then loads clean
records into staging.products.

Failed records are logged and skipped — the pipeline continues with
valid data only.

USAGE:
    python -m mandera_pipeline.transform_products
"""

from datetime import datetime, timezone  # datetime for timestamps; timezone to make them UTC-aware

import psycopg2.extras  # Provides execute_values for efficient bulk inserts

from mandera_pipeline.transform.db_utils import (  # Import all shared utilities from the central helper module
    create_staging_schema,  # Ensures the staging schema and tables exist before writing
    fetch_raw,              # Pulls all rows from a given raw table as a list of dicts
    get_pg_connection,      # Opens and returns an authenticated PostgreSQL connection
)


def transform_products(rows: list, cursor, loaded_at: datetime) -> int:
    """Validate, clean and load product records into staging.products."""
    valid    = []  # Accumulates tuples that have passed all validation checks
    rejected = 0   # Counts records that failed validation and were skipped

    for row in rows:  # Iterate over every raw product record
        if not row.get("product_id") or not row.get("product_name") or not row.get("category"):  # Check that the three required fields are present and non-empty
            print(f"  [REJECTED] Product missing required field: {row.get('product_id')}")  # Log which product_id (or None) triggered the rejection
            rejected += 1  # Increment the rejection counter
            continue  # Skip to the next row — do not add this record to valid

        price = row.get("price")  # Extract the raw price value (may be None or a string)
        if price is None or float(price) <= 0:  # Reject the record if price is missing or not a positive number
            print(f"  [REJECTED] Product {row.get('product_id')} invalid price: {price}")  # Log the specific product and the bad price value
            rejected += 1  # Increment the rejection counter
            continue  # Skip to the next row

        valid.append((  # Build a cleaned tuple in the exact column order expected by the INSERT statement
            row.get("product_id"),  # product_id — kept as-is; already validated above
            row.get("product_name", "").strip().title(),  # product_name — strip whitespace then title-case (e.g. "blue pen" → "Blue Pen")
            row.get("category", "").strip().title(),  # category — strip whitespace then title-case for consistency
            round(float(price), 2),  # price — cast to float and round to two decimal places
            row.get("batch_id") or row.get("batch-id"),  # batch_id — prefer "batch_id"; fall back to hyphenated key from older raw records
            row.get("created_at"),  # created_at — carried over as-is; no sentinel needed for products
            loaded_at,  # loaded_at — the UTC timestamp captured at the start of this pipeline run
        ))

    if valid:  # Only attempt a database write if there is at least one valid record
        psycopg2.extras.execute_values(  # Bulk-insert all valid tuples in a single round-trip to the database
            cursor,  # The open database cursor to execute the statement on
            """
            INSERT INTO staging.products
                (product_id, product_name, category, price, batch_id, created_at, loaded_at)
            VALUES %s
            ON CONFLICT (product_id) DO NOTHING;
            """,  # Skip duplicate product_ids that are already present in staging
            valid,  # The list of cleaned tuples to insert
        )

    print(f"  Products: {len(valid)} loaded, {rejected} rejected")  # Summary log line for this table
    return len(valid)  # Return the count of successfully loaded records to the caller


def main():
    """Run the products-only raw -> staging validate and transform pipeline."""
    print(f"Starting product transform: {datetime.now(timezone.utc).isoformat()}\n")  # Log the UTC start time

    pg_conn   = get_pg_connection()   # Open a connection to the PostgreSQL database
    pg_cursor = pg_conn.cursor()      # Create a cursor for executing SQL statements
    loaded_at = datetime.now(timezone.utc)  # Capture the pipeline start time; used as loaded_at on every row

    try:
        create_staging_schema(pg_cursor)  # Ensure the staging schema and products table exist
        print("  Staging schema ready.\n")  # Confirm schema initialisation to the console

        raw_products = fetch_raw(pg_cursor, "products")  # Pull all rows from raw.products into memory
        n_products   = transform_products(raw_products, pg_cursor, loaded_at)  # Validate, clean, and load the product records

        pg_conn.commit()  # Persist all inserts to the database in a single atomic commit
        print(f"\nTransform complete — {n_products} products loaded.")  # Final summary line

    except Exception as e:
        pg_conn.rollback()  # Roll back all changes so the staging table is not left in a partial state
        print(f"  Transform failed: {e}")  # Log the error message before re-raising
        raise  # Re-raise so the calling process receives a non-zero exit code

    finally:
        pg_cursor.close()  # Release the cursor regardless of success or failure
        pg_conn.close()    # Close the database connection to free the server-side resource
        print("  Connection closed.")  # Confirm clean teardown to the console


if __name__ == "__main__":
    main()  # Entry point — run the product pipeline when the script is executed directly
