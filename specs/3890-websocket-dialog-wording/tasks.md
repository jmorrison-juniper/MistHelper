# Tasks: WebSocket Dialog Target Wording

**Input**: [spec.md](spec.md) and [plan.md](plan.md)

## Phase 1: Tests First

- [x] T001 [US1] [US2] Add unit tests for the four purpose texts and the generic fallback in `tests/unit/websocket_streams/catalog/test_ws_utility_text_3890.py`.
- [x] T002 [US1] Add a test that compares the EX and SRX/SSR target sets with the installed SDK docstring.
- [x] T003 [US1] [US2] Add a test that the safety class and fields of the four utilities stay unchanged.

## Phase 2: Implementation

- [x] T004 [US1] [US2] Add `_UTILITY_SENTENCES` and the `utility_key` argument to `UtilityText.sentence`.
- [x] T005 Pass the utility key from `UtilityDiscovery.entry`.

## Phase 3: Browser Proof

- [x] T006 [US1] [US2] Add `tests/e2e/websockets_tab/test_3890_dialog_wording.py`. It serves the real catalog payload and reads the displayed text of the four forms without a click on Start.

## Phase 4: Polish

- [x] T007 Add `changelog.d/issue-3890-websocket-dialog-wording.md`.
- [x] T008 Run compile, Ruff, Black, mypy, the focused tests, the preflight, and the test-quality gate.
