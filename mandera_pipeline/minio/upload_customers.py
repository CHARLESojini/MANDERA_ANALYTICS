"""
Uploads customer documents from MongoDB to MinIO as a JSON archive.

Each upload creates a timestamped file in MinIO under the customers/ prefix.
This preserves a complete snapshot of the customers collection at the
time of extraction — useful for replayability and auditing.

File path pattern in MinIO:
    customers/YYYY-MM-DD/batch_<id>.json
"""

import io
import json
from datetime import datetime, timezone

from minio import Minio
from pymongo.database import Database


def upload_customers(
    mongo_db: Database,
    client: Minio,
    bucket_name: str,
) -> int:
    """Pull all customer documents from MongoDB and upload to MinIO as JSON.

    The documents are serialized to JSON and uploaded as a single file.
    The file path includes the date and batch_id so every run produces
    a unique, traceable archive file.

    Args:
        mongo_db: Active MongoDB database instance.
        client: Active MinIO client instance.
        bucket_name: Name of the MinIO bucket to upload to.

    Returns:
        Number of customer documents uploaded.
    """

    # Fetch all customer documents from MongoDB
    # We exclude the MongoDB internal _id field using {_id: 0} projection
    # _id is a MongoDB ObjectId which is not JSON serializable by default
    customers = list(mongo_db["customers"].find({}, {"_id": 0}))

    if not customers:
        print("  No customers found in MongoDB.")
        return 0

    # Serialize the list of documents to a JSON string
    # default=str converts any non-serializable types (e.g. datetime) to string
    # indent=2 makes the file human-readable
    json_data = json.dumps(customers, default=str, indent=2)

    # Convert the string to bytes — MinIO requires bytes for upload
    # encode("utf-8") converts the string to a UTF-8 byte stream
    json_bytes = json_data.encode("utf-8")

    # io.BytesIO wraps the bytes in a file-like object
    # MinIO's put_object() expects a file-like object, not raw bytes
    data_stream = io.BytesIO(json_bytes)

    # Build the object path inside the bucket
    # Format: customers/YYYY-MM-DD/batch_<id>.json
    # This groups files by date making it easy to find specific runs
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Get batch_id from the first document to include in the filename
    batch_id  = customers[0].get("batch_id", "unknown")
    object_name = f"customers/{date_str}/batch_{batch_id}.json"

    # Upload the file to MinIO
    # length: total size of the file in bytes — required by MinIO
    # content_type: tells MinIO this is a JSON file
    client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=data_stream,
        length=len(json_bytes),
        content_type="application/json",
    )

    print(f"  Uploaded {len(customers)} customers → {bucket_name}/{object_name}")
    return len(customers)