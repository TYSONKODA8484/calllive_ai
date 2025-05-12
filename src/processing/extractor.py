import os
import re
import json
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini with API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set in .env file")

genai.configure(api_key=api_key)

# Instantiate the Gemini model (Flash for speed)
model = genai.GenerativeModel("gemini-1.5-flash")

def get_structured_data(transcript_turns: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured visitor details and questionnaire completion status.

    Args:
        transcript_turns: List of transcript dialogue strings.
        metadata: Metadata containing questionnaire and permit info.

    Returns:
        Dict with keys:
        - visitor_details
        - questionnaire_completion
    """
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
        text = response.text.strip()
        # Remove markdown formatting like ```json
        cleaned = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        return json.loads(cleaned)

    except Exception as e:
        logger.error(f"[extractor] Gemini extraction failed: {e}")
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
