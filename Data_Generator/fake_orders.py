"""Generate synthetic order records."""

import random
from datetime import datetime, timezone

from Config.settings import (
    ORDERS_MIN,
    ORDERS_MAX,
    ORDER_STATUSES,
    PAYMENT_METHODS,
    SHIPPING_METHODS,
)


def generate(batch_id: str, customer_ids: list[str], product_ids: list[str]) -> list[dict]:
    """Generate 3000 - 6500 order documents referencing existing customer and product IDs."""
    count = random.randint(ORDERS_MIN, ORDERS_MAX)
    orders = []

    for _ in range(count):
        qty = random.randint(1, 10)
        unit_price = round(random.uniform(5.0, 500.0), 2)

        orders.append({
            "order_id": f"ORD{random.randint(10000, 99999)}",
            "customer_id": random.choice(customer_ids),
            "product_id": random.choice(product_ids),
            "quantity": qty,
            "unit_price": unit_price,
            "total_price": round(qty * unit_price, 2),
            "status": random.choice(ORDER_STATUSES),
            "payment_method": random.choice(PAYMENT_METHODS),
            "shipping_method": random.choice(SHIPPING_METHODS),
            "batch_id": batch_id,
            "created_at": datetime.now(timezone.utc),
        })

    return orders
