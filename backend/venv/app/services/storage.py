import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
from google.cloud import bigquery

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sales.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
TABLE_NAME = "sales_records"

SKU_RANKING_METRICS = ("volume", "value")
SKU_RANKING_COLUMNS = ["sku", "product_name", "volume", "value", "rank"]
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
WEEK_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Read-only reference data in the client's own warehouse. Never written to.
BQ_TABLE = os.environ.get("BQ_SELLOUT_TABLE", "aire-data.Aire_Data.sellout")


def get_bigquery_client(project="aire-data") -> bigquery.Client:
    return bigquery.Client(project=project)

def get_connection():
    return sqlite3.connect(DB_PATH)


def _sanitize(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN/NaT with None so the dataframe is safe to JSON-serialise."""
    return df.astype(object).where(pd.notnull(df), None)


def save_records(records: list[dict], source_filename: str, replace: bool = False):
    if replace:
        delete_records_by_filename(source_filename)
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

def get_available_ranking_months() -> list[str]:
    #Distinct calendar months (YYYY-MM, most recent first) with weekly sellout data, derived from each week's start date. 
    # Powers the month picker on the SKU ranking view."""
    query = f"""
        SELECT DISTINCT FORMAT_DATE('%Y-%m', period_start) AS month
        FROM `{BQ_TABLE}`
        WHERE period_type = 'week'
        ORDER BY month DESC
    """
    client = get_bigquery_client()
    df = client.query(query).result().to_dataframe()
    return df["month"].tolist() if not df.empty else []


def get_available_ranking_weeks(month: str) -> list[dict]:
    #Distinct weeks within the given calendar month, labelled "Week 1","Week 2", etc. relative to that month. #Powers the week picker that lets staff drill from a month into a single week. The table's own period_label numbers weeks continuously across the whole year (e.g. "Week 32" in early August), so it's not used here, the week number is computed from each week's ordinal position within the selected month instead.
    if not month or not MONTH_PATTERN.match(month):
        raise ValueError("month must be in YYYY-MM format")

    query = f"""
        SELECT DISTINCT period_start
        FROM `{BQ_TABLE}`
        WHERE period_type = 'week' AND FORMAT_DATE('%Y-%m', period_start) = @month
        ORDER BY period_start
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("month", "STRING", month)]
    )

    client = get_bigquery_client()
    df = client.query(query, job_config=job_config).result().to_dataframe()

    if df.empty:
        return []

    return [
        {
            "value": str(row["period_start"]),
            "label": f"Week {i} ({pd.to_datetime(row['period_start']).strftime('%d-%m-%Y')})",
        }
        for i, (_, row) in enumerate(df.iterrows(), start=1)
    ]


def get_sku_ranking(
    metric: str = "value", order: str = "desc", month: str | None = None, week: str | None = None
) -> pd.DataFrame:
    #Ranks SKUs from the client's BigQuery sellout table by total units sold (volume) or total revenue (value), for a single calendar month or, optionally, a single week within it.

    #A month is required and rows are always restricted to period_type = 'week': the source table can hold multiple granularities of the same underlying data, so summing across them (or across months) would double-count. Weeks are bucketed into the calendar month their start date falls in. Passing `week` (a period_start date) narrows further to that single week instead of summing the whole month.

    #`revenue` in the source table is only populated for FairPrice rows, so SKUs sold solely through other retailers report value=0 rather than being dropped or raising on a null.
    
    if metric not in SKU_RANKING_METRICS:
        raise ValueError(f"metric must be one of {SKU_RANKING_METRICS}")
    if order not in ("asc", "desc"):
        raise ValueError("order must be 'asc' or 'desc'")
    if not month or not MONTH_PATTERN.match(month):
        raise ValueError("month must be in YYYY-MM format")
    if week is not None and not WEEK_PATTERN.match(week):
        raise ValueError("week must be in YYYY-MM-DD format")

    sql_order = "ASC" if order == "asc" else "DESC"
    where_clauses = [
        "sku IS NOT NULL",
        "period_type = 'week'",
        "FORMAT_DATE('%Y-%m', period_start) = @month",
    ]
    query_parameters = [bigquery.ScalarQueryParameter("month", "STRING", month)]
    if week:
        where_clauses.append("period_start = @week")
        query_parameters.append(bigquery.ScalarQueryParameter("week", "DATE", week))

    query = f"""
        SELECT
          sku,
          ANY_VALUE(product_name) AS product_name,
          IFNULL(SUM(quantity_units), 0) AS volume,
          IFNULL(SUM(revenue), 0) AS value
        FROM `{BQ_TABLE}`
        WHERE {' AND '.join(where_clauses)}
        GROUP BY sku
        ORDER BY {metric} {sql_order}
    """
    job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)

    client = get_bigquery_client()
    ranked = client.query(query, job_config=job_config).result().to_dataframe()

    if ranked.empty:
        return pd.DataFrame(columns=SKU_RANKING_COLUMNS)

    ranked["value"] = ranked["value"].round(2)
    ranked = ranked.reset_index(drop=True)
    ranked["rank"] = ranked.index + 1

    return ranked[SKU_RANKING_COLUMNS]