# Tasks: Inventory model filter

## Phase 1: Setup

- [x] T001 Inspect ownership and bootstrap dependencies with `scripts/bootstrap_worktree.py`.

## Phase 2: Foundation

- [x] T002 Read all inventory types through checked pagination in `src/operations/execution/firmware_policy/sdk.py`.

## Phase 3: Installed models

**Goal**: Both interfaces show compatible inventory models.
**Independent test**: Compare default choices with mock organization inventories.

- [x] T003 [US1] Add union membership and strict row validation in `src/operations/execution/firmware_policy/__init__.py`.
- [x] T004 [US1] Use filtered display catalogs in `web_portal/routes/firmware_policy/__init__.py`.
- [x] T005 [US1] Cover types, duplicates, pagination, multiple organizations, and failures in `tests/unit/firmware_policy/test_catalog.py`.
- [x] T006 [US1] Cover CLI default selection and cancellation in `tests/integration/firmware_policy/test_workflow.py`.

## Phase 4: Other supported models

**Goal**: Explicitly reveal all compatible models without weakening validation.
**Independent test**: Select all-model scope and inspect previously hidden choices.

- [x] T007 [US2] Add the CLI scope choice in `src/operations/execution/firmware_policy/cli.py`.
- [x] T008 [US2] Add the all-model control in `web_portal/routes/firmware_policy/templates/firmware_policy.html` and scope handling in `web_portal/static/js/firmware-policy.js`.
- [x] T009 [US2] Cover graphical scope, empty state, invalidation, and errors in `tests/e2e/web_portal/test_firmware_policy.py`.

## Phase 5: Cross-cutting work

- [x] T010 Update `documentation/org-auto-upgrade-policy.md` and `changelog.d/issue-4253-inventory-model-filter.md`.
- [x] T011 Run local gates and report read-only consistency analysis for this feature.
- [x] T012 Prepare explicit commit paths and the repository pull request template for release delivery.

## Dependencies and parallel execution

T002 precedes T003. T003 precedes T004, T005, T006, and T007.
T004 precedes T008 and T009. T008 precedes T009.
T010 can proceed independently after the interface contract is fixed.
T011 follows implementation and tests. T012 follows T011.
After the local commit, run the committed-test gate and create the pull request.
Do not delegate these connected catalog changes to parallel agents.

## Implementation strategy

First prove inventory filtering in the shared display operation.
Then connect the CLI and graphical controls.
Finally run regression tests for unchanged backup and confirmation behavior.

## Verification results

The final feature run passed 367 tests. Firmware-policy package coverage was 93.33 percent.
Repository Ruff, Black, and mypy passed. Mypy checked 850 source files.
Targeted Bandit, complexity, syntax, and docstring checks passed.
The guard and SDK run passed 38 tests and skipped one changelog check before the local commit.
All ten changed Markdown records scored at least 93.
The requirements audit could not create its temporary pip environment because `ensurepip` aborted.
A separate installed audit reported existing pip advisories. No dependency manifest changed.
