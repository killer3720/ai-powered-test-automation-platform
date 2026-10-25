import sqlite3
import json

connection = sqlite3.connect("test_runs.db")
connection.row_factory = sqlite3.Row

# Show all saved test runs
runs = connection.execute(
    """
    SELECT id, requirement, total_test_cases, created_at
    FROM test_runs
    ORDER BY id DESC
    """
).fetchall()

for run in runs:
    print(dict(run))

connection.close()
