# UI Checklist: Offline Dynamic JVD Labs Preview

**Purpose**: Check the page design and the browser evidence before implementation review.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Copy and Layout

- [x] UI-01 The page copy uses plain words and states the offline status (FR-026). Test TR-03 checks the status words. This item is also a manual review.
- [x] UI-02 The copy and the fixtures contain no real device name, address, token, or private framework name. The example uses `edge-a` and `edge-b`.
- [x] UI-03 Each reason appears as one plain sentence. No bare code appears (`contracts/labs-page.md`, "Copy Rules").
- [x] UI-04 The run-name input has a visible label. The error panel names the rule that failed.

## Identifiers

- [x] UI-05 Each new interactive element has a stable `data-testid` (FR-021). Evidence: `contracts/labs-page.md`. Tests TR-04 and TB-01.
- [x] UI-06 The navigation anchor uses the identifier `nav-labs` after T014 (`contracts/labs-page.md`, "Navigation").

## States

- [x] UI-07 The unavailable state shows no device rows and no link rows (FR-014, FR-015). Test TR-11.
- [x] UI-08 A rejected form shows the error panel and no rows (FR-009, FR-010). Tests TR-08 to TR-10.
- [x] UI-09 The default run name comes from the server example (FR-005). Test TR-03.

## Browser Evidence

- [x] UI-10 The browser journey covers the page, one valid submission, and the unavailable state. Tests TB-01 and TB-02.
- [x] UI-11 A failed browser step saves a screenshot to `test-artifacts/labs-preview/`. Test TB-03.
- [x] UI-12 The browser tests skip with a stated cause when Chromium is absent (D-19).

## Open Items

- [ ] UI-13 CI does not run the browser module (D-19). This item stays open until RA-1 frees room in `tests/e2e`.
