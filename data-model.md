# Data Model

Logical schema for the e-commerce sales entities ingested as CSV from S3 or
DBFS. This is the data contract used by Bronze schema application. Quality-issue
inventories belong in `data-quality-strategy.md`, not here.

## `customers`

Expected volume: 10,000 rows.

| Field | Type | Constraint or meaning |
|---|---|---|
| `customer_id` | INT | Primary key |
| `customer_name` | STRING | Customer name |
| `email` | STRING | Customer email |
| `country` | STRING | Customer country |
| `signup_date` | DATE | Signup date |
| `customer_segment` | STRING | `Premium`, `Standard`, or `Basic` |
| `lifetime_value` | DECIMAL(12,2) | Source-provided lifetime value |

## `orders`

Expected volume: 100,000 rows.

| Field | Type | Constraint or meaning |
|---|---|---|
| `order_id` | INT | Primary key |
| `customer_id` | INT | Foreign key to `customers.customer_id` |
| `order_date` | DATE | Order date |
| `product_id` | INT | Foreign key to `products.product_id` |
| `quantity` | INT | Ordered quantity |
| `unit_price` | DECIMAL(12,2) | Unit selling price |
| `total_amount` | DECIMAL(12,2) | Order-line total |
| `order_status` | STRING | `Pending`, `Completed`, or `Cancelled` |
| `payment_date` | DATE | Nullable |

## `products`

Expected volume: 500 rows.

| Field | Type | Constraint or meaning |
|---|---|---|
| `product_id` | INT | Primary key |
| `product_name` | STRING | Product name |
| `category` | STRING | Product category |
| `price` | DECIMAL(12,2) | Product selling price |
| `cost` | DECIMAL(12,2) | Product cost |
| `stock_quantity` | INT | Units currently in stock |
| `reorder_level` | INT | Stock threshold for reordering |

## Relationships

```
customers.customer_id  ←  orders.customer_id
products.product_id    ←  orders.product_id
```

- `orders.customer_id` → `customers.customer_id`
- `orders.product_id` → `products.product_id`

`customers` and `products` have no foreign keys to each other. Cardinality is
one customer to many orders and one product to many orders.

## Decimal precision and scale

`spec.md` does not set precision or scale; it requires a single documented
choice before code is generated.

All money fields use **DECIMAL(12,2)**: `customers.lifetime_value`,
`orders.unit_price`, `orders.total_amount`, `products.price`, and
`products.cost`.

- Scale 2 matches currency to the cent and avoids float rounding in Silver
  arithmetic checks (`total_amount` vs `quantity × unit_price`).
- Precision 12 allows values up to 9,999,999,999.99, which is enough for
  this synthetic catalog, order lines, and lifetime value without implying
  a production finance ledger.

Silver amount comparisons must use this same scale, not floating-point
equality.
