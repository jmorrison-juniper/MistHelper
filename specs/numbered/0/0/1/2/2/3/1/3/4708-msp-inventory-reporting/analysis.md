# Repair Evidence: Issue #4708

## Result

The repair counts collected runner results and labels partial combined reports.
The repair changes no export fields, filenames, API identifiers, or destructive operations.

The baseline is `3964d21d03f9f5717cb8eafb7272ecff21f5362a`.
The issue ownership comment reserves the two existing modules for this repair.
The open-PR check found no overlapping source or test owner.

## Exact File Set

The repair changes these existing files:

- `src/mist/resources/inventory/org_device_inventory_msp.py`
- `tests/unit/inventory/test_org_device_inventory_msp.py`

The repair adds `changelog.d/issue-4708-msp-inventory-reporting.md`.

The repair adds these records under `specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/`:

- `spec.md`, `plan.md`, `tasks.md`, and `analysis.md`
- `design/research.md`, `design/data-model.md`, and `design/quickstart.md`
- `design/contracts/console.md`
- `design/checklists/requirements.md`

No other tracked file changes.

## Before and After

The initial focused regression command selected eight cases:

```sh
.venv/bin/python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py -q -k 'reports_actual_coverage or labels_every_combined_report'
```

Before the source repair, the result was `7 failed, 1 passed, 41 deselected`.
After adding network-guard tests, the same eight cases ran against the base source in memory.
That run returned `7 failed, 1 passed, 47 deselected`.
The complete-report scenario passed. The six count scenarios and partial-report scenario failed.
The base run changed no source file on disk.

A separate mocked comparison blocked sockets and DNS for both source versions.
Its mixed batch had one success, one missing ID, and one runner exception.

Before:

```text
MSP inventory summary complete. Processed 3 organizations.
```

After:

```text
  [2/3] Skipping Missing ID: missing organization ID
MSP inventory summary partial. Succeeded: 1. Skipped or failed: 2.
```

The two-success, one-failure batch previously labeled all three headings `All Orgs`.
After:

```text
MSP inventory summary partial. Succeeded: 2. Skipped or failed: 1.
  Combined MSP Model Count Summary (Partial: 2 succeeded, 1 skipped or failed)
  Combined MSP Firmware Version Summary (Partial: 2 succeeded, 1 skipped or failed)
  Combined MSP Version Distribution per Model (Partial: 2 succeeded, 1 skipped or failed)
```

Complete combined reports retain `All Orgs`.
The zero-success case reports zero successes and produces no combined exports.
Successful empty results still count as successful organizations.
The tests also prove that a later valid organization runs after an earlier failure.

## Exact Local Checks

The command definitions below shorten the table without changing their meaning.

```sh
SOURCE=src/mist/resources/inventory/org_device_inventory_msp.py
TEST=tests/unit/inventory/test_org_device_inventory_msp.py
FEATURE=specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting
```

| Command | Actual result |
| --- | --- |
| `uv run --no-sync python -m pytest --version` | Failed because the worktree environment had no pytest. |
| `uv sync --locked --extra dev` | Passed. Restored 171 locked packages in this worktree. |
| `.venv/bin/python -m black "$SOURCE" "$TEST"` | Passed. Formatted two files. Later runs left both unchanged. |
| `.venv/bin/python -m black --check "$SOURCE" "$TEST"` | Passed. Two files would remain unchanged. |
| `.venv/bin/python -m ruff check "$SOURCE" "$TEST"` | `All checks passed!` |
| `.venv/bin/python -m pytest "$TEST" -q` | `55 passed, 1 warning`. |
| `.venv/bin/python -m pytest "$TEST" -q --cov=src.mist.resources.inventory.org_device_inventory_msp --cov-report=term-missing --cov-fail-under=80` | Passed. 55 tests, 92.01 percent source coverage. |
| `.venv/bin/python -m mypy "$SOURCE" --config-file pyproject.toml` | `Success: no issues found in 1 source file`. |
| `.venv/bin/python -m mypy "$SOURCE" "$TEST" --config-file pyproject.toml` | Nine existing test annotation errors. No source error. |
| `.venv/bin/python -m mypy --config-file pyproject.toml -c "$(git show HEAD:tests/unit/inventory/test_org_device_inventory_msp.py)"` | Before the repair commit, the base test also reported the same nine annotation errors. |
| `.venv/bin/python -m py_compile "$SOURCE"` | Passed with no output. |
| `.venv/bin/python -m bandit -c pyproject.toml "$SOURCE" -q` | Passed with no finding. |
| `.venv/bin/python -m radon cc "$SOURCE" -j \| .venv/bin/complexity-gate --max 10` | `All functions within complexity threshold.` |
| `.venv/bin/python -m pylint "$SOURCE" --fail-under=9.5` | Passed at 9.72/10. Existing style messages remain. |
| `.venv/bin/python -m vulture "$SOURCE" --min-confidence 70` | Passed with no finding. |
| `.venv/bin/python -m pydocstyle "$SOURCE"` | Passed with no output. |
| `.venv/bin/python -m interrogate "$SOURCE" --fail-under 90` | Passed at 100 percent docstring coverage. |
| `.venv/bin/symbol-diff --base HEAD "$SOURCE"` | Before the repair commit, `no module-level name changed`. |
| `find "$FEATURE" -name '*.md' -print0 \| xargs -0 .venv/bin/ste-linter --config .ste-linter.toml --min-score 80` | Eight initial feature records passed at 94 to 97. Final record checks accompany the local handoff. |
| `.venv/bin/ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4708-msp-inventory-reporting.md` | Passed at 95. |
| `git diff --check` | Passed with no output. |
| `git fetch --no-tags origin '+refs/heads/main:refs/remotes/origin/main'` | Passed. No rebase or merge. |
| `git rev-parse --verify 'origin/main^{commit}'` | Resolved the baseline commit shown above. |

The first STE command incorrectly supplied a directory as a file.
It returned exit 2 with `file not found`.
The corrected `find` command checked every initial feature record and skipped none.
This invocation error did not require a repository change.

The test warning concerns a deprecated hook in the installed Dash pytest plugin.
The checkout audit guard reported zero lines before and after each test run.
Six direct rejection tests prove that the offline fixture blocks sockets and DNS.

Post-commit test-quality checks and the final commit ID belong in the local handoff.
They cannot be recorded in the same commit before that commit exists.

The first post-commit input preflight passed with four input reads and four validations.
The first test-quality scan examined one test file and reported 15 new findings.
An in-memory comparison of the unchanged base test found the same 15 findings, but reported zero new findings.
The comparison matched each finding by file, rule, and explanation.
The initial test additions had moved existing tests to different lines.
The baseline identified those moved findings as new.

The correction appends all new tests and fixtures after the original test content.
Local socket imports preserve existing import lines and baseline locations.
No existing assertion or baseline entry changes.
A second local commit records this correction because the assignment prohibits an amended commit.
The final committed test-quality result belongs in the handoff.

The committed Markdown link check examined ten files and found zero broken links.
All nine final feature records passed STE at 94 to 97.

## Specification Analysis

| Requirement | Tasks | Coverage |
| --- | --- | --- |
| FR-001 and FR-002 | T003, T004 | Exact successful and excluded counts. |
| FR-003 | T003, T004 | Visible missing-ID cause. |
| FR-004 | T005, T006 | All three partial headings. |
| FR-005 | T005, T006 | Complete headings, threshold, rows, names, and writer options. |
| FR-006 | T003, T004 | Later valid organizations still run. |
| FR-007 | T002 | Mocked collaborators and explicit network rejection. |
| SC-001 | T003, T004 | Six batch-count scenarios. |
| SC-002 and SC-003 | T005, T006 | Partial run followed by complete run. |
| SC-004 | T005, T006 | Exact export rows for successful organizations. |

All 11 requirements and success criteria have task coverage.
All eight tasks are complete.
All 16 specification checklist items pass.
No unresolved behavioral ambiguity, duplicate requirement, or missing implementation task was found.

## Intentional Changes and Limits

The batch footer now uses explicit success and exclusion counts.
A partial batch says `partial`, including a batch with zero successes.
Missing-ID records now produce console warnings in addition to the existing log warning.
Each partial combined heading now states the counts.
Exported data has no new completeness field because schema changes are outside the reservation.

The change preserves existing broad per-organization exception handling.
The runner contract cannot detect an internal error that the runner conceals before returning.
The nine pre-existing test typing errors remain outside this repair.
The full repository suite, live safe sweep, dependency audit, and CI were not run for this bounded local repair.

PowerShell was unavailable, so prerequisite scripts could not run.
The verified routing algorithm produced the fixed eight-segment route.
A structural check examined 13 managed directories and found no directory above five children.
The feature root has five children after this evidence record.
No shared selector, instruction file, or Git configuration changed.
Optional commit hooks were deferred to local commits after the focused checks.
The branch-creation hook was not run because the assignment requires the existing app-managed worktree.

No push, pull request, rebase, merge, issue closure, hook bypass, bootstrap, live Mist call, SSH call, firmware action, or production database call occurred.
