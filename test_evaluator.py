from evaluator import evaluate_test_case

def test_complete_test_case_passes():
    test_case = {
        "title" : "Verify login with valid credentials",
        "preconditions" : ["A registered user exists"],
        "steps": [
            "Enter a valid emial",
            "Enter a valid password",
            "Click the Login button"
        ],
        "expected_result" : "The user is authenticated successfully",
    }

    result =  evaluate_test_case(test_case)

    assert result["score"] == 100
    assert result["status"] == "pass"


def test_missing_expected_result_needs_review():
    test_case = {
        "title": "Verify login",
        "preconditions": ["A registered user exists"],
        "steps": ["Enter valid credentials"],
        "expected_result": "",
    }

    result = evaluate_test_case(test_case)

    assert result["score"] == 80
    assert result["status"] == "needs_review"


def test_empty_steps_needs_review():
    test_case = {
        "title": "Verify login",
        "preconditions": ["A registered user exists"],
        "steps": [],
        "expected_result": "The user is authenticated.",
    }

    result = evaluate_test_case(test_case)

    assert result["status"] == "needs_review"



from evaluator import evaluate_test_case


def test_empty_title_needs_review():
    test_case = {
        "title": "",
        "preconditions": ["A registered user exists"],
        "steps": ["Enter valid credentials"],
        "expected_result": "The user logs in successfully.",
    }

    result = evaluate_test_case(test_case)

    assert result["checks"]["has_title"] is False
    assert result["status"] == "needs_review"


def test_empty_preconditions_reduces_score():
    test_case = {
        "title": "Verify login",
        "preconditions": [],
        "steps": ["Enter valid credentials"],
        "expected_result": "The user logs in successfully.",
    }

    result = evaluate_test_case(test_case)

    assert result["checks"]["has_preconditions"] is False
    assert result["score"] == 80
    assert result["status"] == "pass"


def test_short_step_is_not_actionable():
    test_case = {
        "title": "Verify login",
        "preconditions": ["A registered user exists"],
        "steps": ["Log"],
        "expected_result": "The user logs in successfully.",
    }

    result = evaluate_test_case(test_case)

    assert result["checks"]["steps_are_actionable"] is False
    assert result["score"] == 80
    assert result["status"] == "pass"


def test_empty_steps_need_review():
    test_case = {
        "title": "Verify login",
        "preconditions": ["A registered user exists"],
        "steps": [],
        "expected_result": "The user logs in successfully.",
    }

    result = evaluate_test_case(test_case)

    assert result["checks"]["has_steps"] is False
    assert result["checks"]["steps_are_actionable"] is True
    assert result["score"] == 80
    assert result["status"] == "needs_review"


def test_missing_expected_result_needs_review():
    test_case = {
        "title": "Verify login",
        "preconditions": ["A registered user exists"],
        "steps": ["Enter valid credentials"],
        "expected_result": "",
    }

    result = evaluate_test_case(test_case)

    assert result["checks"]["has_expected_result"] is False
    assert result["score"] == 80
    assert result["status"] == "needs_review"


def test_missing_title_key_needs_review():
    test_case = {
        "preconditions": ["A registered user exists"],
        "steps": ["Enter valid credentials"],
        "expected_result": "The user logs in successfully.",
    }

    result = evaluate_test_case(test_case)

    assert result["checks"]["has_title"] is False
    assert result["status"] == "needs_review"


def test_non_string_step_is_not_actionable():
    test_case = {
        "title": "Verify login",
        "preconditions": ["A registered user exists"],
        "steps": [123],
        "expected_result": "The user logs in successfully.",
    }

    result = evaluate_test_case(test_case)

    assert result["checks"]["steps_are_actionable"] is False
    assert result["status"] == "pass"
