# Tasks: Keep each action label on one line on a narrow screen

**Issue**: #3278 | **Plan**: [plan.md](plan.md)

- [x] T001 Add the `.portal-table .cell-control` rule to `portal.css`.
- [x] T002 Put the `cell-control` class on the action cell of the organization table.
- [x] T003 Put the `cell-control` class on the action cell of the site table, for both modes.
- [x] T004 Unit test for the cell class of each page state and for the rule declarations.
- [x] T005 Browser test at 390 by 844 pixels for the three page states, with screenshots.
- [x] T006 Guard proof: the new tests fail on the old code.
- [ ] T007 Remove the strict xfail of #3278 from the journeys of #3200 after this change merges.
