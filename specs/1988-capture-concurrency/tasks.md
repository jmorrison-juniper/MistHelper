# Tasks: Capture portal concurrency evaluation

**Input**: Design documents from `specs\1988-capture-concurrency\`

**Prerequisites**: `plan.md`, `spec.md`, and the raw measurement artifact.

**Tests**: Include the benchmark contract test because the evaluation artifact must stay repeatable.

## Phase 1: Setup

**Purpose**: Prepare an isolated branch and read the source rules.

- [x] T001 Read issue #1988 and issue #1823. (delivered: GitHub issue context)
- [x] T002 Add the `in-progress` label to issue #1988. (delivered: GitHub issue label)
- [x] T003 Create worktree `..\MistHelper-1988-concurrency` from `origin/main`. (delivered: local worktree)
- [x] T004 Use branch `chore/1988-capture-concurrency` because `test/` is not in the branch table. (delivered: git branch)
- [x] T005 Verify `mistapi` 0.64.0 and collect 16619 tests with zero collection errors. (delivered: setup command output)

---

## Phase 2: Research

**Purpose**: Identify current portal concurrency and safety constraints before measurement.

- [x] T006 Read `src\upgrade_portal\capture\collector.py` for two-wave capture reads. (delivered: plan.md)
- [x] T007 Read `src\upgrade_portal\runtime\pools.py` for `CAPTURE_WORKER_TARGET`. (delivered: plan.md)
- [x] T008 Read `src\upgrade_portal\upgrade\gate.py` and `phase_gate.py` for rate budget facts. (delivered: plan.md)
- [x] T009 Read `src\upgrade_portal\compare\diff.py` for digest short circuit behavior. (delivered: plan.md)
- [x] T010 Review pull request #2729 file overlap and avoid production portal changes. (delivered: plan.md)

---

## Phase 3: User Story 1 - Review measured evidence (Priority: P1)

**Goal**: Produce a repeatable benchmark and raw measurement artifact.

**Independent Test**: Run `python scripts\benchmarks\bench_capture_concurrency.py`.

- [x] T011 [US1] Create `CaptureConcurrencyBenchmark` in `scripts\benchmarks\bench_capture_concurrency.py`. (delivered: scripts\benchmarks\bench_capture_concurrency.py)
- [x] T012 [US1] Use the repository performance recorder and privacy filter. (delivered: raw-data.events.jsonl)
- [x] T013 [US1] Measure the current four-worker model and two candidates. (delivered: raw-data.jsonl)
- [x] T014 [US1] Record result counts and error counts for each run. (delivered: raw-data.jsonl)

---

## Phase 4: User Story 2 - Keep safety constraints visible (Priority: P2)

**Goal**: Document the four required safety findings.

**Independent Test**: Read `plan.md` and check the four findings.

- [x] T015 [US2] Document the rate-limit finding. (delivered: plan.md)
- [x] T016 [US2] Document the site-lock finding. (delivered: plan.md)
- [x] T017 [US2] Document the complexity-gate finding. (delivered: plan.md)
- [x] T018 [US2] Document the store-contention finding. (delivered: plan.md)

---

## Phase 5: User Story 3 - Repeat the measurement (Priority: P3)

**Goal**: Add a unit test that proves the benchmark writes safe artifacts.

**Independent Test**: Run `python -m pytest tests\unit\benchmarks\test_capture_concurrency_benchmark.py -q`.

- [x] T019 [US3] Add a benchmark artifact test. (delivered: tests\unit\benchmarks\test_capture_concurrency_benchmark.py)
- [x] T020 [US3] Verify the artifact contains no site or token text. (delivered: tests\unit\benchmarks\test_capture_concurrency_benchmark.py)

---

## Phase 6: Validation and pull request

**Purpose**: Prove that the evaluation is safe to merge.

- [ ] T021 Run the required local gates from issue #1988.
- [ ] T022 Create no changelog fragment because this change has no user-visible behavior.
- [ ] T023 Commit, push, open the pull request, and wait for required checks.
- [ ] T024 Add `auto-merge` only after every required check passes, including CodeQL.
- [ ] T025 Verify that issue #1988 closes or close it by hand with evidence.

## Dependencies & Execution Order

Phase 1 precedes all other phases. Phase 2 precedes the benchmark and the recommendation. Phase 3 precedes Phase 4, because the plan needs measured numbers. Phase 5 and Phase 6 follow the completed artifact.

## Parallel Opportunities

T006 through T010 can run in parallel because they read different files. T015 through T018 can run in parallel after the measurement exists.
