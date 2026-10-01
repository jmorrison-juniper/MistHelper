# Tasks: Compact data previews

**Input**: [plan.md](plan.md) and [spec.md](spec.md).

## Phase 1: Claim and Specify

- [x] T001 Verify the live issue, authenticated account, and every open pull request file list. (delivered: issue #3311 reservation comment)
- [x] T002 Claim issue #3311 with the required labels and app session identifier. (delivered: issue #3311 reservation comment)
- [x] T003 Write the unique file-only specification and plan. (delivered: specs/3311-compact-data-previews/spec.md)

## Phase 2: Prove the Failure

- [x] T004 Build the isolated fixture and actual modal harness. (delivered: tests/support/data_preview_harness.py)
- [x] T005 Add the fixed row-height test. (delivered: tests/e2e/test_data_preview_row_height.py)
- [x] T006 Record the original failing bounds and screenshot. The first two rows measured 1265.5 and 4433 pixels. (delivered: session artifacts)

## Phase 3: Repair the Presentation

- [x] T007 Extend the compact cell rules to the preview table. (delivered: web_portal/static/css/portal.css)
- [x] T008 Use safe DOM cell values and a labeled full-value dialog. (delivered: web_portal/static/js/data_preview.js)
- [x] T009 Add offline decision contracts. (delivered: tests/unit/web_portal/test_compact_data_preview.py)
- [x] T010 Add the release note. (delivered: changelog.d/issue-3311-compact-data-previews.md)

## Phase 4: Prove the Repair

- [x] T011 Measure every row at four widths in four themes. Mouse rows measured at most 41.5 pixels. Touch rows measured at most 53.5 pixels. (delivered: tests/e2e/test_data_preview_row_height.py)
- [x] T012 Prove all three pages, sorting, search, and full-value export. (delivered: tests/e2e/test_data_preview_row_height.py)
- [x] T013 Prove exact values, safe markup, keyboard controls, focus return, and touch controls. (delivered: tests/e2e/test_data_preview_row_height.py)
- [x] T014 Save and inspect each required width. Retain the original failure trace and screenshots. (delivered: session artifacts)
- [x] T015 Pass 185 focused tests with no skips. Pass the applicable local gates without baseline or exclusion edits. (delivered: session artifacts)
- [x] T016 Review the specification, implementation, and evidence for agreement. (delivered: specs/3311-compact-data-previews/spec.md)
- [x] T017 Verify the nine reserved commit paths and the required coauthor trailer. (delivered: specs/3311-compact-data-previews/plan.md)

## Publication Condition

The parent must provide an explicit grant with the exact verified main commit.
No push, pull request, or merge is authorized before that grant.

## Local Evidence

The original 1600-by-1000 case failed the fixed 60-pixel budget.
Its first two data rows measured 1265.5 and 4433 pixels.
The repaired table passed all 16 width and theme combinations.
Each combination measured 50 data rows and all 43 columns.
The touch case measured another 50 rows.
The browser used real wheel events to reach the last record and column.
Enter, Space, Tab, Shift+Tab, and Escape passed the full-value journeys.
The three page counts stayed at 50, 50, and 12.
Both 558-character and 2019-character values remained exact.

The configured test-quality ratchet checked 994 files and found no new findings.
The strict runtime audit checked 105 dependencies and found no known vulnerabilities.
The runtime-only audit did not include the Git-only development tools.
The configured type check passed 663 source files.
The explicit type check also passed the three new Python files.
The configured STE heuristic passed all seven files.
The licensed dictionary was unavailable, so this result does not prove dictionary compliance.

## Dependencies

T004 and T005 require T003.
T006 requires T004 and T005.
T007 and T008 require T006.
T009 requires the harness and the fixed decision contract.
T011 through T016 require the completed presentation repair.
T017 requires all local validation.
