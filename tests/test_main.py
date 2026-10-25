
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(monkeypatch):
    # Avoid initializing or changing the real database during tests.
    monkeypatch.setattr(main, "init_db", lambda: None)

    # Use a predictable ID instead of saving a real test run.
    monkeypatch.setattr(
        main,
        "save_test_run",
        Mock(return_value=123),
    )

    with TestClient(main.app) as test_client:
        yield test_client


def test_home_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_requirement_rejects_short_input(client):
    response = client.post(
        "/requirements",
        json={"requirement": "Login"},
    )

    assert response.status_code == 422


def test_generate_tests_without_api_key(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/generate-tests",
        json={
            "requirement": (
                "Users can log in using their registered email "
                "and password"
            )
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "OPENAI_API_KEY is not configured."
    )


def test_generate_tests_success(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Prepare a deterministic test case; no real AI call is made.
    fake_case = main.TestCase(
        id="TC001",
        category="positive",
        title="Verify successful login",
        preconditions=["A registered user exists"],
        steps=[
            "Enter a registered email",
            "Enter the correct password",
            "Click the Login button",
        ],
        expected_result="The user logs in successfully.",
        priority="high",
    )

    fake_collection = main.TestCaseCollection(
        test_cases=[fake_case],
    )

    # Mock the OpenAI client and its structured-output response.
    fake_client = Mock()
    fake_client.responses.parse.return_value = SimpleNamespace(
        output_parsed=fake_collection,
    )

    monkeypatch.setattr(
        main,
        "OpenAI",
        Mock(return_value=fake_client),
    )

    response = client.post(
        "/generate-tests",
        json={
            "requirement": (
                "Users can log in using their registered email "
                "and password"
            )
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["run_id"] == 123
    assert body["total_test_cases"] == 1
    assert body["test_cases"][0]["test_case"]["id"] == "TC001"
    assert "evaluation" in body["test_cases"][0]
    assert "coverage_report" in body
    assert "quality_summary" in body

    main.save_test_run.assert_called_once()
    fake_client.responses.parse.assert_called_once()


def test_retrieve_existing_run(client, monkeypatch):
    saved_runs = [
        {
            "id": 1,
            "requirement": "Users can log in.",
            "total_test_cases": 1,
            "coverage_report": {},
            "quality_summary": {},
            "created_at": "2026-10-24 12:00:00",
        }
    ]

    monkeypatch.setattr(
        main,
        "list_test_runs",
        lambda: saved_runs,
    )

    response = client.get("/test-runs")

    assert response.status_code == 200

    body = response.json()

    # The endpoint wraps the list in a dictionary.
    assert body["total_runs"] == 1
    assert len(body["test_runs"]) == 1
    assert body["test_runs"][0]["id"] == 1
    assert (
        body["test_runs"][0]["requirement"]
        == "Users can log in."
    )


def test_retrieve_missing_run_returns_404(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_test_run",
        lambda run_id: None,
    )

    response = client.get("/test-runs/999999")

    assert response.status_code == 404
