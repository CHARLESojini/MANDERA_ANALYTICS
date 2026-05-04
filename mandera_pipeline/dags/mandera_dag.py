"""
MANDERA_ANALYTICS Pipeline DAG.

Orchestrates the full data pipeline on a schedule:
  1. extract_to_minio       — archive raw MongoDB data to MinIO (JSON)
  2. extract_to_postgres    — load raw MongoDB data into PostgreSQL raw schema
  3. transform_customers    — validate and load clean customer records into staging
  4. transform_products     — validate and load clean product records into staging
  5. transform_orders       — validate and load clean order records into staging
  6. truncate_raw           — clean up raw tables after staging is loaded

Task dependency flow:
  extract_to_minio    ─┐
                       ├─→ transform_customers ─┐
  extract_to_postgres ─┤                        ├─→ transform_orders → truncate_raw
                       └─→ transform_products ──┘

  Customers and products run in parallel after both extracts complete.
  Orders waits for both because it has FK constraints on customers and products.

Schedule:
  8:30 AM WAT  = 07:30 UTC  (30 min after GitHub Actions generates data at 8:00 AM WAT)
  4:30 PM WAT  = 15:30 UTC  (30 min after GitHub Actions generates data at 4:00 PM WAT)
"""

import os  # Used to read environment variables for the truncate task's DB connection
import sys  # Used to manipulate the Python module search path
from datetime import datetime, timedelta  # datetime for start_date; timedelta for retry_delay

from airflow import DAG  # Core DAG class that defines the pipeline
from airflow.operators.python import PythonOperator  # Operator that runs a Python callable as a task

# Add the project root to Python path so DAG tasks can import pipeline modules.
# The project is mounted at /opt/airflow/project inside the Airflow containers.
sys.path.insert(0, "/opt/airflow/project")


# Default arguments
# These are applied to every task in the DAG unless overridden at the task level.
default_args = {
    # Owner of the DAG — displayed in the Airflow UI for filtering and ownership
    "owner": "mandera",

    # Do not run missed scheduled intervals when Airflow first starts up
    "depends_on_past": False,

    # Earliest date Airflow uses when calculating which runs to schedule
    "start_date": datetime(2026, 4, 18),

    # Disable email alerts — no SMTP is configured in this environment
    "email_on_failure": False,
    "email_on_retry": False,

    # Retry a failed task up to 2 times before marking it as failed
    "retries": 2,

    # Wait 5 minutes between each retry attempt
    "retry_delay": timedelta(minutes=5),
}


# Task callables 
# Each function wraps one pipeline module.
# Imports are placed inside each function so they only load when the task runs,
# which avoids import errors during DAG parsing if dependencies are unavailable.


def run_extract_to_minio():
    """Extract raw data from MongoDB and archive it to MinIO as JSON files."""
    from mandera_pipeline.extract_to_minio import main  # Import the MinIO extraction entry point
    main()  # Run the extraction — writes JSON objects to the configured MinIO bucket


def run_extract_to_postgres():
    """Extract raw data from MongoDB and load it into the PostgreSQL raw schema."""
    from mandera_pipeline.extract_to_postgres import main  # Import the PostgreSQL extraction entry point
    main()  # Run the extraction — inserts raw rows into raw.customers, raw.products, raw.orders


def run_transform_customers():
    """Validate raw customer records and load clean ones into staging.customers."""
    from mandera_pipeline.transform.transform_customers import main  # Import from the transform sub-package
    main()  # Runs validation, cleaning, and bulk insert for the customers entity


def run_transform_products():
    """Validate raw product records and load clean ones into staging.products."""
    from mandera_pipeline.transform.transform_products import main  # Import from the transform sub-package
    main()  # Runs validation, cleaning, and bulk insert for the products entity


def run_transform_orders():
    """Validate raw order records and load clean ones into staging.orders.

    Must run after transform_customers and transform_products because staging.orders
    has foreign key constraints referencing both staging.customers and staging.products.
    """
    from mandera_pipeline.transform.transform_orders import main  # Import from the transform sub-package
    main()  # Runs validation, cleaning, and bulk insert for the orders entity


def run_truncate_raw():
    """Truncate raw schema tables after staging has been successfully loaded.

    Raw data is safely archived in MinIO, so truncating the raw PostgreSQL tables
    after each run keeps them clean and ready for the next pipeline cycle.
    """
    import psycopg2  # Import here to avoid loading the driver at DAG parse time

    conn = psycopg2.connect(  # Open a direct connection using environment variables
        host=os.environ["POSTGRES_HOST"],      # Hostname of the PostgreSQL server
        port=os.environ["POSTGRES_PORT"],      # Port number (typically 5432)
        dbname=os.environ["POSTGRES_DB"],      # Target database name
        user=os.environ["POSTGRES_USER"],      # Login username
        password=os.environ["POSTGRES_PASSWORD"],  # Login password
    )
    cursor = conn.cursor()  # Create a cursor for executing the TRUNCATE statement

    try:
        # Remove all rows from the three raw tables in a single atomic statement.
        # CASCADE handles any FK dependencies that might otherwise block the truncation.
        cursor.execute("TRUNCATE TABLE raw.customers, raw.products, raw.orders CASCADE;")
        conn.commit()  # Commit the truncation so it is permanent
        print("Raw tables truncated successfully.")  # Log success to the Airflow task log

    except Exception as e:
        conn.rollback()  # Roll back if anything goes wrong to leave raw tables intact
        print(f"Truncate failed: {e}")  # Log the error before re-raising
        raise  # Re-raise so Airflow marks the task as failed and triggers retries

    finally:
        cursor.close()  # Always release the cursor
        conn.close()    # Always close the connection regardless of outcome


# DAG definition 
with DAG(
    # Unique identifier for this DAG — shown in the Airflow UI and used in API calls
    dag_id="mandera_analytics_pipeline",

    # Apply the shared default arguments defined above
    default_args=default_args,

    # Short description displayed in the Airflow UI DAG list
    description="MANDERA_ANALYTICS full pipeline: extract → transform → truncate",

    # Run at 07:30 UTC (8:30 AM WAT) and 15:30 UTC (4:30 PM WAT) every day
    schedule_interval="30 7,15 * * *",

    # Do not backfill missed runs — only execute going forward from start_date
    catchup=False,

    # Tags make this DAG easy to find when filtering in the Airflow UI
    tags=["mandera", "pipeline", "etl"],

    # Prevent a new run from starting while a previous run is still in progress
    max_active_runs=1,

) as dag:

    # Task 1a: Extract to MinIO 
    # Archives a copy of raw MongoDB data to MinIO for durability and replay.
    # Runs in parallel with extract_to_postgres.
    extract_minio = PythonOperator(
        task_id="extract_to_minio",          # Unique task ID shown in the Airflow UI
        python_callable=run_extract_to_minio, # The function to call when this task runs
    )

    # Task 1b: Extract to PostgreSQL Raw
    # Loads raw MongoDB data into the raw.* tables in PostgreSQL.
    # Runs in parallel with extract_to_minio — both are independent.
    extract_postgres = PythonOperator(
        task_id="extract_to_postgres",
        python_callable=run_extract_to_postgres,
    )

    # Task 2a: Transform Customers
    # Validates and loads clean records into staging.customers.
    # Starts only after BOTH extract tasks have completed successfully.
    transform_customers = PythonOperator(
        task_id="transform_customers",
        python_callable=run_transform_customers,
    )

    # Task 2b: Transform Products
    # Validates and loads clean records into staging.products.
    # Runs in parallel with transform_customers — no dependency between them.
    transform_products = PythonOperator(
        task_id="transform_products",
        python_callable=run_transform_products,
    )

    # Task 3: Transform Orders
    # Validates and loads clean records into staging.orders.
    # Must wait for BOTH transform_customers and transform_products because
    # staging.orders has FK constraints referencing both staging tables.
    transform_orders = PythonOperator(
        task_id="transform_orders",
        python_callable=run_transform_orders,
    )

    # Task 4: Truncate Raw
    # Clears raw.* tables once staging is fully loaded.
    # Runs last — only after all three transform tasks have succeeded.
    truncate_raw = PythonOperator(
        task_id="truncate_raw",
        python_callable=run_truncate_raw,
    )

    # Dependency chain
    #
    # Both extract tasks run in parallel first.
    # Once both finish, customers and products transform in parallel.
    # Orders waits for both customers and products (FK constraint).
    # Truncate runs last after orders succeeds.
    #
    #   extract_minio    ─┐
    #                     ├─→ transform_customers ─┐
    #   extract_postgres ─┤                        ├─→ transform_orders → truncate_raw
    #                     └─→ transform_products ──┘
    #
    [extract_minio, extract_postgres] >> transform_customers  # Both extracts must finish before either transform starts
    [extract_minio, extract_postgres] >> transform_products  # Orders waits for customers and products
    [transform_customers, transform_products] >> transform_orders
    transform_orders >> truncate_raw  # Raw tables are only cleared after all staging loads succeed