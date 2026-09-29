# Quickstart: Alert Digest Acknowledge

## Prerequisites

- Use the assigned worktree `C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge`.
- Use `C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe` for every Python command.
- Do not edit integration-owned files in this feature branch.

## Validate the digest path

1. Run the unit tests for the feature.

   ```powershell
   C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -m pytest tests\unit\reports\alert_digest -q --timeout=120
   ```

2. Confirm the tests prove that menu 280 writes `AlertDigest.csv` and `AlertDigest.md` with no prompt.

3. Confirm the tests prove that an unknown alarm type receives category `unknown`.

## Validate the acknowledgement path

1. Run the operation tests.

   ```powershell
   C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -m pytest tests\unit\reports\alert_digest\test_alert_digest_operation.py -q --timeout=120
   ```

2. Confirm the tests prove that a wrong confirmation sends no request.

3. Confirm the tests prove that `--dry-run` sends no request and reports each alarm ID.

4. Confirm the tests prove that `ACK <count>` sends one bulk request and writes one result row per alarm ID.

## Run local gates

```powershell
C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -m py_compile src\reports\alert_digest\__init__.py src\reports\alert_digest\client.py src\reports\alert_digest\model.py src\reports\alert_digest\operation.py src\reports\alert_digest\prompts.py src\reports\alert_digest\writer.py
C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -m ruff check src\reports\alert_digest tests\unit\reports\alert_digest
C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -m black --check src\reports\alert_digest tests\unit\reports\alert_digest
C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -m mypy src\reports\alert_digest --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -m pydocstyle src\reports\alert_digest
C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -m pytest tests\unit\reports\alert_digest -q --timeout=120
C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -m vulture src\reports\alert_digest --min-confidence 70
C:\Users\jmorrison\mh-fleet\3561-alert-digest-acknowledge\.venv\Scripts\python.exe -m interrogate -v src\reports\alert_digest
```
