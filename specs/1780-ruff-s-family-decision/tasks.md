# Tasks: Ruff S Family Decision

**Feature**: `1780-ruff-s-family-decision` | **Branch**: the implementation needs its own branch | **Date**: 2026-08-05

**GitHub Issue**: [#1780](https://github.com/jmorrison-juniper/MistHelper/issues/1780)

**Input**: Design documents from `specs/1780-ruff-s-family-decision/`

**Prerequisites**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Tests**: The guard in User Story 3 needs one new test. The existing suite must keep its pass count.

**Branch rule**: Create a branch from `main` with the name `chore/1780-ruff-s-family-decision`. Do not reuse the documentation branch.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with another task in the same phase. The tasks touch different files.
- **[Story]**: The user story that owns the task. The value is `US1`, `US2`, or `US3`.
- Each task names an exact file path.

## Rules that apply to every task

1. Use `.venv\Scripts\python.exe` for every Python command. The global interpreter cannot import the project.
2. Every prose line follows the writing guide at `documentation/ASD-STE100_writing-guide.md`.
3. Never run `ruff --fix` with the `S` family selected. The flag adds a `# noqa` comment for every result, and a reviewer cannot read that diff.
4. Run every gate across the whole repository. Do not scope a gate to the changed paths.
5. Do not add `S` to the select list before issue [#1778](https://github.com/jmorrison-juniper/MistHelper/issues/1778) lands. Requirement FR-013 states the order.

---

## Phase 1: Setup

**Purpose**: Confirm the environment before any measurement.

- [ ] T001 Create the branch with `git checkout -b chore/1780-ruff-s-family-decision main`. Confirm the name with `git branch --show-current`.
- [ ] T002 Confirm that `.venv\Scripts\python.exe -m ruff --version` reports `0.16.0` and that `.venv\Scripts\python.exe -m bandit --version` reports `1.9.4`. Install the pinned set with `pip install -r requirements-dev.txt` if a version differs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm that the recorded measurement still holds. No decision starts until this phase closes.

- [ ] T003 Re-run the ruff measurement. Run `.venv\Scripts\python.exe -m ruff check --select S --statistics .` and confirm 13,566 results with 13,440 under `S101`. Run the same command with `--exclude tests` and confirm 121 results.
- [ ] T004 Re-run the bandit measurement. Run `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r . -f json -o "$env:TEMP\bandit_1780.json" -q`. Confirm 43 raw results, 42 under `tools/test_quality_analyzer/fixtures/`, and 0 results in files that git tracks.
- [ ] T005 Re-run the latent annotation search. Run `git grep -n "noqa: S"` across every tracked file. Confirm zero hits. Then run `.venv\Scripts\python.exe -m ruff check --select S --ignore-noqa --statistics .` and compare the total against T003. A higher total means a latent annotation exists.
- [ ] T006 Read the status of issue #1778 with `gh issue view 1778`. Record whether the latent `# noqa: S104` annotation at `mist-ops-platform/src/shared/config/settings.py` line 41 still exists. Requirement FR-013 needs this record.
- [ ] T007 Compare every count from T003 to T006 against [research.md](research.md). If a count differs, record the drift in [research.md](research.md) and read the recommendation again before Phase 3.

**Checkpoint**: The measurement holds. Phase 3 can start.

---

## Phase 3: User Story 1 - Record the decision (Priority: P1)

**Goal**: Choose one option and write a record that a new maintainer can read without a conversation.

**Independent Test**: A reviewer opens the decision record and finds the option, the reason, the date, and a link to the data.

- [ ] T008 [US1] Read [research.md](research.md) section R10, which states the cost of each option. Read the two counter arguments in [plan.md](plan.md). Choose one of the three options.
- [ ] T009 [US1] Create `specs/1780-ruff-s-family-decision/decision.md`. State the chosen option, the date, and the tool versions. Requirements FR-001 and FR-004 demand these fields.
- [ ] T010 [US1] Add the reason to `specs/1780-ruff-s-family-decision/decision.md`. Link to [research.md](research.md) and name the sections that support the reason. Requirements FR-002 and FR-003 demand these links.
- [ ] T011 [US1] Add the rule ownership statement to `specs/1780-ruff-s-family-decision/decision.md`. Name the tool that owns each security rule, or state that the two tools overlap and name the overlap. Requirement FR-006 demands this statement.
- [ ] T012 [US1] Add the review trigger to `specs/1780-ruff-s-family-decision/decision.md`. State what evidence would change the decision later. Name the four bandit rules that ruff does not implement, which are `B613`, `B614`, `B615`, and `B703`. Requirement FR-005 demands this statement.
- [ ] T013 [US1] Add the written answer to each counter argument in [plan.md](plan.md). Cover the 10 results that ruff finds and bandit misses. Cover the inline editor argument. Requirement FR-018 demands a written statement of what the choice gives up.

**Checkpoint**: The decision record is complete. Phase 4 can start.

---

## Phase 4: User Story 2 - Update the suppression contract (Priority: P1)

**Goal**: State which comment form works, so that a developer writes one comment and not two.

**Independent Test**: A reviewer reads `specs/1032-bandit-severity-gate/contracts/suppression-comment.md` and finds a statement about the ruff `S` family.

- [ ] T014 [US2] Read `specs/1032-bandit-severity-gate/contracts/suppression-comment.md` and record what it states about the `S` family today.
- [ ] T015 [US2] Add the comment form statement to `specs/1032-bandit-severity-gate/contracts/suppression-comment.md`. State that bandit reads `# nosec` and that ruff reads `# noqa`. State that the two forms never overlap. Requirement FR-007 demands this statement.
- [ ] T016 [US2] Add the latent annotation warning to `specs/1032-bandit-severity-gate/contracts/suppression-comment.md`. State that a `# noqa: S...` annotation hides nothing today and starts to hide a result the moment somebody selects the `S` family. Link to [research.md](research.md) section R9, which holds the proof. Requirements FR-008 and FR-009 demand this warning.
- [ ] T017 [US2] Add a link from `specs/1032-bandit-severity-gate/contracts/suppression-comment.md` to `specs/1780-ruff-s-family-decision/decision.md`, so that a reader finds the reason behind the rule.

**Checkpoint**: The contract is correct. Phase 5 can start.

---

## Phase 5: User Story 3 - Add the guard (Priority: P2, Option 2 only)

**Goal**: Stop a new latent annotation from reaching `main`.

**Independent Test**: A reviewer adds a `# noqa: S101` annotation to a tracked file and confirms that the test fails and names the file and the line.

**Skip condition**: If the team chooses Option 1 or Option 3, skip this phase. A selected `S` family makes every annotation active, so no latent annotation can exist.

- [ ] T018 [US3] Create `tests/guardrails/test_no_latent_noqa_s.py`. Read the tracked Python file list with `git ls-files "*.py"`. Search each file for a `# noqa` comment that names an `S` code. Follow the existing guard test style in `tests/guardrails/`.
- [ ] T019 [US3] Make the test report the file path and the line number for each hit. Requirement FR-011 demands both fields. Add an inline comment to every line of the test, per Principle VI.
- [ ] T020 [US3] Run the test with `.venv\Scripts\python.exe -m pytest tests/guardrails/test_no_latent_noqa_s.py -q`. Confirm zero hits against the current code base. Requirement FR-012 demands this result.
- [ ] T021 [US3] Prove that the test works. Add a `# noqa: S101` annotation to one tracked file, run the test, and confirm that it fails and names that file and that line. Remove the annotation afterward.

**Checkpoint**: The guard holds. Phase 6 can start.

---

## Phase 6: Apply the choice (Option 1 and Option 3 only)

**Goal**: Change the configuration when the team overrides the recommendation.

**Skip condition**: If the team chooses Option 2, skip this phase. Option 2 changes no configuration.

**Warning**: A change to the select list activates every latent annotation. Run task T022 first, or a hidden security result stays hidden for good.

- [ ] T022 Triage every hidden result. Run `.venv\Scripts\python.exe -m ruff check --select S --ignore-noqa .` and compare the output against a run without the flag. Record a decision for each result that only the first run reports. Requirement FR-015 demands this triage.
- [ ] T023 Add the test tree ignore rule to `pyproject.toml`. Add `S101` to the `tests/**` entry in `[tool.ruff.lint.per-file-ignores]`. The measurement shows 13,440 results without this rule. Add a comment that states the count and the reason.
- [ ] T024 Add `S` to the `select` list in `[tool.ruff.lint]` of `pyproject.toml`. Add a comment that links to `specs/1780-ruff-s-family-decision/decision.md`.
- [ ] T025 Add the second annotation to each of the 62 lines that already hold a `# nosec` comment. [research.md](research.md) section R3 holds the count. Write the ruff annotation first and the bandit comment second, so that both tools read their own form.
- [ ] T026 Triage the 10 production results in [research.md](research.md) section R4. Two of them are default passwords in `src/db/__init__.py` lines 45 and 48. **Warning**: If a value is a real credential, move it to the environment and raise a rotation request. Do not add a suppression comment for a real secret.
- [ ] T027 Under Option 3 only, delete the bandit job from `.github/workflows/ci.yml`. Delete the `[tool.bandit]` table from `pyproject.toml`. Remove `bandit` from `requirements-dev.txt`. Remove the bandit entry from `.pre-commit-config.yaml`.
- [ ] T028 Under Option 3 only, remove every one of the 117 `# nosec` comments across the 51 files that hold one. A comment for a tool that no longer runs is dead text.
- [ ] T029 Under Option 3 only, record what the repository gives up. Name `src/maps`, `mist-ops-platform`, and `web_portal`, which hold 111 Python files that ruff excludes. Name the four bandit rules with no ruff equivalent. Success criterion SC-010 demands this record.

**Checkpoint**: The configuration matches the decision. Phase 7 can start.

---

## Phase 7: Verify and hand over

**Goal**: Prove that every gate stays green and close the loop with the neighboring issues.

- [ ] T030 Run the lint gate and the format gate. Run `.venv\Scripts\python.exe -m ruff check .` and `.venv\Scripts\python.exe -m black --check --diff .`. Confirm that each command exits with code 0.
- [ ] T031 Run the security gate. Run `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r . -q` under Option 1 and Option 2 and confirm the count from T004. Skip this task under Option 3, because the gate no longer exists.
- [ ] T032 Run the test suite. Run `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q` and confirm that the pass count matches the count before the change. Success criterion SC-006 compares against it.
- [ ] T033 Open a separate issue for the 10 production results in [research.md](research.md) section R4. Name the two default passwords in `src/db/__init__.py`. Add the labels `security` and `chore`. Non-goal NG-001 keeps that work outside this scope.
- [ ] T034 Write the pull request body. State the chosen option and link to `specs/1780-ruff-s-family-decision/decision.md`. State the ordering against issue #1778. Reference issue [#1719](https://github.com/jmorrison-juniper/MistHelper/issues/1719), which raised the question. Requirement FR-014 demands both references.
- [ ] T035 Run the writing gate. Run `.venv\Scripts\python.exe -m tools.ste_linter` against every changed Markdown file and confirm a score of 80 or more.
- [ ] T036 Open the pull request. Write `Closes #1780` in the body. Add the labels `chore` and `docs`. Wait for CodeQL to report before adding the `auto-merge` label.

---

## Dependencies

| Task | Depends on | Reason |
| - | - | - |
| T008 | T007 | The choice needs a measurement that still holds. |
| T009 to T013 | T008 | The record needs the chosen option. |
| T015 to T017 | T008 | The contract text depends on the chosen option. |
| T018 | T008 | The guard exists only under Option 2. |
| T022 | T006 | The triage needs the status of issue #1778. |
| T024 | T022, T023 | The select list changes only after the triage and the ignore rule. |
| T034 | T009 | The pull request body links to the decision record. |

## Parallel opportunities

- T003, T004, and T005 read the same working tree and change nothing. Run them in parallel.
- T009 to T013 write one file in sequence. Do not run them in parallel.
- T030, T031, and T032 read the same working tree and change nothing. Run them in parallel.
