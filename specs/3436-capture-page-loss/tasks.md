# Tasks: Capture reads report a lost page

**Input**: Design documents from `specs/3436-capture-page-loss/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), and the documents under `design/`.

**Tests**: The user requires native SDK red and green acceptance tests.

**Organization**: Tasks describe the three independently checkable read paths.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Verify ownership and claim the five source paths before edits. (delivered: `plan.md`)
- [x] T002 Read the current templates and record the feature-only hook equivalent. (delivered: `.spec-context.json`)
- [x] T003 Recover only the own ignored environment after the real bootstrap failure. (delivered: `design/quickstart.md`)

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T004 Build native page scenarios using read-only `tests/support/sdk_pages.py`. (delivered: `tests/unit/upgrade_portal/capture_page_loss/cases.py`)
- [x] T005 Reproduce all five page losses on unchanged starting main. (delivered: `design/quickstart.md`)
- [x] T006 Prove checked walking, malformed records, and transport failures. (delivered: `src/upgrade_portal/capture/devices.py`)

## Phase 3: User Story 1 - Keep device evidence (Priority: P1)

### Tests for User Story 1

- [x] T007 [US1] Cover capture inventory and statistics. (delivered: `tests/unit/upgrade_portal/capture_page_loss/test_devices.py`)
- [x] T008 [US1] Cover fleet readings and unchanged settle decisions. (delivered: `tests/unit/upgrade_portal/capture_page_loss/test_gate.py`)

### Implementation for User Story 1

- [x] T009 [US1] Replace the unchecked capture walk. (delivered: `src/upgrade_portal/capture/devices.py`)
- [x] T010 [US1] Replace the unchecked fleet walk. (delivered: `src/upgrade_portal/upgrade/gate.py`)
- [x] T011 [US1] Update obsolete stand-ins and exact value checks. (delivered: `tests/unit/upgrade_portal/test_capture_devices.py`, `tests/unit/upgrade_portal/test_upgrade_gate.py`)

## Phase 4: User Story 2 - Keep wireless evidence (Priority: P1)

### Tests for User Story 2

- [x] T012 [US2] Check final wireless records and reasons. (delivered: `tests/contract/upgrade_portal/capture_page_loss/test_clients.py`)
- [x] T013 [US2] Prove the three unaffected map reads remain loud. (delivered: `tests/contract/upgrade_portal/capture_page_loss/test_clients.py`)

### Implementation for User Story 2

- [x] T014 [US2] Carry wireless statistics records and reasons. (delivered: `src/upgrade_portal/capture/clients.py`)
- [x] T015 [US2] Carry the real result into final assembly. (delivered: `src/upgrade_portal/capture/collector.py`)
- [x] T016 [US2] Update the affected stand-ins. (delivered: `tests/unit/upgrade_portal/test_capture_clients.py`, `tests/unit/upgrade_portal/test_capture_collector.py`)

## Phase 5: User Story 3 - Keep tier 3 evidence (Priority: P1)

### Tests for User Story 3

- [x] T017 [US3] Check all final extra rows and reasons. (delivered: `tests/contract/upgrade_portal/capture_page_loss/test_extras.py`)

### Implementation for User Story 3

- [x] T018 [US3] Carry checked page outcomes. (delivered: `src/upgrade_portal/capture/extras.py`)
- [x] T019 [US3] Replace obsolete success-fallback tests. (delivered: `tests/unit/upgrade_portal/test_capture_extras.py`)

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T020 Prove the negative decision and changed coverage regions. (delivered: `tests/unit/upgrade_portal/capture_page_loss/test_walk.py`, `design/quickstart.md`)
- [x] T021 Run native cases, complete relevant selections, and configured local gates. (delivered: `design/quickstart.md`)
- [x] T022 Add the unique fragment and verify all nine feature documents. (delivered: `changelog.d/issue-3436-capture-page-loss.md`)
- [x] T023 Prepare the exact 27-file owned manifest and committed-scope check procedure. (delivered: `design/quickstart.md`)
- [x] T024 Preserve the full 23-item template in the session's offline draft. (delivered: `design/quickstart.md`)

## Dependencies & Execution Order

Setup precedes the native red proofs.
The red proofs precede every production edit.
The checked walk precedes all reader migrations.
Each story requires its own final-output proof.
All three stories precede validation, the local commit, and the handoff.
The implementation tasks cover the committed deliverables.
The post-commit check and handoff follow the local protocol in `design/quickstart.md`.
Their exact final SHA and results stay in the session evidence, not a self-referential commit record.

## Parallel Opportunities

The device and gate test cases use independent endpoint boundaries.
The wireless and extra contract cases use independent response sources.
Run related selectors in one pytest invocation after the implementation.
No second agent owns these files.

## Implementation Strategy

Deliver all five surfaces in one local commit.
Do not publish a partial three-read repair.
Do not perform a remote or production action.
Publication, protected merge, and exact-main tests require the parent's later verified-base grant.
Human review remains mandatory.
