# Tasks: Module Logger Migration

**Feature**: `1793-root-logger-calls` | **Branch**: `refactor/1793-module-logger` | **Date**: 2026-08-06

**GitHub Issue**: [#1793](https://github.com/jmorrison-juniper/MistHelper/issues/1793)

**Input**: Design documents from `specs/1793-root-logger-calls/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: The specification requests no new test. The existing suite must keep its pass count for each slice. Each slice ends with a measurement task and a gate task.

**Branch rule**: Create one branch for each slice from `main`. Name the branch `refactor/1793-module-logger-<slice>`. Do not branch from another slice branch.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with another task in the same phase. The tasks touch different files.
- **[Story]**: The user story that owns the task. The value is `US1`, `US2`, or `US3`.
- Each task names an exact file path, an exact area, or an exact command.

## Rules that apply to every edit task

1. Use `.venv\Scripts\python.exe` for every Python command. The global interpreter cannot import the project.
2. Change the logger object only. Do not change a level. Do not change a message text. Do not change an argument list. Requirements FR-004 through FR-006 state this rule.
3. Add no lint suppression. Non-goal NG-001 forbids a `# noqa` directive and a new entry in the ruff `ignore` list.
4. Add the module logger line with an inline comment that states its purpose. Principle VI requires the comment.
5. Keep the lazy `%s` argument form that issue #429 delivered. Do not write an f-string.
6. Follow the Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md` for every prose line.
7. Keep each pull request at or below 500 changed lines. Requirement FR-011 states the limit.

## The conversion pattern

Each converted module gains one line after the import block.

```python
logger = logging.getLogger(__name__)  # Named logger lets an operator filter records by module.
```

Each call then changes its object and nothing else.

```python
logging.info("Fetching device list for site %s", site_id)   # Before
logger.info("Fetching device list for site %s", site_id)    # After
```

---

## Phase 1: Setup

**Purpose**: Confirm the environment before any measurement.

- [ ] T001 Confirm the tool version with `.venv\Scripts\python.exe -m ruff --version`. The expected value is `ruff 0.16.0`. Record any other value in [plan.md](plan.md), because a version change moves the count.
- [ ] T002 Confirm that `.venv\Scripts\python.exe -m pytest --version` runs. Every later test command uses this interpreter.
- [ ] T003 Record the pre-change gate baseline. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Save the unit test pass count, because SC-009 compares against it.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prove the baseline and remove the two coordination risks. No slice starts until this phase closes.

- [ ] T004 Record the baseline. Run `.venv\Scripts\python.exe -m ruff check . --select LOG015 --statistics`. Write the count into [plan.md](plan.md) under "Measurement contract". The expected value is 4478.
- [ ] T005 Check for an open pull request that touches the same areas. Run `gh pr list --json number,title,files`. Issue #886 converts `print()` calls and can edit the same lines. Record any overlap in [plan.md](plan.md).
- [ ] T006 Search the whole tree for an existing module-level name `logger`. Run `.venv\Scripts\python.exe -m ruff check . --select LOG015 --output-format concise` to list the files, then search each file for `logger =`. Record every collision in [plan.md](plan.md). Requirement FR-008 depends on this record.
- [ ] T007 Search the tree for a logger that sets `propagate = False`. A module with that setting does not send a record to the root logger, so the `caplog` fixture cannot see it. Record every site in [plan.md](plan.md).

**Checkpoint**: The baseline reads 4478. The collision list and the propagate list exist. Slice 1 can start.

---

## Phase 3: User Story 1 and 2, Slice 1 - The tests area (Priority: P1)

**Goal**: Convert the 134 calls in `tests/`. This area proves the pattern at the lowest cost.

**Independent Test**: The `LOG015` count drops from 4478 to 4344. The unit suite keeps the T003 pass count.

**Files**: about 20 files under `tests/`. The largest is `tests/unit/refactors/test_fast_mode_small_seams.py` with 53 calls.

- [ ] T008 [US1] List the files in the slice. Run `.venv\Scripts\python.exe -m ruff check tests --select LOG015 --output-format concise`. Search each listed file for an existing name `logger`. Rename the other object if a collision exists, per FR-008.
- [ ] T009 [US1] Add the module logger line to each file in the slice. Place the line after the import block and before the first class or function, per FR-002. Add the inline comment that Principle VI requires.
- [ ] T010 [US1] Rewrite each root logger call in the slice. Change `logging.debug`, `logging.info`, `logging.warning`, `logging.error`, `logging.exception`, and `logging.critical` to the module logger form. Leave `logging.basicConfig` and `logging.getLogger()` unchanged, per FR-009.
- [ ] T011 [US1] Confirm that the call count did not move. Count the logging calls in each changed file before and after the edit. The two counts must match, per FR-007.
- [ ] T012 [US1] Read the whole difference. Confirm that each changed line differs by the object name alone. Count the changed levels and the changed message texts. Both counts must read zero, per SC-003 and SC-004.
- [ ] T013 [US1] Confirm the slice size. Run `git diff --shortstat`. The changed line count must stay at or below 500, per FR-011.
- [ ] T014 [US1] Verify the slice. Run `.venv\Scripts\python.exe -m ruff check . --select LOG015 --statistics` and confirm 4344. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Confirm that the pass count matches T003 and that the `caplog` assertions still pass.
- [ ] T015 [US2] Open the slice pull request. Name the area, the count of converted calls, and the count of touched files in the body, per FR-020. Write `Refs #1793` and not `Closes #1793`, because 13 slices remain.

**Checkpoint**: The count reads 4344. The pattern holds. Slice 2 can start.

---

## Phase 4: User Story 1 and 2, Slices 2 to 7 - The medium production areas (Priority: P1)

**Goal**: Convert 1976 calls across six slices. Each slice repeats the T008 to T015 steps for its own scope.

**Independent Test**: The `LOG015` count drops by the slice size after each slice. The unit suite keeps its pass count.

**Warning**: Do not change a message text and do not change a level. A reviewer who finds one changed message must reject the slice.

- [ ] T016 [US1] Convert slice 2. The scope is `src/auth`, `src/inventory`, and `src/ui`, which hold 393 calls. Repeat the T008 to T015 steps. Split the slice by area if the changed line count passes 500.
- [ ] T017 [US1] Convert slice 3. The scope is `src/device`, `src/site`, and `src/troubleshooting`, which hold 488 calls. Read `src/troubleshooting/marvis_troubleshoot_utils.py` with care, because it holds 76 calls. Repeat the T008 to T015 steps.
- [ ] T018 [P] [US1] Convert slice 4. The scope is `src/org`, which holds 191 calls. Read `src/org/org_ticket_manager.py` with care, because it holds 86 calls. Repeat the T008 to T015 steps.
- [ ] T019 [P] [US1] Convert slice 5. The scope is `src/capture`, which holds 220 calls. Repeat the T008 to T015 steps.
- [ ] T020 [P] [US1] Convert slice 6. The scope is `src/gateway`, which holds 261 calls. Repeat the T008 to T015 steps.
- [ ] T021 [US1] Convert slice 7. The scope is `src/refactors`, which holds 423 calls. Split the slice by file if the changed line count passes 500. Repeat the T008 to T015 steps.

**Checkpoint**: The count reads about 2368. Slice 8 can start.

---

## Phase 5: User Story 1 and 2, Slices 8 to 11 - The four largest files (Priority: P1)

**Goal**: Convert 779 calls across four single-file slices. Each of these files exceeds 100 calls, so each takes its own pull request.

**Independent Test**: The `LOG015` count drops by the file count after each slice. The mypy gate stays green.

**Caution**: A single file cannot split across two pull requests. The module logger line must land with the first converted call in that file. A split leaves the module holding both call forms.

- [ ] T022 [US1] Convert slice 8. The file is `src/firmware/org_ap_upgrader.py`, which holds 143 calls. Repeat the T008 to T015 steps for that file alone.
- [ ] T023 [US1] Convert slice 9. The file is `src/firmware/firmware_manager.py`, which holds 228 calls. Repeat the T008 to T015 steps for that file alone.
- [ ] T024 [US1] Convert slice 10. The scope is the rest of `src/firmware`, which holds 130 calls. `src/firmware/bulk_ap_upgrader.py` holds 105 of them. Repeat the T008 to T015 steps.
- [ ] T025 [US1] Convert slice 11. The file is `MistHelper.py`, which holds 303 calls. Run `.venv\Scripts\python.exe -m mypy src/ MistHelper.py --config-file pyproject.toml` after the edit. Issue #888 widened the mypy scope to cover this file, so a wrong edit fails the type gate.

**Checkpoint**: The count reads about 1589. Slice 12 can start.

---

## Phase 6: User Story 1 and 2, Slices 12 and 13 - The export area and the remainder (Priority: P1)

**Goal**: Convert the last 1589 calls. `src/export` holds 678 of them, so that area splits into two or more slices.

**Independent Test**: The `LOG015` count reaches zero.

- [ ] T026 [US1] Split `src/export` into groups of at most 500 changed lines. List the files with `.venv\Scripts\python.exe -m ruff check src/export --select LOG015 --output-format concise` and record the group boundary in [plan.md](plan.md).
- [ ] T027 [US1] Convert slice 12. The scope is the first `src/export` group. Repeat the T008 to T015 steps.
- [ ] T028 [US1] Convert slice 13. The scope is the second `src/export` group. Repeat the T008 to T015 steps.
- [ ] T029 [US1] List every area that the earlier slices did not cover. Run `.venv\Scripts\python.exe -m ruff check . --select LOG015 --output-format concise` and group the remaining files by area. Record the group boundary in [plan.md](plan.md).
- [ ] T030 [US1] Convert each remaining group as its own slice. Repeat the T008 to T015 steps for each one. Keep every pull request at or below 500 changed lines.
- [ ] T031 [US1] Verify the whole conversion. Run `.venv\Scripts\python.exe -m ruff check . --select LOG015 --statistics` and confirm zero results. SC-001 depends on this run.

**Checkpoint**: The count reads zero. User Story 1 is complete. Phase 7 can start.

---

## Phase 7: User Story 3 - Stop the count from growing again (Priority: P2)

**Goal**: Add `LOG015` to the ruff `select` list. This is the final change of the feature.

**Independent Test**: A reviewer adds one `logging.info(...)` call to a tracked file. The lint gate fails and names `LOG015`.

**Warning**: Run this phase only after Phase 6 reports zero results. The gate fails on every push while any call remains.

- [ ] T032 [US3] Change line 164 of `pyproject.toml` from `select = ["E", "F", "W", "I", "UP", "B", "G"]` to `select = ["E", "F", "W", "I", "UP", "B", "G", "LOG015"]`. Add no other rule, per FR-017.
- [ ] T033 [US3] Add a comment above the `select` list in `pyproject.toml`. State that a root logger record carries no module name and that an operator cannot filter it. Keep the comment inside 120 characters. Depends on T032, because both tasks edit the same file.
- [ ] T034 [US3] Read `src/utils/logger_utils.py` in full. Confirm that the module logger does not sit inside a filter or a handler. A record from inside the logging path can re-enter that path and can recurse without end.
- [ ] T035 [US3] Prove the negative case for SC-008. Add one temporary `logging.info("temp")` call to a tracked file under `src/`. Run `.venv\Scripts\python.exe -m ruff check .` and confirm that it reports `LOG015` and exits with code 1. Remove the line. Run `git status` and confirm that the tree holds no leftover change.

**Checkpoint**: The gate reports a root logger call. SC-007 and SC-008 now hold.

---

## Phase 8: Polish and Final Validation

**Purpose**: Prove every success criterion and close the issue. These tasks change no source line.

- [ ] T036 Run the full gate set exactly as CI runs it. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`, `.venv\Scripts\python.exe -m pylint src/`, `.venv\Scripts\python.exe -m radon cc src/ -a -nb`, `.venv\Scripts\python.exe -m vulture src/ --min-confidence 80`, `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r .`, and `.venv\Scripts\python.exe -m pytest --cov=src/ --cov-fail-under=80`. Do not scope a gate to the changed files only.
- [ ] T037 [P] Prove SC-002. Search every converted module for `logging.getLogger(__name__)` and confirm exactly one match in each one.
- [ ] T038 [P] Prove SC-010. Set the level of one module logger to `DEBUG` and leave the root logger at `INFO`. Run an operation that reaches that module. Confirm that the output holds debug records from that module and holds no debug record from another module.
- [ ] T039 [P] Prove SC-005. Compare the count of logging calls in the tree before the first slice and after the last slice. The two counts must match.
- [ ] T040 Open the final pull request for the gate change. Write `Closes #1793` in the body. Link `specs/1793-root-logger-calls/spec.md`. List every slice pull request number. Complete the checklist in `.github/PULL_REQUEST_TEMPLATE.md`. Add the `auto-merge` label only after every check passes, including CodeQL.

---

## Dependencies and Execution Order

### Phase order

| Phase | Content | Starts after |
| - | - | - |
| 1 | Setup | Nothing |
| 2 | Foundational baseline | Phase 1 |
| 3 | Slice 1, the tests area | Phase 2 records the baseline |
| 4 | Slices 2 to 7, the medium areas | Phase 3 proves the pattern |
| 5 | Slices 8 to 11, the largest files | Phase 4 |
| 6 | Slices 12 and 13, the export area and the remainder | Phase 5 |
| 7 | US3, the gate change | Phase 6 reports zero results |
| 8 | Polish and final validation | Phase 7 |

### Why slice 1 converts the test area first

A test module carries no operator value in its records. A mistake there costs the least. Slice 1 also proves that the `caplog` fixture still captures a record from a named logger, which is the largest test risk in the whole feature.

### Slice exit rule

A slice must reduce the count by its own size and must move no other count. The unit suite must keep its pass count. A slice that fails either check does not merge.

---

## Parallel Opportunities

| Phase | Parallel tasks | Reason |
| - | - | - |
| 4 | T018, T019, T020 | The three areas hold no shared file. |
| 8 | T037, T038, T039 | The three checks read different data. |

**Caution**: Two agents must not open a slice pull request for the same area at the same time. Claim the area on issue #1793 before the branch starts.

---

## Implementation Strategy

### Minimum viable delivery

Slice 1 alone delivers no operator value, because a test record reaches no operator. Slice 2 delivers the first real value, because an operator can then filter three production areas.

### Order of risk

The largest risk is a silent message change. The rewrite is mechanical, so a scripted edit is safe. A scripted edit that also touches a message is not safe. Task T012 is the control, and it runs in every slice.
