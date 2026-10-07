# Quickstart: Validate Portal Run Evidence Isolation

## Prerequisites

Build the worktree environment once.

```powershell
python scripts\bootstrap_worktree.py
```

Activate the environment.

```powershell
.\.venv\Scripts\Activate.ps1
```

## Focused validation

Run the synchronized isolation and existing portal regression tests.

```powershell
python -m pytest tests\unit\web_portal\test_portal_run_isolation.py tests\unit\test_operation_output_file_discovery.py tests\unit\web_portal\test_output_scan_runtime_files.py tests\unit\web_portal\test_output_scan_clock_race.py tests\unit\web_portal\test_portal_log_routing.py tests\unit\web_portal\test_operation_run_registry_caps.py tests\unit\web_portal\test_operation_output_files_cap.py tests\unit\web_portal\test_event_bus.py tests\unit\web_portal\test_event_bus_deadlock.py tests\unit\web_portal\test_portal_silent_completion.py -q
```

Expected result:

- Both synchronized workers are active before release.
- Each run keeps only its logs, debug logs, discard count, and files.
- Each SSE subscriber receives only its requested run.
- Ambiguous paths appear in neither run.
- Single-run new-file and rewrite fallback tests pass.
- Hooks restore after both completion orders and exception cases.

Run the existing browser workflow.

```powershell
python -m pytest tests\e2e\web_portal\test_operations_panel_workflow.py -q
```

Expected result:

- The Results panel still selects the first ordered previewable output.

## Static and quality gates

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
radon cc web_portal\services\operation.py web_portal\services\output_scan.py -j | complexity-gate --max 10
bandit-exclude-check
python -m bandit -c pyproject.toml -r .
vulture src\ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src\ wsgi.py web_portal
interrogate src\ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v
symbol-diff --base origin\main web_portal\services\operation.py
symbol-diff --base origin\main web_portal\services\output_scan.py
```

The current CI mypy and coverage scopes do not inspect `web_portal`.
Do not use those gates as proof of portal isolation.

## Test quality ratchet

Run the live guidance check first.

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides
```

After the implementation commit, run the changed-test gate.

```powershell
test-quality-analyzer --gate `
  --config .github\test-quality-config.toml `
  --baseline .github\test-quality-baseline.json `
  --changed-from origin\main `
  --full-gate-path .github\workflows\ci.yml `
  --full-gate-path requirements-dev.txt
```

Before the push, run both `pytest-chunks` commands from `.github/copilot-instructions.md`.
Run the full test-quality gate before a manual CI request.

## Acceptance checks

Use [run-evidence-isolation.md](contracts/run-evidence-isolation.md) as the ownership contract.
Use [data-model.md](data-model.md) for private state and lifecycle rules.
