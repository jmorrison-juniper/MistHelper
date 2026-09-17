# Tasks: Blind Exception Handler Cleanup Slice 2

**Input**: Design documents from `specs\1794-blind-except-slice2\`

**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 Confirm pull request #2837 merged. (delivered: #2837 merged)
- [x] T002 Create worktree `..\MistHelper-1794-blind-except-slice2`. (delivered: worktree)
- [x] T003 Measure the baseline broad handler count. (delivered: 812)

## Phase 2: Implementation

- [x] T004 [US1] Narrow seven bulk switch upgrade handlers. (delivered: `src\firmware\bulk_switch_upgrader.py`)
- [x] T005 [US1] Narrow five site auto-upgrade handlers. (delivered: `src\firmware\site_auto_upgrade.py`)
- [x] T006 [US1] Narrow one destructive reboot handler. (delivered: `src\device\device_reboot_manager.py`)
- [x] T007 [US1] Narrow one service-ping SDK handler. (delivered: `src\websocket\service_ping_manager.py`)
- [x] T008 [US1] Narrow three Mist SDK export handlers. (delivered: `src\export\site_config_exporter.py`, `src\export\site_client_exporter.py`)

## Phase 3: Tests

- [x] T009 [US1] Add bulk switch programming-error tests. (delivered: `tests\unit\test_bulk_switch_upgrader.py`)
- [x] T010 [US1] Add site auto-upgrade programming-error tests. (delivered: `tests\unit\test_site_auto_upgrade.py`)
- [x] T011 [US1] Add reboot, service-ping, and export programming-error tests. (delivered: targeted test files)

## Phase 4: Validation

- [x] T012 Run targeted unit tests. (delivered: 479 passed)
- [ ] T013 Run repository validation gates.
- [ ] T014 Push and open the pull request.

## Dependencies & Execution Order

Setup precedes implementation. Implementation precedes tests. Targeted tests precede repository gates.
