import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sales.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
TABLE_NAME = "sales_records"

def get_connection():
    return sqlite3.connect(DB_PATH)


def _sanitize(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN/NaT with None so the dataframe is safe to JSON-serialise."""
    return df.astype(object).where(pd.notnull(df), None)


def save_records(records: list[dict], source_filename: str):
    if not records:
        return
    df = pd.DataFrame(records)
    df["ingested_at"] = datetime.utcnow().isoformat()
    df["source_filename"] = source_filename
    conn = get_connection()
    df.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
    conn.close()


def get_recent_records(limit: int = 100):
    conn = get_connection()
    try:
        df = pd.read_sql(
            f"SELECT * FROM {TABLE_NAME} ORDER BY ingested_at DESC LIMIT ?",
            conn, params=(limit,),
        )
    except pd.errors.DatabaseError:
        df = pd.DataFrame()
    conn.close()
    return _sanitize(df)


def get_summary_stats():
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    except pd.errors.DatabaseError:
        df = pd.DataFrame()
    conn.close()

    if df.empty:
        return {"total_orders": 0, "total_revenue": 0, "by_platform": []}

    by_platform = (
        df.groupby("platform")["total_amount"].sum().round(2)
        .reset_index().rename(columns={"total_amount": "revenue"})
        .sort_values("revenue", ascending=False)
    )
    by_platform = _sanitize(by_platform).to_dict(orient="records")

    return {
        "total_orders": int(len(df)),
        "total_revenue": float(round(df["total_amount"].sum(), 2)),
        "by_platform": by_platform,
    }

def getSkuRanking(metric: str = "value", order: str = "desc") -> pd.DataFrame:
    SKU_RANKING_METRICS = ("volume", "value")
    SKU_RANKING_COLUMNS = ["sku", "product_name", "volume", "value", "rank"]
    #Aggregate ingested sales records by SKU, ranked by total units sold (volume) or total revenue (value).
    if metric not in SKU_RANKING_METRICS:
        raise ValueError(f"metric must be one of {SKU_RANKING_METRICS}")
    if order not in ("asc", "desc"):
        raise ValueError("order must be 'asc' or 'desc'")

    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    except pd.errors.DatabaseError:
        df = pd.DataFrame()
    conn.close()

    df = df[df["sku"].notna()] if not df.empty else df
    if df.empty:
        return pd.DataFrame(columns=SKU_RANKING_COLUMNS)

    ranked = (
        df.groupby("sku")
        .agg(
            product_name=("product_name", "first"),
            volume=("quantity", "sum"),
            value=("total_amount", "sum"),
        )
        .reset_index()
    )
    ranked["value"] = ranked["value"].round(2)
    ranked = ranked.sort_values(metric, ascending=(order == "asc")).reset_index(drop=True)
    ranked["rank"] = ranked.index + 1

    return ranked[SKU_RANKING_COLUMNS]