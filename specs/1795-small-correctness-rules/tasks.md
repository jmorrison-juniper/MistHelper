# Tasks: Small Correctness Rule Cleanup

**Feature**: `1795-small-correctness-rules` | **Branch**: `lint/1795-small-correctness` | **Date**: 2026-08-06

**GitHub Issue**: [#1795](https://github.com/jmorrison-juniper/MistHelper/issues/1795)

**Input**: Design documents from `specs/1795-small-correctness-rules/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md). Issue [#1792](https://github.com/jmorrison-juniper/MistHelper/issues/1792) must land before the `DTZ005` family starts.

**Tests**: The specification requests no new test. The existing suite must keep its pass count for each family.

**Branch rule**: Create one branch for each family from `main`. Name the branch `lint/1795-<rule>`. Do not branch from another family branch.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with another task in the same phase. The tasks touch different files.
- **[Story]**: The user story that owns the task. The value is `US1`, `US2`, or `US3`.
- Each task names an exact file path, an exact rule, or an exact command.

## Rules that apply to every edit task

1. Use `.venv\Scripts\python.exe` for every Python command. The global interpreter cannot import the project.
2. Add no lint suppression. Non-goal NG-001 forbids a `# noqa` directive and a new entry in the ruff `ignore` list or the pylint `disable` list.
3. Do not use `--unsafe-fixes`. Ruff marks 16 repairs unsafe because they can change behavior.
4. Every changed Python line carries an inline comment that states why the line exists. Principle VI requires it.
5. Follow the Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md` for every prose line.
6. Land one family in one pull request. Requirement FR-011 states this rule.
7. Keep every line inside 120 characters. An `encoding` argument and a `ClassVar` annotation both make a line longer.

---

## Phase 1: Setup

**Purpose**: Confirm the environment before any measurement.

- [ ] T001 Confirm the tool versions with `.venv\Scripts\python.exe -m ruff --version` and `.venv\Scripts\python.exe -m pylint --version`. The expected values are `ruff 0.16.0` and `pylint 4.0.6`.
- [ ] T002 Confirm that `.venv\Scripts\python.exe -m pytest --version` runs. Every later test command uses this interpreter.
- [ ] T003 Record the pre-change gate baseline. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Save the unit test pass count, because SC-008 compares against it.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prove the baseline for all six families. No edit starts until this phase closes.

- [ ] T004 Record the ruff baseline. Run `.venv\Scripts\python.exe -m ruff check . --select DTZ005,ISC004,C408,RUF012,SIM103 --statistics`. The expected values are `RUF012` 60, `DTZ005` 56, `ISC004` 13, `SIM103` 9, and `C408` 3. Write each value into [plan.md](plan.md).
- [ ] T005 Record the pylint baseline. Run `.venv\Scripts\python.exe -m pylint MistHelper.py src --disable=all --enable=W1514 --score=n`. The expected count is 5. Write the value and the 5 file paths into [plan.md](plan.md).
- [ ] T006 Record the `DTZ005` hidden site. Run `.venv\Scripts\python.exe -m ruff check . --select DTZ005 --ignore-noqa --statistics`. The expected value is 57. The one-site difference names the directive that issue #1792 removes.
- [ ] T007 Record the site list for each family. Run `.venv\Scripts\python.exe -m ruff check . --select DTZ005,ISC004,C408,RUF012,SIM103 --output-format concise` and save the output. Every later task reads this list.

**Checkpoint**: The six baselines exist. Family 1 can start.

---

## Phase 3: User Story 1, Family 1 - W1514, the cross-platform defect (Priority: P1)

**Goal**: Add an explicit encoding to all 5 `open()` calls. This family carries the only real defect in the feature.

**Independent Test**: `pylint MistHelper.py src --disable=all --enable=W1514` reports zero results.

**Warning**: A file that MistHelper writes on Windows under `cp1252` does not read back the same on Linux under `utf-8`. Any character above code point 127 changes or raises a decode error.

- [ ] T008 [US1] Read each of the 5 sites and confirm the file mode. The sites are `MistHelper.py` line 777, `MistHelper.py` line 1154, `src/config/config_utils.py` line 84, `src/utils/rate_limiting.py` line 134, and `src/utils/rate_limiting.py` line 163. A binary mode takes no encoding argument, so record any binary site and remove it from the scope.
- [ ] T009 [US1] Read the pylint job scope in `.github/workflows/ci.yml`. Confirm that the job reads every file that holds a site. Pull request #1788 changed that scope. Record the result in [plan.md](plan.md). Requirement FR-016 demands this check.
- [ ] T010 [US1] Add `encoding="utf-8"` to each text-mode site. Requirement FR-002 forbids the platform default and forbids another encoding. Add an inline comment on each changed line that states the cross-platform reason.
- [ ] T011 [US1] Search the whole tree for a remaining `open()` call in text mode with no encoding argument. Requirement FR-001 and success criterion SC-003 demand zero matches. Include the paths that ruff excludes, because a defect there still reaches an operator.
- [ ] T012 [US1] Prove SC-009. Write a file that holds a character above code point 127 through `src/utils/rate_limiting.py` on Windows. Read that file inside a Linux container. Confirm that the two contents match.
- [ ] T013 [US1] Verify family 1. Run `.venv\Scripts\python.exe -m pylint MistHelper.py src --disable=all --enable=W1514 --score=n` and confirm zero results. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Confirm that the pass count matches T003.
- [ ] T014 [US1] Open the family 1 pull request. Write `Refs #1795` and not `Closes #1795`, because five families remain. Record the T009 result and the T012 proof in the body.

**Checkpoint**: The `W1514` count reads zero. SC-002 and SC-003 now hold. Family 2 can start.

---

## Phase 4: User Story 3, Families 2 to 4 - The mechanical repairs (Priority: P2)

**Goal**: Clear 25 sites across three small families.

**Independent Test**: `C408`, `SIM103`, and `ISC004` each report zero results.

- [ ] T015 [P] [US3] Clear family 2, which is `C408`. Replace each `dict()` call with a `{}` literal. The 3 sites sit at 2 lines in `MistHelper.py` and 1 line in `tests/unit/troubleshooting/test_marvis_troubleshoot_utils_extended.py`. Verify with `.venv\Scripts\python.exe -m ruff check . --select C408` and open the pull request.
- [ ] T016 [P] [US3] Clear family 3, which is `SIM103`. Replace each `if` and `else` pair with a direct return of the condition. The 9 sites sit in `src/api/api_data_fetcher.py`, `src/audit/filter.py`, `src/cache/cache_utils.py`, `src/websocket/service_ping_manager.py`, `tests/unit/org/test_org_synthetic_probes_manager.py`, `tools/codemod_logging_lazy.py`, `tools/compliance_analyzer/analyzers.py`, `tools/ste_linter/parsing/markdown.py`, and `tools/test_quality_analyzer/discovery.py`.
- [ ] T017 [US3] Confirm the return type at each `SIM103` site. Requirement FR-005 demands a boolean return. Wrap the condition in `bool(...)` where the condition returns a truthy value instead of a boolean. Depends on T016, because both tasks read the same sites.
- [ ] T018 [US3] Read each `ISC004` site before any edit. The 13 sites sit in `tools/refactor_analyzer/reporting.py` with 8, in `MistHelper.py` with 4, and in `src/websocket/diagnostics/arp_executor.py` with 1. Confirm at each site that the author joined two string parts on purpose and did not drop a comma. Requirement FR-004 demands this read.
- [ ] T019 [US3] Clear family 4, which is `ISC004`. Join each deliberate concatenation into one string. Add the missing comma at any site that the T018 read found. Record the count of missing commas, because SC-005 reads that count.
- [ ] T020 [US3] Verify families 2 to 4. Run `.venv\Scripts\python.exe -m ruff check . --select C408,SIM103,ISC004 --statistics` and confirm zero results. Run the full gate set and confirm that the unit suite keeps the T003 pass count.

**Checkpoint**: Three families read zero. Family 5 can start.

---

## Phase 5: User Story 3, Family 5 - RUF012, the class constants (Priority: P2)

**Goal**: Add a `typing.ClassVar` annotation to all 60 sites across 32 files.

**Independent Test**: `ruff check . --select RUF012` reports zero results and the mypy gate stays green.

**Warning**: A wrong annotation changes the inferred type for every reader of that attribute. The mypy gate then fails in a file that this work never touched.

- [ ] T021 [US3] Split the 60 sites into two or three groups of at most 25 sites. Record the group boundary in [plan.md](plan.md). The largest file is `src/analytics/site_analytics_configurator.py` with 6 sites.
- [ ] T022 [US3] Confirm that each site holds a class constant and not instance state. Read each attribute and each writer of that attribute. A site that the code writes at run time needs a different repair and moves out of scope.
- [ ] T023 [US3] Add the `ClassVar` annotation to each site in the first group. Add the `from typing import ClassVar` import where the module does not hold it. Run `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml` after each file, per FR-006.
- [ ] T024 [US3] Repeat T023 for each remaining group. Open one pull request for each group. Skip `src/firmware/firmware_manager.py`, `src/reports/e911_bssid.py`, and `src/site/bulk_radius_wlan_config_manager.py` in a group that runs at the same time as the `DTZ005` family, per FR-013.
- [ ] T025 [US3] Verify family 5. Run `.venv\Scripts\python.exe -m ruff check . --select RUF012 --statistics` and confirm zero results. Run `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml` and confirm zero errors. Run the full gate set.

**Checkpoint**: The `RUF012` count reads zero. Family 6 can start.

---

## Phase 6: User Story 2, Family 6 - DTZ005, the naive datetime values (Priority: P1)

**Goal**: Convert all 57 sites and prove that the printed output stayed byte identical at each one.

**Independent Test**: `ruff check . --select DTZ005 --ignore-noqa` reports zero results. Each site holds a written proof.

**Warning**: This family changes behavior. An aware value can print a time zone offset, which changes a log line and can change a filename. A naive value and an aware value raise `TypeError` when they compare.

- [ ] T026 [US2] Confirm that issue #1792 landed. Run `.venv\Scripts\python.exe -m ruff check . --select DTZ005 --statistics` and the same command with `--ignore-noqa`. Both values must read 57. Stop if the default value reads 56, because the directive still hides one site. Requirement FR-012 states this stop condition.
- [ ] T027 [US2] Read pull request #1791 and record the proof method that its author used for 4 sites. This family repeats that method 57 times.
- [ ] T028 [US2] Split the 57 sites into two groups of at most 30 sites. Record the group boundary in [plan.md](plan.md). The largest files are `src/firmware/bulk_switch_upgrader.py` and `src/firmware/firmware_manager.py` with 5 sites each.
- [ ] T029 [US2] Capture the printed output for each site before the change. Run the operation that reaches the site and save the output. This capture is the reference for the proof.
- [ ] T030 [US2] Convert each site in the first group. Pass the time zone to the `datetime.now()` call. Add an inline comment on each changed line that states why the value needs a time zone.
- [ ] T031 [US2] Read every comparison that reads a converted value. Requirement FR-008 forbids a comparison between a naive value and an aware value. Convert both sides or neither. Depends on T030, because the comparison sites read the changed values.
- [ ] T032 [US2] Capture the printed output for each converted site again. Compare the capture against the T029 reference. The two must match byte for byte. Requirement FR-007 and success criterion SC-004 demand this proof. Check the filename as well as the log text, because a printed offset can reach a filename.
- [ ] T033 [US2] Repeat T029 through T032 for the second group. Open one pull request for each group and record the proof for each site in the body.
- [ ] T034 [US2] Verify family 6. Run `.venv\Scripts\python.exe -m ruff check . --select DTZ005 --ignore-noqa --statistics` and confirm zero results. Run the full gate set and confirm that the unit suite keeps the T003 pass count.

**Checkpoint**: Every family reads zero. SC-001 and SC-004 now hold. Phase 7 can start.

---

## Phase 7: User Story 3 - Close the gate (Priority: P2)

**Goal**: Add the five ruff rules to the `select` list. This is the final change of the feature.

**Independent Test**: A reviewer adds one site in any family. The lint gate fails and names the rule.

**Warning**: Run this phase only after Phase 6 reports zero results. The gate fails on every push while any site remains.

- [ ] T035 [US3] Change line 164 of `pyproject.toml` from `select = ["E", "F", "W", "I", "UP", "B", "G"]` to `select = ["E", "F", "W", "I", "UP", "B", "G", "C408", "DTZ005", "ISC004", "RUF012", "SIM103"]`. Add no other rule, per FR-017. Add no whole family, per NG-004.
- [ ] T036 [US3] Add a comment above the `select` list in `pyproject.toml`. State that `DTZ005` protects a comparison and that `RUF012` protects a class constant. Keep the comment inside 120 characters. Depends on T035, because both tasks edit the same file.
- [ ] T037 [US3] Verify the gate. Run `.venv\Scripts\python.exe -m ruff check .` and confirm that it passes with the new list.
- [ ] T038 [US3] Prove the negative case for SC-007. Add one temporary naive `datetime.now()` call to a tracked file under `src/`. Run `.venv\Scripts\python.exe -m ruff check .` and confirm that it reports `DTZ005` and exits with code 1. Repeat with one temporary `dict()` call for `C408`. Remove both lines. Run `git status` and confirm that the tree holds no leftover change.

**Checkpoint**: The gate reports every family. SC-006 and SC-007 now hold.

---

## Phase 8: Polish and Final Validation

**Purpose**: Prove every success criterion and close the issue. These tasks change no source line.

- [ ] T039 Run the full gate set exactly as CI runs it. Run `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`, `.venv\Scripts\python.exe -m pylint src/`, `.venv\Scripts\python.exe -m radon cc src/ -a -nb`, `.venv\Scripts\python.exe -m vulture src/ --min-confidence 80`, `.venv\Scripts\python.exe -m bandit -c pyproject.toml -r .`, and `.venv\Scripts\python.exe -m pytest --cov=src/ --cov-fail-under=80`. Do not scope a gate to the changed files only.
- [ ] T040 [P] Prove SC-005. Read the T019 record and state the count of `ISC004` sites that held a missing comma. A value above zero names a real defect that this work repaired.
- [ ] T041 [P] Prove SC-004. Count the `DTZ005` sites with a written proof and confirm that the count reads 57.
- [ ] T042 [P] Confirm that this work added no suppression. Run `git log -p main..HEAD` across every family branch and search for an added `# noqa` line and for a new entry in the ruff `ignore` list. The expected count is zero, per NG-001.
- [ ] T043 Open the final pull request for the gate change. Write `Closes #1795` in the body. Link `specs/1795-small-correctness-rules/spec.md`. List every family pull request number. State the correction that this specification records, because the issue names five families and this work covers six. Complete the checklist in `.github/PULL_REQUEST_TEMPLATE.md`. Add the `auto-merge` label only after every check passes, including CodeQL.

---

## Dependencies and Execution Order

### Phase order

| Phase | Content | Starts after |
| - | - | - |
| 1 | Setup | Nothing |
| 2 | Foundational baseline | Phase 1 |
| 3 | Family 1, `W1514` | Phase 2 records all six counts |
| 4 | Families 2 to 4, the mechanical repairs | Phase 3 |
| 5 | Family 5, `RUF012` | Phase 4 |
| 6 | Family 6, `DTZ005` | Phase 5 and issue #1792 lands |
| 7 | The gate change | Phase 6 reports zero results |
| 8 | Polish and final validation | Phase 7 |

### Why the order runs from the defect to the behavior change

Family 1 names a real defect that changes file content between two platforms. It lands first, because it delivers value on its own.

Family 6 changes behavior at every site. It lands last, because a mistake there reaches every operator and because it depends on issue #1792.

### Same-file sequencing

| File | Earlier family | Later family |
| - | - | - |
| MistHelper.py | 1 (`W1514`) | 2 (`C408`) and 4 (`ISC004`) |
| src/cache/cache_utils.py | 3 (`SIM103`) | 5 (`RUF012`) |
| src/firmware/firmware_manager.py | 5 (`RUF012`) | 6 (`DTZ005`) |
| src/reports/e911_bssid.py | 5 (`RUF012`) | 6 (`DTZ005`) |
| src/site/bulk_radius_wlan_config_manager.py | 5 (`RUF012`) | 6 (`DTZ005`) |

---

## Parallel Opportunities

| Phase | Parallel tasks | Reason |
| - | - | - |
| 4 | T015, T016 | The two families share no file. |
| 8 | T040, T041, T042 | The three checks read different data. |

The `RUF012` family and the `DTZ005` family hold no parallel opportunity, because they share three files.

---

## Implementation Strategy

### Minimum viable delivery

Family 1 alone delivers real value. Five sites carry a cross-platform defect, and the repair takes one small pull request. A team with time for one family should pick that one.

### Order of risk

The largest risk is a silent output change from family 6. An aware datetime value prints a time zone offset, and that offset can reach a log line or a filename. Task T032 is the control, and it runs at every one of the 57 sites.
