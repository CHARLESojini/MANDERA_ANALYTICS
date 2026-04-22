"""
Manages bucket creation for MANDERA_ANALYTICS pipeline.

A bucket in MinIO is equivalent to a folder at the top level —
all objects (files) are stored inside buckets. Bucket names must
be unique and follow S3 naming conventions (lowercase, no spaces).
"""

import os
from minio import Minio
from dotenv import load_dotenv

load_dotenv()


def ensure_bucket_exists(client: Minio) -> str:
    """Create the raw data bucket in MinIO if it does not already exist.

    This is safe to run multiple times — if the bucket already exists
    it is left unchanged. Think of it as mkdir -p for object storage.

    The bucket name comes from .env (MINIO_BUCKET) so it can be changed
    without touching any code.

    Args:
        client: Active MinIO client instance.

    Returns:
        The bucket name so callers know where to upload files.
    """
    # Get bucket name from .env — e.g. "mandera-raw"
    bucket_name = os.getenv("MINIO_BUCKET")

    # bucket_exists() checks if the bucket already exists
    # If it doesn't exist, create it
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"  Bucket '{bucket_name}' created.")
    else:
        # Bucket already exists — nothing to do
        print(f"  Bucket '{bucket_name}' already exists.")

    return bucket_name