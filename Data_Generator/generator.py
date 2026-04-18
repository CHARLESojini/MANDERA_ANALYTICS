"""
Orchestrates synthetic data generation -> MongoDB Atlas.

Calls each faker module, inserts the results into MongoDB,
and logs what was generated. Designed to be called by GitHub Actions.

USAGE:
    python -m Data_Generator.generator
"""

from pymongo import MongoClient

from Config.settings import MONGO_URL, MONGO_DB, MONGO_COLLECTIONS, generate_batch_id
from Data_Generator import fake_customers, fake_products, fake_orders


def main():
    """Generate customers -> products -> orders and insert into MongoDB."""
    client = MongoClient(MONGO_URL)
    db = client[MONGO_DB]

    # Generate batch_id once so all records in this run share the same ID
    batch_id = generate_batch_id(db)
    print(f"Batch ID: {batch_id}\n")

    try:
        # Generate and insert customers
        customers = fake_customers.generate(batch_id)
        db[MONGO_COLLECTIONS["customers"]].insert_many(customers)
        print(f"  Inserted {len(customers)} customers")

        # Collect customer_ids for orders to reference
        customer_ids = [c["customer_id"] for c in customers]

        # Generate and insert products
        products = fake_products.generate(batch_id)
        db[MONGO_COLLECTIONS["products"]].insert_many(products)
        print(f"  Inserted {len(products)} products")

        # Collect product_ids for orders to reference
        product_ids = [p["product_id"] for p in products]

        # Generate and insert orders (references customers + products)
        orders = fake_orders.generate(batch_id, customer_ids, product_ids)
        db[MONGO_COLLECTIONS["orders"]].insert_many(orders)
        print(f"  Inserted {len(orders)} orders")

        print(f"\nBatch {batch_id} complete.")

    except Exception as e:
        print(f"  Error during generation: {e}")
        raise

    finally:
        client.close()
        print("  MongoDB connection closed.")


if __name__ == "__main__":
    main()
