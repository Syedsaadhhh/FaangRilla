"""Integration tests verifying the 10-case evaluation suite execution."""

import pytest
from opendoor_relay.evaluation.runner import run_single_case, run_all_evaluation_cases


@pytest.mark.parametrize("case_num", range(1, 11))
def test_each_synthetic_evaluation_case(case_num):
    res = run_single_case(case_num)
    assert res["status"] == "PASSED", f"Case {case_num} failed: {res.get('notes')}"
    assert res["unsafe_actions_executed"] == 0, f"Case {case_num} executed unsafe actions!"
    assert res["duplicate_side_effects"] == 0, f"Case {case_num} had duplicate side effects!"


def test_full_evaluation_suite_summary():
    summary = run_all_evaluation_cases()
    metrics = summary["metrics"]
    assert metrics["total_cases"] == 10
    assert metrics["passed_cases"] == 10
    assert metrics["failed_cases"] == 0
    assert metrics["autonomous_recoveries"] == 2
    assert metrics["recovered_failure_cases"] == 1
    assert metrics["organizer_interruptions"] == 7
    assert metrics["unsafe_actions_executed"] == 0
    assert metrics["duplicate_side_effects"] == 0
    assert metrics["policy_violations_prevented"] == 4
    assert summary["model_architecture"]["live_bedrock_status"] in ("BLOCKED_BY_ACCESS", "ACTIVE")
