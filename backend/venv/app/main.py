from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from app.routers import ingest, dashboard

app = FastAPI()

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(dashboard.router)


@app.get("/")
def read_root():
    return {"status": "ok"}

# Simple GET with a path parameter
@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id, "message": f"You requested item {item_id}"}

# Simple GET with a query parameter
@app.get("/greet")
def greet(name: str = "world"):
    return {"message": f"Hello, {name}!"}

# POST endpoint that accepts a JSON body
@app.post("/echo")
def echo(payload: dict):
    return {"you_sent": payload}

# Test that pandas is working correctly
@app.get("/sample-data")
def sample_data():
    df = pd.DataFrame({
        "product": ["Widget A", "Widget B", "Widget C"],
        "sales": [120, 85, 200]
    })
    return df.to_dict(orient="records")