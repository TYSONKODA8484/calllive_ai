import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Import API client and processing/storage modules
from src.api.client import MordorAPIClient
from src.processing.summarizer import get_summary_from_transcript
from src.processing.extractor import get_structured_data
from src.processing.analyzer import analyze_insights
from src.storage.db import save_raw_transcript, save_processed_result

# Import queue utilities
from src.queue.queue import create_queue, start_workers, enqueue_item, wait_for_completion

# Configure logging for observability
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Number of concurrent workers (configurable via .env)
WORKER_COUNT = int(os.getenv("WORKER_COUNT", 5))
QUEUE_MAXSIZE = int(os.getenv("QUEUE_MAXSIZE", 100))

async def process_worker(queue: asyncio.Queue, client: MordorAPIClient):
    """
    Worker coroutine to process transcripts from the queue.
    """
    while True:
        transcript = await queue.get()
        transcript_id = transcript.get("transcript_id")
        logging.info(f"[worker] Processing transcript {transcript_id}")

        # Prepare data for processing
        transcript_turns = [f"{turn['speaker']}: {turn['text']}" for turn in transcript.get('transcript_text', [])]
        metadata = transcript.get('metadata', {})

        # 1. Save raw transcript
        await save_raw_transcript(transcript)

        # 2. Generate summary (run in thread to avoid blocking)
        summary = await asyncio.to_thread(get_summary_from_transcript, transcript_turns)

        # 3. Extract structured data
        structured = await asyncio.to_thread(get_structured_data, transcript_turns, metadata)

        # 4. Analyze insights
        analysis = await asyncio.to_thread(analyze_insights, transcript_turns, structured)

        # Build the result payload
        result = {
            "transcript_id": transcript_id,
            "summary": summary,
            "structured_data": structured,
            "analysis": analysis,
            "processing_timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # 5. Save processed result
        await save_processed_result(result)

        # 6. Submit to API
        try:
            response = await client.submit_processed_result(result)
            logging.info(f"[worker] Submitted {transcript_id}: {response}")
        except Exception as e:
            logging.error(f"[worker] Submission failed for {transcript_id}: {e}")

        queue.task_done()

async def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("CALLLIVE_API_KEY")
    base_url = os.getenv("CALLLIVE_BASE_URL")

    if not api_key or not base_url:
        logging.error("CALLLIVE_API_KEY or CALLLIVE_BASE_URL not set in .env")
        return

    # Authenticate with the CallLive API
    client = MordorAPIClient(api_key, base_url)
    if not await client.authenticate():
        logging.error("Authentication failed. Exiting.")
        return

    # Initialize queue and start workers
    queue = create_queue(maxsize=QUEUE_MAXSIZE)
    start_workers(queue, process_worker, client, WORKER_COUNT)

    # Stream transcripts and enqueue for processing
    async for transcript in client.receive_transcripts():
        logging.info(f"[main] Enqueuing transcript {transcript.get('transcript_id')}")
        enqueue_item(queue, transcript)

    # Wait until all enqueued items are processed
    await wait_for_completion(queue)

if __name__ == "__main__":
    asyncio.run(main())
