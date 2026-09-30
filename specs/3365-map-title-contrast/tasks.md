# Tasks: Readable Maps Title

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the documents under `design/`.

**Organization**: The tasks preserve the user story order.
Tests precede the implementation that they measure.

## Phase 1: Setup

- [x] T001 Check issue ownership and reserve the file set for `web_portal/templates/map_viewer.html` and its regression files. (delivered: issue #3365 ownership comment)
- [x] T002 Read theme helpers and test prior art for `web_portal/templates/map_viewer.html`. (delivered: design/research.md)
- [x] T003 Complete the specification and requirement checklist in `specs/3365-map-title-contrast/`. (delivered: spec.md, checklists/requirements.md)
- [x] T004 Complete the plan and UI contract in `specs/3365-map-title-contrast/`. (delivered: plan.md, design/contracts/ui.md)

## Phase 2: Foundational Checks

- [x] T005 Add actual-color measurement and a strict contrast decision in `tests/e2e/test_map_title_contrast.py`. (delivered: tests/e2e/test_map_title_contrast.py)
- [x] T006 Add direct contrast failure and invalid-input checks in `tests/unit/web_portal/test_map_title_theme.py`. (delivered: tests/unit/web_portal/test_map_title_theme.py, 14 decision checks passed)
- [x] T007 Prove the original dark title fails in `tests/e2e/test_map_title_contrast.py` before editing the template. (delivered: Chromium measured 1.290847:1 and failed the 4.5:1 assertion)

## Phase 3: User Story 1 - Read the Selected Map Title

**Independent Test**: Select the same floor plan in each theme and measure its rendered title contrast.

- [x] T008 [US1] Add initial and saved-theme journeys in `tests/e2e/test_map_title_contrast.py`. (delivered: tests/e2e/test_map_title_contrast.py)
- [x] T009 [US1] Set the layout font from the computed map card text color in `web_portal/templates/map_viewer.html`. (delivered: web_portal/templates/map_viewer.html)
- [x] T010 [US1] Verify the actual fill and at least 4.5:1 contrast with `tests/e2e/test_map_title_contrast.py`. (delivered: dark 8.693491:1, light 15.426285:1)

## Phase 4: User Story 2 - Change the Theme

**Independent Test**: Change the theme in both directions without replacing the floor plan or its viewing range.

- [x] T011 [US2] Add both theme-change directions and a delayed stylesheet journey in `tests/e2e/test_map_title_contrast.py`. (delivered: tests/e2e/test_map_title_contrast.py)
- [x] T012 [US2] Add the stylesheet load listener and font-only plot update in `web_portal/templates/map_viewer.html`. (delivered: web_portal/templates/map_viewer.html)
- [x] T013 [US2] Synchronize the font after plot completion and preserve the late-answer guard in `web_portal/templates/map_viewer.html`. (delivered: pending-image journey and original late-answer journeys passed)
- [x] T014 [US2] Verify an empty map causes no script error with `tests/e2e/test_map_title_contrast.py`. (delivered: empty-map journey passed)

## Phase 5: Quality and Documentation

- [x] T015 Run the new journeys and related map, theme, route, and template checks named in `design/quickstart.md`. (delivered: 51 browser checks and 84 offline checks passed)
- [x] T016 Run syntax, Ruff, Black, the configured mypy scope, and the configured quality ratchet from `design/quickstart.md`. (delivered: local quality checks passed, ratchet checked 2 files with 0 findings)
- [x] T017 Add the release note in `changelog.d/issue-3365-map-title-contrast.md` and the related theme description in `README.md`. Keep `CHANGELOG.md` unchanged. (delivered: changelog.d/issue-3365-map-title-contrast.md, README.md)
- [x] T018 Analyze `spec.md`, `plan.md`, and `tasks.md` against the delivered behavior. (delivered: plan.md consistency analysis, all 8 requirements and 5 success criteria covered)

## Dependencies and Execution Order

T001 through T004 establish ownership and the design.
T005 and T006 precede T007.
T007 precedes any template implementation.
T008 precedes T009 and T010.
T011 precedes T012 through T014.
T015 and T016 follow both user stories.
T017 and T018 follow successful local validation.

## Parallel Opportunities

The offline decision tests and browser measurement can be prepared in parallel.
The local type check and browser journeys can run in parallel.
All edits to the map template remain sequential.
This repair uses one implementation owner.

## Implementation Strategy

Prove the original defect first.
Repair the initial title color.
Repair the theme-change timing.
Validate all preserved map behavior.
Commit and push only after the local evidence passes.
Coordinate the final squash merge with the parent session.
