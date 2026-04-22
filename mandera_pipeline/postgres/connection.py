"""
Manages database connection instances for the MANDERA_ANALYTICS pipeline.

All connection credentials are loaded from .env — never hardcoded here.
Both MongoDB and PostgreSQL connections are created here so every other
module imports from one place. If credentials change, only this file needs updating.
"""

import os

# psycopg2 is the most widely used PostgreSQL driver for Python
# It lets Python talk directly to a PostgreSQL database
import psycopg2

# MongoClient is the entry point for all MongoDB operations
# It manages the connection pool to MongoDB Atlas
from pymongo import MongoClient

# load_dotenv() reads the .env file and injects all key=value pairs
# into os.environ so os.getenv() can find them
from dotenv import load_dotenv

# Must be called before any os.getenv() calls below
load_dotenv()


def get_pg_connection() -> psycopg2.extensions.connection:
    """Create and return a PostgreSQL connection using credentials from .env.

    psycopg2.connect() opens a TCP connection to the PostgreSQL server.
    The connection stays open until .close() is called — always close it
    in a finally block to avoid connection leaks.

    Returns:
        An active psycopg2 connection object.
    """
    return psycopg2.connect(
        # host: the hostname of the PostgreSQL server
        # From Mac (outside Docker): localhost
        # From inside Docker (e.g. pgAdmin): mandera_postgres
        host=os.getenv("POSTGRES_HOST"),

        # port: 5433 on the host machine (mapped from container port 5432)
        port=os.getenv("POSTGRES_PORT"),

        # dbname: the specific database to connect to inside PostgreSQL
        dbname=os.getenv("POSTGRES_DB"),

        # user: the PostgreSQL role/user
        user=os.getenv("POSTGRES_USER"),

        # password: the PostgreSQL user password
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def get_mongo_client() -> MongoClient:
    """Create and return a MongoDB Atlas client using credentials from .env.

    MongoClient manages a connection pool — it reuses connections efficiently
    rather than opening a new one for every query.
    Always call .close() when done to release the pool.

    Returns:
        An active pymongo MongoClient instance.
    """
    # MONGO_URL contains the full Atlas connection string including
    # username, password, cluster host, and options
    # Format: mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/
    return MongoClient(os.getenv("MONGO_URL"))