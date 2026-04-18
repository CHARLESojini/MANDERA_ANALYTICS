"""
Centralized configuration for the Mandera Analytics pipeline.
All modules import from here - no hardcoded connection strings.
"""

import os
from datetime import datetime, timezone

# MongoDB Atlas
MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise EnvironmentError(
        "MONGO_URL is not set. Provide your MongoDB Atlas connection string in .env"
    )
MONGO_DB = os.getenv("MONGO_DB_NAME")

MONGO_COLLECTIONS = {
    "customers": "customers",
    "products": "products",
    "orders": "orders",
}

# Source generation settings (used by generator/)
ORDERS_MIN = 3000
ORDERS_MAX = 6500
CUSTOMERS_MIN = 15
CUSTOMERS_MAX = 25
PRODUCTS_MIN = 5
PRODUCTS_MAX = 10

# Order constants (used by fake_orders/)
ORDER_STATUSES = ["pending", "shipped", "delivered", "cancelled", "returned"]
PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer", "cash_on_delivery"]
SHIPPING_METHODS = ["standard", "express", "overnight", "pickup"]

# Product categories and sample products (used by generator/)
PRODUCT_CATEGORIES = {
    "Electronics": [
        "Laptop", "Smartphone", "Wireless Earbuds", "Smart Watch",
        "Tablet", "Gaming Console",
        "Bluetooth Speaker", "Monitor", "Keyboard", "Webcam",
    ],
    "Clothing": [
        "T-Shirt", "Jeans", "Running Shoes", "Jacket",
        "Hoodie", "Dress", "Shorts",
        "Sneakers", "Socks", "Cap",
    ],
    "Home & Kitchen": [
        "Coffee Maker", "Air Fryer", "Blender", "Bed Sheets", "Cookware Set",
        "Toaster", "Vacuum Cleaner", "Dish Rack", "Knife Set", "Rice Cooker",
    ],
    "Sports & Fitness": [
        "Yoga Mat", "Resistance Bands", "Dumbbells", "Protein Powder", "Jump Rope",
        "Pull-Up Bar", "Foam Roller", "Water Bottle", "Gym Gloves", "Treadmill",
    ],
    "Books": [
        "Fiction Novel", "Self-Help Book", "Cookbook", "Biography", "Tech Manual",
        "Science Fiction", "History Book",
        "Poetry Collection", "Business Strategy", "Children's Book",
    ],
}

def generate_batch_id(db) -> str:
    """Generate a sequential integer batch ID by incrementing a counter in MongoDB.
 
    On the first run this creates a 'batch_counter' document in MongoDB
    and sets the sequence to 1. Every subsequent run increments it by 1,
    producing IDs like 1, 2, 3 ... with no collisions across runs.
 
    Args:
        db: Active pymongo database instance.
 
    Returns:
        A string representation of the current batch sequence number e.g. '1', '2'.
    """
    result = db["batch_counter"].find_one_and_update(
        {"_id": "batch_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return str(result["seq"])