import os
import asyncio
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
dotenv_loaded = load_dotenv()

# Configure logging
logger = logging.getLogger("db")
logging.basicConfig(level=logging.INFO)

# Error tracking file
ERRORS_FILE = "errors.json"

# Determine storage mode: MongoDB or JSON fallback
MONGO_URI = os.getenv("MONGODB_URI")
USE_MONGO = False
_raw_collection = None
_processed_collection = None

# Attempt MongoDB connection
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

# JSON file paths for fallback
RAW_JSON_FILE = "raw_transcripts.json"
PROCESSED_JSON_FILE = "processed_results.json"

async def save_raw_transcript(transcript: dict) -> None:
    """
    Save raw transcript to MongoDB or append to JSON file.
    """
    if USE_MONGO and _raw_collection:
        try:
            await asyncio.to_thread(_raw_collection.insert_one, transcript)
            logger.info(f"Saved raw transcript {transcript.get('transcript_id')} to MongoDB.")
        except Exception as e:
            logger.error(f"Failed to save raw transcript to MongoDB: {e}")
    else:
        entry = {
            **transcript,
            "saved_timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }
        try:
            await asyncio.to_thread(
                lambda: open(RAW_JSON_FILE, "a").write(json.dumps(entry) + "\n")
            )
            logger.info(f"Saved raw transcript {transcript.get('transcript_id')} to JSON file.")
        except Exception as e:
            logger.error(f"Failed to save raw transcript to JSON file: {e}")

async def save_processed_result(result: dict) -> None:
    """
    Save processed result to MongoDB or append to JSON file.
    """
    if USE_MONGO and _processed_collection:
        try:
            await asyncio.to_thread(_processed_collection.insert_one, result)
            logger.info(f"Saved processed result {result.get('transcript_id')} to MongoDB.")
        except Exception as e:
            logger.error(f"Failed to save processed result to MongoDB: {e}")
    else:
        try:
            await asyncio.to_thread(
                lambda: open(PROCESSED_JSON_FILE, "a").write(json.dumps(result) + "\n")
            )
            logger.info(f"Saved processed result {result.get('transcript_id')} to JSON file.")
        except Exception as e:
            logger.error(f"Failed to save processed result to JSON file: {e}")

async def save_error(error_entry: dict) -> None:
    """
    Append an error record to the errors JSON file.
    """
    try:
        await asyncio.to_thread(
            lambda: open(ERRORS_FILE, "a").write(json.dumps(error_entry) + "\n")
        )
        logger.error(f"Logged pipeline error: {error_entry}")
    except Exception as e:
        logger.error(f"Failed to save error to JSON file: {e}")
