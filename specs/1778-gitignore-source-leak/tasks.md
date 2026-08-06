# Tasks: Gitignore Source Leak Repair

**Feature**: `1778-gitignore-source-leak` | **Branch**: the implementation needs its own branch | **Date**: 2026-08-05

**GitHub Issue**: [#1778](https://github.com/jmorrison-juniper/MistHelper/issues/1778)

**Input**: Design documents from `specs/1778-gitignore-source-leak/`

**Prerequisites**: [spec.md](spec.md), [plan.md](plan.md)

**Tests**: The specification requests no new test. The existing suite must keep its pass count. Each phase ends with a measurement task, not with a new test file.

**Branch rule**: Create a branch from `main` with the name `fix/1778-gitignore-source-leak`. Do not reuse the documentation branch.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with another task in the same phase. The tasks touch different files.
- **[Story]**: The user story that owns the task. The value is `US1`, `US2`, or `US3`.
- Each task names an exact file path.

## Rules that apply to every task

1. Use `.venv\Scripts\python.exe` for every Python command. The global interpreter cannot import the project.
2. Every changed Python line carries an inline comment that states why the line exists. Principle VI requires this.
3. Every prose line follows the writing guide at `documentation/ASD-STE100_writing-guide.md`.
4. Do not add a `# noqa: S...` annotation. A latent annotation is the defect that this work removes.
5. Run every gate across the whole repository. Do not scope a gate to the changed paths.
6. Keep the ignore change, the security correction, and the format correction in one pull request.

---

## Phase 1: Setup

**Purpose**: Confirm the environment before any measurement.

- [ ] T001 Create the branch with `git checkout -b fix/1778-gitignore-source-leak main`. Confirm the name with `git branch --show-current`.
- [ ] T002 Confirm that `.venv\Scripts\python.exe -m bandit --version` reports `1.9.4` and that `.venv\Scripts\python.exe -m ruff --version` reports `0.16.0`. Install the pinned set with `pip install -r requirements-dev.txt` if a version differs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prove the baseline and close every open decision. No edit starts until this phase closes.

- [ ] T003 Capture the ignore baseline. Run `git check-ignore -v mist-ops-platform/src/shared/config/settings.py` and confirm that it prints `.gitignore:244:config/`. Run `git ls-files mist-ops-platform | Measure-Object` and confirm that it reports 110 files.
- [ ] T004 Capture the bandit baseline. Run `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r . -f json -o "$env:TEMP\bandit_1778.json" -q`. Confirm 43 raw results, 42 under `tools/test_quality_analyzer/fixtures/`, and 1 remaining `B104` MEDIUM at `mist-ops-platform/src/shared/config/settings.py` line 41. Stop and re-derive the plan if a count differs.
- [ ] T005 Find the local directory that the `config/` rule protects. Search the working tree, the `deploy/` directory, and every document under `documentation/`. Record the result in the pull request body. If no directory needs the rule, record that the rule needs deletion instead of narrowing.
- [ ] T006 Read every one of the 20 files under the three matched directories. Search each file for a credential, a token, an API key, and a private key. Record the result. **Warning**: If a file holds a real credential, stop the work. Move the value to the environment and raise a rotation request before any file enters git.
- [ ] T007 Read every deployment file of `mist-ops-platform` and record how each one sets the API host. Cover `deploy/`, `compose.yml`, `Containerfile`, and `Dockerfile`. This task decides whether a change to the `api_host` default breaks a running service.
- [ ] T008 Decide the answer to the bind address question in [plan.md](plan.md). Record the decision and the reason. The plan prefers a default of `127.0.0.1` with an environment override.
- [ ] T009 Decide whether git tracks the 17 TypeScript files under `ops-portal/src/features/config/` and `ops-portal/src/pages/config/`. Record the decision and the reason. Requirement FR-007 demands this record.

**Checkpoint**: Five decisions are closed. The baseline reads 1 bandit result. Phase 3 can start.

---

## Phase 3: User Story 2 - Correct the security result (Priority: P1)

**Goal**: Remove the `B104` result and the latent annotation from `mist-ops-platform/src/shared/config/settings.py` before the file enters git.

**Independent Test**: A run of `.venv\Scripts\python.exe -m ruff check --select S --ignore-noqa mist-ops-platform/src/shared/config/settings.py` reports no `S104` result.

- [ ] T010 [US2] Apply the T008 decision to line 41 of `mist-ops-platform/src/shared/config/settings.py`. Change the `api_host` default, or keep the bind and add a `# nosec B104` comment that states the reason. Add an inline comment that states why the default binds where it binds.
- [ ] T011 [US2] Delete the `# noqa: S104` annotation from line 41 of `mist-ops-platform/src/shared/config/settings.py`. Requirement FR-012 demands this deletion, because the annotation hides the result the moment anybody selects the ruff `S` family.
- [ ] T012 [US2] Record a judgment for the `S105` result at line 27 of `mist-ops-platform/src/shared/config/settings.py`. The value is `vault_token = "dev-root-token"`. Confirm that the value is a local development token and not a production secret. Do not add a `# noqa: S105` annotation. State the judgment in the pull request body.
- [ ] T013 [US2] Verify User Story 2. Run `.venv\Scripts\python.exe -m ruff check --select S --ignore-noqa mist-ops-platform/src/shared/config/settings.py` and confirm that no `S104` result appears. Run `git grep -n "noqa: S104"` and confirm that the search returns nothing.

**Checkpoint**: The security result is closed. Phase 4 can start.

---

## Phase 4: User Story 3 - Correct the formatting (Priority: P2)

**Goal**: Format the three Python files to the root black configuration, so that the formatter gate stays green after the files enter git.

**Independent Test**: A forced black check on the three files reports zero files to rewrite.

**Caution**: Black reads `.gitignore` and skips an ignored file. A normal run reports success and hides the failure. Force the run.

- [ ] T014 [US3] Run black on `mist-ops-platform/src/shared/config/settings.py` and `mist-ops-platform/src/shared/config/constants.py` with the root configuration. Use an explicit path so that black reads the file. The measurement shows that `settings.py` needs a rewrite of the `database_url` default to one line of 120 characters.
- [ ] T015 [US3] Confirm the format. Run a forced black check on the three Python files and confirm zero files to rewrite. Confirm that the change touched only whitespace and line breaks, and that it changed no value.

**Checkpoint**: The formatter is satisfied. Phase 5 can start.

---

## Phase 5: User Story 1 - Narrow the ignore rule (Priority: P1)

**Goal**: Stop the `config/` pattern from matching a source directory, and keep the exclusion that the rule protects.

**Independent Test**: `git check-ignore -v mist-ops-platform/src/shared/config/settings.py` prints no rule and exits with code 1.

**Caution**: Git cannot re-include a file below an excluded directory. Each negation needs two lines. Lines 246 to 249 of `.gitignore` already hold the pattern.

- [ ] T016 [US1] Edit line 244 of `.gitignore`. Apply the T005 decision. Either delete the `config/` pattern, or anchor it to the one directory it protects. Add a comment above the rule that names that directory and states the reason.
- [ ] T017 [US1] Add the negation lines to `.gitignore` for each directory that T009 chose to track. Write the directory line first and the file glob line second, in the style of lines 246 to 249. Add a comment that names the project that owns each directory.
- [ ] T018 [US1] Verify the ignore rule. Run `git check-ignore -v` against `mist-ops-platform/src/shared/config/settings.py`, against `ops-portal/src/features/config/RevisionDiff.tsx`, and against the local directory that T005 named. Confirm that each result matches the recorded decision.
- [ ] T019 [US1] Confirm that git still ignores the compiled files. Run `git check-ignore -v mist-ops-platform/src/shared/config/__pycache__/settings.cpython-313.pyc` and confirm that the rule now reads `.gitignore:80:__pycache__/`.

**Checkpoint**: The ignore rule is correct. Phase 6 can start.

---

## Phase 6: Track the files and run every gate

**Goal**: Add the new files to git and prove that every gate stays green.

**Independent Test**: Every local gate exits with code 0 on a staged working tree.

- [ ] T020 Stage the new files with `git add`. Read `git status --porcelain` line by line. Confirm that no compiled Python file appears and that no local secret appears. Requirement FR-004 demands this reading.
- [ ] T021 Run the bandit gate. Run `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r . -f json -o "$env:TEMP\bandit_1778_after.json" -q`. Confirm that the run reports 42 results and that all 42 sit under `tools/test_quality_analyzer/fixtures/`. Success criterion SC-003 compares against this count.
- [ ] T022 Run the format gate and the lint gate. Run `.venv\Scripts\python.exe -m black --check --diff .` and `.venv\Scripts\python.exe -m ruff check .`. Confirm that each command exits with code 0.
- [ ] T023 Run the type gate and the test suite. Run `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml` and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Confirm no new error and confirm that the pass count matches the count before the change.
- [ ] T024 Confirm the file count. Run `git ls-files mist-ops-platform | Measure-Object` and confirm 113 files or more. Success criterion SC-002 compares against this count.

**Checkpoint**: Every gate is green. Phase 7 can start.

---

## Phase 7: Polish and hand over

**Goal**: Record every decision and state the order against issue #1780.

- [ ] T025 Write the pull request body. Record the five decisions from Phase 2. Name the directory that the narrowed rule protects. State the judgment for the `S105` value at line 27.
- [ ] T026 State the coordination order in the pull request body. Write that this work must merge before issue [#1780](https://github.com/jmorrison-juniper/MistHelper/issues/1780) selects the ruff `S` family. State the consequence of the other order, which is that the latent annotation hides the MEDIUM result for good. Requirement FR-019 demands this statement.
- [ ] T027 Reference issue [#1719](https://github.com/jmorrison-juniper/MistHelper/issues/1719) in the pull request body. That issue removed every other latent annotation of this kind and left this one out of scope, because a person cannot commit an edit to an untracked file.
- [ ] T028 Run the writing gate. Run `.venv\Scripts\python.exe -m tools.ste_linter` against every changed Markdown file and confirm a score of 80 or more.
- [ ] T029 Open the pull request. Write `Closes #1778` in the body. Add the labels `security` and `chore`. Wait for CodeQL to report before adding the `auto-merge` label.

---

## Dependencies

| Task | Depends on | Reason |
| - | - | - |
| T010 | T007, T008 | The bind change needs the deployment survey and the recorded decision. |
| T014 | T010, T011 | Black must format the final content, not an intermediate form. |
| T016 | T005 | The narrowed rule needs the name of the directory it protects. |
| T017 | T009 | The negation lines need the TypeScript decision. |
| T020 | T013, T015, T018 | The files enter git only after every gate risk closes. |
| T024 | T020 | The file count changes only after the stage step. |

## Parallel opportunities

- T005, T006, and T007 read different files. Run them in parallel.
- T021, T022, and T023 read the same working tree and change nothing. Run them in parallel.
