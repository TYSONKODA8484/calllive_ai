# Sentiment analysis
import os
import re
import json
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analyzer")

# Load environment variables
load_dotenv()

# Configure Gemini with your API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set in .env file")
genai.configure(api_key=api_key)

# Instantiate the model (Gemini Flash for speed)
model = genai.GenerativeModel("gemini-1.5-flash")

def analyze_insights(transcript_turns: list[str], structured_data: dict) -> dict:
    """
    Analyze conversation insights: sentiment, interest level, preparedness, and action items.
    """
    conversation_text = "\n".join(transcript_turns)
    structured_json = json.dumps(structured_data)

    prompt = f"""
You are an assistant that analyzes visitor conversations for a volcanic tourism bureau.
Based on the conversation and structured visitor details, return ONLY a valid JSON object with:

1. sentiment: a float between 0.0 (negative) and 1.0 (positive)
2. interest_level: "low", "medium", or "high"
3. preparedness_level: "low", "medium", or "high"
4. action_items: an array of brief follow-up action items (strings)

Conversation:
{conversation_text}

Structured Visitor Details:
{structured_json}

Return just the JSON object with these keys, no additional text.
""".strip()

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        cleaned = re.sub(r"^```json\s*|\s*```$", "", response_text, flags=re.MULTILINE).strip()
        return json.loads(cleaned)

    except Exception as e:
        logger.error(f"[analyzer] Analysis failed: {e}")
        # Do not reference `response_text` if not set
        return {
            "sentiment": 0.5,
            "interest_level": "medium",
            "preparedness_level": "medium",
            "action_items": []
        }

# Example usage
if __name__ == "__main__":
    sample_convo = [
        "agent: Do you have safety gear?",
        "customer: Yes, I have helmets and ropes."
    ]
    sample_structured = {
        "visitor_details": {"gear_prepared": True},
        "questionnaire_completion": {"gear_discussed": True}
    }
    result = analyze_insights(sample_convo, sample_structured)
    print("Analysis:", result)
