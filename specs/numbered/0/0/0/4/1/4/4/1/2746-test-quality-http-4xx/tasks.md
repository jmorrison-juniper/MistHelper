# Tasks: HTTP 4xx Test-Quality Findings

**Input**: Record `specs/numbered/0/0/0/4/1/4/4/1/2746-test-quality-http-4xx/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, and `design/data-model.md`.

## Format

Each task lists its requirements, exact files, acceptance, one verification command, and status. Status values are open, verified-present, partial, or absent. A `[P]` task has no dependency on an open task.

## Phase 1: Verify and Measure

### T001 [P] Confirm the baseline and the pin

- Requirements: FR-001, FR-006
- Files: `.github/test-quality-baseline.json`, `requirements-dev.txt`
- Acceptance: The baseline holds 38 `missing_fm_http_4xx` entries. Line 197 pins `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- Verification: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`
- Status: verified-present

### T002 Measure the complete report

- Requirements: FR-001, FR-002, FR-004
- Files: None in the repository. Write the report to a folder outside the repository.
- Acceptance: The report lists each `missing_fm_http_4xx` finding and each absent-file entry. The report shows zero new findings. The counts go to `analysis.md`.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- Status: open
- Prerequisite: T001

### T003 Record the class table in the repository

- Requirements: FR-001, FR-002, FR-009
- Files: `specs/numbered/0/0/0/4/1/4/4/1/2746-test-quality-http-4xx/analysis.md`
- Acceptance: The table has 38 rows. Each row has one class and one evidence line. Measured counts from T002 replace any draft count.
- Verification: `python -m pytest tests/guardrails`
- Status: open
- Prerequisite: T002

### T004 Remove class B entries absent from the complete report

- Requirements: FR-004, FR-005, FR-006
- Files: `.github/test-quality-baseline.json`
- Acceptance: The diff removes only class B entries. The diff adds no line. The gate reports zero new findings. The count of `missing_fm_http_4xx` entries falls by the number of removed entries.
- Method: Use the edit tool. Remove each entry by its five-part key. Use `--write-baseline` only when T002 shows that every removed entry is a class B entry.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- Status: open
- Prerequisite: T003

## Phase 2: Upstream Dependency

### T005 [P] Repair applicability and attribution in misthelper-devtools

- Requirements: FR-002, FR-005
- Files: External repository `jmorrison-juniper/misthelper-devtools`, file `misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py`, and class `SourceDrivenCoverageSlicer`, which issue #67 covers.
- Acceptance: A released commit omits each class A and class C finding from a complete report. The release includes its own tests.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- Status: open
- Note: This task runs in the misthelper-devtools repository. Task T006 consumes its result.

### T006 Bump the pin and remove class A and class C entries

- Requirements: FR-002, FR-004, FR-005
- Files: `requirements-dev.txt`, `.github/test-quality-baseline.json`
- Acceptance: Line 197 names the released commit. The complete report omits each removed entry. The gate reports zero new findings.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- Status: open
- Prerequisite: T004, T005

## Phase 3: Existing Coverage and Conditional Tests

### T007 [P] Verify the class C test modules and add a test only for a real gap

- Requirements: FR-003, FR-008
- Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` and `tests/unit/org/test_org_config_migration_workflow.py`. A real gap adds one test to the module that owns the gap.
- Acceptance: Both modules pass. A new test appears only for a real gap in the complete report. A new test fails when its checked behavior is removed in memory.
- Verification: `python -m pytest tests/unit/refactors/test_wlanradius_timer_manager_paths.py tests/unit/org/test_org_config_migration_workflow.py`
- Status: verified-present

## Phase 4: Final Gates and Pull Requests

### T-LOCAL-GATES Run each applicable local gate

- Requirements: FR-005, FR-006
- Files: Changed files only. These are `.github/test-quality-baseline.json`, `requirements-dev.txt` when changed, and the record folder.
- Acceptance: Each applicable gate exits zero. The applicable gates are the test-quality gate, the TestLiveGuides preflight, and the guardrail tests. The pull request body names each gate that does not apply.
- Verification: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`
- Status: open
- Prerequisite: T004 for pull request one, and T006 for pull request two

### T-PR Commit, push, and open the pull request

- Requirements: FR-007, FR-010
- Files: The branch with the files from T004 and the record folder.
- Acceptance: Pull request one uses the title `test(quality): remove unmatched HTTP 4xx baseline entries`. Its body contains `Part of #2746`. The final pull request body contains `Closes #2746`. The body lists each separate issue for FR-007, or it states that none exists.
- Method: Commit with a Conventional Commits subject. Push the branch `test/2746-http-4xx-baseline`. Open the pull request against `main`.
- Caution: A commit pushed after a squash merge creates an orphan pull request. Open a new issue and branch again from main instead.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
- Status: open
- Prerequisite: T-LOCAL-GATES

### T-REMOTE-CI Watch the required checks

- Requirements: FR-005
- Files: None.
- Acceptance: Each required check reports success. The `test_quality_gate` job passes. Auto-merge stays disabled until T-MERGE.
- Method: Run `gh pr checks <number> --watch` with the pull request number.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- Status: open
- Prerequisite: T-PR

### T-MERGE Squash merge after authorization

- Requirements: FR-010
- Files: None.
- Acceptance: The orchestrator authorizes the merge. The squash commit reaches main. The branch and the worktree are removed after the merge.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- Status: open
- Prerequisite: T-REMOTE-CI

## Dependencies and Execution Order

- Pull request one: T001, T002, T003, T004, T007, T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.
- Pull request two: T005, then T006, then T-LOCAL-GATES, T-PR (with `Closes #2746`), T-REMOTE-CI, and T-MERGE.
- Parallel tasks: T001, T005, and T007 have no open dependency.

## Notes

- Caution: `--write-baseline` accepts every current finding, including new ones. Use it only after the gate reports zero new findings.
- Use `--prune-baseline` for absent-file entries only. Class B entries stay until T004 removes them.
