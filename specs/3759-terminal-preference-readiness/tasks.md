# Tasks: Terminal Preference Readiness

**Input**: Design documents from `specs/3759-terminal-preference-readiness/`

**Prerequisites**: `spec.md` and `plan.md`

## Phase 1: J9 Readiness

- [x] T001 Update only the J9 readiness region in `tests/e2e/websockets_tab/test_websockets_terminal.py` to wait for the checked default before the existing snapshot. (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`)
- [x] T002 Add a uniquely named deterministic test module under `tests/e2e/websockets_tab/` that proves delayed initialization passes and missing initialization fails within its supplied timeout. (delivered: `tests/e2e/websockets_tab/test_3759_terminal_preference_readiness.py`)

## Phase 2: Verification

- [x] T003 Run the readiness controls separately with native Playwright and record each result. (delivered: `tests/e2e/websockets_tab/test_3759_terminal_preference_readiness.py`)
- [x] T004 Run the original 65 browser memberships separately and record all collected, completed, skipped, failed, and unexecuted memberships. (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`)
- [x] T005 Run applicable syntax, lint, format, type, test-quality, and security gates without editing files outside the authorized scope. (delivered: `specs/3759-terminal-preference-readiness/plan.md`)
