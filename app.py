"""Minimal backend server for the LLM Judge Tool.

Serves the static frontend and exposes a JSON API endpoint,
POST /api/generate, that accepts a prompt, calls several different LLMs
(via OpenRouter's call_llm function) concurrently, then asks a separate
"judge" LLM to evaluate all of their responses and pick a winner.
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request, send_from_directory

from llm import call_llm

# The set of models compared for every prompt. This is a small, reasonable
# mix of providers/sizes available on OpenRouter. Swapping/extending this
# list does not require any other code changes.
MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku",
    "google/gemini-2.5-flash-lite",
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-small-3.1-24b-instruct",
]

# A single strong model used solely to judge/rank the candidate responses
# above. Kept separate from MODELS so the judge is never asked to judge
# itself as part of the pool of candidates.
JUDGE_MODEL = "openai/gpt-4o-mini"

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


def _build_judge_prompt(prompt: str, results: list):
    """Build the prompt sent to the judge model.

    Only successful (non-error) responses are included as candidates,
    since a model that failed to respond can't fairly be picked as the
    winner. Each candidate is labeled with a stable index (rather than the
    model name) so the judge evaluates responses on merit rather than any
    bias toward/against a particular model's name. Returns a tuple of
    (judge_prompt_text, candidates_list).
    """
    candidates = [r for r in results if r["error"] is None]

    sections = []
    for i, r in enumerate(candidates):
        sections.append(f"Response {i}:\n{r['response']}")
    candidates_text = "\n\n".join(sections)

    judge_prompt_text = (
        "You are an impartial judge evaluating multiple AI assistant "
        "responses to the same user prompt. Pick the single best response "
        "and briefly explain why.\n\n"
        f"User prompt:\n{prompt}\n\n"
        f"Candidate responses:\n\n{candidates_text}\n\n"
        "Respond with ONLY a JSON object (no other text, no markdown "
        "fences) in exactly this format:\n"
        '{"winner_index": <integer index of the best response>, '
        '"reasoning": "<one or two sentence explanation>"}'
    )
    return judge_prompt_text, candidates


def _parse_judge_response(raw: str) -> dict:
    """Extract {"winner_index": int, "reasoning": str} from the judge's
    raw text response, tolerating minor formatting like markdown code
    fences around the JSON."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("no JSON object found in judge response")

    parsed = json.loads(match.group(0))
    winner_index = int(parsed["winner_index"])
    reasoning = str(parsed["reasoning"])
    return {"winner_index": winner_index, "reasoning": reasoning}


def judge_responses(prompt: str, results: list) -> dict:
    """Ask the judge model to pick the best of the successful responses.

    Returns a dict with:
      - "winner": the winning model's name, or None if judging failed
        or there were no successful candidates to judge.
      - "reasoning": the judge's explanation string, or None.
      - "error": an error string if judging failed, else None.

    This function never raises — any failure (judge call error, malformed
    judge output, etc.) is captured and returned as an "error" so the
    caller can still show the 5 individual responses without a winner.
    """
    judge_prompt, candidates = _build_judge_prompt(prompt, results)

    if not candidates:
        return {
            "winner": None,
            "reasoning": None,
            "error": "No successful model responses to judge.",
        }

    try:
        raw = call_llm(JUDGE_MODEL, judge_prompt)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "winner": None,
            "reasoning": None,
            "error": f"Judge call raised an unexpected error ({exc}).",
        }

    if isinstance(raw, str) and raw.startswith("Error:"):
        return {"winner": None, "reasoning": None, "error": raw}

    try:
        parsed = _parse_judge_response(raw)
        winner_model = candidates[parsed["winner_index"]]["model"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        return {
            "winner": None,
            "reasoning": None,
            "error": f"Error: could not parse judge response ({exc}).",
        }

    return {"winner": winner_model, "reasoning": parsed["reasoning"], "error": None}


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

    judgment = judge_responses(prompt, results)

    return jsonify({"prompt": prompt, "results": results, "judgment": judgment})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
