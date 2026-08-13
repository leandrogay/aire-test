from fastapi import APIRouter
from app.services import storage

router = APIRouter()


@router.get("/api/sales")
def get_sales_dashboard(limit: int = 50):
    recent = storage.get_recent_records(limit=limit)
    stats = storage.get_summary_stats()
    return {
        "stats": stats,
        "records": recent.to_dict(orient="records") if not recent.empty else [],
    }