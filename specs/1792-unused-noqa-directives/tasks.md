# Tasks: Unused Noqa Directive Removal

**Feature**: `1792-unused-noqa-directives` | **Branch**: `lint/1792-unused-noqa` | **Date**: 2026-08-06

**GitHub Issue**: [#1792](https://github.com/jmorrison-juniper/MistHelper/issues/1792)

**Input**: Design documents from `specs/1792-unused-noqa-directives/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: The specification requests no new test. The existing suite must keep its pass count. Each phase ends with a measurement task, not with a new test file.

**Branch rule**: Create `lint/1792-unused-noqa` from `main`. Do not branch from another feature branch.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with another task in the same phase. The tasks touch different files.
- **[Story]**: The user story that owns the task. The value is `US1`, `US2`, or `US3`.
- Each task names an exact file path or an exact command.

## Rules that apply to every task

1. Use `.venv\Scripts\python.exe` for every Python command. The global interpreter cannot import the project.
2. Measure with `--extend-select RUF100`. Never measure with `--select RUF100`. The isolated form reports 34 directives that suppress a real result.
3. Add no lint suppression. This work removes suppressions and adds none. Non-goal NG-008 states this rule.
4. Follow the Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md` for every prose line.
5. Keep the repair in one commit and keep the configuration change in a second commit. Both commits land in one pull request.

---

## Phase 1: Setup

**Purpose**: Confirm the environment before any measurement.

- [ ] T001 Create the branch with `git checkout -b lint/1792-unused-noqa main`. Confirm the result with `git branch --show-current`. Stop if the command returns another value.
- [ ] T002 Confirm the tool version with `.venv\Scripts\python.exe -m ruff --version`. The expected value is `ruff 0.16.0`. Record any other value in [plan.md](plan.md), because a version change moves every count.
- [ ] T003 Confirm that `.venv\Scripts\python.exe -m pytest --version` runs. Every later test command uses this interpreter.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prove the baseline and record the two latent suppression counts. No edit starts until this phase closes.

**Warning**: Task T007 protects 88 blind `except` results. If a contributor skips it, issue #1794 loses those results without any signal.

- [ ] T004 Record the repair baseline. Run `.venv\Scripts\python.exe -m ruff check . --extend-select RUF100 --statistics`. Write the count into [plan.md](plan.md) under "Measurement contract". The expected value is 286.
- [ ] T005 Record the isolated count. Run `.venv\Scripts\python.exe -m ruff check . --select RUF100 --statistics`. Write the count into [plan.md](plan.md). The expected value is 320. Subtract the T004 value and confirm that the difference reads 34.
- [ ] T006 Prove that the 34 extra results suppress a real result. Compare the two result sets from T004 and T005 by file and by line. Read four of the extra sites and confirm that each names `E501`, `E731`, `E402`, or `F401`. Requirement FR-002 depends on this proof.
- [ ] T007 Record the `BLE001` latent count. Run `.venv\Scripts\python.exe -m ruff check . --select BLE001 --statistics` and then the same command with `--ignore-noqa`. The expected values are 412 and 500. Write both into [plan.md](plan.md) and confirm that the difference reads 88.
- [ ] T008 Record the `DTZ005` latent count. Run `.venv\Scripts\python.exe -m ruff check . --select DTZ005 --statistics` and then the same command with `--ignore-noqa`. The expected values are 56 and 57. Write both into [plan.md](plan.md). Issue #1795 reads this record.
- [ ] T009 Record the pre-change gate baseline. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Save the unit test pass count, because SC-006 compares against it.

**Checkpoint**: The baseline reads 286 repairs. The three latent records exist. Phase 3 can start.

---

## Phase 3: User Story 1 - Remove every directive that suppresses nothing (Priority: P1)

**Goal**: Reduce the `RUF100` count to zero and change no line of code.

**Independent Test**: A reviewer runs `ruff check . --extend-select RUF100`. The command exits with code 0 and reports zero results.

**Warning**: Run the repair with `--extend-select`. The `--select RUF100 --fix` form deletes 34 live suppressions and breaks the lint gate on the next run.

- [ ] T010 [US1] Run the repair. Use `.venv\Scripts\python.exe -m ruff check . --extend-select RUF100 --fix`. Add no other rule to the command. Requirement FR-005 forbids a mixed repair.
- [ ] T011 [US1] Read the difference for the largest file on its own. Run `git diff -- src/device/ap_profile_migration_manager.py`. That file holds 67 of the 286 directives. Confirm that every removed line is a comment or a comment fragment.
- [ ] T012 [US1] Count the changed lines that are not comments. Run `git diff -U0` and search each changed line for a leading `#` inside the comment position. The expected count is zero. Requirement FR-004 demands this record. Stop if the count is above zero.
- [ ] T013 [US1] Confirm that no useful comment text disappeared. Read the difference for `src/site/address_audit/ui_geocoder.py`, `src/export/site_export_utils.py`, and `src/ssid_consolidation/_ssid_template_phase45.py`. Ruff keeps the rest of a comment when other text follows the directive, so a lost sentence signals a defect.
- [ ] T014 [US1] Review the test file change. Read the difference for `tests/unit/refactors/test_fast_mode_small_seams.py`. A test file change needs the same care as a source file change.
- [ ] T015 [US1] Run the formatter. Use `.venv\Scripts\python.exe -m black .`. A shortened line can change the width that the formatter prefers, so this step must follow the repair.
- [ ] T016 [US1] Verify User Story 1. Run `.venv\Scripts\python.exe -m ruff check . --extend-select RUF100` and confirm zero results. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Confirm that the pass count matches T009.
- [ ] T017 [US1] Commit the repair on its own. Write a Conventional Commits message that names the count of removed directives and the count of touched files. Requirement FR-014 demands both counts.

**Checkpoint**: The `RUF100` count reads zero. SC-001 and SC-002 now hold. Phase 4 can start.

---

## Phase 4: User Story 3 - Protect the blind except work from a silent loss (Priority: P1)

**Goal**: Prove that the true `BLE001` count is 500 and record the proof where issue #1794 reads it.

**Independent Test**: A reviewer runs `ruff check . --select BLE001 --statistics` on the repaired branch. The count reads 500.

**Note on the order**: This phase runs before User Story 2. The gate change is the final change, because the gate fails while any result remains.

- [ ] T018 [US3] Measure `BLE001` again after the repair. Run `.venv\Scripts\python.exe -m ruff check . --select BLE001 --statistics` and the same command with `--ignore-noqa`. Both values must read 500. A lower value means that the repair missed a directive.
- [ ] T019 [US3] Measure `DTZ005` again after the repair. Run `.venv\Scripts\python.exe -m ruff check . --select DTZ005 --statistics` and the same command with `--ignore-noqa`. Both values must read 57.
- [ ] T020 [US3] Write the coordination text for the pull request body. State that 88 lines carried an inert `# noqa: BLE001` directive. State that the true count is 500 and that the earlier default run reported 412. State that issue #1794 must not start before this work lands. Requirements FR-009, FR-010, and FR-011 demand these three statements.
- [ ] T021 [US3] Comment on issue [#1794](https://github.com/jmorrison-juniper/MistHelper/issues/1794) with `gh issue comment 1794 --body-file <file>`. Name the 88-line count and name this pull request. Delete the body file after the command returns.

**Checkpoint**: The true `BLE001` count is on record. SC-005 and SC-007 now hold. Phase 5 can start.

---

## Phase 5: User Story 2 - Stop the count from growing again (Priority: P2)

**Goal**: Add `RUF100` to the ruff `select` list, so that a new directive with no matching result fails the gate.

**Independent Test**: A reviewer adds one directive with no matching result to a tracked file. The lint gate fails and names `RUF100`.

**Warning**: Run this phase only after Phase 3 reports zero results. The gate fails on every push while any result remains.

- [ ] T022 [US2] Change line 164 of `pyproject.toml` from `select = ["E", "F", "W", "I", "UP", "B", "G"]` to `select = ["E", "F", "W", "I", "UP", "B", "G", "RUF100"]`. Add no other rule, per FR-008.
- [ ] T023 [US2] Add a comment above the `select` list in `pyproject.toml`. State that a directive with no matching result is a false record. Keep the comment inside 120 characters. Depends on T022, because both tasks edit the same file.
- [ ] T024 [US2] Verify the gate. Run `.venv\Scripts\python.exe -m ruff check .` and confirm that it passes with the new list.
- [ ] T025 [US2] Prove the negative case for SC-004. Add one temporary `# noqa: E501` directive to a short line in a tracked file under `src/`. Run `.venv\Scripts\python.exe -m ruff check .` and confirm that it reports `RUF100` and exits with code 1. Remove the line. Run `git status` and confirm that the tree holds no leftover change.
- [ ] T026 [US2] Commit the configuration change. Requirement FR-007 demands that this commit land in the same pull request as the T017 commit.

**Checkpoint**: The gate reports a false directive. SC-003 and SC-004 now hold.

---

## Phase 6: Polish and Final Validation

**Purpose**: Prove every success criterion and open the pull request. These tasks change no source line.

- [ ] T027 Run the full gate set exactly as CI runs it. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`, `.venv\Scripts\python.exe -m pylint src/`, `.venv\Scripts\python.exe -m radon cc src/ -a -nb`, `.venv\Scripts\python.exe -m vulture src/ --min-confidence 80`, `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r .`, and `.venv\Scripts\python.exe -m pytest --cov=src/ --cov-fail-under=80`. Do not scope a gate to the changed files only. SC-006 depends on this run.
- [ ] T028 [P] Prove SC-008. Run `git diff --name-only main...HEAD`. Confirm that the list holds no path under `mist-ops-platform`, `web_portal`, `scripts`, or `src/maps`.
- [ ] T029 [P] Measure the count one last time before the push. Run `.venv\Scripts\python.exe -m ruff check . --extend-select RUF100 --statistics` and confirm zero results. A concurrent pull request can add a new directive while this work is open.
- [ ] T030 Open the pull request against `main` from `lint/1792-unused-noqa`. Write `Closes #1792` in the body. Attach the T020 coordination text. Link `specs/1792-unused-noqa-directives/spec.md`. Complete the checklist in `.github/PULL_REQUEST_TEMPLATE.md`. Add the `auto-merge` label only after every check passes, including CodeQL.

---

## Dependencies and Execution Order

### Phase order

| Phase | Content | Starts after |
| - | - | - |
| 1 | Setup | Nothing |
| 2 | Foundational baseline | Phase 1 |
| 3 | US1, the repair | Phase 2 records all three baselines |
| 4 | US3, the coordination record | Phase 3 reports zero results |
| 5 | US2, the gate change | Phase 4 records the 500 count |
| 6 | Polish and final validation | Phase 5 |

### Why User Story 3 runs before User Story 2

The template orders a phase by story priority. This feature runs User Story 3 in the middle. The `BLE001` proof needs the repaired tree, and the gate change must stay last. A gate change before the repair fails every push.

### Same-file sequencing

| Task | Depends on | Reason |
| - | - | - |
| T011 to T015 | T010 | Each task reads the difference that the repair produces. |
| T023 | T022 | Both edit `pyproject.toml`. |
| T026 | T022 and T023 | The commit needs both edits. |

---

## Parallel Opportunities

| Phase | Parallel tasks | Reason |
| - | - | - |
| 2 | T007, T008 | The two commands read different rules. |
| 6 | T028, T029 | The two commands read different data. |

The repair itself holds no parallel opportunity. One command changes all 94 files at once.

---

## Implementation Strategy

### Minimum viable delivery

Phase 1 through Phase 3 deliver the whole repair. A reviewer can merge that state and still gain the value. The count returns over time without Phase 5, so treat Phase 5 as part of the same pull request.

### Order of risk

The repair carries a low risk, because ruff repairs every result without help and because the change removes comment text only. The two real risks are the wrong command form and a concurrent pull request. Task T006 controls the first risk. Task T029 controls the second risk.
