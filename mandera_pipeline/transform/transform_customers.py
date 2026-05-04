"""
Validate and transform raw customer records into staging.customers.

Reads from raw.customers in PostgreSQL, validates each record against
data quality rules, applies cleaning transformations, then loads clean
records into staging.customers.

Failed records are logged and skipped — the pipeline continues with
valid data only.

USAGE:
    python -m mandera_pipeline.transform_customers
"""

from datetime import datetime, timezone  # datetime for timestamps; timezone to make them UTC-aware

import psycopg2.extras  # Provides execute_values for efficient bulk inserts

from mandera_pipeline.transform.db_utils import (  # Import all shared utilities from the central helper module
    UNKNOWN_TIMESTAMP,       # Fallback timestamp for records with a missing created_at
    create_staging_schema,   # Ensures the staging schema and tables exist before writing
    fetch_raw,               # Pulls all rows from a given raw table as a list of dicts
    get_pg_connection,       # Opens and returns an authenticated PostgreSQL connection
)


def transform_customers(rows: list, cursor, loaded_at: datetime) -> int:
    """Validate, clean and load customer records into staging.customers."""
    valid    = []  # Accumulates tuples that have passed all validation checks
    rejected = 0   # Counts records that failed validation and were skipped

    for row in rows:  # Iterate over every raw customer record
        if not row.get("customer_id") or not row.get("name") or not row.get("email"):  # Check that the three required fields are present and non-empty
            print(f"  [REJECTED] Customer missing required field: {row.get('customer_id')}")  # Log which customer_id (or None) triggered the rejection
            rejected += 1  # Increment the rejection counter
            continue  # Skip to the next row — do not add this record to valid

        valid.append((  # Build a cleaned tuple in the exact column order expected by the INSERT statement
            row.get("customer_id"),  # customer_id — kept as-is; already validated above
            row.get("name", "").strip().title(),  # name — strip surrounding whitespace then title-case (e.g. "john doe" → "John Doe")
            row.get("email", "").strip().lower(),  # email — strip whitespace and lowercase for consistency
            row.get("phone", "").strip().replace("-", "").replace(".", "").replace(" ", "") if row.get("phone") else None,  # phone — remove hyphens, dots, and spaces; store None if absent
            row.get("city", "").strip() if row.get("city") else None,  # city — strip whitespace; store None if the field is missing
            row.get("batch_id"),  # batch_id — carried over unchanged to track source ingestion batch
            row.get("created_at") or UNKNOWN_TIMESTAMP,  # created_at — use the sentinel epoch date when the raw value is NULL
            loaded_at,  # loaded_at — the UTC timestamp captured at the start of this pipeline run
        ))

    if valid:  # Only attempt a database write if there is at least one valid record
        psycopg2.extras.execute_values(  # Bulk-insert all valid tuples in a single round-trip to the database
            cursor,  # The open database cursor to execute the statement on
            """
            INSERT INTO staging.customers
                (customer_id, name, email, phone, city, batch_id, created_at, loaded_at)
            VALUES %s
            ON CONFLICT (customer_id) DO NOTHING;
            """,  # Skip duplicate customer_ids that are already present in staging
            valid,  # The list of cleaned tuples to insert
        )

    print(f"  Customers: {len(valid)} loaded, {rejected} rejected")  # Summary log line for this table
    return len(valid)  # Return the count of successfully loaded records to the caller


def main():
    """Run the customers-only raw -> staging validate and transform pipeline."""
    print(f"Starting customer transform: {datetime.now(timezone.utc).isoformat()}\n")  # Log the UTC start time

    pg_conn   = get_pg_connection()   # Open a connection to the PostgreSQL database
    pg_cursor = pg_conn.cursor()      # Create a cursor for executing SQL statements
    loaded_at = datetime.now(timezone.utc)  # Capture the pipeline start time; used as loaded_at on every row

    try:
        create_staging_schema(pg_cursor)  # Ensure the staging schema and customers table exist
        print("  Staging schema ready.\n")  # Confirm schema initialisation to the console

        raw_customers = fetch_raw(pg_cursor, "customers")  # Pull all rows from raw.customers into memory
        n_customers   = transform_customers(raw_customers, pg_cursor, loaded_at)  # Validate, clean, and load the customer records

        pg_conn.commit()  # Persist all inserts to the database in a single atomic commit
        print(f"\nTransform complete — {n_customers} customers loaded.")  # Final summary line

    except Exception as e:
        pg_conn.rollback()  # Roll back all changes so the staging table is not left in a partial state
        print(f"  Transform failed: {e}")  # Log the error message before re-raising
        raise  # Re-raise so the calling process receives a non-zero exit code

    finally:
        pg_cursor.close()  # Release the cursor regardless of success or failure
        pg_conn.close()    # Close the database connection to free the server-side resource
        print("  Connection closed.")  # Confirm clean teardown to the console


if __name__ == "__main__":
    main()  # Entry point — run the customer pipeline when the script is executed directly
