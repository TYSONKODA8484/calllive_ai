import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.storage.db import RAW_JSON_FILE, PROCESSED_JSON_FILE, ERRORS_FILE

app = FastAPI(title="Mount Doom Pipeline Monitor")


def count_lines(path: str) -> int:
    try:
        with open(path, 'r') as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0

@app.get("/monitor/raw_count")
async def raw_count():
    """Number of raw transcripts saved so far."""
    return JSONResponse({"raw_count": count_lines(RAW_JSON_FILE)})

@app.get("/monitor/processed_count")
async def processed_count():
    """Number of processed results saved so far."""
    return JSONResponse({"processed_count": count_lines(PROCESSED_JSON_FILE)})

@app.get("/monitor/pending")
async def pending_count():
    """Approximate queue size: raw_count - processed_count."""
    raw = count_lines(RAW_JSON_FILE)
    processed = count_lines(PROCESSED_JSON_FILE)
    pending = max(0, raw - processed)
    return JSONResponse({"pending_count": pending})

@app.get("/monitor/errors")
async def error_count():
    """Number of pipeline errors logged so far."""
    count = count_lines(ERRORS_FILE)
    return JSONResponse({"error_count": count})

# To run:
# uvicorn src.monitor:app --reload --port 9000
