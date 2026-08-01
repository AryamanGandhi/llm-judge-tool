"""Evaluation script for measuring how well the LLM Judge Tool performs.

Unlike test_app.py / test_llm.py (which just check the code doesn't
crash), this script measures whether the *judge* is actually doing a
good job of picking the best response, across a fixed set of prompts
covering different task types (coding, factual, reasoning, writing).

For each prompt in eval_prompts.EVAL_PROMPTS, this script:
  1. Calls all 5 candidate models (app.MODELS) concurrently, same as the
     real app.
  2. Asks the judge model to pick a winner + reasoning.
  3. For a subset of prompts, re-runs *just* the judge step a second time
     on the same 5 responses, to check whether the judge is consistent
     with itself (same winner both times).

Results (per-prompt model responses, judge winner/reasoning, and the
consistency check outcome) are saved to a timestamped JSON file, and a
summary (win counts per model, judge consistency rate) is printed at the
end.

Usage:
    python run_eval.py              # hits real OpenRouter APIs
    python run_eval.py --mock       # uses canned fake responses, no
                                     # network calls / API cost, useful
                                     # for a quick smoke test of the eval
                                     # pipeline itself
    python run_eval.py --output results/my_run.json
"""

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone

from app import MODELS, _call_one_model, judge_responses
from eval_prompts import EVAL_PROMPTS

# How many of the eval prompts (from the front of the list) get a second,
# repeat judge call for the self-consistency check. Keeps total API calls
# reasonable while still giving a meaningful consistency signal.
CONSISTENCY_CHECK_COUNT = 5


def _mock_call_one_model(model: str, prompt: str) -> dict:
    """A stand-in for app._call_one_model that never hits the network.

    Used only when --mock is passed, so the eval pipeline itself (prompt
    iteration, aggregation, JSON output, consistency checking) can be
    exercised without spending real API credits.
    """
    return {
        "model": model,
        "response": f"[mock response from {model} for: {prompt[:40]}...]",
        "error": None,
    }


def _mock_judge_responses(prompt: str, results: list) -> dict:
    """A stand-in for app.judge_responses used only in --mock mode.

    Deterministically "picks" a winner based on the prompt, so repeated
    calls with the same prompt/results are consistent with each other,
    similar to how a real (well-behaved) judge should behave.
    """
    candidates = [r for r in results if r["error"] is None]
    if not candidates:
        return {"winner": None, "reasoning": None, "error": "No candidates."}
    winner_index = len(prompt) % len(candidates)
    return {
        "winner": candidates[winner_index]["model"],
        "reasoning": "[mock reasoning: chosen deterministically for testing]",
        "error": None,
    }


def run_pipeline_for_prompt(prompt_entry: dict, mock: bool) -> dict:
    """Run the 5-model + judge pipeline for a single eval prompt entry.

    Returns a dict capturing the prompt metadata, each model's response,
    and the judge's verdict.
    """
    call_one_model = _mock_call_one_model if mock else _call_one_model
    judge = _mock_judge_responses if mock else judge_responses

    prompt_text = prompt_entry["prompt"]
    results = [call_one_model(model, prompt_text) for model in MODELS]
    judgment = judge(prompt_text, results)

    return {
        "id": prompt_entry["id"],
        "category": prompt_entry["category"],
        "prompt": prompt_text,
        "results": results,
        "judgment": judgment,
    }


def check_judge_consistency(
    prompt_text: str, results: list, mock: bool, judge_fn=None
) -> dict:
    """Re-run just the judge step a second time on the same responses.

    Returns a dict describing whether the judge picked the same winner
    both times, along with both winners for reference.

    An explicit judge_fn can be passed in (primarily for tests) to
    override the default choice of mock vs. real judge_responses.
    """
    judge = judge_fn or (_mock_judge_responses if mock else judge_responses)

    first = judge(prompt_text, results)
    second = judge(prompt_text, results)

    consistent = first["winner"] is not None and first["winner"] == second["winner"]
    return {
        "first_winner": first["winner"],
        "second_winner": second["winner"],
        "consistent": consistent,
    }


def summarize(eval_results: list, consistency_results: list) -> dict:
    """Aggregate per-prompt results into overall summary statistics.

    - win_counts: how many times each model was picked as the winner
      across all eval prompts (models that never won are omitted).
    - total_judged: how many prompts had a non-error judgment.
    - consistency_rate: fraction of the consistency-checked prompts where
      the judge picked the same winner both times (None if no checks
      were run).
    """
    win_counts = Counter()
    total_judged = 0

    for entry in eval_results:
        winner = entry["judgment"]["winner"]
        if winner is not None:
            win_counts[winner] += 1
            total_judged += 1

    if consistency_results:
        consistent_count = sum(1 for c in consistency_results if c["consistent"])
        consistency_rate = consistent_count / len(consistency_results)
    else:
        consistency_rate = None

    return {
        "total_prompts": len(eval_results),
        "total_judged": total_judged,
        "win_counts": dict(win_counts),
        "consistency_checks_run": len(consistency_results),
        "consistency_rate": consistency_rate,
    }


def run_eval(mock: bool = False) -> dict:
    """Run the full eval suite and return {results, consistency, summary}."""
    eval_results = []
    consistency_results = []

    for i, prompt_entry in enumerate(EVAL_PROMPTS):
        entry = run_pipeline_for_prompt(prompt_entry, mock)
        eval_results.append(entry)

        if i < CONSISTENCY_CHECK_COUNT:
            consistency = check_judge_consistency(
                entry["prompt"], entry["results"], mock
            )
            consistency["id"] = prompt_entry["id"]
            consistency_results.append(consistency)

    summary = summarize(eval_results, consistency_results)

    return {
        "results": eval_results,
        "consistency_checks": consistency_results,
        "summary": summary,
    }


def print_summary(summary: dict) -> None:
    print("\n=== Eval Summary ===")
    print(f"Prompts evaluated: {summary['total_prompts']}")
    print(f"Prompts successfully judged: {summary['total_judged']}")

    print("\nWins per model:")
    if summary["win_counts"]:
        for model, count in sorted(
            summary["win_counts"].items(), key=lambda kv: -kv[1]
        ):
            print(f"  {model}: {count}")
    else:
        print("  (no wins recorded)")

    print(
        f"\nJudge self-consistency: {summary['consistency_checks_run']} checks run, "
        + (
            f"{summary['consistency_rate']:.0%} consistent"
            if summary["consistency_rate"] is not None
            else "N/A"
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use canned fake responses instead of calling real APIs.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write the JSON results file (default: "
        "eval_results/eval_<timestamp>.json)",
    )
    args = parser.parse_args()

    output_path = args.output
    if output_path is None:
        os.makedirs("eval_results", exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join("eval_results", f"eval_{timestamp}.json")

    print(f"Running eval over {len(EVAL_PROMPTS)} prompts (mock={args.mock})...")
    output = run_eval(mock=args.mock)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Full results written to {output_path}")

    print_summary(output["summary"])


if __name__ == "__main__":
    main()
