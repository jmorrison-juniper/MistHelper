# Implementation Plan: Keep each action label on one line on a narrow screen

**Issue**: #3278 | **Spec**: [spec.md](spec.md)

## Design

1. Add the rule `.portal-table .cell-control { white-space: nowrap; }` to
   section 4 of `src/upgrade_portal/app/assets/static/css/portal.css`. A cell
   that never wraps ignores the inherited `word-break` rule.
2. Put `class="cell-control"` on the action cell of
   `templates/select/orgs.html` and `templates/select/sites.html`. The site
   cell holds the Open button in the single-site mode and the check box with
   its Select label in the multi-site mode, so one class serves both modes.

## Tests

- Unit test `tests/unit/upgrade_portal/test_select_action_cells.py`. It renders
  the three page states with Jinja and reads the class of the cell that holds
  each control. It also reads the declarations of the new rule.
- Browser test `tests/e2e/upgrade_portal/test_narrow_action_cells.py`. It opens
  the three pages of the stand-in portal at 390 by 844 pixels. It counts the
  painted lines of each label and the page overflow, and it saves a screenshot.

## Guard proof

- On the old code, the unit test fails 4 of 4. The browser test fails 2 of 3:
  Choose paints 3 lines and Open paints 2 lines.
- The Select label of the stand-in data fits on the old code too, so that
  browser test is a parity guard. The unit test gives the red proof for that
  mode.

## Risks

- A cell that never wraps can make a row wider than the screen. The table sits
  in `.portal-table-scroll`, so the table scrolls sideways. The browser test
  proves that the page overflow stays at zero on all three pages.
