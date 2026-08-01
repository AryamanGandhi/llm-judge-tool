"""Tests for the eval script's own logic (summarize, consistency checks).

These test the aggregation/logic in run_eval.py directly against
hand-constructed mock results — they do not run the real pipeline or hit
any APIs, mocked or otherwise.
"""

from run_eval import check_judge_consistency, summarize


def _make_eval_result(id_, winner):
    """Build a minimal eval-result-shaped dict with the given winner."""
    return {
        "id": id_,
        "category": "test",
        "prompt": "irrelevant",
        "results": [],
        "judgment": {"winner": winner, "reasoning": "because", "error": None},
    }


def test_summarize_counts_wins_per_model_correctly():
    eval_results = [
        _make_eval_result("p1", "model-a"),
        _make_eval_result("p2", "model-b"),
        _make_eval_result("p3", "model-a"),
    ]

    summary = summarize(eval_results, consistency_results=[])

    assert summary["total_prompts"] == 3
    assert summary["total_judged"] == 3
    assert summary["win_counts"] == {"model-a": 2, "model-b": 1}
    assert summary["consistency_checks_run"] == 0
    assert summary["consistency_rate"] is None


def test_summarize_excludes_failed_judgments_from_win_counts():
    eval_results = [
        _make_eval_result("p1", "model-a"),
        _make_eval_result("p2", None),  # judge failed for this prompt
    ]

    summary = summarize(eval_results, consistency_results=[])

    assert summary["total_prompts"] == 2
    assert summary["total_judged"] == 1
    assert summary["win_counts"] == {"model-a": 1}


def test_summarize_computes_consistency_rate():
    consistency_results = [
        {
            "id": "p1",
            "first_winner": "model-a",
            "second_winner": "model-a",
            "consistent": True,
        },
        {
            "id": "p2",
            "first_winner": "model-a",
            "second_winner": "model-b",
            "consistent": False,
        },
    ]

    summary = summarize([], consistency_results=consistency_results)

    assert summary["consistency_checks_run"] == 2
    assert summary["consistency_rate"] == 0.5


def test_check_judge_consistency_detects_matching_winners():
    def fake_judge(prompt, results):
        return {"winner": "model-a", "reasoning": "same both times", "error": None}

    result = check_judge_consistency(
        "some prompt", results=[], mock=False, judge_fn=fake_judge
    )

    assert result["consistent"] is True
    assert result["first_winner"] == "model-a"
    assert result["second_winner"] == "model-a"


def test_check_judge_consistency_detects_differing_winners():
    calls = {"count": 0}

    def fake_judge(prompt, results):
        calls["count"] += 1
        winner = "model-a" if calls["count"] == 1 else "model-b"
        return {"winner": winner, "reasoning": "varies", "error": None}

    result = check_judge_consistency(
        "some prompt", results=[], mock=False, judge_fn=fake_judge
    )

    assert result["consistent"] is False
    assert result["first_winner"] == "model-a"
    assert result["second_winner"] == "model-b"


def test_check_judge_consistency_treats_two_failures_as_not_consistent():
    def fake_judge(prompt, results):
        return {"winner": None, "reasoning": None, "error": "judge failed"}

    result = check_judge_consistency(
        "some prompt", results=[], mock=False, judge_fn=fake_judge
    )

    assert result["consistent"] is False
