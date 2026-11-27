# Tasks: Test quality: repair remaining missing_fm_http_4xx findings

**Input**: Design documents in `specs/numbered/0/0/0/4/1/4/4/2/2747-test-quality-fm-http-4xx/`.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, and `design/quickstart.md`.

**Tests**: The constitution requires tests for each behavior change. Each new test must fail first. Use mocked boundaries only.

**Scope**: Only the `missing_fm_http_4xx` rule. Never edit a 5xx entry.

## Format

- **[P]**: The task can run in parallel with other [P] tasks of its phase.
- **FR** and **SC**: The requirements and success criteria that the task serves.
- **Status**: `open`, `verified-present`, `partial`, or `absent`.

Repository paths below use forward slashes. The record folder is `specs/numbered/0/0/0/4/1/4/4/2/2747-test-quality-fm-http-4xx/`.

## Phase 1: Claim and Census

- [ ] **T001** FR-014, FR-012. Confirm the issue claim and the file overlap.
  - Paths: none (GitHub state).
  - Verify: `gh pr list -R jmorrison-juniper/MistHelper --state open --json number,headRefName,files` (filter the 38 test paths in the output).
  - Acceptance: Only PR #4208 overlaps the 38 test paths (research R-41). Issue #2747 stays `in-progress`.
  - Status: verified-present.

- [ ] **T002** [P] FR-001. Run the preflight guard.
  - Paths: `tests/guardrails/local_test_quality_loop/test_guidance.py`.
  - Verify: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`
  - Acceptance: One test passes. The output reports four inputs read and validated.
  - Status: open.

- [ ] **T003** FR-001, FR-002. Run the census with report and summary paths under `test-artifacts/2747/`.
  - Paths: `test-artifacts/2747/census-4xx.json`, `test-artifacts/2747/census-4xx.md`.
  - Verify: `test-quality-analyzer --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --report test-artifacts/2747/census-4xx.json --summary test-artifacts/2747/census-4xx.md --log-level ERROR`
  - Acceptance: Both files exist. The JSON report holds the keys `findings` and `stale_baseline_entries`.
  - Depends: T002.
  - Status: open.

- [ ] **T004** FR-001, SC-001. Count the census rows for the 4xx rule.
  - Paths: `test-artifacts/2747/census-4xx.json`, `analysis.md` (Census summary).
  - Verify (findings): `Get-Content -Raw test-artifacts\2747\census-4xx.json | ConvertFrom-Json | Select-Object -ExpandProperty findings | Where-Object rule_id -eq 'missing_fm_http_4xx' | Measure-Object | Select-Object -ExpandProperty Count`
  - Verify (stale entries): `Get-Content -Raw test-artifacts\2747\census-4xx.json | ConvertFrom-Json | Select-Object -ExpandProperty stale_baseline_entries | Where-Object { $_ -match 'missing_fm_http_4xx' } | Measure-Object | Select-Object -ExpandProperty Count`
  - Acceptance: `analysis.md` states both counts. The stale count and the finding count appear in the Census summary.
  - Depends: T003.
  - Status: open.

- [ ] **T005** FR-002, SC-001. Complete the triage table from the census.
  - Paths: `specs/numbered/0/0/0/4/1/4/4/2/2747-test-quality-fm-http-4xx/analysis.md`.
  - Verify: `(Select-String -Path specs\numbered\0\0\0\4\1\4\4\2\2747-test-quality-fm-http-4xx\analysis.md -Pattern '^\| \d+ \|').Count`
  - Acceptance: The count equals 38 plus each census finding that has no baseline entry. Each row has one census outcome (present or stale) and one family.
  - Depends: T004.
  - Status: open.

## Phase 2: Upstream Repair (misthelper-devtools)

These tasks change a different repository. They stay outside this record until the owner releases a commit.

- [ ] **T006** [P] FR-005. Repair the applicability inference for family F2.
  - Paths (misthelper-devtools): `src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py` (`FailureModeApplicabilityInferer`, lines 283 to 437), and `tests/` (testpaths at `pyproject.toml` line 81).
  - Required behavior:
    - (a) A nested-project path does not inherit module-level SDK imports.
    - (b) An SDK attribute string creates no HTTP risk unless the source under test calls it.
    - (c) A class-wide body scope narrows to the methods that the test calls.
  - Regression cases: 4 (one per behavior above, plus one class-wide case).
  - Verify (misthelper-devtools): `python -m pytest` (README line 24 at the pinned commit).
  - Acceptance: Each regression case fails before the repair and passes after it.
  - Depends: T005.
  - Status: open. External to this repository.

- [ ] **T007** [P] FR-006. Repair the coverage inference for family F3.
  - Paths (misthelper-devtools): `src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py` (`SourceDrivenCoverageSlicer`, line 438, `_calls_source`, line 500, and `_collect_source_driver_names`, line 538), and `tests/` (testpaths at `pyproject.toml` line 81).
  - Required behavior:
    - (a) A 4xx status literal in a class-scoped helper counts when a source-driving test calls the helper.
    - (b) A call on an instance of a source class counts as source driving.
    - (c) A fixture that returns a source object counts as source driving.
  - Regression cases: 3, one per behavior above.
  - Verify (misthelper-devtools): `python -m pytest`.
  - Acceptance: Each regression case fails before the repair and passes after it. Issue `jmorrison-juniper/misthelper-devtools#67` gets the census table from T005.
  - Depends: T005.
  - Status: open. External to this repository.

- [ ] **T008** FR-009. Release the upstream commit.
  - Paths: none in this repository.
  - Verify: `gh api repos/jmorrison-juniper/misthelper-devtools/commits/<released-commit-sha>` returns the commit.
  - Acceptance: The commit exists on the default branch or on a tag. The devtools test command passes at that commit.
  - Depends: T006 and T007.
  - Status: open. External to this repository.

## Phase 3: Pin and Census After Release

- [ ] **T009** FR-009. Change the devtools pin to the released commit.
  - Paths: `requirements-dev.txt` (line 197).
  - Verify: `Select-String -Path requirements-dev.txt -Pattern '^misthelper-devtools'`
  - Acceptance: The line names the released commit. No other line changes.
  - Depends: T008.
  - Status: open.

- [ ] **T010** FR-009, SC-002. Install the pin, rerun the census, and compare.
  - Paths: `test-artifacts/2747/census-after.json`, `test-artifacts/2747/census-after.md`.
  - Verify (census): `test-quality-analyzer --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --report test-artifacts/2747/census-after.json --summary test-artifacts/2747/census-after.md --log-level ERROR`
  - Verify (gate): `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Acceptance: The gate reports zero new findings and zero parse errors. The 4xx finding count is less than or equal to the T004 count.
  - Depends: T009.
  - Status: open.

## Phase 4: Real-Gap Tests (Family F1 Only)

- [ ] **T011** [P] FR-003, FR-004, FR-010, FR-011, FR-013. Add one native 4xx test to each module that a family F1 row names.
  - Paths: each test module named by an F1 row in `analysis.md`. Before the census, the list is empty. The held file `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` stays unchanged.
  - Required behavior: The test uses a native `requests.Response` or `mistapi.APIResponse` with a 4xx status and a mocked SDK boundary. It asserts the refusal result, the error log, and the SDK call count. It sends no live request.
  - Verify (unmodified code): `python -m pytest <test module> -q`
  - Verify (mutation): run the test with the status guard mutated in memory from a script in `test-artifacts/2747/`. The test must fail.
  - Acceptance: The test passes on unmodified code and fails under the mutation. An empty F1 list closes this task with zero edits.
  - Depends: T005 and T010.
  - Status: open.

## Phase 5: Baseline

- [ ] **T012** FR-008, FR-012, SC-002. Write the baseline and restore each removed non-4xx entry.
  - Paths: `.github/test-quality-baseline.json`.
  - Verify (write): `test-quality-analyzer --write-baseline --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Verify (diff): `git diff --stat -- .github/test-quality-baseline.json`
  - Acceptance: The write adds zero entries. Each removed 4xx entry matches a stale or resolved finding. Each removed entry for another rule returns to the file. The command uses no `--roots` and no `--changed-from`.
  - Caution: `--write-baseline` removes stale entries for every rule. Restore each non-4xx entry with the `edit` tool before the commit.
  - Depends: T010 and T011.
  - Status: open.

## Phase 6: Local Gates and Pull Request

- [ ] **T013** [P] FR-007, FR-011, SC-004. Run the per-file gates on each changed test module and on the record.
  - Paths: each changed test module, and each Markdown file in `specs/numbered/0/0/0/4/1/4/4/2/2747-test-quality-fm-http-4xx/`.
  - Verify: `python -m ruff check <changed file>`, `python -m black --check <changed file>`, `python -m py_compile <changed file>`, `python -m pytest <changed file> -q`, `symbol-diff --base origin/main <changed file>`, and `python -m mypy $MYPY_PATHS --config-file pyproject.toml`. Read `MYPY_PATHS` from `.github/workflows/ci.yml`.
  - Marker check: `Select-String -Path <changed file> -Pattern 'opt-in|noqa|nosec|type: ignore'` returns no match.
  - Record check: `ste-linter --config .ste-linter.toml --min-score 80 <record file>` scores 80 or above for each record file.
  - Acceptance: Each command prints the expected result from the local gates table. The marker check returns zero matches. Each record file scores 80 or above.
  - Depends: T011 and T012.
  - Status: open.

- [ ] **T-LOCAL-GATES** FR-001, FR-009, SC-002, SC-004. Run the repository-level gates.
  - Paths: none beyond the changed files.
  - Verify (preflight): the T002 command.
  - Verify (changed scope): `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
  - Verify (full scope): `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Verify (whitespace): `git diff --check`
  - Acceptance: Both analyzer gates print zero new findings. The whitespace check exits with zero. Commit the intended files before the changed-scope gate.
  - Depends: T013.
  - Status: open.

- [ ] **T-PR** FR-015, SC-006. Commit, push, and open the pull request.
  - Paths: the files in `plan.md` (change map), including `changelog.d/issue-2747-fm-http-4xx.md` (D-8). The fragment uses one `### Changed` heading and one bullet that names issue #2747. The bullet states that the change is test-only.
  - Commit subject: `chore(tests): refresh missing_fm_http_4xx baseline entries`.
  - Branch: `chore/2747-fm-http-4xx`.
  - Pull request title: the commit subject.
  - Pull request body: `Part of #2747` and `Part of #2746`. Do not use a closing keyword. List the gate results from T-LOCAL-GATES and the census counts from T004 and T010.
  - Verify: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body`
  - Acceptance: The title equals the commit subject. The body holds both "Part of" references and no closing keyword.
  - Depends: T-LOCAL-GATES.
  - Status: open.

- [ ] **T-REMOTE-CI** SC-005. Watch the remote checks.
  - Paths: none.
  - Verify: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`
  - Acceptance: Each required check passes on the head commit.
  - Depends: T-PR.
  - Status: open.

- [ ] **T-MERGE** FR-015. Enable auto-merge after the orchestrator authorizes the merge.
  - Paths: none.
  - Verify: `gh pr edit <number> -R jmorrison-juniper/MistHelper --add-label auto-merge`
  - Acceptance: The label is present only after T-REMOTE-CI passes and the orchestrator authorizes the merge. The squash commit lands on `main`. The branch and its worktree are removed after the merge.
  - Depends: T-REMOTE-CI and orchestrator authorization.
  - Status: open.

## Dependencies & Execution Order

T001 and T002 run first. T003 depends on T002. T004 and T005 depend on T003. T006 and T007 depend on T005 and run in parallel. T008 depends on both. T009 and T010 depend on T008. T011 depends on T005 and T010. T012 depends on T010 and T011. T013 depends on T011 and T012. T-LOCAL-GATES depends on T013. T-PR, T-REMOTE-CI, and T-MERGE run in that order.

## Notes

- A [P] mark shows a task that uses different files from its phase neighbors.
- Each new test fails before its repair. Each repair runs only after its census row.
- Commit after each logical group. The pull request holds one commit for the change.
