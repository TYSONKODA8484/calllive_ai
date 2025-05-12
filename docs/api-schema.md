# 🌋 Mount Doom Voice Agent Challenge API

This document outlines the API schema for the Mount Doom Voice Agent Challenge.

## 🛡️ Authentication

### `POST /api/auth`

Obtain a bearer token using your personal API key.

**Request Headers:**

```http
Content-Type: application/json
Request Body:

JSON

{
  "api_key": "your-api-key"
}
Response:

JSON

{
  "token": "your-bearer-token"
}
Usage: Use the token value in the Authorization header for all subsequent requests.

📥 Stream Transcripts
GET /api/v1/transcripts/stream
Receive a continuous stream of transcript JSON objects.

Headers:

HTTP

Authorization: Bearer your-bearer-token
Content-Type: application/json
Response: application/json stream

Each line in the stream is a JSON object with the following structure:

JSON

{
  "transcript_id": "t-abc123",
  "session_id": "sess-xyz789",
  "timestamp": "2025-05-03T04:06:13.515Z",
  "agent_type": "customer_service",
  "duration_seconds": 307,
  "participants": {
    "agent": "Doom Services AI",
    "customer": "Anonymous-User"
  },
  "transcript_text": [
    {
      "speaker": "agent",
      "text": "Hello, welcome to Mount Doom services.",
      "timestamp": "2025-05-03T04:06:19.781Z"
    },
    {
      "speaker": "customer",
      "text": "I want to visit the volcano.",
      "timestamp": "2025-05-03T04:06:32.144Z"
    }
  ],
  "metadata": {
    "questionnaire": {
      "purpose_of_visit_asked": true,
      "experience_assessed": true,
      "risk_acknowledged": true,
      "gear_discussed": true,
      "any_items_to_dispose_of_asked": true
    },
    "visitor_interest_level": "high",
    "potential_issue": "naive",
    "mount_doom_permit_status": "pending",
    "language": "en"
  }
}
📤 Submit Processed Results
POST /api/v1/transcripts/process
Submit the LLM-processed summary, structured data, and analysis.

Headers:

HTTP

Authorization: Bearer your-bearer-token
Content-Type: application/json
Body Example:

JSON

{
  "transcript_id": "t-abc123",
  "summary": "Visitor was interested in hiking Mount Doom but unprepared. Agent explained hazards.",
  "structured_data": {
    "visitor_details": {
      "ring_bearer": false,
      "gear_prepared": true,
      "hazard_knowledge": "limited",
      "fitness_level": "moderate",
      "permit_status": "pending"
    },
    "questionnaire_completion": {
      "purpose_of_visit": true,
      "experience_level": true,
      "risk_acknowledgment": true,
      "gear_assessment": true,
      "item_disposal_intent": true
    }
  },
  "analysis": {
    "sentiment": 0.45,
    "interest_level": "high",
    "preparedness_level": "low",
    "action_items": [
      "Send Mount Doom safety information packet",
      "Provide permit application details",
      "Follow up in 1 week regarding decision"
    ]
  },
  "processing_timestamp": "2025-05-03T04:11:30.123Z"
}
Response:

JSON

{
  "status": "ok",
  "transcript_id": "t-abc123"
}
📊 View Stats
GET /api/v1/stats
Check how many transcripts have been processed so far.

Headers:

HTTP

Authorization: Bearer your-bearer-token
Response:

JSON

{
  "processed_count": 523
}
❤️ Health Check
GET /api/v1/health
Basic endpoint to check if the API is alive.

Response:

JSON

{
  "status": "healthy",
  "time": "2025-05-03T04:45:00.000Z"
}
⚠️ Rate Limits
Endpoint	Limit
/api/v1/transcripts/stream	50 concurrent connections
/api/v1/transcripts/process	100 requests per minute
/api/v1/stats	20 requests per minute