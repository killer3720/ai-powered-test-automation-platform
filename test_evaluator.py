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
