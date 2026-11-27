# Gate Readiness Checklist: Ship the preserved admission scope work

**Purpose**: List each local gate, its command, its expected result, and its applicability before T-LOCAL-GATES starts. The command rows come from the local gates table in `.github/copilot-instructions.md:50`. A checked row means that the command and its expected result are defined. It does not mean that the gate passed. T-LOCAL-GATES records the results.

**Created**: 2026-11-26

**Feature**: [tasks.md](../../tasks.md)

## Changed Files

Source and test files:

- `src/interfaces/wan_performance/collection/request_admission.py`
- `src/foundation/support/utils/logger_utils.py`
- `src/mist/intelligence/reports/subscription_expiry/client.py`
- `src/mist/intelligence/reports/subscription_expiry/sdk_error_lines.py` (new)
- `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`
- `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`

Documents:

- `documentation/operator-guide.md`
- `changelog.d/issue-4943-request-admission-org-scope.md` (new)
- The record files under `specs/numbered/0/0/1/2/4/2/3/3/4943-request-admission-org-scope/`

## Gate Rows

- [x] **Compile**: `python -m py_compile src/interfaces/wan_performance/collection/request_admission.py src/foundation/support/utils/logger_utils.py src/mist/intelligence/reports/subscription_expiry/client.py src/mist/intelligence/reports/subscription_expiry/sdk_error_lines.py`. Expected result: no output.
- [x] **Lint**: `python -m ruff check` with the six changed Python files. Expected result: "All checks passed".
- [x] **Format**: `python -m black --check` with the six changed Python files. Expected result: no file needs a change.
- [x] **Types**: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. The scope comes from `MYPY_PATHS` at `.github/workflows/ci.yml:93`. Expected result: "Success".
- [x] **Tests**: `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. Expected result: all tests pass.
- [x] **Full tests**: the two `pytest-chunks` commands in `.github/copilot-instructions.md`, section Local gates. Expected result: one summary line for each shard, with no failure.
- [x] **Safe sweep**: `python MistHelper.py --test`. Expected result: each safe operation completes. Without a Mist token, the Mist checks skip with a credential reason. Menu 308 is in the safe category (`operation_registry.py:536`).
- [x] **Coverage**: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`. Expected result: coverage of 80 percent or above.
- [x] **Test quality**: the `test-quality-analyzer` procedure in `.github/copilot-instructions.md`, section Test quality ratchet. Expected result: `gate: 0 new findings vs baseline`. Do not edit `.github/test-quality-baseline.json`.
- [x] **Complexity**: `radon cc src/interfaces/wan_performance/collection src/mist/intelligence/reports/subscription_expiry src/foundation/support/utils -j | complexity-gate --max 10`. Expected result: no block above complexity 10.
- [x] **Security lint**: `bandit -c pyproject.toml -r src/interfaces/wan_performance src/mist/intelligence/reports/subscription_expiry src/foundation/support/utils -q`. Expected result: no finding.
- [x] **Dependency audit**: not applicable. The change edits no requirement file.
- [x] **Code quality**: `pylint src/ --fail-under=9.5`. Expected result: score 9.5 or above. The threshold comes from `.github/workflows/ci.yml:122`.
- [x] **Dead code**: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`. Expected result: no finding. The scope comes from `ci.yml:101`.
- [x] **Docstrings**: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`. Expected result: no violation, and coverage of 90 percent or above. The scope comes from `ci.yml:104` and `ci.yml:107`.
- [x] **Menu reference**: not applicable. The change edits no registry row, no menu title, and no generated page.
- [x] **Symbols**: `symbol-diff --base origin/main` for each changed Python file. Expected result: "no module-level name changed". The expected result differs for `request_admission.py` and `client.py`, because the module-level names move into classes. The pull request body lists each moved name.
- [x] **STE**: `ste-linter --config .ste-linter.toml --min-score 80` with each changed Markdown file, which holds the operator guide and the record files. The gate lists the instruction files. AGENTS requires the same score for each Markdown file. Expected result: each file scores 80 or above. Record the score of the operator guide on main before the edit.
- [x] **Ops portal**: not applicable. The change edits no file under `ops-portal/`.
- [x] **Ops platform**: not applicable. The change edits no file under `mist-ops-platform/`.
- [x] **Guardrails**: `python -m pytest tests/guardrails`. Expected result: all guard tests pass. The changelog guard is `tests/guardrails/test_changelog_fragment_policy.py`.
- [x] **SDK compatibility**: `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py`. Expected result: all tests pass.
- [x] **Container**: not applicable. The change starts no container and builds no image.

## Remote Rows

- [x] Each required check passes on the latest commit, including CodeQL (`.github/copilot-instructions.md`, section Git and GitHub in this repository).
- [x] The test quality job of `ci.yml` reports zero new findings.
- [x] The `Conventional Commits PR title` check passes.
