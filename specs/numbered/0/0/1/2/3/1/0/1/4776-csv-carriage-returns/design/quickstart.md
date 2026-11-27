# Quickstart: Preserve CSV Carriage Returns

Run each command from the worktree root. Activate the project environment first. If `.venv` is missing, run the bootstrap commands named in `.github/copilot-instructions.md`.

```powershell
.venv\Scripts\Activate.ps1
```

## Reproduce the defect on main

Run the shared normalizer test before any change.

```powershell
python -m pytest tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py
```

Expected on `main`: `test_newline_and_cr_escaped` passes. Its assertion at line 267 expects the carriage return to be removed (RC-21). The defect is locked into this test.

Expected after T003 and before T010: the same test fails, because the assertion now expects the carriage return to stay.

## Reproduce the CSV defect

Run the `write_to_csv` tests after T005 and before T012.

```powershell
python -m pytest tests/unit/export/test_data_exporter.py
```

Expected before T012: the new CSV cell test fails. The cell does not show a backslash and `r`. It shows no carriage return at all, because `main` removes it.

## Verify each focused test file

Run each command after T010 to T013. Each command must pass.

```powershell
python -m pytest tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py
python -m pytest tests/unit/config/foundation/models/dataproc/test_csv_cell_presenter.py
python -m pytest tests/unit/export/test_data_exporter.py
python -m pytest tests/unit/export/test_endpoint_family_exporter.py
python -m pytest tests/unit/db/sle_window_summary/test_backend_preservation.py
python -m pytest tests/unit/test_device_events_52w_exporter_extended.py
python -m pytest tests/unit/websocket_streams/web/test_ws_hardware_csv.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
```

## Run the local gates

Run each command in the order shown. Stop at the first failure and repair it.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python MistHelper.py --test
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
radon cc src/foundation/models src/operations/exporting/export -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/foundation/models -q
bandit -c pyproject.toml -r src/operations/exporting/export -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base origin/main src/foundation/models/data/data_processing_utils.py
symbol-diff --base origin/main src/operations/exporting/export/data_exporter.py
symbol-diff --base origin/main src/operations/exporting/export/device_events_52w_exporter.py
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4776-csv-carriage-returns.md
```

Expected results:

- `py_compile` prints no output.
- `ruff check .` prints `All checks passed`.
- `black --check .` reports no file that needs a change.
- `mypy` prints `Success`.
- The coverage command reports 80 percent or above.
- `symbol-diff` reports `no module-level name changed` for each file. The new import can make the tool report an added name. Record that name in the pull request body (R-05).
- `ste-linter` reports a score of 80 or above.

## Run the full test suite

Run both commands from the Full tests row of the local gates table. The run takes a long time (R-08).

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected: each command prints one summary line for each shard. Each shard reports no failure.

## Verify the pull request

Check the commit subject and the branch before the push.

```powershell
python -m py_compile MistHelper.py
git branch --show-current
```

Expected: the branch is `fix/4776-csv-carriage-returns`.

Run this command from the branch that holds the pull request. It watches the checks of the current branch.

```powershell
gh pr checks --watch
```

Expected: every required check reports success before the `auto-merge` label is added.

## Revert the change

Run this command after a revert pull request merges. Expected: the old removal behavior returns, and the test file reports the removal assertion as passing again.

```powershell
python -m pytest tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py
```
