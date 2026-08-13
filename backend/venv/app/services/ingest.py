import io
import pandas as pd
from pydantic import ValidationError

from app.schemas.sales_schema import StandardSalesRecord
from app.services.mapper import map_columns, clean_price, clean_quantity, clean_date, clean_text
from app.services import storage


def process_excel_file(file_obj: io.BytesIO, filename: str) -> dict:
    df = pd.read_excel(file_obj, engine="openpyxl")
    df, unmapped_fields = map_columns(df)

    valid_records = []
    errors = []

    for idx, row in df.iterrows():
        try:
            record = {
                "order_id": clean_text(row.get("order_id")),
                "order_date": clean_date(row.get("order_date")),
                "platform": clean_text(row.get("platform")),
                "sku": clean_text(row.get("sku")),
                "product_name": clean_text(row.get("product_name")),
                "category": clean_text(row.get("category")),
                "quantity": clean_quantity(row.get("quantity")),
                "unit_price": clean_price(row.get("unit_price")),
                "total_amount": clean_price(row.get("total_amount")),
                "currency": clean_text(row.get("currency")) or "SGD",
                "customer_id": clean_text(row.get("customer_id")),
                "region": clean_text(row.get("region")),
                "status": clean_text(row.get("status")) or "Completed",
                "payment_method": clean_text(row.get("payment_method")),
            }
            validated = StandardSalesRecord(**record)
            valid_records.append(validated.model_dump(mode="json"))
        except ValidationError as e:
            first = e.errors()[0]
            errors.append({"row": int(idx) + 2, "field": str(first["loc"][0]), "reason": first["msg"]})
        except Exception as e:
            errors.append({"row": int(idx) + 2, "reason": str(e)})

    storage.save_records(valid_records, source_filename=filename)

    return {
        "filename": filename,
        "rows_total": len(df),
        "rows_ingested": len(valid_records),
        "rows_skipped": len(errors),
        "unmapped_fields": unmapped_fields,
        "errors": errors[:20],
        "preview": valid_records[:5],
    }