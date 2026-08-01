"""Minimal backend server for the LLM Judge Tool.

Exposes a single JSON API endpoint, POST /api/generate, that accepts a
prompt and returns a real response from a (currently hardcoded) model via
OpenRouter's call_llm function. Also serves the static frontend so the
whole app can be run and viewed from a single server/port.

This is intentionally simple (single model, no judge yet) — later PRs will
add support for calling multiple models and picking the best response with
an LLM judge.
"""

import os

from flask import Flask, jsonify, request, send_from_directory

from llm import call_llm

# Model used for this first end-to-end wiring. This will be replaced by
# calls to multiple models in a later PR.
DEFAULT_MODEL = "openai/gpt-4o-mini"

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

app = Flask(__name__, static_folder=None)


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "Prompt must not be empty."}), 400

    result = call_llm(DEFAULT_MODEL, prompt)

    if isinstance(result, str) and result.startswith("Error:"):
        return jsonify({"error": result}), 502

    return jsonify({"model": DEFAULT_MODEL, "response": result})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
