"""
Orchestrates synthetic data generation -> MongoDB Atlas.

Calls each faker module, inserts the results into MongoDB,
and logs what was generated. Designed to be called by GitHub Actions.

USAGE:
    python -m Data_Generator.generator
"""

from pymongo import MongoClient

from Config.settings import MONGO_URL, MONGO_DB, MONGO_COLLECTIONS, generate_batch_id
import Data_Generator.fake_customers as fake_customers
import Data_Generator.fake_products as fake_products
import Data_Generator.fake_orders as fake_orders


def main():
    """Generate customers -> products -> orders and insert into MongoDB."""
    client = MongoClient(MONGO_URL)
    db = client[MONGO_DB]

    batch_id = generate_batch_id(db)
    print(f"Batch ID: {batch_id}\n")

    try:
        customers = fake_customers.generate(batch_id)
        db[MONGO_COLLECTIONS["customers"]].insert_many(customers)
        customer_ids = [c["customer_id"] for c in customers]
        print(f"  Inserted {len(customers)} customers")

        products = fake_products.generate(batch_id)
        db[MONGO_COLLECTIONS["products"]].insert_many(products)
        product_ids = [p["product_id"] for p in products]
        print(f"  Inserted {len(products)} products")

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
