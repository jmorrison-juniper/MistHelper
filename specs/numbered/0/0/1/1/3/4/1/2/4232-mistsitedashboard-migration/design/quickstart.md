# Validation guide: Site health dashboard

## Boundary

This slice provides an offline measurement model, not a running dashboard.
Do not supply Mist credentials or start a source container.
No Mist call, cloud write, database change, or deployment is required.

## Environment

If the worktree has no environment, run `python3 scripts/bootstrap_worktree.py`.
Use `.venv/bin/python` on macOS or Linux.
On Windows, use `.venv\Scripts\python.exe`.
The workflow requires PowerShell 7 for the installed prerequisite scripts.

Set `SPECIFY_FEATURE_DIRECTORY` to this feature's repository-relative path for each Spec Kit command.
Do not change `.specify/feature.json`.

## Current checks

Run these commands from the repository root:

```bash
.venv/bin/python -m pytest tests/unit/dataclasses/test_service_measurement.py \
  --cov=src.foundation.models.data.service_measurement --cov-report=term-missing --cov-fail-under=100
.venv/bin/python -m ruff check src/foundation/models/data/service_measurement.py tests/unit/dataclasses/test_service_measurement.py
.venv/bin/python -m black --check src/foundation/models/data/service_measurement.py tests/unit/dataclasses/test_service_measurement.py
.venv/bin/python -m mypy src/foundation/models/data/service_measurement.py --config-file pyproject.toml
.venv/bin/bandit -c pyproject.toml -r src/foundation/models/data/service_measurement.py -q
```

Expect exact score results, explicit invalid-input errors, and full changed-module coverage.
Run STE and local-link checks on every generated Markdown artifact.
Run `speckit-task-audit` against the committed task record.
The [analysis](../analysis.md) records actual commands and results, including unavailable gates.

## Future validation

After the blockers close, add mocked SDK integration tests for the [API contracts](contracts/api.md).
Add browser tests for the eight views in the [portal contract](contracts/portal.md).
Cover empty data, partial refresh, denied access, invalid input, exports, HTTP failures, and stale responses.
Do not substitute a successful model test for these undelivered checks.

Before committing tests, run applicable formatting, lint, types, docstrings, complexity, and security checks.
After committing, run the documented test-quality preflight and changed-test ratchet.
Do not change the quality baseline to hide a new finding.
