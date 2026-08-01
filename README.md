# LLM Judge Tool

A tool that evaluates multiple LLMs on a given task and uses another LLM as a
**judge** to automatically pick the best response.

Instead of manually comparing model outputs by hand, this tool lets you send
the same prompt to several different models, collect their responses, and
have a designated "judge" model score/rank them and select a winner.

All model calls (both the models being evaluated and the judge model) go
through **[OpenRouter](https://openrouter.ai)**, a single API that provides
access to many different LLM providers (OpenAI, Anthropic, Google, Meta,
etc.) without needing separate API keys/integrations for each one.

## How it works (high-level)

1. You submit a prompt / task.
2. The tool sends that prompt to several different models via OpenRouter.
3. Each model's response is collected.
4. A judge LLM is given the original prompt and all the candidate responses,
   and is asked to evaluate and pick the best one (and explain why).
5. The tool returns the winning response (and optionally the judge's
   reasoning) to the user.

> **Project status:** This project is being built iteratively, one small
> pull request at a time — starting from a minimal end-to-end flow and then
> layering on more models, a frontend, evaluation, and testing. See the
> [Roadmap](#roadmap) section below for where things currently stand.

## Prerequisites

- Python 3.10+
- An [OpenRouter](https://openrouter.ai) account and API key

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/AryamanGandhi/llm-judge-tool.git
   cd llm-judge-tool
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set your OpenRouter API key as an environment variable:

   Copy the example env file and fill in your real key:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and replace the placeholder with your real key:

   ```
   OPENROUTER_API_KEY=your-openrouter-api-key-here
   ```

   `.env` is listed in `.gitignore` so your real key is never committed.
   You can get an API key by signing up at [openrouter.ai](https://openrouter.ai)
   and creating a key from your account dashboard.

   Alternatively, you can export it directly in your shell instead of using
   a `.env` file:

   ```bash
   export OPENROUTER_API_KEY="your-openrouter-api-key-here"
   ```

## Running the project

This project is under active, incremental development. So far it includes a
generic `call_llm(model, prompt)` function (in `llm.py`) for calling any
model supported by OpenRouter. You can try it out directly:

```bash
python -c "from llm import call_llm; print(call_llm('openai/gpt-4o-mini', 'Say hi in 3 words.'))"
```

### Running tests

```bash
pytest
```

This runs `test_llm.py` (covering `call_llm`: a successful call, an invalid
model name, and a missing API key) and `test_app.py` (covering the
`/api/generate` backend endpoint: a valid prompt, an empty prompt, a
missing prompt field, and an upstream error). The backend tests mock
`call_llm`, so they run fast and don't require a real API key or network
access. The one live test in `test_llm.py` makes a real call to OpenRouter
and is automatically skipped if `OPENROUTER_API_KEY` is not set.

### Running the app (frontend + backend together)

The backend is a small Flask app (`app.py`) that exposes a
`POST /api/generate` endpoint and also serves the frontend, so you can run
everything from a single server:

```bash
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.
Type a prompt and hit Submit — it will call a single hardcoded model
(`openai/gpt-4o-mini`) via OpenRouter and display the real response (or a
clear error message if something goes wrong, e.g. a missing/invalid API
key). Calling multiple models and picking the best one with a judge model
will be added in later PRs.




## Roadmap

The project is being built as a sequence of small, focused pull requests:

1. ✅ README with project description + setup/run instructions
2. ✅ Generic `call_llm` function to call any model via OpenRouter
3. ✅ Simple frontend
4. ✅ Wire frontend to backend so a prompt returns a real response

5. Frontend call triggers multiple models on the backend
6. Evaluate the responses and pick the best one using an LLM judge
7. Build a test suite to evaluate system performance
8. Iterate on prompts based on test results


## License

TBD.
