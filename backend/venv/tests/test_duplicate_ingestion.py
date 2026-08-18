import io

import openpyxl
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import storage
from app.services.ingest import process_excel_file

client = TestClient(app)

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point storage at a throwaway sqlite file so tests never touch real data."""
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "sales.db")
    yield


def make_record(order_id, sku="SKU-A", total_amount=100.0):
    return {
        "order_id": order_id,
        "order_date": "2026-01-01",
        "platform": "Shopee",
        "sku": sku,
        "product_name": "Widget A",
        "category": "General",
        "quantity": 1,
        "unit_price": total_amount,
        "total_amount": total_amount,
        "currency": "SGD",
        "customer_id": "C1",
        "region": "SG",
        "status": "Completed",
        "payment_method": "Card",
    }


def build_xlsx(rows):
    """Builds a minimal valid sales xlsx in-memory for router/service tests."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Order ID", "Order Date", "Platform", "SKU", "Product Name", "Quantity", "Unit Price", "Total Amount"])
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# --- storage.filename_already_ingested ---


def test_filename_already_ingested_is_false_when_nothing_ingested():
    assert storage.filename_already_ingested("sales.xlsx") is False


def test_filename_already_ingested_is_true_after_saving_that_filename():
    storage.save_records([make_record("O1")], source_filename="sales.xlsx")

    assert storage.filename_already_ingested("sales.xlsx") is True


def test_filename_already_ingested_is_false_for_a_different_filename():
    storage.save_records([make_record("O1")], source_filename="sales.xlsx")

    assert storage.filename_already_ingested("other.xlsx") is False


# --- storage.save_records replace behaviour ---


def test_save_records_without_replace_appends_alongside_existing_rows():
    storage.save_records([make_record("O1")], source_filename="sales.xlsx")
    storage.save_records([make_record("O2")], source_filename="sales.xlsx")

    records = storage.get_recent_records(limit=10)
    assert sorted(records["order_id"].tolist()) == ["O1", "O2"]


def test_save_records_with_replace_deletes_existing_rows_for_that_filename_first():
    storage.save_records([make_record("O1")], source_filename="sales.xlsx")
    storage.save_records([make_record("O2")], source_filename="sales.xlsx", replace=True)

    records = storage.get_recent_records(limit=10)
    assert records["order_id"].tolist() == ["O2"]


def test_save_records_with_replace_only_deletes_rows_for_that_filename():
    storage.save_records([make_record("O1")], source_filename="sales-a.xlsx")
    storage.save_records([make_record("O2")], source_filename="sales-b.xlsx", replace=True)

    records = storage.get_recent_records(limit=10)
    assert sorted(records["order_id"].tolist()) == ["O1", "O2"]


# --- services.ingest.process_excel_file ---


def test_process_excel_file_ingests_normally_when_filename_is_new():
    result = process_excel_file(build_xlsx([["O1", "2026-01-01", "Shopee", "SKU-A", "Widget A", 1, 10.0, 10.0]]), "sales.xlsx")

    assert result["duplicate"] is False
    assert result["rows_ingested"] == 1
    assert storage.filename_already_ingested("sales.xlsx") is True


def test_process_excel_file_returns_duplicate_without_parsing_when_already_ingested():
    storage.save_records([make_record("O1")], source_filename="sales.xlsx")

    # Deliberately garbage bytes: if this were parsed as an .xlsx, it would raise.
    result = process_excel_file(io.BytesIO(b"not a real spreadsheet"), "sales.xlsx")

    assert result == {
        "filename": "sales.xlsx",
        "duplicate": True,
        "message": "'sales.xlsx' has already been ingested. Confirm to overwrite the existing data.",
    }


def test_process_excel_file_overwrites_existing_data_when_overwrite_is_true():
    storage.save_records([make_record("O1")], source_filename="sales.xlsx")

    result = process_excel_file(
        build_xlsx([["O2", "2026-01-02", "Shopee", "SKU-A", "Widget A", 1, 20.0, 20.0]]),
        "sales.xlsx",
        overwrite=True,
    )

    assert result["duplicate"] is False
    assert result["rows_ingested"] == 1
    records = storage.get_recent_records(limit=10)
    assert records["order_id"].tolist() == ["O2"]


# --- POST /api/ingest ---


def test_uploading_a_new_filename_ingests_successfully():
    xlsx = build_xlsx([["O1", "2026-01-01", "Shopee", "SKU-A", "Widget A", 1, 10.0, 10.0]])

    res = client.post("/api/ingest", files={"file": ("sales.xlsx", xlsx, XLSX_MEDIA_TYPE)})

    assert res.status_code == 200
    body = res.json()
    assert body["duplicate"] is False
    assert body["rows_ingested"] == 1


def test_uploading_the_same_filename_again_returns_409_and_does_not_change_data():
    first = build_xlsx([["O1", "2026-01-01", "Shopee", "SKU-A", "Widget A", 1, 10.0, 10.0]])
    client.post("/api/ingest", files={"file": ("sales.xlsx", first, XLSX_MEDIA_TYPE)})

    second = build_xlsx([["O2", "2026-01-02", "Shopee", "SKU-A", "Widget A", 1, 20.0, 20.0]])
    res = client.post("/api/ingest", files={"file": ("sales.xlsx", second, XLSX_MEDIA_TYPE)})

    assert res.status_code == 409
    body = res.json()
    assert body["duplicate"] is True
    assert body["filename"] == "sales.xlsx"

    records = storage.get_recent_records(limit=10)
    assert records["order_id"].tolist() == ["O1"]


def test_uploading_the_same_filename_with_overwrite_replaces_the_data():
    first = build_xlsx([["O1", "2026-01-01", "Shopee", "SKU-A", "Widget A", 1, 10.0, 10.0]])
    client.post("/api/ingest", files={"file": ("sales.xlsx", first, XLSX_MEDIA_TYPE)})

    second = build_xlsx([["O2", "2026-01-02", "Shopee", "SKU-A", "Widget A", 1, 20.0, 20.0]])
    res = client.post(
        "/api/ingest",
        files={"file": ("sales.xlsx", second, XLSX_MEDIA_TYPE)},
        data={"overwrite": "true"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["duplicate"] is False
    assert body["rows_ingested"] == 1

    records = storage.get_recent_records(limit=10)
    assert records["order_id"].tolist() == ["O2"]
