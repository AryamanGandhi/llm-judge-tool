"""Tests for the Flask backend's /api/generate endpoint.

These tests use unittest.mock to patch llm.call_llm so they run fast, do
not require a real OPENROUTER_API_KEY, and don't make real network calls.
"""

from unittest.mock import patch

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_generate_returns_response_for_valid_prompt(client):
    with patch("app.call_llm", return_value="Hello there!") as mock_call_llm:
        response = client.post("/api/generate", json={"prompt": "Say hi"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["response"] == "Hello there!"
    assert "model" in data
    mock_call_llm.assert_called_once()


def test_generate_handles_empty_prompt(client):
    response = client.post("/api/generate", json={"prompt": ""})

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_generate_handles_missing_prompt_field(client):
    response = client.post("/api/generate", json={})

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_generate_handles_call_llm_error_gracefully(client):
    with patch(
        "app.call_llm",
        return_value="Error: OPENROUTER_API_KEY environment variable is not set.",
    ):
        response = client.post("/api/generate", json={"prompt": "Say hi"})

    assert response.status_code == 502
    data = response.get_json()
    assert "error" in data
    assert data["error"].startswith("Error:")
