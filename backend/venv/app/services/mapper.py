import pandas as pd
from datetime import datetime

COLUMN_ALIASES = {
    "order_id": ["order id", "orderid", "order no", "order no.", "order number", "invoice no", "invoice no.", "invoice number"],
    "order_date": ["order date", "date", "purchase date", "transaction date"],
    "platform": ["platform", "channel", "marketplace", "source", "sales channel"],
    "sku": ["sku", "product code", "item code", "product sku"],
    "product_name": ["product name", "item", "item name", "product", "description"],
    "category": ["category", "product category", "item category"],
    "quantity": ["quantity", "qty", "units", "units sold"],
    "unit_price": ["unit price", "price", "price per unit", "unit cost"],
    "total_amount": ["total amount", "amount", "total", "total price", "order total"],
    "currency": ["currency", "curr"],
    "customer_id": ["customer id", "buyer id", "customer"],
    "region": ["region", "state", "location", "delivery region"],
    "status": ["status", "order status"],
    "payment_method": ["payment method", "payment type", "payment"],
}

CURRENCY_SYMBOLS = ["$", "S$", "SGD", "RM", "PHP", "USD", "MYR", "₱"]


def normalize_column_name(col: str) -> str:
    return str(col).strip().lower().replace("_", " ")


def map_columns(df: pd.DataFrame):
    """Renames source columns to standard schema field names. Returns the
    renamed dataframe and a list of schema fields no column was found for."""
    normalized_lookup = {normalize_column_name(col): col for col in df.columns}
    rename_map = {}
    mapped_targets = set()

    for target_field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized_lookup:
                rename_map[normalized_lookup[alias]] = target_field
                mapped_targets.add(target_field)
                break

    df = df.rename(columns=rename_map)
    unmapped_targets = [f for f in COLUMN_ALIASES if f not in mapped_targets]
    return df, unmapped_targets


def clean_price(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value)
    for symbol in CURRENCY_SYMBOLS:
        text = text.replace(symbol, "")
    text = text.replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def clean_quantity(value):
    if pd.isna(value):
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def clean_date(value):
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.date()
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return None
    return parsed.date()


def clean_text(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    return str(value).strip()