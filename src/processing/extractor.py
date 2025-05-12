import os
import re
import json
import logging
from dotenv import load_dotenv

# Attempt to import the Google Gemini SDK; allow running in mock mode without it
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("extractor")

# Feature flag: use mock extractor outputs to avoid Gemini quota issues (optional)
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"

# Gemini setup only if mock is off
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not USE_MOCK_LLM:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env file")
    if not genai:
        raise ImportError("google-generativeai SDK is required for real extraction")
    genai.configure(api_key=GEMINI_API_KEY)
    # Use Gemini 2.0 Flash Lite for higher rate limits
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
else:
    model = None


def get_structured_data(transcript_turns: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured visitor details and questionnaire completion status.

    Returns keys:
    - visitor_details
    - questionnaire_completion
    """
    # Mock fallback
    if USE_MOCK_LLM:
        logger.info("[extractor] Mock extractor mode enabled; returning placeholder.")
        return {
            "visitor_details": {
                "ring_bearer": False,
                "gear_prepared": False,
                "hazard_knowledge": "none",
                "fitness_level": "medium",
                "permit_status": metadata.get("mount_doom_permit_status", "pending")
            },
            "questionnaire_completion": metadata.get("questionnaire", {})
        }

    full_text = "\n".join(transcript_turns)
    questionnaire_json = json.dumps(metadata.get("questionnaire", {}), indent=2)

    prompt = f"""
You are an expert data extractor for a volcanic tourism bureau.
Extract EXACTLY and ONLY a valid JSON object with two keys:

1. visitor_details: {{
     "ring_bearer": true or false,
     "gear_prepared": true or false,
     "hazard_knowledge": "none" or "limited" or "basic" or "advanced",
     "fitness_level": "low" or "medium" or "high",
     "permit_status": "pending" or "approved" or "denied"
   }}

2. questionnaire_completion: Copy the JSON object below exactly as-is with boolean values:
{questionnaire_json}

Conversation:
{full_text}

Return only the JSON object without any additional text, markdown, or comments.
""".strip()

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        cleaned = re.sub(r"^```(?:json)?|```$", "", response_text, flags=re.MULTILINE).strip()
        return json.loads(cleaned)

    except Exception as e:
        logger.error(f"[extractor] Gemini extraction failed: {e}")
        # Graceful fallback
        return {
            "visitor_details": {
                "ring_bearer": None,
                "gear_prepared": None,
                "hazard_knowledge": None,
                "fitness_level": None,
                "permit_status": metadata.get("mount_doom_permit_status", "pending")
            },
            "questionnaire_completion": metadata.get("questionnaire", {})
        }

# Example usage
if __name__ == "__main__":
    sample_convo = [
        "agent: Do you have your permit?",
        "customer: I'm applying now."
    ]
    sample_meta = {
        "questionnaire": {"purpose_of_visit_asked": True, "gear_discussed": False},
        "mount_doom_permit_status": "pending"
    }

    result = get_structured_data(sample_convo, sample_meta)
    print("Structured Data:", json.dumps(result, indent=2))
