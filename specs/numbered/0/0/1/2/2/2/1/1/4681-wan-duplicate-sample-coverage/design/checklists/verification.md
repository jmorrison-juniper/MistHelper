# Verification Checklist: WAN Duplicate Sample Coverage

**Purpose**: Track each verification step for the fix.
**Created**: 2026-11-26
**Feature**: `spec.md`

## Before Implementation

- [x] The defect exists on the PR #4208 head. See RC-05 to RC-11 in `design/research.md`.
- [x] `main` does not contain the defect. See RC-02 in `design/research.md`.
- [ ] PR #4208 releases both files. Pending. Its state was open on 2026-11-26. Task T002 tracks it.

## Tests

- [ ] The duplicate tests fail before the fix. Pending. Task T003 writes them.
- [ ] The duplicate tests pass after the fix. Pending. Task T006 makes them pass.
- [ ] The summary tests pass after the fix. Pending. Task T008 makes them pass.

## Gates and Release

- [ ] The local gates pass as listed in `design/quickstart.md`. Pending. Task T-LOCAL-GATES runs them.
- [ ] CI reports success on the fix pull request. Pending. Task T-REMOTE-CI checks it.
- [ ] The changelog guard and the documentation check pass. Pending. Tasks T010 and T011 cover them.

## Notes

- Each pending item names the task that completes it.
