import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

from src.api.client import MordorAPIClient
from src.processing.summarizer import get_summary_from_transcript
from src.processing.extractor import get_structured_data
from src.processing.analyzer import analyze_insights
from src.storage.db import save_raw_transcript, save_processed_result, save_error

# Load environment
load_dotenv()
CALLLIVE_API_KEY = os.getenv("CALLLIVE_API_KEY")
CALLLIVE_BASE_URL = os.getenv("CALLLIVE_BASE_URL")
if not CALLLIVE_API_KEY or not CALLLIVE_BASE_URL:
    logging.error("CALLLIVE_API_KEY or CALLLIVE_BASE_URL not set in .env")
    raise SystemExit(1)

# Configure logging
tlogging = logging.getLogger()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Rate limiter for submissions
class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self._semaphore = asyncio.Semaphore(max_calls)
        self._max = max_calls
        self._period = period
        asyncio.create_task(self._refill())

    async def _refill(self):
        while True:
            await asyncio.sleep(self._period)
            to_release = self._max - self._semaphore._value
            for _ in range(to_release):
                self._semaphore.release()

    async def acquire(self):
        await self._semaphore.acquire()

async def process_worker(client: MordorAPIClient, rate_limiter: RateLimiter, queue: asyncio.Queue):
    while True:
        transcript = await queue.get()
        transcript_id = transcript.get("transcript_id")
        logging.info(f"[worker] Processing transcript {transcript_id}")
        try:
            # 1. Save raw transcript
            await save_raw_transcript(transcript)

            # 2. Summarize, extract, analyze
            turns = [turn["text"] for turn in transcript.get("transcript_text", [])]
            summary = get_summary_from_transcript(turns)
            structured = get_structured_data(turns, transcript.get("metadata", {}))
            analysis = analyze_insights(turns, structured)

            # 3. Build result payload
            result = {
                "transcript_id": transcript_id,
                "summary": summary,
                "structured_data": structured,
                "analysis": {
                    **analysis,
                    "processing_timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }

            # 4. Save processed result
            await save_processed_result(result)

            # 5. Throttle and submit to API
            await rate_limiter.acquire()
            response = await client.submit_processed_result(result)
            logging.info(f"[worker] Submitted {transcript_id}: {response}")
        except Exception as e:
            # Log and record the error
            error_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "transcript_id": transcript_id,
                "error": str(e)
            }
            await save_error(error_entry)
            logging.error(f"[worker] Error processing {transcript_id}: {e}")
        finally:
            queue.task_done()

async def main():
    # Initialize API client and authenticate
    client = MordorAPIClient(CALLLIVE_API_KEY, CALLLIVE_BASE_URL)
    if not await client.authenticate():
        logging.error("Authentication failed. Exiting.")
        return

    # Setup queue and rate limiter
    queue = asyncio.Queue()
    rate_limiter = RateLimiter(100, 60)  # 100 submits per 60 seconds

    # Launch worker tasks
    workers = [asyncio.create_task(process_worker(client, rate_limiter, queue)) for _ in range(10)]

    # Stream and enqueue transcripts
    async for transcript in client.receive_transcripts():
        tid = transcript.get("transcript_id")
        logging.info(f"[main] Enqueuing transcript {tid}")
        await queue.put(transcript)

    # Wait for all tasks to finish
    await queue.join()
    for w in workers:
        w.cancel()

if __name__ == "__main__":
    asyncio.run(main())
