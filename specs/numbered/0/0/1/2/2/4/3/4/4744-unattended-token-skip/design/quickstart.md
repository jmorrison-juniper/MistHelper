# Quickstart: Unattended token skip for menu 247

This page gives the reproduction steps and the verification commands for issue #4744. The reproduction uses mocks. It makes no Mist request and needs no token.

## Prerequisites

- An implementation worktree of the repository. Use the bootstrap steps in `.github/copilot-instructions.md`: install Python 3.15.2 through UV, then create `.venv`.
- Do not set `MIST_APITOKEN` or `MIST_API_TOKEN` for these commands. The mocked tests need neither variable.

## Reproduce the Defect

1. Open the implementation worktree in PowerShell. Activate the environment.

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. Run the regression on the current code.

   ```powershell
   python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py -k "menu_247" -q
   ```

3. Expected result on the current code: the regression fails. The captured events hold one pass event and no skip event. The verification mock and the writer mock record no calls.

## Verify the Fix

1. Run the new and changed tests in the runner test module.

   ```powershell
   python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py -k "menu_247 or provider or operator_prompt or skip_in_summary" -q
   ```

   Expected result: each selected test passes.

2. Run the whole runner test module.

   ```powershell
   python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py -q
   ```

3. Run the exporter, the action, and the standalone test modules.

   ```powershell
   python -m pytest tests/unit/export/test_self_account_exporter.py tests/unit/marvis/actions/test_selection.py tests/unit/marvis/actions/test_operation.py tests/unit/config/standalone/foundation/runtime/startup/test_standalone_interactive_test_runner.py -q
   ```

## Local Gates

Run each command in the implementation worktree. Task T-LOCAL-GATES runs this list. The expected results come from the local gates table in `.github/copilot-instructions.md`.

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile MistHelper.py` | No output |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| Changed tests | `python -m pytest tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py tests/unit/export/test_self_account_exporter.py tests/unit/marvis/actions/test_selection.py tests/unit/marvis/actions/test_operation.py -q` | All tests pass |
| Guardrails | `python -m pytest tests/guardrails -q` | All tests pass |
| Full tests, shard 1 | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` | One summary line, no failed chunk |
| Full tests, shard 2 | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | One summary line, no failed chunk |
| Safe sweep | `python MistHelper.py --test` | Each safe operation completes |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | Combined coverage is 80 percent or above |
| Test quality preflight | `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | All tests pass |
| Test quality | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc src/foundation/support/menu_testing -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10 |
| Security lint | `bandit -c pyproject.toml -r src/foundation/support/menu_testing -q` | No finding |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation, and coverage is 90 percent or above |
| Menu reference | `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`, then `git status --short` | No generated file changes |
| Symbols | `symbol-diff --base origin/main src/foundation/support/menu_testing/interactive_test_runner.py` | `no module-level name changed`, exit code 0 |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 documentation/cli-reference.md` | Score 80 or above |
| Not applicable | `pip-audit -r requirements.txt`, the ops portal gates, and the ops platform gates | Not applicable. The change touches no dependency, portal, or platform file. State this in the pull request. |

## Notes

- Run the test quality required check after the local commit and before the push.
- Record each gate result in the pull request body. Do not record a result for a gate that did not run.
- Do not run `python MistHelper.py --testinteractive` with a real token for this issue. The unattended sweep calls the Mist API for other options.
