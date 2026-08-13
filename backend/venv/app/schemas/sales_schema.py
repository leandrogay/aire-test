from pydantic import BaseModel
from datetime import date
from typing import Optional


class StandardSalesRecord(BaseModel):
    order_id: str
    order_date: date
    platform: str
    product_name: str
    quantity: int
    unit_price: float
    total_amount: float
    status: str

    sku: Optional[str] = None
    category: Optional[str] = None
    currency: str = "SGD"
    customer_id: Optional[str] = None
    region: Optional[str] = None
    payment_method: Optional[str] = None