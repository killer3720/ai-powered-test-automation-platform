from typing import Any

def evaluate_test_case( test_case : dict[str, Any]) ->dict[str, Any]:
    """Evaluate basic completeness and claruty of a generated test case."""

    title = test_case.get("title")
    preconditon = test_case.get("preconditions")
    steps = test_case.get("steps")
    expected_result = test_case.get("expected_result")

    checks = {
        "has_title" : bool(test_case.get("title", "").strip()),
        "has_preconditions": bool(test_case.get("preconditions")),
        "has_steps": bool(test_case.get("steps")),
        "has_expected_result": bool(
            test_case.get("expected_result", "").strip()
        ),
        "steps_are_actionable" : all(
            isinstance( step, str ) and len(step.strip()) >= 5
            for step in test_case.get("steps", [])
        ),
    }
    passed = sum(checks.values())
    total = len(checks)
    score = round((passed/total) * 100)

    # These are mandatory for a test case to be considered complete
    mandatory_checks_passed = (
        checks["has_title"] and checks["has_steps"] and checks["has_expected_result"]
    )
    if mandatory_checks_passed and score >= 75:
        status = "pass"
    else:
        status = "needs_review"

    return {
        "score" : score,
        "checks" : checks,
        "passed_checks" : passed,
        "total_checks" : total,
        "status" : status,
    }