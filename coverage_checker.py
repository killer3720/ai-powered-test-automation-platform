
def check_requirement_coverage(
    requirement: str,
    test_cases: list[dict],
) -> dict:
    """Check whether basic login scenarios appear in the test suite."""

    requirement_lower = requirement.lower()

    scenarios = {
        "successful_login": ["login", "log in", "sign in"],
        "invalid_credentials": ["invalid credentials", "incorrect password"],
        "access_denied": ["denied", "reject", "not grant access"],
    }

    suite_text = " ".join(
        [
            str(case.get("title", ""))
            + " "
            + str(case.get("expected_result", ""))
            + " "
            + " ".join(case.get("steps", []))
            for case in test_cases
        ]
    ).lower()

    results = {}

    for scenario, keywords in scenarios.items():
        requirement_mentions_scenario = any(
            keyword in requirement_lower for keyword in keywords
        )

        if requirement_mentions_scenario:
            results[scenario] = any(
                keyword in suite_text for keyword in keywords
            )

    total = len(results)
    covered = sum(results.values())

    return {
        "coverage_score": (
            round(covered / total * 100) if total else None
        ),
        "scenarios": results,
        "covered_scenarios": covered,
        "applicable_scenarios": total,
    }
