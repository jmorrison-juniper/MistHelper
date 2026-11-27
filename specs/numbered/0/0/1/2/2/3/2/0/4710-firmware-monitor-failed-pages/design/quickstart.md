# Quickstart: Firmware Monitor Treats Failed Stats Pages as Failed Checks

## Prerequisites

- Windows 11 with the repository virtual environment in `.venv`. Activate it with `.venv\Scripts\Activate.ps1`.
- Run every command from the repository root.
- No live Mist token is needed. Every test mocks the SDK calls.
- Do not run live Mist, SSH, firmware, or database operations. The brief and issue #4710 forbid them.

## Scenario 1: Reproduce the Defect Before the Change

This scenario proves the defect with offline tests. It follows the issue reproduction steps, which use synthetic responses.

1. Add tests N1 to N13 from `tasks.md`, Phases 1 and 2. Keep the existing tests unchanged.
2. Run the module:

   ```text
   python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py -q
   ```

3. Expected result before the change: tests N1 to N8, N11, N12, and N13 fail. Tests N9, N10, N14, and the existing tests pass.
4. A failing test for an HTTP 403 or HTTP 503 first page shows a returned count of zero. That count leads to the completion banner.

## Scenario 2: Verify the Fix

1. Run the monitor tests:

   ```text
   python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py -q
   ```

   Expected result: every test passes.

2. Run the firmware unit tests:

   ```text
   python -m pytest tests/unit/firmware -q
   ```

   Expected result: every test passes.

## Scenario 3: Run the Local Gates

Run each command below for the changed files. Stop at the first failed command. Record the output in the pull request.

```text
python -m py_compile MistHelper.py
python -m py_compile src/operations/execution/firmware/firmware_manager.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
python MistHelper.py --test
radon cc src/operations/execution/firmware/firmware_manager.py -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/operations/execution/firmware -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base origin/main src/operations/execution/firmware/firmware_manager.py
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4710-firmware-monitor-failed-pages.md
```

The full-test shards from `.github/copilot-instructions.md` (row Full tests, line 62) are:

```text
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

## Scenario 4: Run the Test-Quality Ratchet

1. Commit the intended tests first. Stop if a relevant change remains unstaged or untracked.
2. Run the required input preflight:

   ```text
   python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
   ```

3. Run the check after the local commit and before the push:

   ```text
   test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
   ```

4. Run the full-suite check before the push:

   ```text
   test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
   ```

   Expected result: `gate: 0 new findings vs baseline`.

## Scenario 5: Confirm the Menu Flow Without a Live Call

This scenario is optional and offline. It does not change any file.

1. Read `MistHelper.py` lines 5192 to 5202 to confirm that menu 137 calls `check_firmware_upgrade_status`.
2. Read `firmware_manager.py` lines 363 to 369 to confirm that scope 5 drops the exit code.
3. Expected result: the operator sees console text only. A scripted caller of `_continuous_monitoring_mode` receives the exit code.
