import os
import importlib
import pytest
import json
from types import SimpleNamespace

@pytest.fixture(autouse=True)
def env_cleanup(monkeypatch):
    # Reset env vars before each test
    monkeypatch.delenv("USE_MOCK_LLM", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    yield

# --- Mock mode test ---
def test_mock_analysis(monkeypatch):
    # Enable mock LLM mode
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    from src.processing import analyzer
    importlib.reload(analyzer)

    # Call analyzer
    result = analyzer.analyze_insights(
        ["agent: Hello", "customer: Hi"],
        {"visitor_details": {}, "questionnaire_completion": {}}
    )
    assert isinstance(result, dict)
    assert result["sentiment"] == 0.5
    assert result["interest_level"] == "medium"
    assert result["preparedness_level"] == "medium"
    assert result["action_items"] == []

# --- Real mode test ---
def test_real_analysis(monkeypatch):
    # Disable mock and set dummy key
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    from src.processing import analyzer
    importlib.reload(analyzer)

    # Fake response JSON
    fake_json = {
        "sentiment": 0.8,
        "interest_level": "high",
        "preparedness_level": "low",
        "action_items": ["Follow up"]
    }
    fake_text = json.dumps(fake_json)
    fake_response = SimpleNamespace(text=fake_text)
    analyzer.model = SimpleNamespace(generate_content=lambda prompt: fake_response)

    result = analyzer.analyze_insights(
        ["agent: Test"],
        {"visitor_details": {}, "questionnaire_completion": {}}
    )
    assert result == fake_json

# --- Error fallback test ---
def test_analysis_fallback(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    from src.processing import analyzer
    importlib.reload(analyzer)

    # Make generate_content throw
    def raise_exc(prompt):
        raise RuntimeError("LLM Error")
    analyzer.model = SimpleNamespace(generate_content=raise_exc)

    result = analyzer.analyze_insights(
        ["dummy"],
        {"visitor_details": {}, "questionnaire_completion": {}}
    )
    # Should fallback to defaults
    assert result["sentiment"] == 0.5
    assert result["interest_level"] == "medium"
    assert result["preparedness_level"] == "medium"
    assert result["action_items"] == []
