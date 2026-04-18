"""Generating sysntetic customer record from fakers"""

import random

from datetime import datetime, timezone

from faker import faker

from Config.settings import CUSTOMERS_MIN, CUSTOMERS_MAX

fake = faker()

def generate(batch_id: str) -> list[dict]:
    """generate 15-25 customers documents."""
    count = random.randint(CUSTOMERS_MIN, CUSTOMERS_MAX)
    customers = []

    for _ in range(count):
        customers.append({
            "customer_id": f"cust{random.randint(10000,99999)}",
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "city": fake.city(),
            "batch_id": batch_id,
            "creatred_at": datetime.now(timezone. utc),
        })

    return customers 