import os
import sys
import asyncio
import time
from dotenv import load_dotenv

# Ensure project root is on PYTHONPATH so we can import src modules
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure mock LLM and JSON fallback storage
os.environ["USE_MOCK_LLM"] = "true"
load_dotenv()

# Import your processing modules
from src.processing.summarizer import get_summary_from_transcript
from src.processing.extractor import get_structured_data
from src.processing.analyzer import analyze_insights

async def worker(queue: asyncio.Queue):
    """
    Worker coroutine: pulls transcripts off the queue, processes them end-to-end,
    but skips actual HTTP submission/storage for speed measurement.
    """
    while True:
        transcript = await queue.get()
        try:
            # Build transcript_turns list of strings
            transcript_turns = [turn["text"] for turn in transcript["transcript_text"]]
            # Summarize
            _ = get_summary_from_transcript(transcript_turns)
            # Extract structured data
            structured = get_structured_data(transcript_turns, transcript.get("metadata", {}))
            # Analyze insights
            _ = analyze_insights(transcript_turns, structured)
        except Exception:
            pass
        finally:
            queue.task_done()

async def run_performance_test(num_transcripts: int = 1000, num_workers: int = 10):
    # Create dummy transcripts
    transcripts = []
    for i in range(num_transcripts):
        transcripts.append({
            "transcript_id": f"perf-{i}",
            "transcript_text": [
                {"text": "agent: Hello there!"},
                {"text": "customer: Hi! Interested in a tour."}
            ],
            "metadata": {
                "questionnaire": {},
                "mount_doom_permit_status": "pending"
            }
        })

    queue = asyncio.Queue()
    # Start worker tasks
    workers = [asyncio.create_task(worker(queue)) for _ in range(num_workers)]

    start_time = time.perf_counter()
    # Enqueue all transcripts
    for t in transcripts:
        await queue.put(t)

    # Wait until queue is fully processed
    await queue.join()
    elapsed = time.perf_counter() - start_time

    print(f"Processed {num_transcripts} transcripts in {elapsed:.2f} seconds using {num_workers} workers.")

    # Cancel worker tasks
    for w in workers:
        w.cancel()

if __name__ == "__main__":
    # Adjust counts here if desired
    asyncio.run(run_performance_test(num_transcripts=1000, num_workers=10))
