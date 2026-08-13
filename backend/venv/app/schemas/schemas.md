# Standard Sales Schema

Every ingested sales record is standardised to this shape before storage.

| Field | Type | Required | Description |
|---|---|---|---|
| order_id | string | Yes | Unique order or invoice identifier |
| order_date | date (YYYY-MM-DD) | Yes | Date the order was placed |
| platform | string | Yes | Sales channel, e.g. Shopee, Lazada, TikTok Shop, Website |
| product_name | string | Yes | Name of the product sold |
| quantity | integer | Yes | Units sold in this order line |
| unit_price | float | Yes | Price per unit |
| total_amount | float | Yes | Total value of the order line |
| status | string | Yes | Order status, e.g. Completed, Refunded, Cancelled |
| sku | string | No | Product code |
| category | string | No | Product category |
| currency | string | No (defaults to SGD) | Currency code |
| customer_id | string | No | Customer or buyer identifier |
| region | string | No | Delivery region or state |
| payment_method | string | No | Payment method used |

Column names in raw source files do not need to match these exactly — the
mapper in `backend/app/services/mapper.py` recognises common aliases
(e.g. "Qty" → quantity, "Item" → product_name, "Amount" → total_amount).