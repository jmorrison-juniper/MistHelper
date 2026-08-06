# Tasks: Blind Except Handler Audit

**Feature**: `1794-blind-except-handlers` | **Branch**: `refactor/1794-blind-except` | **Date**: 2026-08-06

**GitHub Issue**: [#1794](https://github.com/jmorrison-juniper/MistHelper/issues/1794)

**Input**: Design documents from `specs/1794-blind-except-handlers/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md). Issue [#1792](https://github.com/jmorrison-juniper/MistHelper/issues/1792) must land first.

**Tests**: The specification requests no new test. The existing suite must keep its pass count for each slice.

**Branch rule**: Create one branch for each slice from `main`. Name the branch `refactor/1794-blind-except-<slice>`. Do not branch from another slice branch.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with another task in the same phase. The tasks touch different files.
- **[Story]**: The user story that owns the task. The value is `US1`, `US2`, or `US3`.
- Each task names an exact area, an exact file path, or an exact command.

## Rules that apply to every edit task

1. Use `.venv\Scripts\python.exe` for every Python command. The global interpreter cannot import the project.
2. Add no lint suppression. Requirement FR-013 forbids a `# noqa: BLE001` directive. A `keep` outcome uses a plain comment.
3. Read the caller before any `narrow` outcome. A narrow clause lets an error propagate, and the caller must handle it.
4. Add a log call at every site that the code continues past. The call must include the exception detail, per FR-011.
5. Every changed Python line carries an inline comment that states why the line exists. Principle VI requires it.
6. Follow the Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md` for every prose line.
7. Audit at most 40 sites in one pull request. Requirement FR-015 states the limit.

## The three outcomes

| Outcome | When | What the site looks like afterward |
| - | - | - |
| `delete` | No exception can reach the block | The `try` and the `except` are gone. The body stays. |
| `narrow` | One exception class or a small set can reach the block | The clause names the classes. The log call names the error. |
| `keep` | The breadth is correct at that site | The clause still names `Exception`. A comment states the reason. A log call records the error. |

---

## Phase 1: Setup

**Purpose**: Confirm the environment and the prerequisite before any measurement.

- [ ] T001 Confirm the tool versions with `.venv\Scripts\python.exe -m ruff --version` and `.venv\Scripts\python.exe -m pylint --version`. The expected values are `ruff 0.16.0` and `pylint 4.0.6`.
- [ ] T002 Confirm that `.venv\Scripts\python.exe -m pytest --version` runs. Every later test command uses this interpreter.
- [ ] T003 Record the pre-change gate baseline. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Save the unit test pass count, because SC-010 compares against it.

---

## Phase 2: User Story 2 - Trust the baseline before the first edit (Priority: P1)

**Purpose**: Produce the reconciliation record. No edit starts until this phase closes.

**Warning**: Task T004 is a stop condition. If the two ruff counts differ, issue #1792 has not landed. Stop and wait. A start on the 412 count leaves 88 sites unaudited, and the gate never reports them.

- [ ] T004 [US2] Confirm that issue #1792 landed. Run `.venv\Scripts\python.exe -m ruff check . --select BLE001 --statistics` and the same command with `--ignore-noqa`. Both values must read 500. Stop if the default value reads 412, because the inert directives still exist.
- [ ] T005 [US2] Measure the pylint count on the current tree. Run `.venv\Scripts\python.exe -m pylint MistHelper.py src --disable=all --enable=W0718 --score=n` and count the reported lines. Do not trust the value of 493 in the `pyproject.toml` comment, because the tree changed since that comment.
- [ ] T006 [US2] Record the root that each tool reads. Ruff reads the whole repository and drops `mist-ops-platform`, `web_portal`, `scripts`, and `src/maps`. Pylint reads `MistHelper.py` and `src` only. Write both lists into [plan.md](plan.md).
- [ ] T007 [US2] Explain every site in the difference between the two counts. List the ruff sites outside the pylint root, such as the 8 sites in `starlink_dashboard.py` and every site under `tools/` and `tests/`. List the pylint sites outside the ruff root. Requirement FR-003 blocks the first slice until each site holds an explanation.
- [ ] T008 [US2] Record the per-area counts with `--ignore-noqa`. Run `.venv\Scripts\python.exe -m ruff check . --select BLE001 --ignore-noqa --output-format concise` and group the results by area. Compare the result against the table in [spec.md](spec.md). Record any drift.
- [ ] T009 [US2] Read the state of issue [#1709](https://github.com/jmorrison-juniper/MistHelper/issues/1709) with `gh issue view 1709`. That issue covers the 33 sites in `MistHelper.py`. Record the decision to land it first or to fold it into slice 11.

**Checkpoint**: The reconciliation record exists and explains every difference. SC-001 now holds. Slice 2 can start.

---

## Phase 3: User Story 1 and 3, Slices 2 to 5 - The small areas (Priority: P1)

**Goal**: Audit 133 sites across four slices. Each slice repeats the same six steps for its own scope.

**Independent Test**: The `BLE001` count drops by the slice size after each slice. The unit suite keeps the T003 pass count.

### The six steps that every slice repeats

- [ ] T010 [US1] List the sites in the slice. Run `.venv\Scripts\python.exe -m ruff check <area> --select BLE001 --output-format concise`. Write each site into the pull request body with a blank outcome column.
- [ ] T011 [US1] Read each site and its caller. Select `delete`, `narrow`, or `keep` from the policy table in [spec.md](spec.md). Apply the order in FR-010. Try `delete` first, then `narrow`, then `keep`.
- [ ] T012 [US1] Apply each outcome. Add a log call with the exception detail at every site that the code continues past. Add a comment at every `keep` site that states why the breadth is correct.
- [ ] T013 [US1] Record the outcome for each site in the pull request body. Requirement FR-018 demands one row for each site. A blank row blocks the merge.
- [ ] T014 [US1] Read the whole difference. Confirm that no changed line adds a `# noqa: BLE001` directive. Requirement FR-013 forbids it and SC-006 measures it.
- [ ] T015 [US1] Verify the slice. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`, `.venv\Scripts\python.exe -m radon cc src/ -a -nb`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Confirm that the pass count matches T003 and that no block scores above 10.

### The four small slices

- [ ] T016 [US3] Run slice 2. The scope is `src/analytics`, `src/ui`, and `starlink_dashboard.py`, which hold 30 sites. Repeat the T010 to T015 steps. Note that pylint never reads `starlink_dashboard.py`, so those 8 sites need a ruff-only check.
- [ ] T017 [US3] Run slice 3. The scope is `src/api`, `src/utils`, and `src/websocket`, which hold 44 sites. Split the slice by area, because 44 exceeds the limit of 40. Read `src/utils/logger_utils.py` with care, because a log call inside a logging filter can recurse without end.
- [ ] T018 [P] [US3] Run slice 4. The scope is `src/site` and `src/db`, which hold 35 sites. Repeat the T010 to T015 steps.
- [ ] T019 [P] [US3] Run slice 5. The scope is `src/gateway`, which holds 24 sites. Repeat the T010 to T015 steps.

**Checkpoint**: The count reads about 367. Slice 6 can start.

---

## Phase 4: User Story 1 and 3, Slices 6 to 11 - The medium areas and the largest files (Priority: P1)

**Goal**: Audit 206 sites across six slices.

**Independent Test**: The `BLE001` count drops by the slice size after each slice.

**Caution**: The `src/ssh` area holds 18 sites that the default ruff run hides today. Those sites received no earlier review at all.

- [ ] T020 [US3] Run slice 6. The scope is `src/ssh`, which holds 32 sites. 18 of them carried an inert directive before issue #1792 landed. Read those 18 with extra care, because no earlier reviewer saw them.
- [ ] T021 [US3] Run slice 7. The scope is `src/device`, which holds 34 sites. Read `src/device/virtual_chassis.py` with care, because it holds 10 sites.
- [ ] T022 [US3] Run slice 8. The scope is `src/refactors`, which holds 43 sites. Split the slice into two pull requests, because 43 exceeds the limit of 40.
- [ ] T023 [US3] Run slice 9. The file is `src/firmware/firmware_manager.py`, which holds 28 sites. Repeat the T010 to T015 steps for that file alone.
- [ ] T024 [US3] Run slice 10. The scope is the rest of `src/firmware`, which holds 34 sites. `src/firmware/bulk_switch_upgrader.py` holds 10 and `src/firmware/bulk_ap_upgrader.py` holds 11.
- [ ] T025 [US3] Run slice 11. The file is `MistHelper.py`, which holds 33 sites. Confirm the T009 decision about issue #1709 first. Run `.venv\Scripts\python.exe -m mypy src/ MistHelper.py --config-file pyproject.toml` after the edit, because issue #888 widened the mypy scope to cover this file.

**Checkpoint**: The count reads about 161. Slice 12 can start.

---

## Phase 5: User Story 1 and 3, Slices 12 to 14 - The export area and the remainder (Priority: P1)

**Goal**: Audit the last 161 sites. `src/export` holds 94 of them, so that area splits into three slices.

**Independent Test**: The `BLE001` count reaches zero under `--ignore-noqa`.

- [ ] T026 [US1] Split `src/export` into groups of at most 40 sites. List the files with `.venv\Scripts\python.exe -m ruff check src/export --select BLE001 --ignore-noqa --output-format concise` and record the group boundary in [plan.md](plan.md). Note that `src/export/const_definitions_exporter.py` holds 11 sites.
- [ ] T027 [US1] Run slice 12. The scope is the first `src/export` group. Repeat the T010 to T015 steps. This area holds the highest defect risk, because an export handler that returns an empty list produces a silent empty report.
- [ ] T028 [US1] Run slice 13. The scope is the second `src/export` group. Repeat the T010 to T015 steps.
- [ ] T029 [US1] List every area that the earlier slices did not cover. Run `.venv\Scripts\python.exe -m ruff check . --select BLE001 --output-format concise` and group the remaining files by area. Record the group boundary in [plan.md](plan.md).
- [ ] T030 [US1] Run slice 14 and every further slice that the remainder needs. Repeat the T010 to T015 steps for each one. Keep every pull request at or below 40 sites.
- [ ] T031 [US1] Verify the whole audit. Run `.venv\Scripts\python.exe -m ruff check . --select BLE001 --ignore-noqa --statistics` and confirm zero results. SC-002 depends on this run.

**Checkpoint**: The count reads zero. User Story 1 is complete. Phase 6 can start.

---

## Phase 6: Close both gates (Priority: P2)

**Goal**: Add `BLE001` to the ruff `select` list and remove `W0718` from the pylint `disable` list. This is the final change of the feature.

**Independent Test**: A reviewer adds one handler that catches `Exception`. Both the ruff gate and the pylint gate fail.

**Warning**: Run this phase only after Phase 5 reports zero results. Both gates fail on every push while any site remains.

- [ ] T032 Change line 164 of `pyproject.toml` from `select = ["E", "F", "W", "I", "UP", "B", "G"]` to `select = ["E", "F", "W", "I", "UP", "B", "G", "BLE001"]`. Add no other rule, per NG-009.
- [ ] T033 Change line 481 of `pyproject.toml` from `disable = ["C0114", "C0115", "C0116", "W0613", "W0718"]` to `disable = ["C0114", "C0115", "C0116", "W0613"]`. Requirement FR-020 demands this change. Depends on T032, because both tasks edit the same file.
- [ ] T034 Rewrite the comment block at `pyproject.toml` lines 471 to 480. Delete the sentence that states the 493-site count and the intentional judgment. Replace it with a reference to this specification and to the audit record. Requirement FR-022 demands this change.
- [ ] T035 Verify both gates. Run `.venv\Scripts\python.exe -m ruff check .` and `.venv\Scripts\python.exe -m pylint src/`. Both must pass with the new configuration.
- [ ] T036 Prove the negative case for SC-009. Add one temporary handler that catches `Exception` to a tracked file under `src/`. Run both gate commands and confirm that each one reports the site and exits with a non-zero code. Remove the handler. Run `git status` and confirm that the tree holds no leftover change.

**Checkpoint**: Both gates report a blind handler. SC-008 and SC-009 now hold.

---

## Phase 7: Polish and Final Validation

**Purpose**: Prove every success criterion and close the issue. These tasks change no source line.

- [ ] T037 Run the full gate set exactly as CI runs it. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`, `.venv\Scripts\python.exe -m pylint src/`, `.venv\Scripts\python.exe -m radon cc src/ -a -nb`, `.venv\Scripts\python.exe -m vulture src/ --min-confidence 80`, `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r .`, and `.venv\Scripts\python.exe -m pytest --cov=src/ --cov-fail-under=80`. Do not scope a gate to the changed files only.
- [ ] T038 [P] Prove SC-003. Count the sites in every slice pull request body and confirm that the total reads 500 and that no row holds a blank outcome.
- [ ] T039 [P] Prove SC-006. Run `git log -p main..HEAD` across every slice branch and search for an added `# noqa: BLE001` line. The expected count is zero.
- [ ] T040 [P] Prove SC-005. List every site with a `keep` outcome and confirm that each one holds a log call with the exception detail.
- [ ] T041 Prove SC-011. Ask a reviewer who did not write the change to read three `keep` comments. The reviewer must state the reason for each one in under one minute and without help from the author. This task needs a second person and an agent session cannot run it.
- [ ] T042 Open the final pull request for the gate change. Write `Closes #1794` in the body. Link `specs/1794-blind-except-handlers/spec.md`. List every slice pull request number and attach the reconciliation record. Complete the checklist in `.github/PULL_REQUEST_TEMPLATE.md`. Add the `auto-merge` label only after every check passes, including CodeQL.

---

## Dependencies and Execution Order

### Phase order

| Phase | Content | Starts after |
| - | - | - |
| 1 | Setup | Nothing |
| 2 | US2, the reconciliation record | Issue #1792 lands |
| 3 | Slices 2 to 5, the small areas | Phase 2 explains every difference |
| 4 | Slices 6 to 11, the medium areas and the largest files | Phase 3 |
| 5 | Slices 12 to 14, the export area and the remainder | Phase 4 |
| 6 | Both gate changes | Phase 5 reports zero results |
| 7 | Polish and final validation | Phase 6 |

### Why the reconciliation runs before any edit

An audit that starts from the 412 count leaves 88 sites unaudited. The gate then reports a clean state that is not true. Task T004 is the stop condition, and it blocks every later phase.

### Slice exit rule

A slice must reduce the count by its own size and must move no other count. Each site in the slice must hold a recorded outcome. The unit suite must keep its pass count.

### Cross-issue coordination

| Issue | Overlap | Control |
| - | - | - |
| #1792 | Removes the 88 inert directives | Task T004 blocks the start until the two counts match |
| #1709 | Covers the 33 sites in `MistHelper.py` | Task T009 records the decision. Task T025 applies it. |
| #887 | Recorded the 493-site pylint count | Task T034 rewrites the comment that holds that count |

---

## Parallel Opportunities

| Phase | Parallel tasks | Reason |
| - | - | - |
| 3 | T018, T019 | The two scopes hold no shared file. |
| 7 | T038, T039, T040 | The three checks read different data. |

**Caution**: Two agents must not open a slice pull request for the same area at the same time. Claim the area on issue #1794 before the branch starts.

---

## Implementation Strategy

### Minimum viable delivery

Slice 12 delivers the largest value on its own. The `src/export` area holds 94 sites, and an export handler that returns an empty collection produces a silent empty report. A reviewer who has time for one slice should pick that one.

### Order of risk

The largest risk is a false clean state. Two paths lead there. The first path starts the audit from the 412 count. The second path adds a `# noqa: BLE001` directive to reach a green gate. Task T004 controls the first path. Task T014 and task T039 control the second path.
