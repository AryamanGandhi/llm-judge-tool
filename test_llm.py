"""Tests for the generic call_llm function.

The "valid model/prompt" test is a LIVE test that hits the real OpenRouter
API. It requires a valid OPENROUTER_API_KEY to be set in the environment
(e.g. via a local .env file) and will be skipped automatically if no key is
present (for example, in CI where no secret is configured).

The other two tests (invalid model, missing API key) do not require any
real network credentials to be meaningful:
- The invalid-model test still hits the real API (if a key is present) but
  asserts that call_llm handles OpenRouter's error response gracefully
  instead of raising.
- The missing-API-key test temporarily clears OPENROUTER_API_KEY from the
  environment and asserts call_llm short-circuits with a clear error
  message, without making any network request at all.
"""

import os

import pytest

from llm import call_llm

# A small, inexpensive model to use for the live test.
VALID_TEST_MODEL = "openai/gpt-4o-mini"

HAS_API_KEY = bool(os.environ.get("OPENROUTER_API_KEY"))


@pytest.mark.skipif(
    not HAS_API_KEY,
    reason="OPENROUTER_API_KEY not set; skipping live API test.",
)
def test_call_llm_returns_response_for_valid_model_and_prompt():
    result = call_llm(VALID_TEST_MODEL, "Reply with exactly the word: pong")

    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert len(result.strip()) > 0


def test_call_llm_handles_invalid_model_name_without_crashing():
    # Should not raise, even though this model name does not exist.
    result = call_llm("this-model/does-not-exist-12345", "Hello")

    assert isinstance(result, str)
    if not HAS_API_KEY:
        # Without a key at all, we short-circuit before ever making a
        # network call and hitting the invalid model.
        assert result == "Error: OPENROUTER_API_KEY environment variable is not set."
    else:
        assert result.startswith("Error:")


def test_call_llm_handles_missing_api_key_without_crashing(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    result = call_llm(VALID_TEST_MODEL, "Hello")

    assert result == "Error: OPENROUTER_API_KEY environment variable is not set."


def test_call_llm_handles_empty_prompt_without_crashing():
    result = call_llm(VALID_TEST_MODEL, "")

    assert isinstance(result, str)
    assert result.startswith("Error:")


def test_call_llm_includes_temperature_in_payload_when_given(monkeypatch):
    """When a temperature is passed, it should be forwarded to OpenRouter
    in the JSON payload (used by the judge to get more consistent
    results). When omitted, the payload should not include the key at
    all, letting the provider's own default apply."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key-for-test")

    captured_payloads = []

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured_payloads.append(json)
        return FakeResponse()

    monkeypatch.setattr("llm.requests.post", fake_post)

    call_llm(VALID_TEST_MODEL, "Hello", temperature=0.0)
    call_llm(VALID_TEST_MODEL, "Hello")

    assert captured_payloads[0]["temperature"] == 0.0
    assert "temperature" not in captured_payloads[1]


def test_call_llm_caps_max_tokens_by_default(monkeypatch):
    """call_llm should always send a max_tokens value to OpenRouter (a
    sane default if the caller doesn't specify one), so that models which
    would otherwise default to a very large max_tokens don't blow past
    what the account's credit balance can afford."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key-for-test")

    captured_payloads = []

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured_payloads.append(json)
        return FakeResponse()

    monkeypatch.setattr("llm.requests.post", fake_post)

    call_llm(VALID_TEST_MODEL, "Hello")
    call_llm(VALID_TEST_MODEL, "Hello", max_tokens=250)

    from llm import DEFAULT_MAX_TOKENS

    assert captured_payloads[0]["max_tokens"] == DEFAULT_MAX_TOKENS
    assert captured_payloads[1]["max_tokens"] == 250
