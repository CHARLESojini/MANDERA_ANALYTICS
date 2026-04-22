"""
Creates the raw and staging schemas and tables in PostgreSQL.

Two schemas are used to separate pipeline layers:
  raw     — unmodified data exactly as it arrives from MongoDB
  staging — cleaned, validated and transformed data ready for analytics

Running this file multiple times is safe — IF NOT EXISTS prevents errors.
No foreign key constraints in the raw layer — data quality is not enforced here.
FK constraints and data quality checks belong in the staging layer.
"""

import psycopg2


def create_raw_schema(cursor: psycopg2.extensions.cursor) -> None:
    """Create the raw schema and raw tables in PostgreSQL if they don't exist.

    The raw schema is the landing zone — data arrives here exactly as it
    came from MongoDB with no transformations applied. Think of it as
    a snapshot of the source system at a point in time.

    Args:
        cursor: Active PostgreSQL cursor to execute SQL statements.
    """

    # CREATE SCHEMA IF NOT EXISTS — creates a namespace called 'raw'
    # A schema is like a folder inside the database that groups related tables
    # IF NOT EXISTS makes this safe to run on every pipeline execution
    cursor.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    # raw.customers
    # One row per customer document from MongoDB
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw.customers (
            customer_id     VARCHAR PRIMARY KEY,  -- unique string ID from fake_customers.py
            name            VARCHAR,              -- full name — free text, VARCHAR is correct
            email           VARCHAR,              -- email — free text, VARCHAR is correct
            phone           VARCHAR,              -- phone has symbols (+, -, ()) — VARCHAR is correct
            city            VARCHAR,              -- city name — free text
            batch_id        INTEGER,              -- INTEGER: auto-incrementing counter (1, 2, 3...)
            created_at      TIMESTAMP             -- UTC timestamp of when record was generated
        );
    """)

    # raw.products
    # One row per product document from MongoDB
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw.products (
            product_id      VARCHAR PRIMARY KEY,  -- unique string ID from fake_products.py
            product_name    VARCHAR,              -- product name — free text
            category        VARCHAR,              -- category name — free text
            price           NUMERIC(10, 2),       -- price: NUMERIC stores exact decimals
                                                  -- (10 total digits, 2 after decimal point)
                                                  -- FLOAT would introduce rounding errors
            batch_id        INTEGER,              -- INTEGER: auto-incrementing counter
            created_at      TIMESTAMP             -- UTC timestamp of generation
        );
    """)

    # raw.orders
    # One row per order document from MongoDB
    # customer_id and product_id reference other tables but no FK constraint here
    # Raw layer accepts data as-is — referential integrity is checked in staging
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw.orders (
            order_id        VARCHAR PRIMARY KEY,  -- unique string order ID
            customer_id     VARCHAR,              -- references a customer (no FK in raw)
            product_id      VARCHAR,              -- references a product (no FK in raw)
            quantity        SMALLINT,             -- SMALLINT: max value is 10, range is 0-32767
                                                  -- more efficient than INTEGER for small numbers
            unit_price      NUMERIC(10, 2),       -- exact decimal — avoids float rounding errors
            total_price     NUMERIC(10, 2),       -- quantity x unit_price — exact decimal
            status          VARCHAR,              -- e.g. pending, shipped, delivered
            payment_method  VARCHAR,              -- e.g. credit_card, paypal
            shipping_method VARCHAR,              -- e.g. standard, express
            batch_id        INTEGER,              -- INTEGER: auto-incrementing counter
            created_at      TIMESTAMP             -- UTC timestamp of generation
        );
    """)


def create_staging_schema(cursor: psycopg2.extensions.cursor) -> None:
    """Create the staging schema and staging tables in PostgreSQL if they don't exist.

    The staging schema holds cleaned and validated data after transformation.
    Unlike raw, staging enforces:
      - Foreign key constraints (orders must reference valid customers and products)
      - NOT NULL constraints on critical fields
      - Correct data types matching the actual nature of each field
      - loaded_at timestamp to track when records entered staging

    This is the layer that analytics tools and dashboards query from.

    Args:
        cursor: Active PostgreSQL cursor to execute SQL statements.
    """

    # staging schema — a separate namespace from raw, keeping layers clean
    cursor.execute("CREATE SCHEMA IF NOT EXISTS staging;")

    # staging.customers
    # Cleaned customer records — critical fields enforce NOT NULL
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.customers (
            customer_id     VARCHAR PRIMARY KEY,
            name            VARCHAR NOT NULL,     -- NOT NULL: name is required in staging
            email           VARCHAR NOT NULL,     -- NOT NULL: email is required for deduplication
            phone           VARCHAR,              -- optional — can be null
            city            VARCHAR,              -- optional — can be null
            batch_id        INTEGER,              -- INTEGER: matches the counter type
            created_at      TIMESTAMP,            -- when the record was originally generated
            loaded_at       TIMESTAMP             -- when this record was loaded into staging
        );
    """)

    # staging.products 
    # Cleaned product records — name, category and price are required
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.products (
            product_id      VARCHAR PRIMARY KEY,
            product_name    VARCHAR NOT NULL,     -- NOT NULL: every product must have a name
            category        VARCHAR NOT NULL,     -- NOT NULL: every product must have a category
            price           NUMERIC(10, 2),       -- exact decimal — avoids float rounding errors
            batch_id        INTEGER,              -- INTEGER: matches the counter type
            created_at      TIMESTAMP,            -- when the record was originally generated
            loaded_at       TIMESTAMP             -- when this record was loaded into staging
        );
    """)

    # staging.orders 
    # Cleaned order records with FK constraints enforcing referential integrity
    # REFERENCES ensures every order links to a real customer and product
    # Orders must be inserted AFTER customers and products in staging
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging.orders (
            order_id        VARCHAR PRIMARY KEY,
            customer_id     VARCHAR NOT NULL REFERENCES staging.customers(customer_id),
            product_id      VARCHAR NOT NULL REFERENCES staging.products(product_id),
            quantity        SMALLINT NOT NULL,    -- SMALLINT: max is 10, never null
            unit_price      NUMERIC(10, 2) NOT NULL, -- required — no free orders
            total_price     NUMERIC(10, 2) NOT NULL, -- required — derived field
            status          VARCHAR NOT NULL,     -- required — must know order state
            payment_method  VARCHAR,              -- optional
            shipping_method VARCHAR,              -- optional
            batch_id        INTEGER,              -- INTEGER: matches the counter type
            created_at      TIMESTAMP,            -- when the record was originally generated
            loaded_at       TIMESTAMP             -- when this record was loaded into staging
        );
    """)