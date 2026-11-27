# UI Checklist: Read-only Mist target discovery

**Purpose**: Confirm that the discovery panel shows each state clearly and never implies an empty list for a failed read.
**Created**: 2026-11-26
**Feature**: `design/contracts/ui.md`, `spec.md` User Story 2

## States

- [x] Each state has one label: Not checked, Verified, Unavailable, Denied, or Failed (contract `ui.md`, State Labels).
- [x] The label Not checked marks the page before the first check. The API never returns it (research D-4).
- [x] Each state group has one plain sentence (contract `ui.md`, Reason Sentences).
- [x] A failed or unavailable state never shows an empty list (FR-003, TC-06, TC-07, TC-15).

## Target Selection

- [x] A site is selected by its identifier only (FR-011, contract `ui.md`, Duplicate Names).
- [x] A duplicate site name shows a text warning and keeps the identifier as the option value (FR-011, TC-16).
- [x] A gateway shows its assignment as assigned or unassigned (FR-012, TC-17).
- [x] A target change dispatches `cisco-target-changed` and does not clear the review in this issue (FR-014, D-11).

## Copy and Safety

- [x] The read-only notice states that selecting a target does not change Mist (FR-013).
- [x] The page never implies that selecting a target authorizes a write (FR-013).
- [x] The copy uses plain words for a junior network operations engineer (constitution, Audience Standard, and plan, Technical Context).

## Accessibility and Test Hooks

- [x] The state line uses `role="status"` and `aria-live="polite"` (contract `ui.md`, Markers).
- [x] Each control carries a stable `data-testid` (contract `ui.md`, Markers, and the repository web UI test rule).
- [x] Each gateway checkbox has a label with the gateway name and serial.

## Browser Behavior

- [x] The browser smoke tests TC-23 and TC-24 cover the unavailable state and the event (tasks T008 and T014).
- [x] The page stores no value in browser storage (FR-007, contract `ui.md`).
