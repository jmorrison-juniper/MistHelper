# Tasks: Bandit Severity Gate Hardening

**Feature**: `1032-bandit-severity-gate` | **Branch**: `security/889-bandit-ll` | **Date**: 2026-07-28

**GitHub Issue**: [#889](https://github.com/jmorrison-juniper/MistHelper/issues/889)

**Input**: Design documents from `specs/1032-bandit-severity-gate/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md), [contracts/suppression-comment.md](contracts/suppression-comment.md)

**Tests**: The specification requests no new test. The existing suite must keep its pass count. Each group therefore ends with a measurement task and a gate task, not with a new test file.

**Branch rule**: Stay on `security/889-bandit-ll`. Do not create a branch. Do not switch a branch.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with another task in the same phase. The tasks touch different files.
- **[Story]**: The user story that owns the task. The value is `US1`, `US2`, or `US3`.
- Each task names an exact file path.
- Each task names the ledger row numbers from [data-model.md](data-model.md) section 3.

## Rules that apply to every edit task

1. Locate each finding by the **anchor text** in the ledger, not by the baseline line number. Group D2 shifts every later line in two files.
2. Every changed Python line carries an inline comment that states why the line exists. Principle VI requires this.
3. Every meaningful action logs before the action and logs after the action. Principle VII requires this. `src/utils/logger_utils.py` is the single recorded deviation.
4. Every added `# nosec` comment follows [contracts/suppression-comment.md](contracts/suppression-comment.md). The form is `# nosec RULE - reason.` with an ASCII hyphen.
5. Every comment and every prose line follows the Simplified Technical English guide at `documentation/ASD-STE100_writing-guide.md`.
6. Leave every existing `# noqa: S...` annotation in place. Research decision R4 proves that the annotation suppresses nothing. Removal is a separate cleanup.
7. Keep a line inside 120 characters at the repository root and inside 99 characters under `mist-ops-platform/`.

---

## Phase 1: Setup

**Purpose**: Confirm the environment before any measurement.

- [ ] T001 Confirm the branch with `git branch --show-current` and verify that it returns `security/889-bandit-ll`. Stop if it returns another value.
- [ ] T002 Activate the virtual environment with `.venv\Scripts\Activate.ps1` and confirm `bandit --version` reports `1.9.4`. Install it with `pip install "bandit[toml]"` if the venv does not hold it.
- [ ] T003 Confirm that `.venv\Scripts\python.exe -m pytest --version` runs. The global Python cannot import the project, so every test command uses this interpreter.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prove the baseline and remove the two coordination risks. No edit starts until this phase closes.

- [ ] T004 Write the reusable filter script to `$env:TEMP\bandit_1032_filter.ps1`. The script reads the bandit JSON report, normalizes each `filename` to a forward slash, drops a path that `git ls-files` does not list, and drops a path that starts with `tools/test_quality_analyzer/fixtures/`. Keep the script outside the repository so that SC-009 stays true.
- [ ] T005 Capture the baseline snapshot. Run `bandit -c pyproject.toml -r . -f json -o "$env:TEMP\bandit_1032.json" -q`, then run the T004 filter. Record the raw count, the tracked count, and the in-scope count in `specs/1032-bandit-severity-gate/data-model.md` section 1.5.
- [ ] T006 Verify the baseline against [quickstart.md](quickstart.md) step 2.3. The in-scope total must read 54. The per-rule counts must read B101 18, B105 11, B107 1, B110 7, B404 4, B603 9, B606 1, and B607 3. Stop and re-derive the ledger in `specs/1032-bandit-severity-gate/data-model.md` if any count differs.
- [ ] T007 Read the current scope of issue [#1709](https://github.com/jmorrison-juniper/MistHelper/issues/1709) with `gh issue view 1709`. Confirm that the issue targets `MistHelper.py` only and that it names none of the 7 B110 line numbers in ledger rows 27 to 33. Requirement FR-016 demands this check.
- [ ] T008 Record the pre-change gate baseline. Run `ruff check .`, `black --check --diff .`, `mypy src/ --config-file pyproject.toml`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Save the unit test pass count, because SC-007 compares against it.

**Checkpoint**: The baseline reads 54 findings. Issue #1709 holds no line-level overlap. Group A can start.

---

## Phase 3: User Story 1, Group A - The subprocess family (Priority: P1)

**Goal**: Clear all 17 findings for rules B404, B603, B606, and B607. This group is the most mechanical, and 13 of its 17 findings sit outside `src/`.

**Independent Test**: A fresh scan reports 0 for B404, 0 for B603, 0 for B606, and 0 for B607. Every other rule count holds its baseline value.

**Rows covered**: 1 to 14 from [data-model.md](data-model.md) section 3.

- [ ] T009 [P] [US1] Resolve the `uv` executable in `starlink_dashboard.py` for ledger rows 7 and 11. Call `shutil.which("uv")` before each call, log the lookup before it runs, log the resolved path after it returns, and pass the resolved path to `subprocess.run`. Add one combined `# nosec B603 B607 - ...` comment on each of the two statements, near the `["uv", "--version"]` anchor and the PyQt6 install anchor.
- [ ] T010 [US1] Add the remaining Group A comments to `starlink_dashboard.py` for ledger rows 3, 8, 9, 10, 12, and 14. Add `# nosec B404` on `import subprocess`, `# nosec B603` on the four `sys.executable` calls and on the `["uv", "pip", "install"] + packages` call, and `# nosec B606` on the `os.execv(sys.executable, ...)` call. Each reason names the source of every argument. Depends on T009, because both tasks edit the same file.
- [ ] T011 [P] [US1] Clear ledger rows 4 and 13 in `tools/compliance_analyzer/engine.py`. Add `# nosec B404` on `import subprocess`. Resolve `git` with `shutil.which("git")`, log before and after the lookup, pass the resolved path, and add one combined `# nosec B603 B607 - ...` comment on the `["git", "check-ignore", "--stdin"]` statement.
- [ ] T012 [P] [US1] Clear ledger rows 1 and 5 in `src/site/address_audit/ui_geocoder.py`. Add `# nosec B404` on `import subprocess` in the style of `MistHelper.py` line 47, which names the seam and the runner. Add `# nosec B603` on the `proc = subprocess.Popen(` statement and state the source of each argument.
- [ ] T013 [P] [US1] Clear ledger rows 2 and 6 in `src/utils/zscaler_probe.py`. Add `# nosec B404` on `import subprocess`. Add `# nosec B603` on the `completed = subprocess.run(` statement. Keep the existing inert `# noqa: S603` annotation on that line, per research decision R4.
- [ ] T014 [US1] Verify Group A. Re-run T005 and the T004 filter. Confirm that B404, B603, B606, and B607 each read 0 and that B101 reads 18, B105 reads 11, B107 reads 1, and B110 reads 7. Run `ruff check .` and `black --check --diff .`. Start `starlink_dashboard.py` and confirm that `tools/compliance_analyzer/engine.py` still reads the git ignore list. Append one evidence line for each SUPPRESS row to the ledger in `specs/1032-bandit-severity-gate/data-model.md`.

**Checkpoint**: The in-scope total reads 37. Group B can start.

---

## Phase 4: User Story 1, Group B - The credential-string family (Priority: P1)

**Goal**: Clear all 12 findings for rules B105 and B107. Every value must first prove that it is not a secret.

**Independent Test**: A fresh scan reports 0 for B105 and 0 for B107. No value moved to the environment, because no value is a credential.

**Rows covered**: 15 to 26.

**Warning**: T015 is a stop condition. If any value is a real credential, stop the group. Move the value to the environment and raise a rotation request. A suppression comment must never cover a real secret. Requirement FR-014 states this rule.

- [ ] T015 [US1] Prove that no Group B value is a credential. Read each value at ledger rows 15 to 26 and record its category in `specs/1032-bandit-severity-gate/data-model.md`. The expected categories are a Vault path prefix, an error-message fragment, a typed confirmation word, a prompt sentinel, an attribute name, a CSS alpha value, and a null-byte delimiter. Also search every caller of `EmailAdapter.__init__` in `mist-ops-platform/src/` and confirm that no caller passes a literal credential, per research decision R8.
- [ ] T016 [P] [US1] Clear ledger row 16 in `src/db/redis_writer.py`. Add `# nosec B105 - ...` on the `ALREADY_EXISTS_TOKEN` constant and state that the value is an error-message fragment used for matching.
- [ ] T017 [P] [US1] Clear ledger rows 17 and 18 in `src/gateway/wan_probe_device_override_manager.py`. Add `# nosec B105 - ...` on `APPLY_CONFIRM_TOKEN` and on `CANCEL_TOKEN`. State that one value is the typed confirmation word and that the other is the prompt cancel keyword.
- [ ] T018 [P] [US1] Clear ledger row 19 in `src/maps/_flask_viewer.py`. Add `# nosec B105 - ...` on `_TOKEN_ATTR` and state that the value is an attribute name, not a token value.
- [ ] T019 [P] [US1] Clear ledger rows 20, 21, and 22 in `src/maps/plotly_map_figure_builder.py`. Add `# nosec B105 - ...` on `_FILL_ALPHA_TOKEN`, on `_BORDER_ALPHA_TOKEN`, and on `_LABEL_BG_ALPHA_TOKEN`. State that each value is a CSS alpha string.
- [ ] T020 [P] [US1] Clear ledger rows 23 and 24 in `src/wan_vpn_builder.py`. Add `# nosec B105 - ...` on `CANCEL_TOKEN` and on `CONFIRM_TOKEN`. State that one value is the prompt sentinel and that the other is the typed confirmation word.
- [ ] T021 [P] [US1] Clear ledger row 25 in `tools/ste_linter/parsing/wordcount.py`. Add `# nosec B105 - ...` on `_PROTECTED_TOKEN` and state that the value is a null-byte delimiter that survives a whitespace split.
- [ ] T022 [P] [US1] Clear ledger row 15 in `mist-ops-platform/src/shared/mist/session.py`. Add `# nosec B105 - ...` on `VAULT_SECRET_PREFIX` and state that the value is a Vault path prefix. Keep the line inside 99 characters, because that subtree holds its own `ruff` configuration.
- [ ] T023 [P] [US1] Clear ledger row 26 in `mist-ops-platform/src/shared/services/notification.py`. Add `# nosec B107 - ...` on the `password: str = ""` default in `EmailAdapter.__init__` and state that the empty string is a "not provided" sentinel. Keep the signature unchanged, per research decision R8. Keep the line inside 99 characters.
- [ ] T024 [US1] Verify Group B. Re-run T005 and the T004 filter. Confirm that B105 and B107 each read 0 and that B110 reads 7 and B101 reads 18. Run `ruff check .` and `black --check --diff .`. Run `mypy src/ --config-file pyproject.toml`. Append one evidence line for each of the 12 rows to the ledger in `specs/1032-bandit-severity-gate/data-model.md`.

**Checkpoint**: The in-scope total reads 25. Group C can start.

---

## Phase 5: User Story 1, Group C - Silent exception handling (Priority: P1)

**Goal**: Clear all 7 findings for rule B110. Five findings gain a narrowed exception type and a debug log. Two findings gain a suppression with a stated reason.

**Independent Test**: A fresh scan reports 0 for B110. The unit suite keeps the pass count from T008. `src/utils/logger_utils.py` holds no new log call.

**Rows covered**: 27 to 33.

**Caution**: This group changes behavior. Narrow the exception type to the specific error that the block expects. A narrowed clause adds no branch, so the `radon` score stays flat.

- [ ] T025 [P] [US1] Clear ledger rows 27 and 28 in `mist-ops-platform/src/api/routes/health.py`. Replace the bare `except` on the Redis probe and on the worker probe with the specific exception type. Log the failure at debug level before the block returns. Keep each line inside 99 characters.
- [ ] T026 [P] [US1] Clear ledger row 29 in `src/auth/interactive/login_orchestrator.py`. Narrow the exception type around `configure_session_timeout(apisession)` and log the failure at debug level.
- [ ] T027 [P] [US1] Clear ledger row 30 in `src/export/site_insights/device_metric_operation.py`. Narrow the exception type at the `pass  # WHY: Degrade gracefully` block and log the failure at debug level.
- [ ] T028 [P] [US1] Clear ledger row 31 in `src/firmware/firmware_manager.py`. Narrow the exception type inside `_display_ssr_inventory_stats` and log the failure at debug level.
- [ ] T029 [P] [US1] Clear ledger row 32 in `src/utils/logger_utils.py`. Add `# nosec B110 - ...` on the `record.args = ()` cleanup block. State that a log call inside the logging filter can re-enter the filter and can recurse without end. Add no log call. This is the single recorded deviation from Principle VII.
- [ ] T030 [P] [US1] Clear ledger row 33 in `src/utils/zscaler_probe.py`. Add `# nosec B110 - ...` on the `conn.close()` cleanup block and state that the block is a best-effort cleanup. Keep the existing `# pragma: no cover` annotation.
- [ ] T031 [US1] Verify Group C. Re-run T005 and the T004 filter. Confirm that B110 reads 0 and that B101 reads 18. Run `ruff check .`, `black --check --diff .`, `mypy src/ --config-file pyproject.toml`, `radon cc src/ -a -nb`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Confirm that the pass count matches T008 and that `src/utils/logger_utils.py` holds no new log call. Append the evidence for rows 32 and 33 to the ledger in `specs/1032-bandit-severity-gate/data-model.md`.

**Checkpoint**: The in-scope total reads 18. Group D1 can start.

---

## Phase 6: User Story 1, Group D1 - Assert statements that only narrow a type (Priority: P1)

**Goal**: Clear the 11 B101 findings that carry no runtime duty. Requirement FR-010 permits a suppression here. Each comment must name the guard that already proves the value.

**Independent Test**: A fresh scan reports 7 for B101, which is the Group D2 remainder. Every other rule count reads 0. `mypy src/` stays green, because every `assert` stays in place.

**Rows covered**: 34 to 44.

- [ ] T032 [P] [US1] Clear ledger rows 34 to 38 in `src/export/data_exporter.py`. Add `# nosec B101 - ...` on `assert configure_db_logging is not None`, on `assert DatabaseConfig is not None`, on `assert DatabaseRouter is not None`, on `assert DataExporter._router is not None`, and on `assert api_function_name is not None`. Name `_polyglot_db_layer_available` for the first three and name the caller guard for the last two.
- [ ] T033 [P] [US1] Clear ledger rows 39 to 42 in `src/firmware/firmware_manager.py`. Add `# nosec B101 - ...` on `assert prepared is not None`, on `assert org_and_sites is not None`, on `assert config_and_version is not None`, and on `assert selected_sites is not None`. Each reason names the early return that proves the value.
- [ ] T034 [P] [US1] Clear ledger row 43 in `src/firmware/site_auto_upgrade.py`. Add `# nosec B101 - ...` on `assert isinstance(resolved, SiteAutoUpgradeConfig)` and name the `"config" in cfg` branch that already proves the shape.
- [ ] T035 [P] [US1] Clear ledger row 44 in `src/gateway/_wan2_variable_device.py`. Add `# nosec B101 - ...` on `assert self._pool_fn is not None`. Keep the existing inert `# noqa: S101` annotation, per research decision R4.
- [ ] T036 [US1] Verify Group D1. Re-run T005 and the T004 filter. Confirm that B101 reads 7 and that every other in-scope rule reads 0. Run `ruff check .`, `black --check --diff .`, and `mypy src/ --config-file pyproject.toml`. Append one evidence line for each of the 11 rows to the ledger in `specs/1032-bandit-severity-gate/data-model.md`.

**Checkpoint**: The in-scope total reads 7. Group D2 can start.

---

## Phase 7: User Story 1, Group D2 - Assert statements that guard runtime behavior (Priority: P1)

**Goal**: Convert the last 7 B101 findings into explicit checks that raise. Python removes an `assert` under the `-O` flag, so a runtime guard must not depend on one. Requirement FR-009 demands this conversion.

**Independent Test**: `validate_template` raises `ValueError` on a bad template and its docstring names `ValueError`. The unit suite passes under `.venv\Scripts\python.exe -O -m pytest tests/unit -q`.

**Rows covered**: 45 to 51.

**Caution**: Each conversion adds one branch. Keep every converted function inside 25 lines and 5 blocks, per the Five-Item Rule. Confirm that `radon` reports no block above 10 in `src/`.

- [ ] T037 [P] [US1] Convert ledger rows 45 and 46 in `src/firmware/site_auto_upgrade.py`. Replace `assert isinstance(self.org_id, str)` and `assert isinstance(self.dry_run, bool)` inside `SiteAutoUpgradeConfig.__post_init__` with explicit checks that raise `TypeError`. Each message names the field and the expected type. Keep the function inside 25 lines.
- [ ] T038 [US1] Convert ledger rows 47 to 51 in `src/maps/plotly_map_templates.py`. Replace the five asserts inside `_rule_css_length`, `_rule_html_entry`, `_rule_html_style`, and `_rule_meta_shape` with explicit checks that raise. Raise `ValueError` for the four content checks. Raise `TypeError` for the `isinstance` check at row 50. Each message names the rule that failed.
- [ ] T039 [US1] Update the linked docstring in `src/maps/plotly_map_templates.py`. Change the `Raises:` section of `validate_template` from `AssertionError` to `ValueError`. The `pydocstyle` gate and the `interrogate` gate read this docstring. Depends on T038, because both tasks edit the same file.
- [ ] T040 [US1] Re-run the affected test files with `.venv\Scripts\python.exe -m pytest tests/maps/test_plotly_map_templates.py tests/unit -k site_auto_upgrade --no-cov -q`. Confirm that no test expects `AssertionError` from either module, as research decision R5 verified.
- [ ] T041 [US1] Verify Group D2 and close User Story 1. Re-run T005 and the T004 filter. Confirm that B101 reads 0 and that the in-scope total reads 0. Run `ruff check .`, `black --check --diff .`, `mypy src/ --config-file pyproject.toml`, `pylint src/ --ignore=maps,ssh,ui`, `radon cc src/ -a -nb`, `vulture src/ --min-confidence 80`, and `.venv\Scripts\python.exe -m pytest tests/unit --no-cov -q`. Confirm that no block scores above 10.

**Checkpoint**: The in-scope total reads 0. User Story 1 is complete. SC-001, SC-004, and SC-006 now hold.

---

## Phase 8: User Story 3 - Understand each accepted finding without asking the author (Priority: P3)

**Goal**: Prove that every added suppression comment names a rule identifier and states a verified reason.

**Independent Test**: A reviewer lists every added `# nosec` line. Each line passes the contract in [contracts/suppression-comment.md](contracts/suppression-comment.md).

**Note on the order**: This phase runs before User Story 2. The plan and research decision R9 require the workflow change to be the final code change, because CI fails while any finding remains.

- [ ] T042 [US3] List every added suppression with `git diff main...HEAD -- '*.py' | Select-String -Pattern 'nosec'`. Check each line against `specs/1032-bandit-severity-gate/contracts/suppression-comment.md`. Confirm that each line names at least one rule identifier, holds one reason sentence, uses an ASCII hyphen, and stays inside its line-length limit. Reject any bare suppression, per FR-007 and SC-005.
- [ ] T043 [US3] Check every added comment against `documentation/ASD-STE100_writing-guide.md`. Confirm the active voice, a simple tense, one idea for each sentence, no semicolon, no Latin abbreviation, and American spelling. Requirement FR-019 demands this check.
- [ ] T044 [US3] Ask a reviewer who did not write the change to read three added suppression comments. The reviewer must state the reason for each comment in under one minute and without help from the author. SC-008 defines this outcome.

**Checkpoint**: Every suppression carries a verified reason. SC-005 and SC-008 now hold.

---

## Phase 9: User Story 2, Group E - Fail the build on any bandit finding (Priority: P2)

**Goal**: Remove the `-ll` flag from the security gate. This is the final code change of the feature.

**Independent Test**: A text search of the bandit step returns no match for `-ll`. The CI bandit job passes on the clean branch.

**Rows covered**: 52 and 53.

**Warning**: Run this phase only after Phase 7 reports an in-scope total of 0. The gate fails on every push while any finding remains.

- [ ] T045 [US2] Change line 219 of `.github/workflows/ci.yml` from `run: bandit -c pyproject.toml -r . -ll` to `run: bandit -c pyproject.toml -r .`. Keep `-c pyproject.toml` and keep `-r .`, per FR-004. Add no severity flag and no confidence flag, per FR-003.
- [ ] T046 [US2] Replace the second comment line above the same step in `.github/workflows/ci.yml`. Change `# -ll gates on MEDIUM+ severity (LOW findings surface in logs but don't fail)` to `# No severity flag: the gate fails on a finding at any severity, including LOW (issue #889)`. Requirement FR-005 demands this statement. Depends on T045, because both tasks edit the same file.
- [ ] T047 [US2] Verify Group E. Run `Select-String -Path .github\workflows\ci.yml -Pattern '\-ll'` and confirm no match inside the bandit step. Confirm that the step holds no `-l`, no `--severity-level`, no `-i`, and no `--confidence-level`. Confirm that the `pip install 'bandit[toml]'` step and the `[tool.bandit]` table in `pyproject.toml` stay unchanged.

**Checkpoint**: The gate fails on any severity. SC-002 now holds.

---

## Phase 10: Polish and Final Validation

**Purpose**: Prove every success criterion and open the pull request. These tasks change no source line.

- [ ] T048 Run the full gate suite exactly as CI runs it, from the repository root. Run `ruff check .`, `black --check --diff .`, `mypy src/ --config-file pyproject.toml`, `pylint src/ --ignore=maps,ssh,ui`, `radon cc src/ -a -nb`, `vulture src/ --min-confidence 80`, `.venv\Scripts\python.exe -m pytest --cov=src/ --cov-fail-under=80`, `bandit -c pyproject.toml -r .` with no `-ll`, and `pip-audit`. Do not scope a gate to the changed files only. SC-007 depends on this run.
- [ ] T049 Prove the negative case for SC-003. Add one temporary `assert True` line to a tracked file under `src/`. Run `bandit -c pyproject.toml -r .` and confirm that it reports one B101 finding and exits with code 1. Remove the line. Run `git status` and confirm that the tree holds no leftover change.
- [ ] T050 [P] Prove SC-006. Run `.venv\Scripts\python.exe -O -m pytest tests/unit -q`. The `-O` flag removes every `assert`, so a suite that keeps the T008 pass count proves that no converted guard lost its duty.
- [ ] T051 [P] Prove SC-009. Run `git diff --name-only main...HEAD`. Confirm that the list holds the 21 source files and `.github/workflows/ci.yml` only. Confirm that the list holds no path under `tools/test_quality_analyzer/fixtures/`, no `_tr042_synthetic.py`, and no `mist-ops-platform/src/shared/config/settings.py`.
- [ ] T052 Open the pull request against `main` from `security/889-bandit-ll`. Write `Closes #889` in the body. Link `specs/1032-bandit-severity-gate/spec.md`. Attach the completed ledger from `specs/1032-bandit-severity-gate/data-model.md` as the evidence for all 54 rows. Complete the checklist in `.github/PULL_REQUEST_TEMPLATE.md`. Add the `auto-merge` label only after every check passes, including CodeQL.

---

## Dependencies and Execution Order

### Phase order

| Phase | Content | Starts after |
| - | - | - |
| 1 | Setup | Nothing |
| 2 | Foundational baseline | Phase 1 |
| 3 | US1 Group A, the subprocess family | Phase 2 |
| 4 | US1 Group B, the credential strings | Phase 3 reports 0 for B404, B603, B606, and B607 |
| 5 | US1 Group C, the silent exceptions | Phase 4 reports 0 for B105 and B107 |
| 6 | US1 Group D1, the type-narrowing asserts | Phase 5 reports 0 for B110 |
| 7 | US1 Group D2, the runtime guards | Phase 6 reports 7 for B101 |
| 8 | US3, the suppression audit | Phase 7 reports 0 in scope |
| 9 | US2 Group E, the gate flip | Phase 8 accepts every comment |
| 10 | Polish and final validation | Phase 9 |

### Why User Story 3 runs before User Story 2

The template orders a phase by story priority. This feature inverts the last two phases. Research decision R9 and the plan both require the workflow change to be the final code change. CI fails on every push while any finding remains, so an early flip would hide a real regression inside expected noise.

### Group exit rule

A group must reach zero for its own rules before the next group starts. No other rule count may move. A moved count means that an edit relocated a finding instead of clearing it. Section 2 of [data-model.md](data-model.md) defines this rule.

### Cross-phase file dependencies

Four files appear in more than one group. The phases run in order, so no conflict arises. Do not reorder these tasks.

| File | Earlier task | Later task |
| - | - | - |
| `src/utils/zscaler_probe.py` | T013, Group A | T030, Group C |
| `src/firmware/firmware_manager.py` | T028, Group C | T033, Group D1 |
| `src/firmware/site_auto_upgrade.py` | T034, Group D1 | T037, Group D2 |
| `src/maps/plotly_map_templates.py` | T038, Group D2 | T039, the docstring |

### Same-file sequencing inside a phase

| Task | Depends on | Reason |
| - | - | - |
| T010 | T009 | Both edit `starlink_dashboard.py`. |
| T039 | T038 | Both edit `src/maps/plotly_map_templates.py`. |
| T046 | T045 | Both edit `.github/workflows/ci.yml`. |

---

## Parallel Opportunities

| Phase | Parallel tasks | Files |
| - | - | - |
| 3 | T009, T011, T012, T013 | 4 files |
| 4 | T016 to T023 | 8 files |
| 5 | T025 to T030 | 6 files |
| 6 | T032 to T035 | 4 files |
| 7 | T037, T038 | 2 files |
| 10 | T050, T051 | No source file |

The largest parallel set is Phase 4, which holds 8 independent single-file edits after the T015 credential proof closes.

---

## Task Count Summary

| Group | Phase | Story | Edit tasks | Support tasks | Total | Ledger rows |
| - | - | - | - | - | - | - |
| Setup | 1 | none | 0 | 3 | 3 | none |
| Foundational | 2 | none | 0 | 5 | 5 | none |
| A, subprocess family | 3 | US1 | 5 | 1 | 6 | 1 to 14, 17 findings |
| B, credential strings | 4 | US1 | 8 | 2 | 10 | 15 to 26, 12 findings |
| C, silent exceptions | 5 | US1 | 6 | 1 | 7 | 27 to 33, 7 findings |
| D1, type narrowing | 6 | US1 | 4 | 1 | 5 | 34 to 44, 11 findings |
| D2, runtime guards | 7 | US1 | 3 | 2 | 5 | 45 to 51, 7 findings |
| Suppression audit | 8 | US3 | 0 | 3 | 3 | none |
| E, the gate flip | 9 | US2 | 2 | 1 | 3 | 52 and 53 |
| Polish | 10 | none | 0 | 5 | 5 | none |
| **Total** | | | **28** | **24** | **52** | **54 findings** |

User Story 1 holds 33 tasks across five groups. User Story 2 holds 3 tasks. User Story 3 holds 3 tasks.

---

## Implementation Strategy

### The smallest useful increment

Phase 1 through Phase 3 form the smallest useful increment. Group A clears 17 of the 54 findings, and 13 of those sit outside `src/`. Those 13 face only `ruff`, `black`, and `bandit`, so the gate risk is the lowest of any group. A reviewer can accept Group A on its own.

### The delivery order

1. Land Group A and Group B. Both are comment-only changes with no behavior change.
2. Land Group C and Group D1. Group C changes exception handling, so it needs the unit suite.
3. Land Group D2. This group converts 7 guards and changes an exception type, so it needs the affected test files and the complexity gate.
4. Land the audit in Phase 8. It changes no code.
5. Land Group E last. The gate then enforces the clean state.

### Stop conditions

| Condition | Action |
| - | - |
| The baseline in T006 does not read 54. | Stop. Re-derive the ledger before any edit. |
| A Group B value is a real credential. | Stop. Move the value to the environment and raise a rotation request. Do not add a suppression. |
| Issue #1709 grows to cover one of the 7 B110 lines. | Stop. Coordinate with the owner of #1709 before the Group C edit. |
| A group verification shows a moved count on another rule. | Stop. Find the edit that relocated the finding. |
| A reviewer rejects a suppression. | Replace the suppression with a fix. Requirement FR-008 ranks a fix above a suppression. |
