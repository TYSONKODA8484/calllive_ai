import os
import asyncio
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("db")
logging.basicConfig(level=logging.INFO)

# Determine storage mode
MONGO_URI = os.getenv("MONGODB_URI")
USE_MONGO = False
_raw_collection = None
_processed_collection = None

# Try connecting to MongoDB
try:
    from pymongo import MongoClient
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsAllowInvalidCertificates=True
    )
    client.admin.command("ping")
    db = client.get_database("calllive")
    _raw_collection = db.get_collection("raw_transcripts")
    _processed_collection = db.get_collection("processed_results")
    USE_MONGO = True
    logger.info("Connected to MongoDB successfully.")
except Exception as e:
    USE_MONGO = False
    logger.error(f"MongoDB connection failed: {e}. Falling back to JSON storage.")

# File-based fallback
RAW_JSON_FILE = "raw_transcripts.json"
PROCESSED_JSON_FILE = "processed_results.json"

async def save_raw_transcript(transcript: dict) -> None:
    """
    Save raw transcript to MongoDB or JSON.
    """
    if USE_MONGO and _raw_collection:
        try:
            await asyncio.to_thread(_raw_collection.insert_one, transcript)
            logger.info(f"Saved raw transcript {transcript.get('transcript_id')} to MongoDB.")
        except Exception as e:
            logger.error(f"Failed to save raw transcript to MongoDB: {e}")
    else:
        try:
            entry = {
                **transcript,
                "saved_timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            }
            def write_json():
                with open(RAW_JSON_FILE, "a") as f:
                    f.write(json.dumps(entry) + "\n")
            await asyncio.to_thread(write_json)
            logger.info(f"Saved raw transcript {transcript.get('transcript_id')} to JSON file.")
        except Exception as e:
            logger.error(f"Failed to save raw transcript to JSON file: {e}")

async def save_processed_result(result: dict) -> None:
    """
    Save processed result to MongoDB or JSON.
    """
    if USE_MONGO and _processed_collection:
        try:
            await asyncio.to_thread(_processed_collection.insert_one, result)
            logger.info(f"Saved processed result {result.get('transcript_id')} to MongoDB.")
        except Exception as e:
            logger.error(f"Failed to save processed result to MongoDB: {e}")
    else:
        try:
            def write_json():
                with open(PROCESSED_JSON_FILE, "a") as f:
                    f.write(json.dumps(result) + "\n")
            await asyncio.to_thread(write_json)
            logger.info(f"Saved processed result {result.get('transcript_id')} to JSON file.")
        except Exception as e:
            logger.error(f"Failed to save processed result to JSON file: {e}")
