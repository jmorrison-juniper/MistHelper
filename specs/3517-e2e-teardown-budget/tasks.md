# Tasks: The session teardown of the E2E suite gets a budget of its own

**Issue**: #3517
**Specification**: `specs/3517-e2e-teardown-budget/spec.md`
**Plan**: `specs/3517-e2e-teardown-budget/plan.md`

## Phase 1: The specification

- [x] T001 Write `specs/3517-e2e-teardown-budget/spec.md`.
- [x] T002 Write `specs/3517-e2e-teardown-budget/plan.md`.
- [x] T003 Write `specs/3517-e2e-teardown-budget/tasks.md`.

## Phase 2: The repair in `tests/e2e/conftest.py`

- [ ] T004 Add the class `SessionTeardownBudget` with `DEFAULT_SECONDS = 300`,
  the override variable name, and a `seconds` method that validates the
  override and raises a named error for an invalid value. FR-002 and FR-008.
- [ ] T005 Add the class `PhaseTrailWriter` with the default path under
  `test-artifacts/`, the override variable name, a `path` method, and a
  `write` method that appends one JSON line and closes the file. FR-005,
  FR-006, and FR-007.
- [ ] T006 Add the hookwrapper `pytest_runtest_teardown` with `tryfirst=True`.
  It returns at once when `nextitem` is not `None`, when the plugin is absent,
  or when the item carries no timer. Otherwise it cancels the item timer and
  arms a replacement timer with the teardown budget. FR-001, FR-003, FR-004.
- [ ] T007 Add the hook `pytest_runtest_logreport` that calls
  `PhaseTrailWriter.write`. FR-005.
- [ ] T008 Give each new executable line an inline comment, and give each
  action an `info` line before it and a `debug` line after it.

## Phase 3: The guard

- [ ] T009 Create `tests/guardrails/e2e_timeout_budget/__init__.py`.
- [ ] T010 Write the project builder of the guard. It writes a synthetic
  conftest that loads the two repair hooks from the real
  `tests/e2e/conftest.py`, and three test modules that use `time.sleep` only.
- [ ] T011 `test_shared_budget_loses_the_report`: the red case exits 1 and
  prints no summary line. SC-001.
- [ ] T012 `test_separate_budget_keeps_the_report`: the repaired case prints
  the summary line and names the failed test. SC-002.
- [ ] T013 `test_teardown_budget_still_ends_an_overrun`: a teardown that
  exceeds its own budget ends the run. SC-003.
- [ ] T014 `test_phase_trail_survives_the_stop`: the trail of the red case
  holds the setup record and the call record of the failed test. SC-004.
- [ ] T015 `test_guard_reports_what_it_measured`: the guard prints the number
  of runs and the seconds of each run, and it fails when it cannot read its
  input. NFR-002 and NFR-003.

## Phase 4: The release note

- [ ] T016 Write `changelog.d/issue-3517-e2e-teardown-budget.md` with one
  `###` heading and one `Fixed` bullet that names issue #3517.

## Phase 5: The gates

- [ ] T017 `python -m ruff check .`
- [ ] T018 `python -m black --check .`
- [ ] T019 `python -m mypy` with the paths of `.github/workflows/ci.yml`.
- [ ] T020 `bandit -c pyproject.toml -r tests -q`
- [ ] T021 `radon cc tests/e2e tests/guardrails/e2e_timeout_budget -j |
  complexity-gate --max 10`
- [ ] T022 `symbol-diff --base origin/main tests/e2e/conftest.py`
- [ ] T023 `python -m pytest tests/guardrails/e2e_timeout_budget -p no:randomly`
- [ ] T024 `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- [ ] T025 The test quality ratchet of `.github/copilot-instructions.md`.
- [ ] T026 Commit with the Conventional Commits subject, `Closes #3517`, and
  the required trailer. Do not push, rebase, merge, or arm auto-merge.

## Dependencies

- T004 through T008 depend on T001 through T003.
- T010 depends on T004 through T007, because the guard loads the real hooks.
- T011 through T015 depend on T010.
- T017 through T025 depend on T016.
- T026 depends on T025.
