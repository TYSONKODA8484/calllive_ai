import os
import logging
from dotenv import load_dotenv

# Attempt to import the Google Gemini SDK; allow running in mock mode without it
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Load environment variables from .env
load_dotenv()

# Configure logging
logger = logging.getLogger("summarizer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Feature flag: mock summaries to avoid Gemini quota issues
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"

# Gemini setup only if mock is off
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not USE_MOCK_LLM:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env file")
    if not genai:
        raise ImportError("google-generativeai SDK is required for real summarization")
    genai.configure(api_key=GEMINI_API_KEY)
    genai_model = genai.GenerativeModel("gemini-1.5-flash")
else:
    genai_model = None


def get_summary_from_transcript(transcript_turns: list[str]) -> str:
    """
    Generate a concise summary of a customer-agent conversation.
    Falls back to mock text or error message if LLM fails.
    """
    if USE_MOCK_LLM:
        logger.info("[summarizer] Mock summary mode enabled; returning placeholder.")
        return "Customer expressed interest in Mount Doom hike and requested booking details."

    full_text = "\n".join(transcript_turns)
    prompt = f"""
You are a helpful travel assistant for a volcanic tourism bureau.
Summarize the following conversation in 3-4 sentences, focusing on visitor intent, concerns, and suggested next steps.

Conversation:
{full_text}

Return only the summary text without additional formatting.
""".strip()

    try:
        response = genai_model.generate_content(prompt)
        summary = response.text.strip()
        return summary
    except Exception as e:
        logger.error(f"[summarizer] Summarization failed: {e}")
        return "Summary unavailable due to an error."


# Quick manual test
if __name__ == "__main__":
    sample_conversation = [
        "agent: Hello, this is Doom Services AI. How can I assist today?",
        "customer: I'm interested in visiting Mount Doom but unsure about safety.",
        "agent: What gear do you currently have?",
        "customer: Just regular hiking boots."
    ]
    print(get_summary_from_transcript(sample_conversation))
