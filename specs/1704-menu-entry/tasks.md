# Tasks: Menu Entry Rows and Menu Dependency Factories

**Input**: `specs/1704-menu-entry/spec.md` and `specs/1704-menu-entry/plan.md`

## Phase 1: Specification

- [x] T001 Write the feature specification for issues #1704 and #1705. (delivered: `specs/1704-menu-entry/spec.md`)
- [x] T002 Write the technical plan for the menu row and factory refactor. (delivered: `specs/1704-menu-entry/plan.md`)
- [x] T003 Write the implementation task list with proof file paths. (delivered: `specs/1704-menu-entry/tasks.md`)

## Phase 2: Menu row model

- [x] T004 Add the immutable `MenuEntry` dataclass. (delivered: `src/utils/menu_entry.py`)
- [x] T005 Convert `menu_actions` values to named row objects. (delivered: `MistHelper.py`)
- [x] T006 Update CLI and interactive menu dispatch to read named row fields. (delivered: `MistHelper.py`)
- [x] T007 Update systematic test dispatch to read `supports_fast`. (delivered: `MistHelper.py`)

## Phase 3: Dependency factories

- [x] T008 Add the site export utility factory class. (delivered: `MistHelper.py`)
- [x] T009 Add the routing utility factory class. (delivered: `MistHelper.py`)
- [x] T010 Add the gateway template manager factory class. (delivered: `MistHelper.py`)
- [x] T011 Replace the repeated constructor blocks with factory calls. (delivered: `MistHelper.py`)

## Phase 4: Related surfaces

- [x] T012 Update the interactive test runner to read named row fields. (delivered: `src/troubleshooting/interactive_test_runner.py`)
- [x] T013 Update the web portal executor to read named row fields. (delivered: `web_portal/services/operation.py`)
- [x] T014 Update the static portal registry to return named rows. (delivered: `web_portal/menu_registry.py`)
- [x] T015 Update the menu reference generator for named row syntax. (delivered: `scripts/generate_menu_wiki.py`)

## Phase 5: Tests and documents

- [x] T016 Add menu metadata regression tests. (delivered: `tests/unit/test_menu_entry_metadata.py`)
- [x] T017 Update existing tests that patched or inspected menu rows. (delivered: `tests/unit/troubleshooting/test_interactive_test_runner.py`)
- [x] T018 Update existing menu wiring tests. (delivered: `tests/integration/test_menu_org_license_async_claim_status.py`)
- [x] T019 Update existing portal tests. (delivered: `tests/unit/web_portal/test_operation_destructive_gate.py`)
- [x] T020 Regenerate the menu reference documents. (delivered: `documentation/menu_reference.md`)
- [x] T021 Add the release-note fragment. (delivered: `changelog.d/issue-1704-menu-entry.md`)

## Phase 6: Verification

- [x] T022 Run the local gates that complete on Windows and the targeted regression tests. (delivered: `specs/1704-menu-entry/analysis.md`)
- [x] T023 Write the final analysis with evidence for each criterion. (delivered: `specs/1704-menu-entry/analysis.md`)
