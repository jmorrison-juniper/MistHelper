---
description: "Task list for the Redis time-series entity identifier fallback"
---

# Tasks: Redis Time-Series Entity Identifier Fallback

**Input**: Design documents from `/specs/990-redis-entity-id/`

**Branch**: `feat/990-redis-entity-id`. The branch already exists. Do not create a
branch. Do not switch a branch.

**Issue**: GitHub issue #990, part 2 only. Part 1 already landed on the main
branch. The Non-Goals section of `spec.md` lists every part 1 item.

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`quickstart.md`, and `contracts/entity-id-resolution.md`.

**Tests**: The specification requests tests. Functional Requirement FR-009 names
three branches. Success Criterion SC-003 requires a test for each branch. The
task list therefore holds test tasks.

**Organization**: The tasks group by user story. Each user story maps to one
branch of the resolution rule.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task runs in parallel with another task. The two tasks touch
  different files and hold no dependency on each other.
- **[Story]**: The user story that owns the task. The values are US1, US2, and
  US3.

## Path Conventions

The project keeps a single source package under `src/` and a single test package
under `tests/`. The commands below run from the repository root.

**Warning**: The global `python` on this host is broken. It fails to import
`requests` and `mistapi`. Call `.venv\Scripts\python.exe` for every command.

---

## Phase 1: Setup

**Purpose**: Record the state before the first edit. The baseline numbers prove
that the change adds no regression.

- [X] T001 Confirm the working state. Read `specs/990-redis-entity-id/quickstart.md`. Confirm that the branch `feat/990-redis-entity-id` is the current branch. Do not create a branch. Do not switch a branch.
- [X] T002 [P] Capture the baseline test result for `tests/unit/test_redis_writer.py`. Run `.venv\Scripts\python.exe -m pytest tests/unit/test_redis_writer.py -q`. Record the pass count. Every test must pass.
- [X] T003 [P] Capture the baseline complexity score for `src/db/redis_writer.py`. Run `.venv\Scripts\python.exe -m radon cc src/db/redis_writer.py -s -n A`. Record the highest block score. The expected value is 5.

**Checkpoint**: The baseline holds a passing suite and a highest block score of 5.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the one resolution rule and wire it into the extraction path.
Requirement FR-013 states that the file must hold one rule for the batch path.
All three user stories read that one rule.

**Warning**: No user story test can pass until this phase completes. Task T008
changes the return shape of `_extract_chunk`. Task T009 repairs the one existing
test that the change breaks. Land T008 and T009 together.

- [X] T004 Add the module constant `BATCH_ENTITY_FALLBACK_KEYS = ("device_id", "site_id", "org_id", "mac", "id")` in `src/db/redis_writer.py` beside `WEBHOOK_ENTITY_KEYS` at line 45. Add a same-line `# WHY:` comment. The constant is a tuple, so no caller can change it at run time.
- [X] T005 Replace the inline tuple inside `_pick_entity_field` in `src/db/redis_writer.py` at line 447 with a read of `BATCH_ENTITY_FALLBACK_KEYS`. Keep the return values unchanged. Update the same-line `# WHY:` comment, because the comment still names an inline tuple.
- [X] T006 Add the static method `_is_usable(value: Any) -> bool` to `RedisTimeSeriesWriter` in `src/db/redis_writer.py`. Return `False` for `None`. Return `False` when the text form holds only blank space. Return `True` in every other case. The method must return `True` for the number `0`. Do not use a plain truth test, because a truth test rejects `0`.
- [X] T007 Add the static method `_resolve_entity_id(record: dict[str, Any], entity_key_field: str) -> tuple[str, str]` to `RedisTimeSeriesWriter` in `src/db/redis_writer.py`. Read the strategy field first and return the source `strategy`. Then walk `BATCH_ENTITY_FALLBACK_KEYS` and return the source `fallback`. Return the text `unknown` and the source `unknown` last. Match every row of the decision table in `specs/990-redis-entity-id/data-model.md`. Place the method beside `_pick_entity_field`.
- [X] T008 Replace the direct lookup at line 190 inside `_extract_chunk` in `src/db/redis_writer.py`. Call `_resolve_entity_id` and tally the returned source into a local `Counter`. Return the counter as a third item. Add `from collections import Counter` to the import block. Keep the method pure, because a thread pool calls it.
- [X] T009 Update the mock in `test_over_1000_records_uses_thread_pool` in `tests/unit/test_redis_writer.py` at line 204. Change the `return_value` from the two-item pair `([], {})` to the three-item triple `([], {}, Counter())`. Import `Counter` in the test. The two-item pair is too short for the new unpack in `_extract_parallel`. The mock produces no time-series key, so Success Criterion SC-002 still holds.
- [X] T010 Merge the chunk counters inside `_extract_parallel` in `src/db/redis_writer.py`. Unpack three items from each future result. Merge the counters with `Counter.update`. Return the merged counter as a third item.
- [X] T011 Emit the summary from `_extract_all_adds` in `src/db/redis_writer.py`. Log an info event before the extraction. Unpack three items from the sequential path and from the parallel path. Emit one debug summary that reports the three counts. Return the first two items only, so the signature that `write` consumes does not change.

**Checkpoint**: The resolution rule exists in one place. The counter travels
through the return value. No thread shares a mutable counter.

---

## Phase 3: User Story 1 - A NOC engineer separates composite-key records (Priority: P1) - MVP

**Goal**: A record that omits the strategy field resolves to a real entity
identifier. The record no longer lands in the `unknown` bucket.

**Independent Test**: Write a record set in which the strategy field is absent
and a common identifier is present. Confirm that the writer creates one key for
each distinct identifier. Confirm that the writer creates no key that carries the
text `unknown`.

**Branch under test**: The `fallback` branch. This branch is the second of the
three branches that Requirement FR-009 names.

- [X] T012 [US1] Add a unit test for the fallback branch in `tests/unit/test_redis_writer.py`. Build a record that omits the strategy field and carries `device_id`. Assert that `_resolve_entity_id` returns the `device_id` value and the source `fallback`. This test covers Requirement FR-002 and Acceptance Scenario 1 of User Story 1.
- [X] T013 [US1] Add a unit test for distinct keys in `tests/unit/test_redis_writer.py`. Build two records that omit the strategy field and carry the `device_id` values `dev-1` and `dev-2`. Give each record one numeric field. Assert that `_extract_chunk` produces two distinct time-series keys. Assert that no key holds the text `unknown`. This test covers Acceptance Scenarios 2 and 3 of User Story 1 and Success Criterion SC-001.
- [X] T014 [US1] Add a parametrized unit test for the unusable strategy values in `tests/unit/test_redis_writer.py`. Cover the strategy values `None`, the empty text value, and a text value that holds only blank space. Give each record a usable `device_id`. Assert that every case returns the `device_id` value and the source `fallback`. This test covers the first three Edge Cases and the usable-value rule.
- [X] T015 [US1] Add a unit test for the fallback order in `tests/unit/test_redis_writer.py`. Build one record that carries `site_id` and `org_id` and assert that `site_id` wins. Build one record that carries an empty `device_id` and a usable `site_id` and assert that `site_id` wins. This test covers Requirement FR-006 and the fallback-order Edge Cases.

**Checkpoint**: Run `.venv\Scripts\python.exe -m pytest tests/unit/test_redis_writer.py -q`. Every test passes. User Story 1 works on its own.

---

## Phase 4: User Story 2 - An existing export keeps its current keys (Priority: P2)

**Goal**: A record that carries the strategy field produces the same key as
before. The existing history and the new points join the same series.

**Independent Test**: Write a record set in which every record carries the
strategy field. Compare the generated keys against the keys that the baseline
build produces. Confirm that the two sets match.

**Branch under test**: The `strategy` branch. This branch is the first of the
three branches that Requirement FR-009 names.

- [X] T016 [US2] Add a unit test for the strategy branch in `tests/unit/test_redis_writer.py`. Build a record that carries the strategy field with a usable value. Assert that `_resolve_entity_id` returns the text form of that value and the source `strategy`. This test covers Requirement FR-001 and Acceptance Scenario 1 of User Story 2.
- [X] T017 [US2] Add a unit test for the strategy priority in `tests/unit/test_redis_writer.py`. Build a record that carries both the strategy field and a `device_id` field. Give the two fields different values. Assert that the strategy value wins and that the source is `strategy`. This test covers Acceptance Scenario 2 of User Story 2 and Invariant INV-3.
- [X] T018 [US2] Add a unit test for the value `0` in `tests/unit/test_redis_writer.py`. Build a record whose strategy field holds the number `0`. Assert that `_resolve_entity_id` returns the text `0` and the source `strategy`. A plain truth test would reject `0` and would fall through to the fallback list. This test guards that defect. The test covers Invariant INV-5 and the `0` Edge Case.
- [X] T019 [US2] Add a regression test for the byte-identical key in `tests/unit/test_redis_writer.py`. Build one record that carries the strategy field `entity_id` with the value `dev-1` and one numeric field `cpu`. Call `_extract_chunk` and assert the exact key text `testFunc:dev-1:cpu`. Assert that the key holds three parts that a colon separates. This test covers Requirement FR-005 and Success Criteria SC-002 and SC-004.

**Checkpoint**: Run `.venv\Scripts\python.exe -m pytest tests/unit/test_redis_writer.py -q`. Every test passes. No expected key in an existing test changes. The only existing test that changed is the mock in task T009.

---

## Phase 5: User Story 3 - A record without any identifier still writes (Priority: P3)

**Goal**: A record that carries no identifier still writes. The writer keeps the
`unknown` sentinel and keeps the key length stable.

**Independent Test**: Write a record that carries only numeric fields. Confirm
that the writer creates a key that carries the text `unknown`. Confirm that the
write completes.

**Branch under test**: The `unknown` branch. This branch is the third of the
three branches that Requirement FR-009 names.

- [X] T020 [US3] Add a unit test for the sentinel branch in `tests/unit/test_redis_writer.py`. Build a record that carries only a numeric field. Assert that `_resolve_entity_id` returns the text `unknown` and the source `unknown`. Assert that `_extract_chunk` builds a key that carries the text `unknown`. This test covers Requirement FR-003 and Acceptance Scenario 1 of User Story 3.
- [X] T021 [US3] Add a unit test for the empty record in `tests/unit/test_redis_writer.py`. Pass an empty dictionary to `_resolve_entity_id`. Assert that the method returns the text `unknown` and the source `unknown`. Assert that the method raises no error. This test covers Acceptance Scenario 2 of User Story 3 and Invariant INV-1.

**Checkpoint**: All three user stories work on their own. All three branches hold a test. Success Criterion SC-003 is met.

---

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Cover the observability rule, the prose rules, and every quality
gate. These items serve all three user stories.

- [X] T022 [P] Add one entry under the `## [Unreleased]` heading in `CHANGELOG.md`. Name the defect, name the fallback order `device_id`, `site_id`, `org_id`, `mac`, `id`, and name the issue number 990. Follow the Keep a Changelog format. This task covers Requirement FR-010.
- [X] T023 Add a unit test for the resolution summary in `tests/unit/test_redis_writer.py`. Capture the log output of `_extract_all_adds` for a mixed record set. Assert that the writer emits exactly one debug summary for the call. Assert that the summary reports three counts. Assert that the three counts sum to the record count. Assert that the writer emits no log line for a single record. This test covers Requirements FR-007 and FR-008 and Success Criterion SC-007.
- [X] T024 Audit the inline comments in `src/db/redis_writer.py` and in `tests/unit/test_redis_writer.py`. Confirm that every changed line carries a same-line comment that states the reason for the line. Match the existing `# WHY:` style of the source file. This task covers Requirement FR-011.
- [X] T025 Run the lint gate and the format gate across the whole repository. Run `.venv\Scripts\python.exe -m ruff check .` and `.venv\Scripts\python.exe -m black --check --diff .`. Both commands must exit with the code 0. Warning: a gate that runs only against the changed path can pass while the workflow gate fails.
- [X] T026 Run the type gate. Run `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`. The command must exit with the code 0. The package `src.db` turns off three strict checks, so read `pyproject.toml` line 315 before a change to a type hint.
- [X] T027 Run the test gate and the coverage gate. Run `.venv\Scripts\python.exe -m pytest --cov=src/ --cov-fail-under=80 -q`. The command must exit with the code 0.
- [X] T028 Run the complexity gate and the security gate. Run `.venv\Scripts\python.exe -m radon cc src/ -a -nb` and `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r .`. The radon step must print no block above the score 10. Both commands must exit with the code 0. This task and tasks T025 to T027 together cover Success Criterion SC-006.
- [X] T029 Grade the prose. Run `.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 CHANGELOG.md`. The score must be 80 or above. Apply the same rule to every comment in `src/db/redis_writer.py`. This task covers Requirement FR-012 and Success Criterion SC-008.
- [X] T030 Walk steps 2 to 6 of `specs/990-redis-entity-id/quickstart.md`. Confirm each expected result. Confirm every row of the edge-case table in step 5. Confirm the Definition of Done table at the end of the file.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Holds no dependency. Start here.
- **Foundational (Phase 2)**: Depends on Phase 1. Blocks every user story.
- **User Stories (Phases 3 to 5)**: Each phase depends on Phase 2. After Phase 2
  completes, the three story phases hold no dependency on each other.
- **Polish (Phase 6)**: Depends on Phases 2 to 5.

### Task Dependencies

| Task | Depends on | Reason |
| - | - | - |
| T005 | T004 | The method reads the new constant. |
| T007 | T004, T006 | The rule reads the constant and the usable-value test. |
| T008 | T007 | The call site calls the new rule. |
| T009 | T008 | The mock repairs the return shape that T008 changed. |
| T010 | T008 | The merge reads the third item that T008 returns. |
| T011 | T008, T010 | The summary reads the merged counter. |
| T012 to T021 | T011 | Every story test reads the finished rule. |
| T023 | T011 | The summary test reads the emitted event. |
| T027 | T009 | The suite fails until the mock returns three items. |

### Within Each User Story

Each story phase holds test tasks only. The one shared rule already sits in
Phase 2. Requirement FR-013 forbids a second rule, so no story phase adds source
logic.

### Parallel Opportunities

The parallel set is small, because the change touches three files only.

- **Phase 1**: Task T002 and task T003 run in parallel. Both commands read only.
- **Phase 6**: Task T022 runs in parallel with every other Phase 6 task. It edits
  `CHANGELOG.md`, and no other task edits that file.
- **Phases 3 to 5**: The three story phases run in parallel across three people.
  Every task inside them edits `tests/unit/test_redis_writer.py`, so the tasks
  inside one phase run in order.
- **Phase 2**: No task runs in parallel. Every task edits
  `src/db/redis_writer.py`, and tasks T005 through T011 form a dependency chain.

---

## Implementation Strategy

### Minimum viable product

User Story 1 is the minimum viable product. It fixes the defect that issue #990
reports. Complete Phase 1, Phase 2, and Phase 3. Then run the gates in Phase 6.

### Incremental delivery

1. Complete Phase 1 and Phase 2. The rule now exists and the suite passes.
2. Complete Phase 3. The defect is fixed and User Story 1 is testable.
3. Complete Phase 4. The regression guard proves that no existing key changes.
4. Complete Phase 5. The sentinel path holds a test.
5. Complete Phase 6. Every gate passes and the changelog holds an entry.

### Risk register

| Risk | Task that handles it |
| - | - |
| The return shape of `_extract_chunk` grows from two items to three items. The existing mock in `test_over_1000_records_uses_thread_pool` then fails to unpack. | T009 |
| A plain truth test rejects the entity identifier `0` and sends the record to the fallback list. | T006, T018 |
| A change to the resolution rule splits an existing history into two series. | T019 |
| A per-record log line floods the output for a large export. | T023 |
| A gate that runs only against the changed path passes while the workflow gate fails. | T025 to T028 |
