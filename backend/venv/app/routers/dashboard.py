from fastapi import APIRouter, HTTPException
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

@router.get("/api/sales/skus")
def getSkuRanking(metric: str = "value", order: str = "desc"):
    try:
        ranked = storage.getSkuRanking(metric=metric, order=order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "metric": metric,
        "order": order,
        "skus": ranked.to_dict(orient="records") if not ranked.empty else [],
    }