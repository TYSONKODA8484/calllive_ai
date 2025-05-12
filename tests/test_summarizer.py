import os
import importlib
import pytest
from types import SimpleNamespace

@pytest.fixture(autouse=True)
def env_cleanup(monkeypatch):
    monkeypatch.delenv("USE_MOCK_LLM", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    yield

# --- Mock mode test ---
def test_mock_summary(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    from src.processing import summarizer
    importlib.reload(summarizer)

    result = summarizer.get_summary_from_transcript(["a", "b", "c"])
    assert isinstance(result, str)
    assert "Customer expressed interest" in result

# --- Real mode test ---
def test_real_summary(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    from src.processing import summarizer
    importlib.reload(summarizer)

    # stub out the LLM call
    fake_text = "This is a real summary."
    summarizer.genai_model = SimpleNamespace(
        generate_content=lambda prompt: SimpleNamespace(text=fake_text)
    )

    result = summarizer.get_summary_from_transcript(["line1", "line2"])
    assert result == fake_text

# --- Error fallback test ---
def test_summary_fallback_on_error(monkeypatch):
    monkeypatch.setenv("USE_MOCK_LLM", "false")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    from src.processing import summarizer
    importlib.reload(summarizer)

    # force an exception inside generate_content
    summarizer.genai_model = SimpleNamespace(
        generate_content=lambda prompt: (_ for _ in ()).throw(RuntimeError("LLM down"))
    )

    result = summarizer.get_summary_from_transcript(["oops"])
    assert result == "Summary unavailable due to an error."
