# Tasks: Black Gate Failure From the Mando Pin

**Input**: Records in `specs\numbered\0\0\1\2\4\0\3\2\4892-black-gate-mando-pin\`. Use `plan.md`, `spec.md`, `design\research.md`, and `design\contracts\dependabot-mando-ignore.md`.

**Tests**: Two guard tests are required. Each change carries its tests (`AGENTS.md`, Code quality, Tests).

**Organization**: Tasks follow the user stories in `spec.md`. Each task names its requirement IDs and one verification command from the local gates table in `plan.md`.

## Format

- `[P]` marks a task that can run in parallel with other `[P]` tasks.
- Status values are `open`, `verified-present`, `partial`, or `absent`. Every task starts as `open`.

Warning: do not start the remote CI watch before the local gates pass. A red remote run consumes CI minutes.

## Phase 1: Guard Test First (User Story 2)

- [ ] T001 [US2] [FR-005] Add class `DependabotPolicy` and two test functions to `tests\guardrails\test_dependency_lock_file.py`.
  - Acceptance: The first test fails on the current `.github\dependabot.yml`, because the pip entry has no mando rule. The second test fails on a pip entry without a mando rule.
  - Verification: `python -m pytest tests\guardrails\test_dependency_lock_file.py` (Tests row). The first test must fail before T002.
  - Status: open

## Phase 2: Configuration (User Story 2)

- [ ] T002 [US2] [FR-003] [FR-004] Add an `ignore` list with `dependency-name: "mando"` and `versions: [">=0.8"]` to the pip entry in `.github\dependabot.yml`. Depends on T001.
  - Acceptance: The pip entry (lines 3 to 11) carries the rule. A comment block above the rule names radon, issue #4892, and the removal condition. The npm entry does not change.
  - Verification: `python -m pytest tests\guardrails\test_dependency_lock_file.py` (Tests row). Both new tests pass.
  - Status: open

## Phase 3: Changelog and Record (User Stories 1 and 3)

- [ ] T003 [P] [US3] [FR-007] Create `changelog.d\issue-4892-black-gate-mando-pin.md`.
  - Acceptance: One `###` heading names the change. One bullet starts with `- **Fixed**:` and names issue #4892.
  - Verification: `python -m pytest tests\guardrails\test_changelog_fragment_policy.py` (Tests row).
  - Status: open

- [ ] T004 [P] [US1] [US3] [FR-001] [FR-008] Copy the ten Markdown files of this record to `specs\numbered\0\0\1\2\4\0\3\2\4892-black-gate-mando-pin\`.
  - Acceptance: The folder holds the same files and folders as the draft. The route parents hold five children or fewer (research R-32, R-33).
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80` with the ten file paths (STE row).
  - Status: open

- [ ] T005 [P] [FR-002] [FR-006] Confirm that `requirements-dev.txt`, `requirements.txt`, `uv.lock`, and `.github\workflows\ci.yml` stay unchanged.
  - Acceptance: The four paths show no diff against `origin/main`. The lock guard test still checks each requirement (research R-15).
  - Verification: `python -m pytest tests\guardrails\test_dependency_lock_file.py` (Tests row).
  - Status: open

## Phase 4: Gates and Delivery

- [ ] T-LOCAL-GATES [FR-009] Run each applicable gate in `plan.md`, section Gate Applicability, on the changed files: `.github\dependabot.yml`, `tests\guardrails\test_dependency_lock_file.py`, `changelog.d\issue-4892-black-gate-mando-pin.md`, and the record folder.
  - Acceptance: Compile, Lint, Format, Tests, Tests changelog, Full tests, Security lint, Symbols, and STE pass. Record each output line. The test quality gate runs in T-PR after the local commit.
  - Verification: `python -m black --check .` (Format row), with the other rows of the table.
  - Status: open

- [ ] T-PR [FR-001] [FR-006] [FR-009] Commit the changed paths from T001 to T004, run the test quality gate, push, and open the pull request.
  - Acceptance: The commit subject is `fix(ci): ignore mando releases that radon 6.0.1 rejects`. The body holds `Closes #4892` and the Co-authored-by trailer. The branch is `fix/4892-black-gate-mando-pin`. The pull request body lists each gate result and the file summary. The body states that pull request #4888 stays open. Add the `in-progress` label to issue #4892 before the branch.
  - Verification: `test-quality-analyzer --gate` with the command block in `.github\copilot-instructions.md` line 124 (R-68), run on the commit before the push.
  - Status: open

- [ ] T-REMOTE-CI [SC-001] [SC-002] [SC-005] Watch the CI run on the fix pull request. The workflow file is `.github\workflows\ci.yml`, and this change does not edit it.
  - Acceptance: `Black (format check)`, `Dependency lock and exports`, `Conventional Commits PR title`, and `STE compliance` report success. Record each conclusion.
  - Verification: `python -m black --check .` (Format row), run locally with the same result before the push.
  - Status: open

- [ ] T-MERGE [FR-006] [SC-006] Enable auto-merge, squash merge, and delete the branch after the orchestrator authorizes the merge. The merge carries the four changed paths from T001 to T004.
  - Acceptance: The squash commit lands on `main`. Issue #4892 closes by its `Closes` line. Pull request #4888 stays open.
  - Verification: `python -m pytest tests\guardrails\test_dependency_lock_file.py` on the updated `main` (Tests row).
  - Status: open

Warning: do not merge pull request #4888. Its requirements file cannot install, so each job that installs it fails.

Caution: do not push to the branch `dependabot/pip/mando-0.8.2`. Dependabot owns that branch.

## Dependencies and Execution Order

- T001 comes first. T002 depends on T001.
- T003, T004, and T005 run in parallel after T002.
- T-LOCAL-GATES runs after T003, T004, and T005.
- T-PR runs after T-LOCAL-GATES. T-REMOTE-CI runs after T-PR. T-MERGE runs after T-REMOTE-CI and the orchestrator approval.

## Parallel Example

```text
After T002:
  T003 writes changelog.d\issue-4892-black-gate-mando-pin.md
  T004 writes the record folder
  T005 reads the four unchanged pin files
```

## Notes

- Each task names exact repository paths.
- Each task names one verification command from the local gates table.
- The change uses no Mist API call, so no SDK check applies.
