
import sqlite3
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Store the SQLite database in the project directory.
DATABASE_PATH = Path(__file__).resolve().parent / "test_automation.db"


def get_connection():
    """Create and return a SQLite database connection."""
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the database tables if they do not already exist."""
    logger.info("Initializing SQLite database")

    try:
        with get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requirement TEXT NOT NULL,
                    total_test_cases INTEGER NOT NULL,
                    test_cases TEXT NOT NULL,
                    coverage_report TEXT NOT NULL,
                    quality_summary TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

        logger.info("SQLite database initialized successfully")

    except sqlite3.Error:
        logger.exception("Failed to initialize SQLite database")
        raise


def save_test_run(
    requirement: str,
    total_test_cases: int,
    test_cases: list[dict[str, Any]],
    coverage_report: dict[str, Any],
    quality_summary: dict[str, Any],
) -> int:
    """Save a completed test run and return its database ID."""
    logger.info("Saving test run with %d test cases", total_test_cases)

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO test_runs (
                    requirement,
                    total_test_cases,
                    test_cases,
                    coverage_report,
                    quality_summary
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    requirement,
                    total_test_cases,
                    json.dumps(test_cases),
                    json.dumps(coverage_report),
                    json.dumps(quality_summary),
                ),
            )

            run_id = cursor.lastrowid

        if run_id is None:
            raise RuntimeError("Database did not return a test run ID")

        logger.info("Test run saved successfully: run_id=%s", run_id)
        return run_id

    except (sqlite3.Error, TypeError, ValueError):
        logger.exception("Failed to save test run")
        raise


def get_test_run(run_id: int) -> dict[str, Any] | None:
    """Retrieve a test run by ID, returning None if it does not exist."""
    logger.info("Fetching test run: run_id=%s", run_id)

    try:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM test_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()

        if row is None:
            logger.warning("Test run not found: run_id=%s", run_id)
            return None

        result = dict(row)
        result["test_cases"] = json.loads(result["test_cases"])
        result["coverage_report"] = json.loads(
            result["coverage_report"]
        )
        result["quality_summary"] = json.loads(
            result["quality_summary"]
        )

        logger.info("Test run retrieved: run_id=%s", run_id)
        return result

    except (sqlite3.Error, json.JSONDecodeError):
        logger.exception("Failed to retrieve test run: run_id=%s", run_id)
        raise


def list_test_runs() -> list[dict[str, Any]]:
    """Retrieve all test runs, newest first."""
    logger.info("Fetching all test runs")

    try:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    requirement,
                    total_test_cases,
                    coverage_report,
                    quality_summary,
                    created_at
                FROM test_runs
                ORDER BY id DESC
                """
            ).fetchall()

        runs = []

        for row in rows:
            run = dict(row)
            run["coverage_report"] = json.loads(
                run["coverage_report"]
            )
            run["quality_summary"] = json.loads(
                run["quality_summary"]
            )
            runs.append(run)

        logger.info("Retrieved %d test runs", len(runs))
        return runs

    except (sqlite3.Error, json.JSONDecodeError):
        logger.exception("Failed to list test runs")
        raise
