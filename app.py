"""Minimal backend server for the LLM Judge Tool.

Serves the static frontend and exposes a JSON API endpoint,
POST /api/generate, that accepts a prompt and calls several different
LLMs (via OpenRouter's call_llm function) concurrently, returning all of
their responses labeled by model name.

This is intentionally simple (no judge yet) — a later PR will add an LLM
judge that picks the best response out of the candidates returned here.
"""

import os
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request, send_from_directory

from llm import call_llm

# The set of models compared for every prompt. This is a small, reasonable
# mix of providers/sizes available on OpenRouter. Swapping/extending this
# list does not require any other code changes.
MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-haiku",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-small-3.1-24b-instruct",
]

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

app = Flask(__name__, static_folder=None)


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


def _call_one_model(model: str, prompt: str) -> dict:
    """Call a single model and return a result dict, never raising.

    call_llm already returns an "Error: ..." string instead of raising for
    expected failure modes (missing key, bad model, network issues), but we
    also guard with a try/except here so that one model failing in an
    unexpected way can never take down the whole request.
    """
    try:
        response = call_llm(model, prompt)
    except Exception as exc:  # pragma: no cover - defensive fallback
        response = f"Error: unexpected failure calling {model} ({exc})."

    is_error = isinstance(response, str) and response.startswith("Error:")
    return {
        "model": model,
        "response": None if is_error else response,
        "error": response if is_error else None,
    }


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "Prompt must not be empty."}), 400

    # Call all models concurrently so total latency is roughly the slowest
    # single call, not the sum of all of them.
    with ThreadPoolExecutor(max_workers=len(MODELS)) as executor:
        results = list(executor.map(lambda m: _call_one_model(m, prompt), MODELS))

    return jsonify({"prompt": prompt, "results": results})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

