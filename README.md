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
`/api/generate` backend endpoint: all 5 models are called concurrently for
a valid prompt, one model failing doesn't break the others, an empty
prompt, a missing prompt field, and an unexpected exception from one
model). The backend tests mock `call_llm`, so they run fast and don't
require a real API key or network access. The one live test in
`test_llm.py` makes a real call to OpenRouter and is automatically skipped
if `OPENROUTER_API_KEY` is not set.


### Running the app (frontend + backend together)

The backend is a small Flask app (`app.py`) that exposes a
`POST /api/generate` endpoint and also serves the frontend, so you can run
everything from a single server:

```bash
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.
Type a prompt and hit Submit — it will call 5 different models
(a mix of OpenAI, Anthropic, Google, Meta, and Mistral models, see the
`MODELS` list in `app.py`) concurrently via OpenRouter, and display each
model's response side by side, labeled by model name. If a model fails
(e.g. a missing/invalid API key or an upstream error), only that model's
card shows an error — the others still render normally.

Once all 5 responses come back, a separate **judge model**
(`JUDGE_MODEL` in `app.py`, currently `openai/gpt-4o-mini`) is given the
original prompt plus all of the successful responses and asked to pick
the single best one, with a brief explanation. The judge's verdict is
shown as a banner above the responses (🏆 winner + reasoning), and the
winning model's card is highlighted with a badge. If the judge call
itself fails or its output can't be parsed, the 5 responses are still
shown as normal — you'll just see a small "Judge unavailable" note
instead of a winner.

### Running the evaluation suite

While `pytest` (above) checks that the code doesn't crash, `run_eval.py`
measures whether the **judge is actually good at its job** — i.e. does
it consistently pick sensible winners across a variety of task types.

```bash
python run_eval.py            # real run, hits OpenRouter (uses API credits)
python run_eval.py --mock     # fast, free dry run using canned fake
                               # responses — useful for sanity-checking
                               # the eval script itself
python run_eval.py --output eval_results/my_run.json   # custom output path
```

What it does:

1. Runs the full 5-model + judge pipeline (same code as the app) against
   a fixed set of ~12 prompts in `eval_prompts.py`, covering coding,
   factual/reasoning, and writing tasks.
2. For the first 5 prompts, re-runs *just* the judge step a second time
   on the same 5 responses, to check whether the judge picks the same
   winner both times (a self-consistency check).
3. Writes full per-prompt results (every model's response, the judge's
   winner + reasoning, and the consistency check outcome) to a timestamped
   JSON file under `eval_results/` (gitignored — this is generated output,
   not something to commit).
4. Prints a summary: how many times each model won overall, and the
   judge's self-consistency rate.

Example summary output from a real run:

```
=== Eval Summary ===
Prompts evaluated: 12
Prompts successfully judged: 12

Wins per model:
  anthropic/claude-3-haiku: 6
  openai/gpt-4o-mini: 3
  google/gemini-2.5-flash-lite: 3

Judge self-consistency: 5 checks run, 80% consistent
```

A consistency rate below 100% is expected and informative — it means the
judge occasionally flips its pick when re-evaluating identical responses,
which is useful signal for tuning the judge prompt in a future PR (see
Roadmap item 8).

`test_run_eval.py` covers the script's own aggregation logic
(`summarize`, `check_judge_consistency`) with hand-constructed mock
results, so those tests are fast and don't touch the network at all.

## Roadmap

The project is being built as a sequence of small, focused pull requests:

1. ✅ README with project description + setup/run instructions
2. ✅ Generic `call_llm` function to call any model via OpenRouter
3. ✅ Simple frontend
4. ✅ Wire frontend to backend so a prompt returns a real response
5. ✅ Frontend call triggers multiple models on the backend
6. ✅ Evaluate the responses and pick the best one using an LLM judge
7. ✅ Build a test suite (`run_eval.py`) to evaluate system performance
8. Iterate on prompts based on test results

## License

TBD.


