"""
Orchestrates extraction from MongoDB Atlas into MinIO object storage.

Pulls customers, products and orders from MongoDB and uploads them
as timestamped JSON files to MinIO. Each collection gets its own
folder and each run gets its own file — nothing is ever overwritten.

This creates a permanent raw archive that can be used to:
  - Replay the pipeline if PostgreSQL data is lost or corrupted
  - Audit exactly what data existed at any point in time
  - Feed future data lake or analytics workloads

USAGE:
    python -m mandera_pipeline.extract_to_minio
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Each import below is a focused module with a single responsibility
from mandera_pipeline.minio.connection import get_minio_client
from mandera_pipeline.minio.bucket import ensure_bucket_exists
from mandera_pipeline.minio.upload_customers import upload_customers
from mandera_pipeline.minio.upload_products import upload_products
from mandera_pipeline.minio.upload_orders import upload_orders

# get_mongo_client is reused from the postgres subpackage
# No need to duplicate connection logic — one source of truth
from mandera_pipeline.postgres.connection import get_mongo_client

load_dotenv()


def main() -> None:
    """Orchestrate the full MongoDB -> MinIO raw archive extraction."""

    print(f"Starting MinIO extraction: {datetime.now(timezone.utc).isoformat()}\n")

    # Open connections 

    # Connect to MongoDB Atlas
    mongo_client = get_mongo_client()
    mongo_db     = mongo_client[os.getenv("MONGO_DB_NAME")]

    # Connect to MinIO running in Docker
    minio_client = get_minio_client()

    try:
        # Step 1: Ensure the bucket exists 
        # Creates the bucket if it doesn't exist yet
        # Returns the bucket name so upload functions know where to write
        bucket_name = ensure_bucket_exists(minio_client)

        # Step 2: Upload each collection as a JSON file 
        # Each function uploads one collection to its own folder in the bucket
        # Files are timestamped so every run creates a new file — no overwrites

        n_customers = upload_customers(mongo_db, minio_client, bucket_name)
        n_products  = upload_products(mongo_db, minio_client, bucket_name)
        n_orders    = upload_orders(mongo_db, minio_client, bucket_name)

        print(f"\nMinIO extraction complete.")
        print(f"  Customers : {n_customers}")
        print(f"  Products  : {n_products}")
        print(f"  Orders    : {n_orders}")

    except Exception as e:
        # Log the error clearly — MinIO errors often relate to connectivity
        # or missing credentials so the message helps with debugging
        print(f"  MinIO extraction failed: {e}")
        raise

    finally:
        # Always close the MongoDB connection
        # MinIO client has no explicit close — it's stateless HTTP calls
        mongo_client.close()
        print("  MongoDB connection closed.")


if __name__ == "__main__":
    main()