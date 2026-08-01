"""Tests for the Flask backend's /api/generate endpoint.

These tests use unittest.mock to patch call_llm (imported into app.py) so
they run fast, do not require a real OPENROUTER_API_KEY, and don't make
real network calls.
"""

from unittest.mock import patch

import pytest

from app import MODELS, app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_generate_calls_all_models_and_returns_response_for_each(client):
    with patch("app.call_llm", return_value="A response.") as mock_call_llm:
        response = client.post("/api/generate", json={"prompt": "Say hi"})

    assert response.status_code == 200
    data = response.get_json()

    assert data["prompt"] == "Say hi"
    assert len(data["results"]) == len(MODELS)

    called_models = {call.args[0] for call in mock_call_llm.call_args_list}
    assert called_models == set(MODELS)

    for result in data["results"]:
        assert result["model"] in MODELS
        assert result["response"] == "A response."
        assert result["error"] is None


def test_generate_handles_one_model_failing_without_breaking_others(client):
    failing_model = MODELS[0]

    def fake_call_llm(model, prompt):
        if model == failing_model:
            return "Error: something went wrong with this model."
        return f"Good response from {model}"

    with patch("app.call_llm", side_effect=fake_call_llm):
        response = client.post("/api/generate", json={"prompt": "Say hi"})

    assert response.status_code == 200
    data = response.get_json()

    results_by_model = {r["model"]: r for r in data["results"]}

    failing_result = results_by_model[failing_model]
    assert failing_result["response"] is None
    assert failing_result["error"].startswith("Error:")

    for model in MODELS:
        if model == failing_model:
            continue
        ok_result = results_by_model[model]
        assert ok_result["error"] is None
        assert ok_result["response"] == f"Good response from {model}"


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


def test_generate_handles_unexpected_exception_from_one_model(client):
    """A model call that raises an unexpected exception should not crash
    the whole request — it should show up as an error for that model."""
    failing_model = MODELS[0]

    def fake_call_llm(model, prompt):
        if model == failing_model:
            raise RuntimeError("boom")
        return f"Good response from {model}"

    with patch("app.call_llm", side_effect=fake_call_llm):
        response = client.post("/api/generate", json={"prompt": "Say hi"})

    assert response.status_code == 200
    data = response.get_json()

    results_by_model = {r["model"]: r for r in data["results"]}
    failing_result = results_by_model[failing_model]
    assert failing_result["response"] is None
    assert failing_result["error"].startswith("Error:")
