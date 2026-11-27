# Quickstart: Offline Dynamic JVD Labs Preview

Use this guide to reproduce the gap and to verify the change. Run each command from the repository root in PowerShell. Run `.venv\Scripts\Activate.ps1` first.

## Reproduce the current gap

1. Run `python -c "import src.interfaces.labs"`. Expected result: `ModuleNotFoundError`.
2. Run `git grep -n "/labs" -- web_portal`. Expected result: no output. The portal names no Labs route on `main`.
3. Run `git grep -n "labs" -- web_portal/templates/base.html`. Expected result: no output. The navigation holds no Labs anchor.

## Run the tests

Run the test modules in this order after T011 is complete.

1. `python -m pytest tests/integration/web_portal/labs/test_labs_units.py`
2. `python -m pytest tests/integration/web_portal/labs/test_labs_routes.py`
3. `python -m playwright install chromium`
4. `python -m pytest tests/integration/web_portal/labs/test_labs_browser.py`

Expected result: each module reports passes. The browser module reports skips with a stated cause when Chromium is absent.

## Run the gates

Run each command below. Record the summary line and the count of examined files for each gate. Mark a gate as not applicable only with the reason named in this section.

| Gate | Command |
| - | - |
| Compile | `python -m py_compile MistHelper.py` |
| Lint | `python -m ruff check .` |
| Format | `python -m black --check .` |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` |
| Tests | `python -m pytest tests/integration/web_portal/labs` |
| Full tests | Run the two `pytest-chunks` commands in the Local gates section of `.github/copilot-instructions.md` (R-41). |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` |
| Test quality | Run the commands in the Test quality ratchet section of `.github/copilot-instructions.md`. |
| Complexity | `radon cc src/interfaces/labs -j \| complexity-gate --max 10` |
| Security lint | `bandit -c pyproject.toml -r src/interfaces/labs -q` |
| Code quality | `pylint src/ --fail-under=9.5` |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` |
| Symbols | `symbol-diff --base origin/main web_portal/app.py` (after T013 only) |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md changelog.d/issue-4631-offline-jvd-preview.md specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/spec.md specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/plan.md specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/tasks.md specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/analysis.md` |

The STE command lists the spec, plan, tasks, and analysis files. When the record folder is committed, add each file under `design/` to the same command. R-76 gives the gate text.

Not applicable, with the reason:

- Menu reference: no menu operation changes (D-22).
- Safe sweep (`python MistHelper.py --test`): no operation registry or menu changes.
- Ops portal and ops platform gates: no change under `ops-portal/` or `mist-ops-platform/`.
- Dependency audit (`pip-audit -r requirements.txt`): no dependency changes (D-22).
- Container build: no image change occurs before the merge.

## Check the guards

1. `python -m pytest tests/guardrails/test_nested_package_structure.py tests/guardrails/test_src_domain_structure.py tests/guardrails/test_e2e_package_structure.py`
2. `python -m pytest tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_markdown_links.py`
3. `python -m pytest tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py`

## Check the changed files

1. Run `git diff --name-only origin/main`. Expected result: only the paths in `plan.md`, section "File Change Map".
2. Run `git grep -n -i "vmm_topology" -- src tests`. Expected result: one import string in `src/interfaces/labs/planner.py` and no fixture file.
3. Run `git grep -n -i "mistapi" -- src/interfaces/labs`. Expected result: no output.

## Manual check after registration

1. Start the web portal as `documentation/operator-guide.md` describes.
2. Open `http://127.0.0.1:8055/labs/`. Confirm the offline text, the server example, and the run-name form.
3. Submit the default run name. Confirm the device rows, the link rows, and the fingerprint.
4. Submit a run name with a space. Confirm the error panel and no rows.

## Cleanup

- No container starts. No container cleanup applies.
- Remove `test-artifacts/labs-preview/` after review when no screenshot is needed. Git ignores this folder.
