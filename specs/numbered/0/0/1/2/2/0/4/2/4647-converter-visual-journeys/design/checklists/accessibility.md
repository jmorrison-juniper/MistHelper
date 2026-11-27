# Accessibility Requirements Checklist: Add independently authored converter visual journeys

**Purpose**: Confirm that keyboard, focus, status, and viewport requirements are complete and testable before implementation starts.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

- [x] A11Y001 Each control is reachable by keyboard in the order that `contracts/portal-journey.md` defines (FR-007, T011).
- [x] A11Y002 The focus outline is visible in each shipped theme. The stylesheet falls back to `currentColor` where the focus token is absent (RC-35 to RC-38). Tested by T011.
- [x] A11Y003 Each status starts with a word label, so color is not needed to read it (FR-006, contract status table).
- [x] A11Y004 The status region announces changes politely (RC-09).
- [x] A11Y005 The phone viewport has no horizontal overflow (FR-009, RC-40). Tested by T012.
- [x] A11Y006 The presentation adds no animation or transition. Explained: the converter adds no motion, so no motion setting applies (FR-016).
- [x] A11Y007 Focus moves to the content that each action reveals or completes (contract focus rules). Tested by T011.
