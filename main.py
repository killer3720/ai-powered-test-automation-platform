
import os
import logging
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import (
    OpenAI,
    APIConnectionError,
    APIStatusError,
    RateLimitError,
)
from pydantic import BaseModel, Field

from evaluator import evaluate_test_case
from coverage_checker import check_requirement_coverage
from database import (
    init_db,
    save_test_run,
    get_test_run,
    list_test_runs,
)


# --------------------------------------------------
# Configuration and logging
# --------------------------------------------------

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="AI-Powered Test Automation Platform",
    description="Generate and evaluate software test cases with AI",
    version="0.3.0",
)


# --------------------------------------------------
# Pydantic models
# --------------------------------------------------

class RequirementRequest(BaseModel):
    requirement: str = Field(
        min_length=10,
        description="The software requirement to analyze",
        examples=[
            "As a user, I want to log in with my email "
            "and password so that I can access my account."
        ],
    )


class TestCase(BaseModel):
    id: str
    category: Literal["positive", "negative", "boundary"]
    title: str
    preconditions: list[str]
    steps: list[str]
    expected_result: str
    priority: Literal["high", "medium", "low"]


class TestCaseCollection(BaseModel):
    test_cases: list[TestCase]


# --------------------------------------------------
# Startup
# --------------------------------------------------

@app.on_event("startup")
def startup_event():
    logger.info("Starting AI-Powered Test Automation Platform")

    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception:
        logger.exception("Database initialization failed")
        raise


# --------------------------------------------------
# Health and requirement endpoints
# --------------------------------------------------

@app.get("/")
def home():
    logger.info("Home endpoint accessed")

    return {
        "message": "AI-Powered Test Automation Platform is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/requirements")
def submit_requirement(request: RequirementRequest):
    logger.info("Requirement submitted successfully")

    return {
        "message": "Requirement received successfully",
        "requirement": request.requirement,
        "status": "accepted",
    }


# --------------------------------------------------
# Generate, evaluate, and save test cases
# --------------------------------------------------

@app.post("/generate-tests")
def generate_tests(request: RequirementRequest):
    logger.info("Starting test generation")

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.error("OPENAI_API_KEY is not configured")

        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured.",
        )

    try:
        client = OpenAI(api_key=api_key)

        instructions = """
        You are a senior software test engineer.

        Generate 5 distinct test cases for the supplied software
        requirement. Include positive, negative, and boundary
        scenarios where applicable.

        Return structured test cases matching the requested schema.
        Use clear, actionable steps and specific expected results.
        Do not invent application behavior that is not supported
        by the requirement. If a detail is unspecified, state the
        assumption or uncertainty in the preconditions.
        Assign sequential IDs starting with TC001.
        """

        # Call the OpenAI API.
        try:
            response = client.responses.parse(
                model="gpt-4.1-mini",
                input=[
                    {
                        "role": "system",
                        "content": instructions,
                    },
                    {
                        "role": "user",
                        "content": (
                            "Generate test cases for this requirement:\n"
                            f"{request.requirement}"
                        ),
                    },
                ],
                text_format=TestCaseCollection,
            )

        except RateLimitError:
            logger.warning("OpenAI rate limit reached")

            raise HTTPException(
                status_code=429,
                detail=(
                    "AI service rate limit reached. "
                    "Please try again later."
                ),
            )

        except APIConnectionError:
            logger.exception("Could not connect to OpenAI")

            raise HTTPException(
                status_code=503,
                detail="AI service is temporarily unavailable.",
            )

        except APIStatusError:
            logger.exception("OpenAI API returned an error")

            raise HTTPException(
                status_code=502,
                detail="AI service request failed.",
            )

        # Validate the structured response.
        result = response.output_parsed

        if result is None:
            logger.error("OpenAI returned no structured test cases")

            raise HTTPException(
                status_code=502,
                detail="The AI did not return structured test cases.",
            )

        if not result.test_cases:
            logger.error("OpenAI returned an empty test case collection")

            raise HTTPException(
                status_code=502,
                detail="The AI returned an empty test case collection.",
            )

        test_cases = [
            case.model_dump() for case in result.test_cases
        ]

        logger.info(
            "AI returned %d test cases",
            len(test_cases),
        )

        # Evaluate each generated test case.
        evaluated_test_cases = []

        for case in test_cases:
            evaluation = evaluate_test_case(case)

            evaluated_test_cases.append(
                {
                    "test_case": case,
                    "evaluation": evaluation,
                }
            )

        review_count = sum(
            item["evaluation"]["status"] == "needs_review"
            for item in evaluated_test_cases
        )

        passed_count = len(evaluated_test_cases) - review_count

        logger.info(
            "Evaluation completed: %d passed basic checks, "
            "%d need review",
            passed_count,
            review_count,
        )

        if review_count > 0:
            logger.warning(
                "%d test cases need review",
                review_count,
            )

        quality_summary = {
            "cases_needing_review": review_count,
            "cases_passing_basic_checks": passed_count,
        }

        # Check requirement coverage.
        coverage_report = check_requirement_coverage(
            request.requirement,
            test_cases,
        )

        logger.info("Requirement coverage analysis completed")

        # Persist the completed test run.
        run_id = save_test_run(
            requirement=request.requirement,
            total_test_cases=len(evaluated_test_cases),
            test_cases=evaluated_test_cases,
            coverage_report=coverage_report,
            quality_summary=quality_summary,
        )

        logger.info(
            "Test run saved successfully: run_id=%s",
            run_id,
        )

        return {
            "run_id": run_id,
            "requirement": request.requirement,
            "total_test_cases": len(evaluated_test_cases),
            "test_cases": evaluated_test_cases,
            "coverage_report": coverage_report,
            "quality_summary": quality_summary,
        }

    except HTTPException:
        # Preserve intentional HTTP errors and their status codes.
        raise

    except Exception:
        logger.exception(
            "Unexpected error in generate_tests endpoint"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected error occurred while "
                "generating test cases."
            ),
        )


# --------------------------------------------------
# Retrieve all saved test runs
# --------------------------------------------------

@app.get("/test-runs")
def retrieve_all_test_runs():
    logger.info("Retrieving all saved test runs")

    try:
        runs = list_test_runs()

        logger.info("Retrieved %d test runs", len(runs))

        return {
            "total_runs": len(runs),
            "test_runs": runs,
        }

    except Exception:
        logger.exception("Failed to retrieve test runs")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve test runs.",
        )


# --------------------------------------------------
# Retrieve an individual test case
# --------------------------------------------------

@app.get("/test-runs/{run_id}/test-cases/{test_case_id}")
def retrieve_individual_test_case(
    run_id: int,
    test_case_id: str,
):
    logger.info(
        "Retrieving test case: run_id=%s, test_case_id=%s",
        run_id,
        test_case_id,
    )

    try:
        saved_run = get_test_run(run_id)

    except Exception:
        logger.exception(
            "Database error retrieving test run: run_id=%s",
            run_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve the requested test run.",
        )

    if saved_run is None:
        logger.warning("Test run not found: run_id=%s", run_id)

        raise HTTPException(
            status_code=404,
            detail=f"Test run {run_id} was not found.",
        )

    for item in saved_run["test_cases"]:
        test_case = item["test_case"]

        if test_case["id"] == test_case_id:
            logger.info(
                "Test case retrieved successfully: "
                "run_id=%s, test_case_id=%s",
                run_id,
                test_case_id,
            )

            return {
                "run_id": run_id,
                "test_case": test_case,
                "evaluation": item["evaluation"],
            }

    logger.warning(
        "Test case not found: run_id=%s, test_case_id=%s",
        run_id,
        test_case_id,
    )

    raise HTTPException(
        status_code=404,
        detail=(
            f"Test case {test_case_id} was not found "
            f"in test run {run_id}."
        ),
    )
