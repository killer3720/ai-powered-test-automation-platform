
import sqlite3
import json

connection = sqlite3.connect("test_runs.db")

runs = connection.execute(
    """
    SELECT id, test_cases_json
    FROM test_runs
    ORDER BY id DESC
    """
).fetchall()

for run_id, test_cases_json in runs:
    test_cases = json.loads(test_cases_json)

    print(f"\nTest Run ID: {run_id}")

    for item in test_cases:
        # Each item contains a test_case and its evaluation.
        test_case = item["test_case"]

        print(
            f"Test Case ID: {test_case['id']} | "
            f"Title: {test_case['title']}"
        )

connection.close()
