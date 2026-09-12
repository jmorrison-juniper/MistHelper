# Tasks: Automated Sweep Safety Procedure

**Feature**: `1796-comment-sweep-safety` | **Branch**: `chore/1796-sweep-safety` | **Date**: 2026-08-06

**GitHub Issue**: [#1796](https://github.com/jmorrison-juniper/MistHelper/issues/1796)

**Input**: Design documents from `specs/1796-comment-sweep-safety/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: The specification requests new tests. Part C adds the `--fast` flag tests. Part A adds the tool tests. The existing suite must keep its pass count.

**Branch rule**: Create `chore/1796-sweep-safety` from `main`. Do not branch from another feature branch.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with another task in the same phase. The tasks touch different files.
- **[Story]**: The user story that owns the task. The value is `US1`, `US2`, or `US3`.
- Each task names an exact file path or an exact command.

## Rules that apply to every edit task

1. Use `.venv\Scripts\python.exe` for every Python command. The global interpreter cannot import the project.
2. Add no lint suppression. Non-goal NG-001 forbids a `# noqa` directive and a `# type: ignore` comment. The single `# nosec B404` comment on the `subprocess` import is the one recorded exception, and it needs a stated reason.
3. Every added Python line carries an inline comment that states why the line exists. Principle VI requires it.
4. Every meaningful action logs before the action and after the action. Principle VII requires it.
5. Follow the Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md` for every prose line.
6. Use `pathlib` for every path. Never hardcode a path separator, because the tool runs on Windows and on Linux.
7. Keep every function inside 5 parameters, 5 blocks, and 25 lines. The Five-Item Rule states the caps.

---

## Phase 1: Setup

**Purpose**: Confirm the environment and read the reference case.

- [ ] T001 Create the branch with `git checkout -b chore/1796-sweep-safety main`. Confirm the result with `git branch --show-current`.
- [ ] T002 Confirm that `.venv\Scripts\python.exe -m pytest --version` runs. Every later test command uses this interpreter.
- [ ] T003 Read the reference case. Run `git show --stat 08a75d2` and confirm that the commit reports 53 insertions and 515 deletions in one file. That commit is pull request #1791, which carries both defects and the repair.
- [ ] T004 Read the current state of the declaration. Confirm that `MistHelper.py` line 2382 holds `FAST_MODE_ENABLED: bool = False`. Confirm that line 5101 holds `global FAST_MODE_ENABLED` inside `_setup_runtime_flags`.
- [ ] T005 Record the pre-change gate baseline. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py --config-file pyproject.toml`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Save the unit test pass count, because SC-009 compares against it.

---

## Phase 2: User Story 1, Part A - The symbol table tool (Priority: P1)

**Goal**: Build a tool that reports the module-level names that a change lost and the names that it added.

**Independent Test**: The tool reports the lost name `FAST_MODE_ENABLED` when a reviewer replays the pull request #1791 sweep.

**Warning**: The declaration uses an annotated assignment. Python parses that statement as `ast.AnnAssign`, not as `ast.Assign`. A tool that matches `ast.Assign` alone reports zero lost names on the exact defect it exists to catch. The generator `scripts/generate_menu_wiki.py` already lost months of output to this trap.

- [ ] T006 Create the package directory `tools/symbol_diff/` with an empty `__init__.py`. Requirement FR-020 places the tool next to `tools/ste_linter` and `tools/compliance_analyzer`.
- [ ] T007 [US1] Write the `collect_names` method in `tools/symbol_diff/comparator.py`. The method reads a source string with `ast.parse` and returns the module-level names. Handle `ast.Assign`, `ast.AnnAssign`, `ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.ClassDef`, `ast.Import`, and `ast.ImportFrom`. Requirement FR-005 and FR-018 state this behavior.
- [ ] T008 [US1] Add the syntax error path to `collect_names`. Catch `SyntaxError` and print a message that names the file and the line. Do not raise. Requirement FR-018 and success criterion SC-007 demand a clear message, because defect 2 left a file that does not compile.
- [ ] T009 [US1] Write the `read_revision` method in `tools/symbol_diff/comparator.py`. The method runs `git show <revision>:<path>` and returns the text. Pass a fixed argument list and request no shell. Add a `# nosec B404` comment on the `import subprocess` line in the style of `MistHelper.py` line 47, which names the seam and names the runner.
- [ ] T010 [US1] Write the `compare` method in `tools/symbol_diff/comparator.py`. The method returns the lost names and the added names. Requirement FR-006 demands both directions, because an added name can shadow an import.
- [ ] T011 [US1] Write the `report` method and the `run` method in `tools/symbol_diff/comparator.py`. The `run` method accepts a base revision and a list of paths, per FR-019. The `report` method returns exit code 1 when the delta holds any name and returns 0 when it holds none.
- [ ] T012 [US1] Write the module entry point in `tools/symbol_diff/__init__.py`. Parse `--base` and the path list with `argparse`. Call one method on `SymbolTableComparator`. Add no wrapper function, per the project rule against wrappers.
- [ ] T013 [US1] Prove SC-006. Run `.venv\Scripts\python.exe -m tools.symbol_diff --base 08a75d2~1 MistHelper.py` against a tree that replays the sweep before the repair. Confirm that the output names `FAST_MODE_ENABLED` as a lost name and that the exit code reads 1.
- [ ] T014 [US1] Prove SC-007. Write a temporary file that holds invalid Python. Run the tool against it. Confirm that the tool prints a message that names the file and the line, and that the tool raises no unhandled error. Delete the temporary file.
- [ ] T015 [US1] Write `tests/unit/tools/test_symbol_diff.py`. Cover the annotated assignment case, the plain assignment case, the class case, the import case, the lost name case, the added name case, and the syntax error case. The annotated assignment case is the most important one, because it is the defect from issue #1796.
- [ ] T016 [US1] Verify part A. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r tools/symbol_diff`, and `.venv\Scripts\python.exe -m pytest tests/unit/tools/test_symbol_diff.py --no-cov -q`. Confirm that every check passes.

**Checkpoint**: The tool reports the reference defect. SC-005, SC-006, and SC-007 now hold. Part B can start.

---

## Phase 3: User Story 3, Part B - The written procedure (Priority: P2)

**Goal**: Record the four checks where a contributor finds them.

**Independent Test**: A contributor searches the project instructions for the word "sweep" and finds the procedure.

- [ ] T017 [US3] Add a section named "Automated Sweep Safety" to `.github/copilot-instructions.md`. Requirement FR-001 names that file as the location. Place the section near the "Full Deployment Pipeline" section, because both describe a pre-commit step.
- [ ] T018 [US3] Write the four check rows into the new section. State the compile check per FR-002, the lint check per FR-003, the type check per FR-004, and the symbol table check per FR-005. State the exact command and the expected result for each one. Depends on T017, because both tasks edit the same file.
- [ ] T019 [US3] State the type check scope by reference, not by value. The section must point at the `MYPY_PATHS` value in `.github/workflows/ci.yml` line 59. A repeated value drifts when issue #888 or a later change moves the scope.
- [ ] T020 [US3] Write the three sweep rules into the same section. State that a comment sweep deletes comment lines only, per FR-008. State that the pull request body records the count of other deletions, per FR-009. State that a rebase repeats every check, per FR-010.
- [ ] T021 [US3] Write the title rule into the same section. A sweep pull request title must name the sweep, per FR-011. State that a title such as "delete comments" sets the wrong expectation and that a reviewer then reads a 515-line difference as safe.
- [ ] T022 [US3] Add a one-line pointer in `agents.md` under "Key Conventions". Do not repeat the procedure text. That file already names `.github/copilot-instructions.md` as the canonical source.
- [ ] T023 [US3] Prove SC-010. Search both files for the word "sweep" and confirm that the search finds the procedure and finds the pointer.
- [ ] T024 [US3] Check the new prose against the Simplified Technical English rules. Run `.venv\Scripts\python.exe -m tools.ste_linter .github/copilot-instructions.md` and `.venv\Scripts\python.exe -m tools.ste_linter agents.md`. Each file must score 80 or above.

**Checkpoint**: The procedure exists where a contributor finds it. SC-001, SC-008, and SC-010 now hold. Part C can start.

---

## Phase 4: User Story 2, Part C - The fast flag test (Priority: P1)

**Goal**: Prove that the `--fast` flag sets the module global and that a removal of the declaration fails the suite.

**Independent Test**: A reviewer removes the declaration from `MistHelper.py`. The unit suite fails and the message names the flag.

**Caution**: The test changes a module global. It must restore the earlier value after each run, or a later test reads a changed flag.

- [ ] T025 [US2] Write `tests/unit/test_fast_mode_flag.py`. Add a fixture that saves the current value of `MistHelper.FAST_MODE_ENABLED` and restores it after each test, per FR-016.
- [ ] T026 [US2] Write the positive test. Call `_setup_runtime_flags` with a namespace that holds `fast=True`. Read `MistHelper.FAST_MODE_ENABLED` on the module itself and confirm the value `True`. Requirement FR-012 and FR-015 state this behavior.
- [ ] T027 [US2] Write the negative test. Call `_setup_runtime_flags` with a namespace that holds `fast=False`. Read the module global and confirm the value `False`. Requirement FR-013 states this behavior.
- [ ] T028 [US2] Write the declaration test. Confirm that the `MistHelper` module holds the name `FAST_MODE_ENABLED` at module level and that its type is `bool`. This test fails when a sweep deletes the declaration, per FR-014.
- [ ] T029 [US2] Prove SC-002. Remove the declaration from `MistHelper.py` in the working tree. Run `.venv\Scripts\python.exe -m pytest tests/unit/test_fast_mode_flag.py --no-cov -q` and confirm that a test fails and that the message names the flag. Restore the declaration with `git checkout -- MistHelper.py`. Run `git status` and confirm that the tree holds no leftover change.
- [ ] T030 [US2] Confirm that the new test does not read a test double. Requirement FR-015 forbids it. The two existing references in `tests/unit/serial_cc/test_switch_vc_stats.py` set an attribute on a deps object, and neither one caught the defect. Leave those two references unchanged, per NG-003.
- [ ] T031 [US2] Verify part C. Run `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q` and confirm that the pass count equals the T005 value plus the new tests. Confirm that no earlier test failed after the flag change.

**Checkpoint**: The test covers the `--fast` flag. SC-002, SC-003, and SC-004 now hold.

---

## Phase 5: Polish and Final Validation

**Purpose**: Prove every success criterion and open the pull request. These tasks change no source line.

- [ ] T032 Run the full gate set exactly as CI runs it. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py --config-file pyproject.toml`, `.venv\Scripts\python.exe -m pylint src/`, `.venv\Scripts\python.exe -m radon cc src/ -a -nb`, `.venv\Scripts\python.exe -m vulture src/ --min-confidence 80`, `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r .`, and `.venv\Scripts\python.exe -m pytest --cov=src/ --cov-fail-under=80`. Do not scope a gate to the changed files only.
- [ ] T033 [P] Apply the new procedure to this pull request. Run all four checks on every changed file. State the count of deleted lines that are not comments in the pull request body. The expected value is zero, because this work deletes no line.
- [ ] T034 [P] Confirm that this work added no suppression beyond the recorded one. Run `git diff main...HEAD` and search for an added `# noqa` line and an added `# type: ignore` line. The expected count is zero. The single `# nosec B404` comment from T009 is the one recorded exception, per NG-001.
- [ ] T035 [P] Confirm the Five-Item Rule. Read every method in `tools/symbol_diff/comparator.py` and confirm 5 parameters, 5 blocks, and 25 lines at most. Confirm that the class holds at most 5 public methods.
- [ ] T036 Comment on the four planned sweeps. Run `gh issue comment <number> --body-file <file>` for issues #1792, #1793, #1795, and #886. Name this procedure and name the tool command. Delete the body file after each command returns.
- [ ] T037 Open the pull request against `main` from `chore/1796-sweep-safety`. Write `Closes #1796` in the body. Link `specs/1796-comment-sweep-safety/spec.md`. State the T033 count. Complete the checklist in `.github/PULL_REQUEST_TEMPLATE.md`. Add the `auto-merge` label only after every check passes, including CodeQL.

---

## Dependencies and Execution Order

### Phase order

| Phase | Content | Starts after |
| - | - | - |
| 1 | Setup and the reference case | Nothing |
| 2 | Part A, the symbol table tool | Phase 1 |
| 3 | Part B, the written procedure | Phase 2, because the procedure names the tool command |
| 4 | Part C, the fast flag test | Phase 1. It runs in parallel with Phase 2 and Phase 3. |
| 5 | Polish and final validation | Phase 3 and Phase 4 |

### Why the tool lands before the procedure

The procedure states the exact command for each check. The symbol table command does not exist until Part A lands. A procedure that names a command that nobody can run has no effect.

### Why Part C runs in parallel

The `--fast` flag test reads `MistHelper.py`. It does not read the new tool and it does not read the procedure. A contributor can build it at the same time as Part A.

---

## Parallel Opportunities

| Phase | Parallel tasks | Reason |
| - | - | - |
| 2 and 4 | The whole of Phase 4 runs beside Phase 2 | The two parts touch different files. |
| 5 | T033, T034, T035 | The three checks read different data. |

---

## Implementation Strategy

### Minimum viable delivery

Part C alone delivers real value. The `--fast` flag test catches the exact defect from issue #1796 at every later change, including a hand edit. It takes one small file.

Part A and Part B together deliver the general protection. They catch a lost name that no test covers, which is the wider class of defect.

### Order of risk

The largest risk is a tool that reports a clean result on the defect it exists to catch. The declaration uses an annotated assignment, and a tool that matches `ast.Assign` alone misses it. Task T007 and task T015 control that risk, and task T013 proves the result against the real reference case.
