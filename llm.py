"""Generic helper for calling any LLM model through OpenRouter.

OpenRouter (https://openrouter.ai) exposes an OpenAI-compatible chat
completions endpoint that can route requests to many different models
(OpenAI, Anthropic, Google, Meta, etc.) using a single API key. This module
provides a single generic function, `call_llm`, that sends a prompt to a
given model via OpenRouter and returns the model's text response.
"""

import os
from typing import Optional

import requests
from dotenv import load_dotenv

# Load variables from a local .env file (if present) into the environment.
load_dotenv()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# How long to wait (in seconds) for OpenRouter to respond before giving up.
DEFAULT_TIMEOUT_SECONDS = 30


def call_llm(
    model: str,
    prompt: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    temperature: Optional[float] = None,
) -> str:
    """Call any model supported by OpenRouter with a single prompt.

    Args:
        model: The OpenRouter model identifier, e.g. "openai/gpt-4o-mini"
            or "anthropic/claude-3.5-sonnet". See https://openrouter.ai/models
            for the full list of supported models.
        prompt: The user prompt/message to send to the model.
        timeout: Max number of seconds to wait for a response.
        temperature: Optional sampling temperature to forward to
            OpenRouter (0.0 = most deterministic, higher = more random).
            If omitted, the provider's own default is used. Useful for
            callers (like an LLM judge) that want more consistent,
            repeatable outputs.

    Returns:
        The model's text response as a string. If something goes wrong
        (missing API key, network error, invalid model, bad response, etc.)
        a human-readable error string prefixed with "Error:" is returned
        instead of raising an exception. This keeps the function safe to
        call from higher-level code (e.g. a loop calling several models)
        without needing to wrap every call in a try/except.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return "Error: OPENROUTER_API_KEY environment variable is not set."

    if not model:
        return "Error: no model specified."

    if not prompt:
        return "Error: prompt must be a non-empty string."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if temperature is not None:
        payload["temperature"] = temperature

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
    except requests.exceptions.RequestException as exc:
        return f"Error: network request to OpenRouter failed ({exc})."

    if response.status_code != 200:
        # Try to surface OpenRouter's own error message if it provided one,
        # e.g. for an invalid API key or an unknown/invalid model name.
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            detail = response.text
        return f"Error: OpenRouter request failed ({response.status_code}): {detail}"

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        return f"Error: could not parse OpenRouter response ({exc})."
