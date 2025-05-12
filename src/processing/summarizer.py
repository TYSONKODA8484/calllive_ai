import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

def get_summary_from_transcript(transcript_turns: list[str]) -> str:
    """
    Generate a concise summary of a customer-agent conversation using Gemini Flash.

    Args:
        transcript_turns: A list of strings, each representing a line of dialogue.

    Returns:
        A summary paragraph as a string.
    """
    full_text = "\n".join(transcript_turns)

    prompt = f"""
You are a helpful travel assistant working with a volcanic tourism bureau.
Summarize the following conversation into 4-5 sentences, focusing on visitor intent, concerns, and next steps.

Transcript:
{full_text}
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        # Graceful fallback with logging
        print(f"[summarizer] Gemini summarization failed: {e}")
        return ""  # Return empty string to allow continuation


# Example
if __name__ == "__main__":
    sample = [
        "agent: Hello, this is Doom Services AI. I understand you're interested in visiting Mount Doom.",
        "customer: Yes! I'm really excited but a bit worried about what to bring.",
        "agent: Safety is key — do you have mountaineering experience?",
        "customer: Not really... this is my first real volcano hike."
    ]
    print(get_summary_from_transcript(sample))
