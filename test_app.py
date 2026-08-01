"""Tests for the Flask backend's /api/generate endpoint.

These tests use unittest.mock to patch call_llm (imported into app.py) so
they run fast, do not require a real OPENROUTER_API_KEY, and don't make
real network calls.
"""

import json
from unittest.mock import patch

import pytest

from app import JUDGE_MODEL, MODELS, app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_generate_calls_all_models_and_returns_response_for_each(client):
    def fake_call_llm(model, prompt):
        if model == JUDGE_MODEL and model not in MODELS:
            return json.dumps({"winner_index": 0, "reasoning": "It's fine."})
        return "A response."

    with patch("app.call_llm", side_effect=fake_call_llm) as mock_call_llm:
        response = client.post("/api/generate", json={"prompt": "Say hi"})

    assert response.status_code == 200

    data = response.get_json()

    assert data["prompt"] == "Say hi"
    assert len(data["results"]) == len(MODELS)

    called_models = {call.args[0] for call in mock_call_llm.call_args_list}
    assert called_models == set(MODELS) | {JUDGE_MODEL}

    for result in data["results"]:
        assert result["model"] in MODELS
        assert result["response"] == "A response."
        assert result["error"] is None


def test_generate_handles_one_model_failing_without_breaking_others(client):
    failing_model = MODELS[0]

    def fake_call_llm(model, prompt):
        if model == failing_model:
            return "Error: something went wrong with this model."
        if model == JUDGE_MODEL:
            return json.dumps({"winner_index": 0, "reasoning": "Good enough."})
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
        if model == JUDGE_MODEL:
            return json.dumps({"winner_index": 0, "reasoning": "Fine."})
        return f"Good response from {model}"

    with patch("app.call_llm", side_effect=fake_call_llm):
        response = client.post("/api/generate", json={"prompt": "Say hi"})

    assert response.status_code == 200
    data = response.get_json()

    results_by_model = {r["model"]: r for r in data["results"]}
    failing_result = results_by_model[failing_model]
    assert failing_result["response"] is None
    assert failing_result["error"].startswith("Error:")


def test_generate_judge_picks_a_winner_from_mocked_responses(client):
    """The judge should correctly parse a winner_index from its mocked
    response and translate it into the corresponding model's name, along
    with the reasoning string."""

    def fake_call_llm(model, prompt):
        if model == JUDGE_MODEL:
            # Candidates are indexed in MODELS order; pick index 2.
            return json.dumps(
                {"winner_index": 2, "reasoning": "This response was the clearest."}
            )
        return f"Response from {model}"

    with patch("app.call_llm", side_effect=fake_call_llm):
        response = client.post("/api/generate", json={"prompt": "Say hi"})

    assert response.status_code == 200
    data = response.get_json()

    judgment = data["judgment"]
    assert judgment["error"] is None
    assert judgment["winner"] == MODELS[2]
    assert judgment["reasoning"] == "This response was the clearest."


def test_generate_judge_failure_does_not_break_the_request(client):
    """If the judge call itself fails (returns an Error: string), the
    5 responses should still be returned, with the judgment marked as
    failed rather than the whole request erroring out."""

    def fake_call_llm(model, prompt):
        if model == JUDGE_MODEL and model not in MODELS:
            return "Error: judge model is temporarily unavailable."
        return f"Response from {model}"

    with patch("app.call_llm", side_effect=fake_call_llm):
        response = client.post("/api/generate", json={"prompt": "Say hi"})

    assert response.status_code == 200
    data = response.get_json()

    assert len(data["results"]) == len(MODELS)
    for result in data["results"]:
        assert result["error"] is None
        assert result["response"] is not None

    judgment = data["judgment"]
    assert judgment["winner"] is None
    assert judgment["error"].startswith("Error:")


def test_generate_judge_handles_malformed_json_response(client):
    """If the judge responds with text that isn't valid JSON, judging
    should fail gracefully (an error, no winner) rather than raising and
    crashing the whole request."""

    def fake_call_llm(model, prompt):
        if model == JUDGE_MODEL:
            return "I think response 2 is best, no JSON here!"
        return f"Response from {model}"

    with patch("app.call_llm", side_effect=fake_call_llm):
        response = client.post("/api/generate", json={"prompt": "Say hi"})

    assert response.status_code == 200
    data = response.get_json()

    judgment = data["judgment"]
    assert judgment["winner"] is None
    assert judgment["error"] is not None
