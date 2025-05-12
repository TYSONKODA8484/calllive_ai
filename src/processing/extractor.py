import os
import re
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini with your API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set in .env file")
genai.configure(api_key=api_key)

# Instantiate the model (Gemini Flash for speed)
model = genai.GenerativeModel("gemini-1.5-flash")

def get_structured_data(transcript_turns: list[str], metadata: dict) -> dict:
    """
    Extract structured visitor details and questionnaire completion status.

    Args:
        transcript_turns: List of transcript lines.
        metadata: Original metadata dict from API (contains questionnaire info and permit status).

    Returns:
        A dict matching the 'structured_data' schema:
        {
          "visitor_details": { ... },
          "questionnaire_completion": { ... }
        }
    """
    # Combine dialogue lines
    full_text = "\n".join(transcript_turns)
    # Prepare metadata as JSON string for prompt
    questionnaire_json = json.dumps(metadata.get("questionnaire", {}))

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
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Remove any markdown code fences
        cleaned = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
        # Parse JSON
        return json.loads(cleaned)
    except Exception as e:
        print(f"[extractor] Parsing failed: {e}\nResponse was: {text}")
        # Fallback: derive from metadata only
        return {
            "visitor_details": {
                "ring_bearer": None,
                "gear_prepared": None,
                "hazard_knowledge": None,
                "fitness_level": None,
                "permit_status": metadata.get("mount_doom_permit_status")
            },
            "questionnaire_completion": metadata.get("questionnaire", {})
        }

# Example usage for local testing
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
    print("Structured Data:", result)
