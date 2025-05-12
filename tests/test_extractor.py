import os
import importlib
import pytest
import json
from types import SimpleNamespace

@pytest.fixture(autouse=True)
def env_cleanup(monkeypatch):
    # Ensure environment variables are reset between tests
    monkeypatch.delenv("USE_MOCK_LLM", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    yield

# --- Mock mode test ---
def test_mock_extraction(monkeypatch):
    # Enable mock extractor mode
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    # Reload module to pick up environment change
    from src.processing import extractor
    importlib.reload(extractor)

    # Sample input
    transcript_turns = ["agent: Hello", "customer: Hi"]
    metadata = {"questionnaire": {"purpose_of_visit_asked": True},
                "mount_doom_permit_status": "pending"}
    result = extractor.get_structured_data(transcript_turns, metadata)

    # In mock mode, visitor_details should be default values
    assert isinstance(result, dict)
    vd = result["visitor_details"]
    assert vd["ring_bearer"] is False
    assert vd["gear_prepared"] is False
    assert vd["hazard_knowledge"] == "none"
    assert vd["fitness_level"] == "medium"
    assert vd["permit_status"] == "pending"
    # questionnaire_completion should echo metadata
    assert result["questionnaire_completion"] == metadata["questionnaire"]

# --- Real mode test ---
def test_real_extraction(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    from src.processing import extractor
    importlib.reload(extractor)

    # Prepare a fake JSON response from the LLM
    fake_json = {
        "visitor_details": {
            "ring_bearer": True,
            "gear_prepared": False,
            "hazard_knowledge": "limited",
            "fitness_level": "high",
            "permit_status": "approved"
        },
        "questionnaire_completion": {"purpose_of_visit_asked": True}
    }
    fake_text = json.dumps(fake_json)
    fake_response = SimpleNamespace(text=fake_text)
    # Monkeypatch the model
    extractor.model = SimpleNamespace(generate_content=lambda prompt: fake_response)

    transcript_turns = ["agent: Ask details", "customer: I want level 5"]
    metadata = {"questionnaire": {"purpose_of_visit_asked": True}}
    result = extractor.get_structured_data(transcript_turns, metadata)

    assert result == fake_json

# --- Exception fallback test ---
def test_extraction_fallback(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    from src.processing import extractor
    importlib.reload(extractor)

    # Patch generate_content to raise an error
    def raise_exc(prompt):
        raise RuntimeError("LLM down")
    extractor.model = SimpleNamespace(generate_content=raise_exc)

    transcript_turns = ["dummy"]
    metadata = {"questionnaire": {}, "mount_doom_permit_status": "denied"}
    result = extractor.get_structured_data(transcript_turns, metadata)

    # On error, visitor_details fields are None except permit_status
    vd = result["visitor_details"]
    assert vd["ring_bearer"] is None
    assert vd["gear_prepared"] is None
    assert vd["hazard_knowledge"] is None
    assert vd["fitness_level"] is None
    assert vd["permit_status"] == "denied"
    assert result["questionnaire_completion"] == {}
