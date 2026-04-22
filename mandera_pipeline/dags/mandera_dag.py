"""
MANDERA_ANALYTICS Pipeline DAG.

Orchestrates the full data pipeline on a schedule:
  1. extract_to_minio      — archive raw MongoDB data to MinIO (JSON)
  2. extract_to_postgres   — load raw MongoDB data into PostgreSQL raw schema
  3. validate_and_transform — validate and transform raw to staging
  4. truncate_raw          — clean up raw tables after staging is loaded

Task dependency flow:
  extract_to_minio    ─┐
                       ├─→ validate_and_transform → truncate_raw
  extract_to_postgres ─┘

Schedule:
  8:30 AM WAT  = 07:30 UTC  (30 min after GitHub Actions generates data at 8:00 AM WAT)
  4:30 PM WAT  = 15:30 UTC  (30 min after GitHub Actions generates data at 4:00 PM WAT)
"""

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Add the project root to Python path so DAG tasks can import pipeline modules
# The project is mounted at /opt/airflow/project in the Airflow containers
sys.path.insert(0, "/opt/airflow/project")


#  Default arguments applied to every task in the DAG 
default_args = {
    # Owner of the DAG — shown in the Airflow UI
    "owner": "mandera",

    # Do not run missed scheduled runs when Airflow first starts
    "depends_on_past": False,

    # Start date — Airflow uses this to calculate schedule intervals
    "start_date": datetime(2026, 4, 18),

    # Send email on failure — set to False for now
    "email_on_failure": False,
    "email_on_retry": False,

    # Retry once if a task fails, wait 5 minutes before retrying
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


# Task functions 
# Each function imports and calls the relevant pipeline module
# Imports are inside the functions so they only load when the task runs


def run_extract_to_minio():
    """Extract raw data from MongoDB and archive to MinIO as JSON files."""
    from mandera_pipeline.extract_to_minio import main
    main()


def run_extract_to_postgres():
    """Extract raw data from MongoDB and load into PostgreSQL raw schema."""
    from mandera_pipeline.extract_to_postgres import main
    main()


def run_validate_and_transform():
    """Validate raw data and load clean records into PostgreSQL staging schema."""
    from mandera_pipeline.transform_to_staging import main
    main()


def run_truncate_raw():
    """Truncate raw schema tables after staging has been successfully loaded.

    This keeps the raw tables clean for the next pipeline run.
    Raw data is preserved in MinIO — truncating raw.* is safe.
    """
    import psycopg2

    conn = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    cursor = conn.cursor()

    try:
        # TRUNCATE removes all rows but keeps the table structure
        # CASCADE handles any foreign key dependencies
        cursor.execute("TRUNCATE TABLE raw.customers, raw.products, raw.orders;")
        conn.commit()
        print("Raw tables truncated successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Truncate failed: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


#  DAG definition 
with DAG(
    # Unique identifier for this DAG — shown in the Airflow UI
    dag_id="mandera_analytics_pipeline",

    default_args=default_args,

    # Human readable description shown in the Airflow UI
    description="MANDERA_ANALYTICS full pipeline: extract → validate → transform → truncate",

    # Run at 8:30 AM and 4:30 PM WAT (UTC+1)
    # 07:30 UTC and 15:30 UTC
    schedule_interval="30 7,15 * * *",

    # Do not backfill missed runs
    catchup=False,

    # Tags make it easy to filter DAGs in the UI
    tags=["mandera", "pipeline", "etl"],

    # Only one run at a time — prevents overlapping pipeline runs
    max_active_runs=1,

) as dag:

    #  Task 1a: Extract to MinIO 
    extract_minio = PythonOperator(
        task_id="extract_to_minio",
        python_callable=run_extract_to_minio,
    )

    #  Task 1b: Extract to PostgreSQL Raw 
    # Runs in parallel with extract_minio
    extract_postgres = PythonOperator(
        task_id="extract_to_postgres",
        python_callable=run_extract_to_postgres,
    )

    # Task 2: Validate and Transform 
    # Runs after BOTH extract tasks complete successfully
    validate_transform = PythonOperator(
        task_id="validate_and_transform",
        python_callable=run_validate_and_transform,
    )

    #  Task 3: Truncate Raw 
    # Runs after staging is loaded — cleans up raw tables
    truncate_raw = PythonOperator(
        task_id="truncate_raw",
        python_callable=run_truncate_raw,
    )

    # Task dependencies 
    # extract_minio and extract_postgres run in parallel (no dependency between them)
    # validate_transform waits for BOTH to complete
    # truncate_raw runs last after validate_transform succeeds
    [extract_minio, extract_postgres] >> validate_transform >> truncate_raw