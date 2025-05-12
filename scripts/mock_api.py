from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
import asyncio
import json
from datetime import datetime, timezone

app = FastAPI(title="Mock Mount Doom API")

# In-memory store for processed results and stats
processed_count = 0

# Reduced mock transcripts for Gemini quota-safe testing
sample_transcripts = [
    {
        "transcript_id": f"t-mock-{i}",
        "session_id": f"sess-mock-{i}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_type": "customer_service",
        "duration_seconds": 120 + i,
        "participants": {"agent": "Doom Services AI", "customer": f"User{i}"},
        "transcript_text": [
            {
                "speaker": "agent",
                "text": "Hello! Welcome to Mount Doom tours.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "speaker": "customer",
                "text": "I want to book a hike.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ],
        "metadata": {
            "questionnaire": {"purpose_of_visit_asked": True, "gear_discussed": False},
            "visitor_interest_level": "high",
            "mount_doom_permit_status": "pending",
            "language": "en"
        }
    }
    for i in range(1, 3)  # Only 2 transcripts for quota-safe testing
]

@app.post("/api/auth")
async def auth(body: dict):
    api_key = body.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key required")
    return {"token": "mock-token"}

@app.get("/api/v1/transcripts/stream")
async def stream_transcripts(request: Request):
    async def event_generator():
        for transcript in sample_transcripts:
            if await request.is_disconnected():
                break
            yield json.dumps(transcript).encode('utf-8') + b"\n"
            await asyncio.sleep(0.2)
    return StreamingResponse(event_generator(), media_type="application/json")

@app.post("/api/v1/transcripts/process")
async def process_transcript(body: dict):
    global processed_count
    processed_count += 1
    return {"status": "ok", "transcript_id": body.get("transcript_id")}

@app.get("/api/v1/stats")
async def get_stats():
    return {"processed_count": processed_count}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "time": datetime.now(timezone.utc).isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
