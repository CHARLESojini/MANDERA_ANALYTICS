"""
Shared database utilities for the MANDERA_ANALYTICS staging pipeline.

Provides connection management, schema initialisation, and raw data
fetching used by each individual transformation module.
"""

import os  # Used to read environment variables (DB credentials)
from datetime import datetime, timezone  # datetime for timestamps; timezone for UTC-aware datetimes

import psycopg2  # PostgreSQL adapter — opens connections and runs queries
import psycopg2.extras  # Extra helpers, e.g. execute_values for bulk inserts
from dotenv import load_dotenv  # Reads a .env file and injects its values into os.environ

load_dotenv()  # Load .env so all os.getenv() calls below find the credentials


# Sentinel value used when created_at is NULL in the raw data (legacy batches had a typo)
UNKNOWN_TIMESTAMP = datetime(1970, 1, 1, tzinfo=timezone.utc)  # Unix epoch in UTC — signals "unknown date"


def get_pg_connection():
    """Create and return a PostgreSQL connection using env credentials."""
    return psycopg2.connect(  # Open a new connection to the database and return it
        host=os.getenv("POSTGRES_HOST"),      # Database server hostname from .env
        port=os.getenv("POSTGRES_PORT"),      # Port number (default 5432 for Postgres)
        dbname=os.getenv("POSTGRES_DB"),      # Name of the target database
        user=os.getenv("POSTGRES_USER"),      # Login username
        password=os.getenv("POSTGRES_PASSWORD"),  # Login password
    )


def create_staging_schema(cursor):
    """Create staging schema and tables if they don't already exist."""
    cursor.execute("CREATE SCHEMA IF NOT EXISTS staging;")  # Create the staging schema only if it is missing

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.customers (
            customer_id     VARCHAR PRIMARY KEY,          -- Unique identifier for each customer
            name            VARCHAR NOT NULL,             -- Customer full name; required
            email           VARCHAR NOT NULL,             -- Customer email address; required
            phone           VARCHAR,                      -- Optional cleaned phone number
            city            VARCHAR,                      -- Optional city of residence
            batch_id        INTEGER,                      -- Source ingestion batch number
            created_at      TIMESTAMP WITH TIME ZONE,    -- When the customer record was originally created
            loaded_at       TIMESTAMP WITH TIME ZONE     -- When this pipeline run inserted the row
        );
    """)  # Create the customers staging table if it does not already exist

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.products (
            product_id      VARCHAR PRIMARY KEY,          -- Unique identifier for each product
            product_name    VARCHAR NOT NULL,             -- Display name of the product; required
            category        VARCHAR NOT NULL,             -- Product category; required
            price           NUMERIC(10, 2),               -- Sale price with two decimal places
            batch_id        INTEGER,                      -- Source ingestion batch number
            created_at      TIMESTAMP WITH TIME ZONE,    -- When the product record was originally created
            loaded_at       TIMESTAMP WITH TIME ZONE     -- When this pipeline run inserted the row
        );
    """)  # Create the products staging table if it does not already exist

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.orders (
            order_id        VARCHAR PRIMARY KEY,          -- Unique identifier for each order
            customer_id     VARCHAR NOT NULL,             -- FK reference to the customer who placed the order
            product_id      VARCHAR NOT NULL,             -- FK reference to the product that was ordered
            quantity        SMALLINT NOT NULL,            -- Number of units purchased; must be positive
            unit_price      NUMERIC(10, 2) NOT NULL,      -- Price per single unit at time of order
            total_price     NUMERIC(10, 2) NOT NULL,      -- Computed total: quantity × unit_price
            status          VARCHAR NOT NULL,             -- Order lifecycle status (e.g. 'shipped')
            payment_method  VARCHAR,                      -- Optional payment method (e.g. 'card')
            shipping_method VARCHAR,                      -- Optional shipping method (e.g. 'express')
            batch_id        INTEGER,                      -- Source ingestion batch number
            created_at      TIMESTAMP WITH TIME ZONE,    -- When the order was originally placed
            loaded_at       TIMESTAMP WITH TIME ZONE     -- When this pipeline run inserted the row
        );
    """)  # Create the orders staging table if it does not already exist


def fetch_raw(cursor, table: str) -> list:
    """Fetch all records from a raw schema table as a list of dicts."""
    cursor.execute(f"SELECT * FROM raw.{table};")  # Run a full-table scan on the requested raw table
    columns = [desc[0] for desc in cursor.description]  # Extract column names from the cursor metadata
    return [dict(zip(columns, row)) for row in cursor.fetchall()]  # Pair each row's values with its column names and return as a list of dicts
