# Quickstart: validate RRM optimize or reset plan capture

## Prerequisites

- Use `C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe`.
- Run commands from `C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan`.
- Do not use a live site for validation unless a maintenance window is approved.

## Unit validation

```powershell
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m pytest tests/unit/site/rrm_reset -q --timeout=120
```

Expected result: all RRM reset tests pass.

## Gate validation

```powershell
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m py_compile src/site/rrm_reset/__init__.py src/site/rrm_reset/client.py src/site/rrm_reset/model.py src/site/rrm_reset/operation.py src/site/rrm_reset/writer.py
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m ruff check src/site/rrm_reset tests/unit/site/rrm_reset
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m black --check src/site/rrm_reset tests/unit/site/rrm_reset
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m mypy src/site/rrm_reset --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3571-rrm-reset-plan\.venv\Scripts\python.exe -m pydocstyle src/site/rrm_reset
```

Expected result: all gates pass.

## Manual dry-run validation

1. Register the deferred menu entry from `wiring.md` in an integration branch.
2. Select menu `291`.
3. Select a site.
4. Select `OPTIMIZE`.
5. Enable dry-run.
6. Confirm that `RrmPlanBefore.csv` is written.
7. Confirm that no Mist change request is sent.

Expected result: only the before capture is written during dry-run.
