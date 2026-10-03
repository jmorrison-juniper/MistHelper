# Quickstart: Synthetic Test Trigger

## Prerequisites

- Use the feature worktree.
- Use `C:\Users\jmorrison\mh-fleet\3563-synthetic-test-trigger\.venv\Scripts\python.exe`.
- Provide a valid Mist API session only for a live run.

## Local validation

Run the targeted gates.

```powershell
C:\Users\jmorrison\mh-fleet\3563-synthetic-test-trigger\.venv\Scripts\python.exe -m py_compile src\mist\intelligence\troubleshooting\synthetic_test_trigger\__init__.py src\mist\intelligence\troubleshooting\synthetic_test_trigger\client.py src\mist\intelligence\troubleshooting\synthetic_test_trigger\models.py src\mist\intelligence\troubleshooting\synthetic_test_trigger\operation.py
C:\Users\jmorrison\mh-fleet\3563-synthetic-test-trigger\.venv\Scripts\python.exe -m ruff check src\mist\intelligence\troubleshooting\synthetic_test_trigger tests\unit\troubleshooting\synthetic_test_trigger
C:\Users\jmorrison\mh-fleet\3563-synthetic-test-trigger\.venv\Scripts\python.exe -m black --check src\mist\intelligence\troubleshooting\synthetic_test_trigger tests\unit\troubleshooting\synthetic_test_trigger
C:\Users\jmorrison\mh-fleet\3563-synthetic-test-trigger\.venv\Scripts\python.exe -m mypy src\mist\intelligence\troubleshooting\synthetic_test_trigger --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3563-synthetic-test-trigger\.venv\Scripts\python.exe -m pydocstyle src\mist\intelligence\troubleshooting\synthetic_test_trigger
C:\Users\jmorrison\mh-fleet\3563-synthetic-test-trigger\.venv\Scripts\python.exe -m pytest tests\unit\troubleshooting\synthetic_test_trigger -q --timeout=120
```

## Manual live run after integration

1. Start MistHelper.
2. Select menu `283`.
3. Select a site.
4. Select `site`, `device`, or `radius` scope.
5. Review the summary.
6. Enter `y` only when the trigger is correct.
7. Confirm that `data\SyntheticTestTrigger.csv` contains the request summary and the result.

Expected result: The operation starts one synthetic test, polls until completion or timeout, and writes one safe export row.
