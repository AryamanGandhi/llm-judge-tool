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

This runs `test_llm.py`, which covers a successful call, an invalid model
name, and a missing API key. The "valid response" test makes a real,
live call to OpenRouter and is automatically skipped if `OPENROUTER_API_KEY`
is not set in the environment.

Run instructions will continue to be filled in and kept up to date here as
more functionality (frontend, multi-model calls, judge evaluation) is added.


## Roadmap

The project is being built as a sequence of small, focused pull requests:

1. ✅ README with project description + setup/run instructions
2. ✅ Generic `call_llm` function to call any model via OpenRouter
3. Simple frontend
4. Wire frontend to backend so a prompt returns a real response
5. Frontend call triggers multiple models on the backend
6. Evaluate the responses and pick the best one using an LLM judge
7. Build a test suite to evaluate system performance
8. Iterate on prompts based on test results


## License

TBD.
