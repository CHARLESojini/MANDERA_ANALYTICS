"""
Manages the MinIO client connection for MANDERA_ANALYTICS pipeline.

All credentials are loaded from .env — never hardcoded here.
The MinIO client is the entry point for all object storage operations
including creating buckets, uploading and downloading files.
"""

import os
from minio import Minio
from dotenv import load_dotenv

# Must be called before any os.getenv() calls below
load_dotenv()


def get_minio_client() -> Minio:
    """Create and return a MinIO client using credentials from .env.

    The Minio client connects to the MinIO server running in Docker.
    secure=False means we use HTTP instead of HTTPS — appropriate for
    local development. In production this would be True with a valid cert.

    Returns:
        An active Minio client instance.
    """
    return Minio(
        # endpoint: the MinIO server address
        # From Mac (outside Docker): localhost:9000
        # Port 9000 is the API port — 9001 is the console UI
        endpoint=os.getenv("MINIO_ENDPOINT"),

        # access_key: equivalent to a username for MinIO
        access_key=os.getenv("MINIO_ACCESS_KEY"),

        # secret_key: equivalent to a password for MinIO
        secret_key=os.getenv("MINIO_SECRET_KEY"),

        # secure=False: use HTTP not HTTPS for local development
        secure=False,
    )