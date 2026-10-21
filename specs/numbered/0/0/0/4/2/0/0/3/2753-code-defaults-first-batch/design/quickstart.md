# Validation Guide: Code Defaults First Batch

These commands define the bounded implementation checks. Planning did not run them.
Run them from the repository root. Use controlled responses and no production credentials.

## Prerequisites

Check ownership with `gh pr list --json number,headRefName,files` and inspect `git status --short` before editing.
If an overlapping file has another owner, stop that file's work.
When the worktree lacks its environment, run:

```bash
python3 scripts/bootstrap_worktree.py
source .venv/bin/activate
```

On Windows, use the documented PowerShell bootstrap and activation commands.
Confirm that Python is version 3.13 or newer.
Do not change dependency manifests merely to install a planning tool.

Implementation setup result: Python 3.13.13 was present. The documented
`python3 scripts/bootstrap_worktree.py` command created `.venv`, installed both requirement files,
downloaded Chromium, and found no corrupt package installs. The Python prerequisite script is
absent. The PowerShell prerequisite command is unavailable because `pwsh` is not installed.
The complete paginated PR check reviewed 11 open pull requests and 553 file records with no
overlap in the approved source or test paths.

## Bounded Behavior Tests

The exact assessment section 10 command is:

```bash
python -m pytest tests/unit/device/test_ap_profile_migration_manager.py tests/unit/test_zone_analyzer.py tests/unit/test_csv_comparator.py tests/unit/inventory/test_csv_comparator_broad_handlers.py tests/unit/refactors/test_inventory_csvcomparator.py tests/unit/test_address_utils.py tests/unit/org/test_org_config_migration_conflicts.py tests/unit/org/test_org_config_migration_workflow.py
```

Expected: valid cases retain results. Missing required inputs visibly fail in their tests.
No test contacts an external service.
Do not run the full suite for this bounded batch.

After implementation, run the new scan and workflow tests:

```bash
python -m pytest tests/integration/helpers/code_defaults
python -m src.foundation.support.code_defaults scan --root .
python -m src.foundation.support.code_defaults guard --root .
```

Expected: deterministic inventory output, explicit parsed-file counts, and an unchanged or decreased accepted high-severity baseline.
The guard tests must also prove failure for regressions and invalid inputs.
The scanner and baseline did not exist during planning.

## Source Gates

Read `MYPY_PATHS` from the current `.github/workflows/ci.yml`.
Its planning-time value is shown in the explicit command below.

```bash
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
radon cc src -j | complexity-gate --max 10
bandit -c pyproject.toml -r src -q
symbol-diff --base origin/main src/mist/resources/device/ap_profile_migration_manager.py src/mist/intelligence/analytics/zone_analyzer.py src/mist/resources/inventory/csv_comparator.py src/foundation/support/utils/address_utils.py src/mist/resources/org/org_config_migration_manager.py
```

Expected: no lint or format errors, no type errors, no complexity or security finding, and no lost existing declaration.
Apply the existing docstring, dead-code, and code-quality gates to the changed implementation scope as required by repository guidance.
Run the existing structural guards after adding the packages:

```bash
python -m pytest tests/guardrails/test_nested_package_structure.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_move_module_guidance.py
```

Expected: no new structural excess and no unmanaged process record.
No production module moves are planned.

## Test Quality Ratchet

Follow the current repository procedure. Execute each command separately and stop at the first failure.
The intended base is `main`.
Commit the intended tests before the analyzer and stop if relevant changes remain outside that commit.

```bash
git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
git rev-parse --verify "origin/main^{commit}"
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected: preflight passes and the analyzer reports `gate: 0 new findings vs baseline`.
Do not rewrite `.github/test-quality-baseline.json` to conceal a new finding.
Before any later push, run the documented full test-quality scan.
That scan is not the full pytest suite.

## Completion Evidence

Record exact commands, exit statuses, parsed-file counts, candidate dispositions, and baseline changes.
Use [contracts/audit.md](contracts/audit.md) for the required positive and negative cases.
Report absent evidence as absent. Do not claim the larger issue is complete.

## Recorded Implementation Results

The latest paginated ownership check examined 11 open pull requests and 553 file records.
It found no overlap with the approved file manifest.

The full scan completed at revision `40f69666f1c3a4f711805d968e210923a216fd7f`.
It discovered and parsed 1,059 tracked Python files. It found 2,410 candidates and zero parse
failures. It classified 2,213 candidates as outside this batch. The 99 candidates associated
with #2862 remain excluded.

The five-file scan parsed all five expected files and found 197 candidates:

| Classification | Count |
| --- | ---: |
| Already validated | 70 |
| Valid optional | 56 |
| Display only | 66 |
| Excluded under #2863 ownership | 5 |
| **Accepted high-severity** | **0** |

The baseline records every current candidate and has `accepted_high: []` and
`accepted_total: 0`. It records source revision `ca55339958143c96b60df549ae07b274e89dec2a`.
The guard passed, parsed all five files, and reported no new or removed high identities.
A repeated full scan returned identical content before the baseline-only commit.

The exact eight-module assessment test command passed 557 tests.
`python -m pytest tests/integration/helpers/code_defaults` passed 43 tests.
The three documented structural guards passed 35 tests.
The controlled new-candidate and count-neutral regression tests passed two cases.
Failing-before and mutation evidence remains in the Copilot session artifacts.

The required test-quality preflight passed. The analyzer checked eight test files and reported
`gate: 0 new findings vs baseline`. It reported two skipped files and no parse errors.

The following source gates passed: Ruff, Black, Mypy, the documented `src` complexity gate,
Bandit, symbol compatibility, pydocstyle, Vulture, Interrogate, Pylint, and `py_compile`.
Mypy reported no issues across 864 source files. Black left 2,490 files unchanged.
Interrogate reported 99.7 percent coverage. Pylint scored 9.92 out of 10.
The feature Markdown passed `ste-linter` with a minimum score of 92.
A local relative-link check examined eight Markdown files and found no missing links.

An exploratory complexity command included two out-of-scope script packages and failed on six
existing functions there. The documented `src`-only complexity command passed.
`markdown-link-check` was not installed. No full test suite, `MistHelper.py --test`, cloud request,
or device action ran.
