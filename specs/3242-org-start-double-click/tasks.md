# Tasks: Close the multi-site Start button on the first click

**Issue**: #3242 | **Plan**: [plan.md](plan.md)

- [x] T001 Write the contract tests of the replay refusal on both server paths.
- [x] T002 Write the browser journey of the double click on Review, on Start, and on the cancel button.
- [x] T003 Write the browser journey of the start from a second tab and its job link.
- [x] T004 Write the browser journey of a fault refusal that opens the Start button again.
- [x] T005 Write the browser journey of a restored page that loads again.
- [x] T006 Guard proof: T001 to T005 fail on the old code.
- [x] T007 Add `OrgReplayRefusal` to `routes/org_upgrade.py`, and call it from both refusal paths.
- [x] T008 Add the close, the open, the replay refusal, and the restore rule to `portal.js`.
- [x] T009 Run the upgrade portal unit, contract, and browser tests for regressions.
- [x] T010 Add the documentation section and the release note.
