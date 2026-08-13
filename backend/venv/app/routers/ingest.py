import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ingest import process_excel_file

router = APIRouter()


@router.post("/api/ingest")
async def ingest_sales_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls files are supported.")

    contents = await file.read()
    try:
        result = process_excel_file(io.BytesIO(contents), file.filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to process file: {str(e)}")

    return result