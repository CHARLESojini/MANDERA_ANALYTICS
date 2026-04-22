"""
Uploads product documents from MongoDB to MinIO as a JSON archive.

Each upload creates a timestamped file in MinIO under the products/ prefix.
This preserves a complete snapshot of the products collection at the
time of extraction — useful for replayability and auditing.

File path pattern in MinIO:
    products/YYYY-MM-DD/batch_<id>.json
"""

import io
import json
from datetime import datetime, timezone

from minio import Minio
from pymongo.database import Database


def upload_products(
    mongo_db: Database,
    client: Minio,
    bucket_name: str,
) -> int:
    """Pull all product documents from MongoDB and upload to MinIO as JSON.

    Args:
        mongo_db: Active MongoDB database instance.
        client: Active MinIO client instance.
        bucket_name: Name of the MinIO bucket to upload to.

    Returns:
        Number of product documents uploaded.
    """

    # Exclude MongoDB's internal _id field — not JSON serializable
    products = list(mongo_db["products"].find({}, {"_id": 0}))

    if not products:
        print("  No products found in MongoDB.")
        return 0

    # Serialize to JSON string then encode to bytes for upload
    json_data   = json.dumps(products, default=str, indent=2)
    json_bytes  = json_data.encode("utf-8")
    data_stream = io.BytesIO(json_bytes)

    # Build timestamped file path inside the bucket
    date_str    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    batch_id = products[0].get("batch_id") or products[0].get("batch-id", "unknown")
    object_name = f"products/{date_str}/batch_{batch_id}.json"

    client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=data_stream,
        length=len(json_bytes),
        content_type="application/json",
    )

    print(f"  Uploaded {len(products)} products → {bucket_name}/{object_name}")
    return len(products)