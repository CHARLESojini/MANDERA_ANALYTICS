"""
Uploads order documents from MongoDB to MinIO as a JSON archive.

Each upload creates a timestamped file in MinIO under the orders/ prefix.
Orders are the largest collection so the file size will be significantly
bigger than customers or products — this is expected and handled correctly
by MinIO's streaming upload.

File path pattern in MinIO:
    orders/YYYY-MM-DD/batch_<id>.json
"""

import io
import json
from datetime import datetime, timezone

from minio import Minio
from pymongo.database import Database


def upload_orders(
    mongo_db: Database,
    client: Minio,
    bucket_name: str,
) -> int:
    """Pull all order documents from MongoDB and upload to MinIO as JSON.

    Args:
        mongo_db: Active MongoDB database instance.
        client: Active MinIO client instance.
        bucket_name: Name of the MinIO bucket to upload to.

    Returns:
        Number of order documents uploaded.
    """

    # Exclude MongoDB's internal _id field — not JSON serializable
    orders = list(mongo_db["orders"].find({}, {"_id": 0}))

    if not orders:
        print("  No orders found in MongoDB.")
        return 0

    # Serialize to JSON string then encode to bytes for upload
    # Orders collection is large — json.dumps handles any size correctly
    json_data   = json.dumps(orders, default=str, indent=2)
    json_bytes  = json_data.encode("utf-8")
    data_stream = io.BytesIO(json_bytes)

    # Build timestamped file path inside the bucket
    date_str    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    batch_id    = orders[0].get("batch_id", "unknown")
    object_name = f"orders/{date_str}/batch_{batch_id}.json"

    client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=data_stream,
        length=len(json_bytes),
        content_type="application/json",
    )

    print(f"  Uploaded {len(orders)} orders → {bucket_name}/{object_name}")
    return len(orders)