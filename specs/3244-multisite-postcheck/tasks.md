# Tasks: Take a post-check capture of each site of a multi-site upgrade

**Issue**: #3244 | **Plan**: [plan.md](plan.md)

- [x] T001 Write the unit tests of the stage and the rows.
- [x] T002 Write the unit tests of the view.
- [x] T003 Write the unit tests of the walk end, for the finish and for each stop.
- [x] T004 Write the unit tests of the bridge and of the key with the ordinal 2.
- [x] T005 Write the contract tests of the poll field and the page card.
- [x] T006 Guard proof: T001 to T005 fail on the old code.
  - The new unit modules import `org_postcheck`, `org_postcheck_view`, and
    `org_cascade/close.py`. The old code holds none of them.
  - Red run 1: an empty `postchecks` field fails 2 of the 5 new contract tests.
  - Red run 2: a close with no stage fails 3 close tests and 3 walk tests.
- [x] T007 Add the ordinal parameter to `assembly.standalone_capture_key`.
- [x] T008 Add `upgrade/org_postcheck.py` and `upgrade/org_postcheck_view.py`.
- [x] T009 Add `OrgCascadeClose` in `org_cascade/close.py`, and the `post_check` field in `walk.py`.
- [x] T010 Add `routes/org_postcheck.py` and pass the bridge from `_start_phase_watch`.
- [x] T011 Add the field `postchecks` to the page view and the poll.
- [x] T012 Add the partial `org_postcheck_list.html` and the paint in `portal.js`.
- [x] T013 Change the stand-in capture runner and the scripted starter.
- [x] T014 Write the browser journey, with screenshots.
- [x] T015 Run the upgrade portal unit, contract, and browser tests for regressions.
