# Tasks: Browser Skip Visibility

**Input**: Design documents in `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/`

**Prerequisites**: `plan.md`, `spec.md`, issue #3380, and `.specify/memory/constitution.md`

**Tests**: This feature is a test repair. The red-first guard and browser evidence are mandatory.

**Organization**: The phases follow the required delivery order. Do not start a later phase before the prior checkpoint passes.

## Approved Implementation Manifest

Only these paths can change during implementation:

1. `tests/guardrails/test_e2e_missing_element_skip_policy.py`
2. `tests/e2e/web_portal/test_operations_panel_workflow.py`
3. `tests/e2e/upgrade_portal/test_browser_token_signin.py`
4. `tests/e2e/upgrade_portal/test_capture.py`
5. `tests/e2e/upgrade_portal/test_comparison.py`
6. `tests/e2e/upgrade_portal/test_history.py`
7. `tests/e2e/upgrade_portal/test_signin.py`
8. `tests/e2e/upgrade_portal/test_site_selection.py`
9. `tests/e2e/upgrade_portal/test_stop.py`
10. `tests/e2e/upgrade_portal/test_run_controls/test_existing.py`
11. `tests/e2e/upgrade_portal/test_two_operators.py`
12. `specs/1823-upgrade-capture-portal/contracts/ui-testids.md`
13. `changelog.d/issue-3380-skip-visibility.md`

Production code and shared fixtures are outside the manifest.
Do not change a file under `src/`.
Do not change any `conftest.py` file or shared seeded-data fixture.
Do not change `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`.
Do not add another E2E file.

## Phase 1: Setup and Scope Freeze

**Purpose**: Confirm the approved inputs and protect unrelated work before the red-first change.

- [ ] T001 Confirm the current branch, clean ownership, and exact 13-path implementation manifest in `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md`.
- [ ] T002 Confirm that no open pull request owns a path listed in `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md`, and record any blocker in issue #3380.

**Checkpoint**: The implementer owns every approved path and has not changed production code or shared fixtures.

---

## Phase 2: User Story 1 - Report Missing Test Preconditions (Priority: P1) MVP

**Goal**: Make every approved missing-content or missing-data condition fail with a specific message.

**Independent Test**: The guard first reports 16 findings against unchanged E2E files. It later reports 16 examined sites and zero findings.

### Red-First AST Guard

- [ ] T003 [US1] Add immutable records for R-01 through R-16 and AST scan tests in `tests/guardrails/test_e2e_missing_element_skip_policy.py`, including repair ID, path, owner, message fragment, line, and condition reporting.
- [ ] T004 [US1] Add negative, positive, and absent-site tests in `tests/guardrails/test_e2e_missing_element_skip_policy.py` so a forbidden skip fails, an explicit failure passes, and a missing manifest site fails.
- [ ] T005 [US1] Run `python -B -m pytest -p no:cacheprovider -s -q tests\guardrails\test_e2e_missing_element_skip_policy.py` before any E2E edit, require exactly 16 examined sites and 16 findings, and retain the complete red output for the pull request and issue #3380.

### Repair the 16 Approved UI-Loss Skips

- [ ] T006 [US1] Replace R-01 with a named failure when no accordion reveals an operation row in `tests/e2e/web_portal/test_operations_panel_workflow.py`.
- [ ] T007 [US1] Replace R-02 with a named failure when no element matches the required row prefix in `tests/e2e/upgrade_portal/test_browser_token_signin.py`.
- [ ] T008 [US1] Replace R-03 with a named failure when the site picker has no site row in `tests/e2e/upgrade_portal/test_capture.py`.
- [ ] T009 [US1] Replace R-05, R-06, and R-07 with named table, comparison, and stored-capture failures in `tests/e2e/upgrade_portal/test_comparison.py`.
- [ ] T010 [US1] Replace R-08, R-09, and R-10 with named site-row, history-row, and previous-page-link failures in `tests/e2e/upgrade_portal/test_history.py`.
- [ ] T011 [US1] Replace R-11 with a named failure when no element matches the required row prefix in `tests/e2e/upgrade_portal/test_signin.py`.
- [ ] T012 [US1] Replace R-12 and R-13 with named row-prefix and inventory-row failures in `tests/e2e/upgrade_portal/test_site_selection.py`.
- [ ] T013 [US1] Replace R-14 with a named failure when the site picker has no site row in `tests/e2e/upgrade_portal/test_stop.py`.
- [ ] T014 [US1] Replace R-15 with a named failure when the site picker has no site row in `tests/e2e/upgrade_portal/test_run_controls/test_existing.py`.
- [ ] T015 [US1] Replace R-16 with a named failure when the site picker has no site row in `tests/e2e/upgrade_portal/test_two_operators.py`.
- [ ] T016 [US1] Replace R-04 with an explicit named failure at the existing version-control condition in `tests/e2e/upgrade_portal/test_capture.py`, without changing selectors yet.
- [ ] T017 [US1] Rerun the AST guard in `tests/guardrails/test_e2e_missing_element_skip_policy.py`, require 16 examined sites and zero findings, and stop if any approved skip remains.

**Checkpoint**: All 16 approved missing-content skips are explicit failures. The capture walk still uses its old selector until Phase 3.

---

## Phase 3: User Story 2 - Repair the Capture Click Walk Selectors (Priority: P1)

**Goal**: Use all three current version controls and preserve both browser-driven confirm visits.

**Independent Test**: The focused capture journey passes once with zero skips and reaches confirm through the save and History paths.

- [ ] T018 [US2] Remove `VERSION_SELECT_ALL_ID` and add the ordered AP, switch, and gateway selector tuple in `tests/e2e/upgrade_portal/test_capture.py`.
- [ ] T019 [US2] Require each type selector to be visible and to offer a real option in `tests/e2e/upgrade_portal/test_capture.py`, with each failure naming its selector.
- [ ] T020 [US2] Select option index 1 for each type control while preserving the save click, first confirm checks, History navigation, run selection, confirm link, second confirm checks, and owned-run cleanup in `tests/e2e/upgrade_portal/test_capture.py`.

**Checkpoint**: The capture walk uses only `upgrade-version-select-ap`, `upgrade-version-select-switch`, and `upgrade-version-select-gateway`.

---

## Phase 4: User Story 3 - Preserve Capability Skips (Priority: P2)

**Goal**: Keep skips only for a genuine unavailable browser capability.

**Independent Test**: Capability failures still skip with a specific cause. Missing UI or seeded data fails.

- [ ] T021 [US3] Review the E2E paths in `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md` and confirm that only R-01 through R-16 changed from skip to failure.
- [ ] T022 [US3] Confirm that capability skips remain unchanged in each E2E path listed in `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md`.
- [ ] T023 [US3] Confirm that no unrelated skip, marker, timeout, order, or assertion changed in each E2E path listed in `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md`.

**Checkpoint**: Capability skips remain specific. Missing expected content cannot report a skip.

---

## Phase 5: Contract and Release Note

**Purpose**: Correct the old contract and publish the user-visible test reliability repair.

- [ ] T024 Replace the stale `upgrade-version-select-all` row with the AP, switch, and gateway controls in `specs/1823-upgrade-capture-portal/contracts/ui-testids.md`, and state that the bulk control is removed.
- [ ] T025 Add the issue #3380 fixed entry in `changelog.d/issue-3380-skip-visibility.md`, with one `###` heading and one `Fixed` bullet.

**Checkpoint**: The old UI contract names only live type controls, and the feature owns one release-note fragment.

---

## Phase 6: Focused Tests and Quality Gates

**Purpose**: Prove the guard, each affected browser path, the full portal folder, and every applicable repository gate.

- [ ] T026 Set `UPGRADE_PORTAL_E2E_STRICT=1`, run `tests/guardrails/test_e2e_missing_element_skip_policy.py`, and require 16 examined sites with zero findings.
- [ ] T027 Run `tests/e2e/upgrade_portal/test_capture.py::TestUpgradeJourney::test_walk_from_the_site_list_reaches_the_confirm_page` with `--browser-channel msedge -q -rs`, and require one pass with zero skips.
- [ ] T028 Run the ten E2E files listed in `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md` with `--browser-channel msedge -q -rs`, and require zero missing-content skips.
- [ ] T029 Run the full folder that contains `tests/e2e/upgrade_portal/test_capture.py` with `--browser-channel msedge -q -rs`, record all counts, and verify each remaining skip.
- [ ] T030 Run `python -m py_compile MistHelper.py`, `python -m ruff check .`, `python -m black --check .`, and the configured mypy command from `plan.md`.
- [ ] T031 Run `python -m pytest tests\guardrails`, `bandit -c pyproject.toml -r . -q`, and the configured complexity gate from `plan.md`.
- [ ] T032 Run the configured vulture, pydocstyle, and interrogate commands from `plan.md`, and stop at the first failure.
- [ ] T033 Run `tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` and the full `test-quality-analyzer --gate` check against the repository configuration.
- [ ] T034 Inspect the complete diff against `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md` and prove that no excluded file or behavior changed.

**Checkpoint**: Focused tests and quality gates pass before delivery work starts.

---

## Phase 7: Rebase

**Purpose**: Move the verified feature onto the current `origin/main` before the final commit.

- [ ] T035 Fetch `origin/main`, rebase the current branch with the safe procedure, and preserve only paths in `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md`.
- [ ] T036 Rerun `tests/guardrails/test_e2e_missing_element_skip_policy.py` and the E2E files listed in `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md` after the rebase.

**Checkpoint**: The verified implementation is based on current `origin/main`.

---

## Phase 8: Commit

**Purpose**: Create the final local commit after the rebase.

- [ ] T037 Stage each implementation path in `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md` explicitly, then commit with the required subject, closure, and coauthor.
- [ ] T038 Run the required committed-tree comparison for `tests/guardrails/test_e2e_missing_element_skip_policy.py` with `test-quality-analyzer --changed-from "origin/main"`, and require zero new findings.

**Checkpoint**: The final commit contains only the approved manifest and passes the committed-tree quality comparison.

---

## Phase 9: Push Once

**Purpose**: Publish one verified branch revision without an intermediate push.

- [ ] T039 Push the commit that contains `tests/guardrails/test_e2e_missing_element_skip_policy.py` exactly once with `--force-with-lease`, and do not push while checks run.

**Checkpoint**: The remote branch contains the one verified publication revision.

---

## Phase 10: Create the Pull Request

**Purpose**: Open one pull request that contains the complete evidence.

- [ ] T040 Read `.github/PULL_REQUEST_TEMPLATE.md`, create the pull request to `main`, use a valid Conventional Commit title, include `Closes #3380`, and list the exact red proof, green proof, test counts, quality-gate results, manifest, and exclusions.

**Checkpoint**: The pull request names every changed path and proves that production code and shared fixtures remain unchanged.

---

## Phase 11: Post the Issue Report

**Purpose**: Give issue #3380 the final delivery record after the pull request exists.

- [ ] T041 Post one issue #3380 report that names `specs/numbered/0/0/1/0/2/0/1/0/3380-skip-visibility/tasks.md`, the pull request, commit, red and green proofs, test counts, gates, manifest, and exclusions.

**Checkpoint**: Issue #3380 has the complete implementation and verification record.

---

## Dependencies and Execution Order

### Required Phase Order

1. Phase 1 freezes the scope.
2. Phase 2 adds the guard, proves 16 red findings, and repairs all 16 skips.
3. Phase 3 repairs the capture selectors.
4. Phase 4 proves that capability skips remain.
5. Phase 5 updates the old UI contract and release note.
6. Phase 6 runs focused tests and quality gates.
7. Phase 7 rebases the verified change.
8. Phase 8 creates and checks the final commit.
9. Phase 9 pushes once.
10. Phase 10 creates the pull request.
11. Phase 11 posts the issue report.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after scope freeze and blocks every later repair.
- **User Story 2 (P1)**: Starts only after the guard reports zero findings for all 16 repaired skips.
- **User Story 3 (P2)**: Starts after the capture selector repair and audits the final skip categories.

### Parallel Opportunities

There are no approved parallel implementation tasks.
The red-first proof and the required publication order make this work sequential.
Several tasks share `tests/e2e/upgrade_portal/test_capture.py`, so parallel edits can lose evidence or create conflicts.

## Sequential Execution Examples

### User Story 1

```text
T003 -> T004 -> T005 -> T006 through T016 in order -> T017
```

### User Story 2

```text
T018 -> T019 -> T020
```

### User Story 3

```text
T021 -> T022 -> T023
```

## Implementation Strategy

### MVP First

1. Complete the scope freeze.
2. Add the AST guard.
3. Record exactly 16 findings against the unchanged implementation.
4. Repair only R-01 through R-16.
5. Require the guard to report zero findings.

This MVP completes User Story 1 and prevents future missing-content skips at the approved sites.

### Incremental Delivery

1. Complete User Story 1 and preserve the red-first evidence.
2. Complete User Story 2 and prove both confirm visits through browser actions.
3. Complete User Story 3 and preserve genuine capability skips.
4. Update the old contract and release note.
5. Run all validation before rebase, commit, one push, pull request creation, and issue reporting.

## Notes

- Every task is mandatory and sequential.
- Do not weaken the guard after the 16-finding red run.
- Do not change an approved guard record to hide a failure.
- Do not add a dependency, baseline, exclusion, suppression, or tool-policy change.
- Do not cancel a foreign run or replace a browser action with an API call.
- Keep the issue open until the pull request delivery and verification are complete.
