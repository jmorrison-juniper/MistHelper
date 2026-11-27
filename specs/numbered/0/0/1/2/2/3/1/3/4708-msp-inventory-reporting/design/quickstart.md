# Quickstart: MSP inventory batch coverage

This guide shows how to reproduce the defect and how to run the gates for this change. It uses mocks only. It makes no live Mist call.

## Prerequisites

- A worktree on the branch `fix/4708-msp-inventory-reporting`, created from `main`.
- The `.venv` folder of that worktree. Run `python scripts/bootstrap_worktree.py` only when `.venv` is absent. `documentation/development-setup.md` describes the bootstrap.
- Activate the environment with `.venv\Scripts\Activate.ps1` on Windows, or with `source .venv/bin/activate` on macOS and Linux.

## Reproduce the Defect

1. Read `src/mist/resources/inventory/org_device_inventory_msp.py` line 516. The line prints the record count as the processed count.
2. Read the remote evidence in `design/research.md`, rows R-14, R-15, and R-16. These rows confirm the same lines on `main`.
3. After T003 adds the new tests, run this command on `main`:

```text
python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py -k "footer or continues or zero or empty" -q
```

Expected result on `main`: the tests `footer_reports_partial_skip_and_failure`, `continues_after_earlier_failure`, and `zero_successes_writes_no_combined_reports` fail. The tests `footer_reports_complete_coverage` and `empty_successful_result_counts_as_success` pass.

## Verify the Change

Run these steps after T008.

1. Run the focused module tests:

```text
python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py
```

Expected result: all tests pass. The module holds 49 tests after the change, with 41 existing tests and 8 new tests.

2. Confirm that the partial footer prints for a mixed batch. Use the test `test_execute_msp_footer_reports_partial_skip_and_failure` as the evidence. Do not run a live batch.

## Gate Run

Run each gate below after activating `.venv`. Record each result in the pull request body. A gate that does not apply names its reason.

| Gate | Command | Expected result |
| --- | --- | --- |
| Lint | `python -m ruff check .` | `All checks passed!` |
| Format | `python -m black --check .` | No file needs a change. |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success`. The scope comes from `MYPY_PATHS` in `.github/workflows/ci.yml` line 93. |
| Tests | `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py` | All tests pass. |
| Full tests | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | Coverage is 80 percent or above. The run may take a long time. |
| Test quality | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc src/mist/resources/inventory/org_device_inventory_msp.py -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10. |
| Security lint | `bandit -c pyproject.toml -r src/mist/resources/inventory/org_device_inventory_msp.py -q` | No finding at any severity. |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above. The threshold comes from `.github/workflows/ci.yml` line 122. |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding. |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation. Docstring coverage is 90 percent or above. |
| Menu reference | `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` | No changed file after the run. |
| Symbols | `symbol-diff --base origin/main src/mist/resources/inventory/org_device_inventory_msp.py` | Exit code 0. No existing module-level name is removed or changed. Added names are listed. |
| Safe sweep | `python MistHelper.py --test` | Run only when no `MIST_APITOKEN` or `MIST_API_TOKEN` variable is set. Menu 13 belongs to the `safe` category, so the sweep runs it. |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4708-msp-inventory-reporting.md specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/spec.md specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/plan.md specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/tasks.md specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/analysis.md` | Each file scores 80 or above. |
| Citations | `check-citations src tests` | Every code citation resolves. |
| Diagram references | `diagram-refs --source-files MistHelper.py src/ --allowlist-file .github/diagram-refs-allowlist.txt` | Every diagram reference resolves. |
| Task audit | `speckit-task-audit` | Advisory. The report lists the open task boxes in this record. |

Gates that do not apply to this change:

- Compile (`python -m py_compile MistHelper.py`): this change does not edit `MistHelper.py`.
- Dependency audit (`pip-audit -r requirements.txt`): the change edits no dependency manifest.
- Full tests with `pytest-chunks`: the two shards cover the upgrade portal trees. The change edits no portal file.
- Ops portal and ops platform gates: the change edits no file in `ops-portal/` or `mist-ops-platform/`.
- End-to-end browser gate: the change edits no web UI file.
- Container build: the change edits no `Containerfile` and no compose file.
- Move-module gates: the change moves no module.
