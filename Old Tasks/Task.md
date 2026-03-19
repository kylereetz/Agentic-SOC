# Current Task
Refactor the `approve_action` function in `soc/api/main.py` to handle invalid action IDs gracefully.

## Requirements
1. Locate the `approve_action` endpoint at `@app.post("/approve/{action_id}")` in `soc/api/main.py`.
2. Currently, the endpoint raises a 404 `HTTPException` if `responder.approve_action(action_id)` returns `False`.
3. Enhance this logic: add input validation for the `action_id` parameter to ensure it is not empty and matches the expected alphanumeric/UUID pattern.
4. Integrate the Python `logging` module to log a warning or error when an invalid format is detected or when the action is not found, ensuring the failed attempt is recorded in the SOC audit logs.
5. Write or update a test in `soc/tests/test_main.py` to verify that an invalid `action_id` correctly triggers the 404 and the new logging mechanism without crashing the application.