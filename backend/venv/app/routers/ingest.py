import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from app.services.ingest import process_excel_file

router = APIRouter()


@router.post("/api/ingest")
async def ingest_sales_file(file: UploadFile = File(...), overwrite: bool = Form(False)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls files are supported.")

    contents = await file.read()
    try:
        result = process_excel_file(io.BytesIO(contents), file.filename, overwrite=overwrite)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to process file: {str(e)}")

    if result.get("duplicate"):
        return JSONResponse(status_code=409, content=result)

    return result