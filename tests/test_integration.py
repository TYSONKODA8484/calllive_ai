import os
import importlib
import pytest
import sys, os
# add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from types import SimpleNamespace
from scripts.mock_api import app as mock_app
from fastapi.testclient import TestClient
from src.api.client import MordorAPIClient
# …rest of your test…

# Adjust PYTHONPATH to include src if necessary
# This assumes your tests root sees the src package

@pytest.fixture(autouse=True)
def env_cleanup(monkeypatch):
    # Ensure environment variables are reset between tests
    monkeypatch.delenv("USE_MOCK_LLM", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    yield

def test_mock_summary(monkeypatch):
    # Enable mock LLM mode
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    # Reload module to pick up env var
    from src.processing import summarizer
    importlib.reload(summarizer)

    # Should return the placeholder text
    summary = summarizer.get_summary_from_transcript([
        "agent: Hello!",
        "customer: Hi there."
    ])
    assert "Mount Doom hike" in summary
    assert isinstance(summary, str)

def test_real_summary(monkeypatch):
    # Disable mock mode
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    # Provide a dummy API key to satisfy import
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    # Reload module after env update
    from src.processing import summarizer
    importlib.reload(summarizer)

    # Replace the real Gemini model with a fake one
    fake_response = SimpleNamespace(text="This is a real summary.")
    fake_model = SimpleNamespace(generate_content=lambda prompt: fake_response)
    summarizer.genai_model = fake_model

    result = summarizer.get_summary_from_transcript([
        "agent: Test summary.",
        "customer: Summarize this."
    ])
    assert result == "This is a real summary."

def test_error_fallback(monkeypatch):
    # Simulate an exception during real LLM call
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    from src.processing import summarizer
    importlib.reload(summarizer)

    # Patch generate_content to raise
    def raise_error(prompt):
        raise RuntimeError("API failure")
    summarizer.genai_model = SimpleNamespace(generate_content=raise_error)

    result = summarizer.get_summary_from_transcript([
        "some", "text"
    ])
    assert result == "Summary unavailable due to an error."
