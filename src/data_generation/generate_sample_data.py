"""Generate reproducible synthetic e-commerce CSVs with seeded quality defects.

The output schemas follow ``data-model.md``. The defect types and exact counts
follow ``data-quality-strategy.md``: 460 exercise-required rows plus 240
supplemental rows, for 700 distinct problematic rows.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    from faker import Faker
except ImportError as exc:  # pragma: no cover - exercised only without setup
    raise SystemExit(
        "Faker is required. Install project dependencies with "
        "'python -m pip install -r requirements.txt'."
    ) from exc


RANDOM_SEED = 20260831
AS_OF_DATE = date(2026, 8, 31)

CUSTOMER_COUNT = 10_000
ORDER_COUNT = 100_000
PRODUCT_COUNT = 500

CUSTOMER_SEGMENTS = ("Premium", "Standard", "Basic")
ORDER_STATUSES = ("Pending", "Completed", "Cancelled")
PRODUCT_CATEGORIES = (
    "Electronics",
    "Home",
    "Books",
    "Sports",
    "Beauty",
    "Clothing",
)

CUSTOMER_FIELDS = (
    "customer_id",
    "customer_name",
    "email",
    "country",
    "signup_date",
    "customer_segment",
    "lifetime_value",
)
ORDER_FIELDS = (
    "order_id",
    "customer_id",
    "order_date",
    "product_id",
    "quantity",
    "unit_price",
    "total_amount",
    "order_status",
    "payment_date",
)
PRODUCT_FIELDS = (
    "product_id",
    "product_name",
    "category",
    "price",
    "cost",
    "stock_quantity",
    "reorder_level",
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CENT = Decimal("0.01")


def parse_args() -> argparse.Namespace:
    """Parse output configuration while keeping generation rules fixed."""
    default_output = Path(__file__).resolve().parents[2] / "data"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output,
        help=f"Directory for generated CSVs (default: {default_output})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed (default: {RANDOM_SEED})",
    )
    return parser.parse_args()


def money_from_cents(cents: int) -> Decimal:
    """Create an exact DECIMAL(12,2)-compatible amount from integer cents."""
    return (Decimal(cents) / Decimal(100)).quantize(CENT)


def format_money(value: Decimal) -> str:
    """Serialize a money value with exactly two decimal places for CSV."""
    return f"{value.quantize(CENT):.2f}"


def random_date(
    rng: random.Random,
    start_date: date,
    end_date: date,
) -> date:
    """Return a reproducible date in the inclusive range."""
    if start_date > end_date:
        raise ValueError(f"Invalid date range: {start_date} > {end_date}")
    day_offset = rng.randint(0, (end_date - start_date).days)
    return start_date + timedelta(days=day_offset)


def reserve_disjoint_indices(
    rng: random.Random,
    population_size: int,
    group_sizes: Sequence[int],
) -> list[list[int]]:
    """Reserve shuffled, non-overlapping row indices for seeded defects."""
    required = sum(group_sizes)
    if required > population_size:
        raise ValueError(
            f"Cannot reserve {required} indices from {population_size} rows"
        )

    indices = list(range(population_size))
    rng.shuffle(indices)
    groups: list[list[int]] = []
    cursor = 0
    for group_size in group_sizes:
        groups.append(indices[cursor : cursor + group_size])
        cursor += group_size
    return groups


def generate_products(
    fake: Faker,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], set[int]]:
    """Generate products and seed 20 supplemental catalog defects."""
    products: list[dict[str, Any]] = []
    for product_id in range(1, PRODUCT_COUNT + 1):
        category = rng.choice(PRODUCT_CATEGORIES)
        price = money_from_cents(rng.randint(500, 50_000))
        cost = (price * Decimal(rng.randint(35, 80)) / Decimal(100)).quantize(CENT)
        products.append(
            {
                "product_id": product_id,
                "product_name": (
                    f"{fake.color_name()} {category} {fake.word().title()} "
                    f"{product_id:04d}"
                ),
                "category": category,
                "price": format_money(price),
                "cost": format_money(cost),
                "stock_quantity": rng.randint(0, 1_000),
                "reorder_level": rng.randint(5, 100),
            }
        )

    zero_price_indices, negative_margin_indices = reserve_disjoint_indices(
        rng,
        PRODUCT_COUNT,
        (10, 10),
    )

    for row_index in zero_price_indices:
        # Set cost to zero too, so this row represents only the price defect.
        products[row_index]["price"] = "0.00"
        products[row_index]["cost"] = "0.00"

    for row_index in negative_margin_indices:
        price = Decimal(products[row_index]["price"])
        products[row_index]["cost"] = format_money(price + Decimal("1.00"))

    bad_indices = set(zero_price_indices) | set(negative_margin_indices)
    clean_product_ids = {
        int(row["product_id"])
        for index, row in enumerate(products)
        if index not in bad_indices
    }
    return products, clean_product_ids


def generate_customers(
    fake: Faker,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], set[int]]:
    """Generate customers and seed 60 required plus 80 supplemental defects."""
    customers: list[dict[str, Any]] = []
    for customer_id in range(1, CUSTOMER_COUNT + 1):
        # Faker supplies realistic syntax; example.com keeps all data synthetic.
        email_local = fake.user_name().replace(" ", ".")
        customers.append(
            {
                "customer_id": customer_id,
                "customer_name": fake.name(),
                "email": f"{email_local}.{customer_id}@example.com",
                "country": fake.country_code(),
                "signup_date": random_date(
                    rng,
                    date(2020, 1, 1),
                    AS_OF_DATE,
                ).isoformat(),
                "customer_segment": rng.choice(CUSTOMER_SEGMENTS),
                "lifetime_value": format_money(
                    money_from_cents(rng.randint(0, 5_000_000))
                ),
            }
        )

    (
        null_email_indices,
        duplicate_id_indices,
        malformed_email_indices,
        future_signup_indices,
        invalid_segment_indices,
    ) = reserve_disjoint_indices(
        rng,
        CUSTOMER_COUNT,
        (50, 10, 40, 20, 20),
    )

    for row_index in null_email_indices:
        customers[row_index]["email"] = None

    # Ten rows form five duplicate pairs, so exactly ten rows fail uniqueness.
    for first_index, second_index in zip(
        duplicate_id_indices[::2],
        duplicate_id_indices[1::2],
    ):
        customers[second_index]["customer_id"] = customers[first_index]["customer_id"]

    malformed_values = ("not-an-email", "user@", "user@example")
    for offset, row_index in enumerate(malformed_email_indices):
        customers[row_index]["email"] = malformed_values[
            offset % len(malformed_values)
        ]

    for offset, row_index in enumerate(future_signup_indices, start=1):
        customers[row_index]["signup_date"] = (
            AS_OF_DATE + timedelta(days=offset)
        ).isoformat()

    for row_index in invalid_segment_indices:
        customers[row_index]["customer_segment"] = "Unknown"

    all_bad_indices = (
        set(null_email_indices)
        | set(duplicate_id_indices)
        | set(malformed_email_indices)
        | set(future_signup_indices)
        | set(invalid_segment_indices)
    )
    id_counts = Counter(int(row["customer_id"]) for row in customers)
    clean_customer_ids = {
        int(row["customer_id"])
        for index, row in enumerate(customers)
        if index not in all_bad_indices
        and id_counts[int(row["customer_id"])] == 1
    }
    return customers, clean_customer_ids


def generate_orders(
    rng: random.Random,
    clean_customer_ids: set[int],
    clean_product_ids: set[int],
    products: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate orders and seed 400 required plus 140 supplemental defects."""
    customer_choices = sorted(clean_customer_ids)
    product_choices = sorted(clean_product_ids)
    product_prices = {
        int(row["product_id"]): Decimal(str(row["price"])) for row in products
    }

    orders: list[dict[str, Any]] = []
    for order_id in range(1, ORDER_COUNT + 1):
        customer_id = rng.choice(customer_choices)
        product_id = rng.choice(product_choices)
        order_date = random_date(rng, date(2022, 1, 1), AS_OF_DATE)
        quantity = rng.randint(1, 10)
        unit_price = product_prices[product_id]
        total_amount = (unit_price * quantity).quantize(CENT)
        order_status = rng.choices(
            ORDER_STATUSES,
            weights=(10, 80, 10),
            k=1,
        )[0]

        payment_date: str | None = None
        if order_status == "Completed":
            latest_payment_date = min(
                order_date + timedelta(days=7),
                AS_OF_DATE,
            )
            payment_date = random_date(
                rng,
                order_date,
                latest_payment_date,
            ).isoformat()

        orders.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": order_date.isoformat(),
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": format_money(unit_price),
                "total_amount": format_money(total_amount),
                "order_status": order_status,
                "payment_date": payment_date,
            }
        )

    (
        null_customer_indices,
        null_product_indices,
        orphan_customer_indices,
        orphan_product_indices,
        duplicate_order_indices,
        non_positive_quantity_indices,
        zero_unit_price_indices,
        amount_mismatch_indices,
        invalid_status_indices,
    ) = reserve_disjoint_indices(
        rng,
        ORDER_COUNT,
        (100, 200, 50, 30, 20, 50, 40, 40, 10),
    )

    for row_index in null_customer_indices:
        orders[row_index]["customer_id"] = None

    for row_index in null_product_indices:
        orders[row_index]["product_id"] = None

    for offset, row_index in enumerate(orphan_customer_indices, start=1):
        orders[row_index]["customer_id"] = 1_000_000 + offset

    for offset, row_index in enumerate(orphan_product_indices, start=1):
        orders[row_index]["product_id"] = 1_000_000 + offset

    # Twenty rows form ten duplicate pairs, so exactly twenty rows fail.
    for first_index, second_index in zip(
        duplicate_order_indices[::2],
        duplicate_order_indices[1::2],
    ):
        orders[second_index]["order_id"] = orders[first_index]["order_id"]

    for row_index in non_positive_quantity_indices:
        orders[row_index]["quantity"] = -1
        unit_price = Decimal(str(orders[row_index]["unit_price"]))
        orders[row_index]["total_amount"] = format_money(-unit_price)

    for row_index in zero_unit_price_indices:
        # Keep arithmetic consistent, isolating this row as a price defect.
        orders[row_index]["unit_price"] = "0.00"
        orders[row_index]["total_amount"] = "0.00"

    for row_index in amount_mismatch_indices:
        expected = (
            Decimal(str(orders[row_index]["unit_price"]))
            * int(orders[row_index]["quantity"])
        ).quantize(CENT)
        orders[row_index]["total_amount"] = format_money(
            expected + Decimal("1.00")
        )

    for row_index in invalid_status_indices:
        orders[row_index]["order_status"] = "Unknown"

    return orders


def duplicate_row_indices(
    rows: Sequence[dict[str, Any]],
    key: str,
) -> set[int]:
    """Return every row index belonging to a duplicated key group."""
    counts = Counter(row[key] for row in rows)
    return {
        index
        for index, row in enumerate(rows)
        if counts[row[key]] > 1
    }


def assert_count(label: str, actual: int, expected: int) -> None:
    """Raise a clear validation error when a seeded count differs."""
    if actual != expected:
        raise ValueError(f"{label}: expected {expected}, found {actual}")


def validate_seeded_issues(
    customers: Sequence[dict[str, Any]],
    orders: Sequence[dict[str, Any]],
    products: Sequence[dict[str, Any]],
) -> None:
    """Verify every issue count and the 700 distinct-row target before write."""
    assert_count("customer rows", len(customers), CUSTOMER_COUNT)
    assert_count("order rows", len(orders), ORDER_COUNT)
    assert_count("product rows", len(products), PRODUCT_COUNT)

    customer_ids = {int(row["customer_id"]) for row in customers}
    product_ids = {int(row["product_id"]) for row in products}

    customer_duplicate_indices = duplicate_row_indices(
        customers,
        "customer_id",
    )
    order_duplicate_indices = duplicate_row_indices(orders, "order_id")

    customer_issue_sets = {
        "NULL customer email": {
            index for index, row in enumerate(customers) if row["email"] is None
        },
        "duplicate customer_id rows": customer_duplicate_indices,
        "malformed customer email": {
            index
            for index, row in enumerate(customers)
            if row["email"] is not None
            and EMAIL_PATTERN.fullmatch(str(row["email"])) is None
        },
        "future signup_date": {
            index
            for index, row in enumerate(customers)
            if date.fromisoformat(str(row["signup_date"])) > AS_OF_DATE
        },
        "invalid customer_segment": {
            index
            for index, row in enumerate(customers)
            if row["customer_segment"] not in CUSTOMER_SEGMENTS
        },
    }
    expected_customer_counts = {
        "NULL customer email": 50,
        "duplicate customer_id rows": 10,
        "malformed customer email": 40,
        "future signup_date": 20,
        "invalid customer_segment": 20,
    }

    order_issue_sets = {
        "NULL order customer_id": {
            index
            for index, row in enumerate(orders)
            if row["customer_id"] is None
        },
        "NULL order product_id": {
            index
            for index, row in enumerate(orders)
            if row["product_id"] is None
        },
        "orphan order customer_id": {
            index
            for index, row in enumerate(orders)
            if row["customer_id"] is not None
            and int(row["customer_id"]) not in customer_ids
        },
        "orphan order product_id": {
            index
            for index, row in enumerate(orders)
            if row["product_id"] is not None
            and int(row["product_id"]) not in product_ids
        },
        "duplicate order_id rows": order_duplicate_indices,
        "non-positive quantity": {
            index
            for index, row in enumerate(orders)
            if int(row["quantity"]) <= 0
        },
        "zero unit_price": {
            index
            for index, row in enumerate(orders)
            if Decimal(str(row["unit_price"])) == Decimal("0.00")
        },
        "total_amount mismatch": {
            index
            for index, row in enumerate(orders)
            if Decimal(str(row["total_amount"]))
            != (
                Decimal(str(row["unit_price"])) * int(row["quantity"])
            ).quantize(CENT)
        },
        "invalid order_status": {
            index
            for index, row in enumerate(orders)
            if row["order_status"] not in ORDER_STATUSES
        },
    }
    expected_order_counts = {
        "NULL order customer_id": 100,
        "NULL order product_id": 200,
        "orphan order customer_id": 50,
        "orphan order product_id": 30,
        "duplicate order_id rows": 20,
        "non-positive quantity": 50,
        "zero unit_price": 40,
        "total_amount mismatch": 40,
        "invalid order_status": 10,
    }

    product_issue_sets = {
        "zero product price": {
            index
            for index, row in enumerate(products)
            if Decimal(str(row["price"])) == Decimal("0.00")
        },
        "product cost above price": {
            index
            for index, row in enumerate(products)
            if Decimal(str(row["cost"])) > Decimal(str(row["price"]))
        },
    }
    expected_product_counts = {
        "zero product price": 10,
        "product cost above price": 10,
    }

    for issue_sets, expected_counts in (
        (customer_issue_sets, expected_customer_counts),
        (order_issue_sets, expected_order_counts),
        (product_issue_sets, expected_product_counts),
    ):
        for label, expected in expected_counts.items():
            assert_count(label, len(issue_sets[label]), expected)

    customer_bad_rows = set().union(*customer_issue_sets.values())
    order_bad_rows = set().union(*order_issue_sets.values())
    product_bad_rows = set().union(*product_issue_sets.values())
    assert_count("distinct bad customer rows", len(customer_bad_rows), 140)
    assert_count("distinct bad order rows", len(order_bad_rows), 540)
    assert_count("distinct bad product rows", len(product_bad_rows), 20)
    assert_count(
        "total distinct problematic rows",
        len(customer_bad_rows) + len(order_bad_rows) + len(product_bad_rows),
        700,
    )


def write_csv(
    destination: Path,
    fieldnames: Iterable[str],
    rows: Sequence[dict[str, Any]],
) -> None:
    """Write one source file using its exact data-contract column order."""
    with destination.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Generate, self-validate, and write all three source CSV files."""
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    fake = Faker("en_US")
    fake.seed_instance(args.seed)

    products, clean_product_ids = generate_products(fake, rng)
    customers, clean_customer_ids = generate_customers(fake, rng)
    orders = generate_orders(
        rng,
        clean_customer_ids,
        clean_product_ids,
        products,
    )

    # Validate before writing so a rule change cannot silently corrupt fixtures.
    validate_seeded_issues(customers, orders, products)

    write_csv(output_dir / "customers.csv", CUSTOMER_FIELDS, customers)
    write_csv(output_dir / "orders.csv", ORDER_FIELDS, orders)
    write_csv(output_dir / "products.csv", PRODUCT_FIELDS, products)

    print(f"Generated {CUSTOMER_COUNT:,} customers: {output_dir / 'customers.csv'}")
    print(f"Generated {ORDER_COUNT:,} orders: {output_dir / 'orders.csv'}")
    print(f"Generated {PRODUCT_COUNT:,} products: {output_dir / 'products.csv'}")
    print("Validated 460 required + 240 supplemental = 700 distinct bad rows.")


if __name__ == "__main__":
    main()
