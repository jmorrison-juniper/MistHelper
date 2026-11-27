# Specification Analysis Report: Versioned Proposal Review and Safe Export

This report checks `spec.md`, `plan.md`, `tasks.md`, and the design files against the remote code on `main`. Row numbers refer to `design/research.md`, section R4. Finding severities are High, Medium, or Low.

## Findings

| ID | Severity | Finding | Evidence | Action |
| - | - | - | - | - |
| A-1 | High | The integration test folder reaches six children if issue #4648 adds its two planned direct files. Issues #4636 and #4641 add two more children to the current two. | Row 23. Research R6. Issue #4648 draft spec, lines for `test_parity.py` and `test_portal_browser.py`. | Issue #4648 nests its files in a feature package. The owner records the change in that record. |
| A-2 | High | Issue #4648 limits converter routes to an approved set (its draft FR-016 and SC-008). This change adds three routes. | Issue #4648 draft spec. Spec assumption A-2. | The coordinator adds the three version 2 routes to the approved set before issue #4648 merges. |
| A-3 | High | `models.py` holds five top-level classes. A new class there breaks the five-name limit. Issue #4636 moves the module. | Row 13. Decision D-14. | Issue #4641 starts after issue #4636 merges. Tasks T002 and T003 wait for that merge. |
| A-4 | Medium | Task IDs T017 and T018 mean different work in issue #4224 (DNS export tests) and in the full-parity map (proposal review). | Rows 60, 61, and 68. | This record follows the full-parity meaning that the issue names. Issue #4224 adds a mapping note. |
| A-5 | Medium | Full-parity T017 names `tests/integration/web_portal/cisco_config_converter/test_proposals.py`. This record uses the nested `proposals/` package. | Row 60. Decision D-12. | The full-parity owner records the path change in the parity map. |
| A-6 | Medium | The full-parity spec uses role for Branch, Hub, and Standalone (FR-005). This record uses template type for the DNS values `standalone` and `spoke`. | Row 64. Decision D-10. | Issue #4638 owns hardware role. This record reserves the scope field for it. |
| A-7 | Medium | The constitution asks for a README update on each behavior change. The README names no converter, so this change adds no README text. | Rows 32 and 77. Decision D-16. | The owner decides the README scope for the whole converter program. |
| A-8 | Low | `StructuredProposal` declares ten keys. The class-member guidance says five. | Plan Complexity Tracking. Decision D-19. | The owner reviews the justification in the pull request. |
| A-9 | Low | The version 1 converter files hold no inline comment. The constitution requires one on each executable line. | Row 12. | Remediation R-1. Tasks T006 and T007 add comments to each touched block. |
| A-10 | Medium | A restart with a random portal secret clears every review. Issue #4636 owns the fallback decision. | Row 30. Decision D-15. | The owner decides the credential policy in issue #4636. This record marks the decision as human. |
| A-11 | Low | The browser test edits a shared test file. The edit stays inside the converter class and changes no shared fixture. | Row 24. Decision D-13. | The owner confirms the placement in the pull request. |
| A-12 | Medium | Issue #4224 plan states Python 3.13. The constitution requires Python 3.15 or newer. | Rows 40 and 70. | The owner of issue #4224 corrects the parent plan. |
| A-13 | Low | Issue #4224 names a unit test path that is absent on `main`. | Row 71. | The owner of issue #4224 corrects the path in the parent task list. |
| A-14 | Low | Open PR #4208 touches the shared portal files. This change touches neither file. | Research R2. | No action. The overlap check is clear. |
| A-15 | Medium | Issue #4641 depends on four open issues (#4637 to #4640) for the fields that the proposal consumes. | Issue #4641 prerequisites. Assumption A-1. | Tasks T006 and T007 wait for those merges. |
| A-16 | Medium | Full-parity T006 sets a 15-minute review lifetime. Version 2 must apply the same lifetime. | Row 78. Decision D-20. | FR-023 and test 19 enforce the lifetime. The full-parity owner confirms the value. |

### Defects in Existing Work

- A-4: Task IDs collide between issue #4224 and the full-parity map.
- A-9: Version 1 converter files lack inline comments.
- A-12: The parent plan states an outdated Python version.
- A-13: The parent task list names an absent test path.

### Defects in Related Draft Work

- A-1: Issue #4648 draft places two direct files in a full folder.
- A-2: Issue #4648 draft limits routes to an approved set that excludes this change.

## Coverage Summary

- All 23 functional requirements map to at least one task and one test or existing guard. The map is in `tasks.md`, section Requirement Traceability.
- FR-023 maps to test 19 and tasks T005 and T007. Decision D-20 records the 15-minute value.
- All 7 success criteria map to tasks or tests:
  - SC-001 maps to tests 1 to 21 and task T-LOCAL-GATES.
  - SC-002 maps to test 16.
  - SC-003 maps to tasks T001 and T008.
  - SC-004 maps to tests 9, 11, 13, and 14.
  - SC-005 maps to tests 7 and 17.
  - SC-006 maps to test 21.
  - SC-007 maps to task T012.
- Each user story has at least one independent test. User Story 4 uses the existing version 1 tests.

## Constrained-Field Coverage

| Directory or module | Now | After this change | Limit | Row |
| - | - | - | - | - |
| Converter root | 5 | 5 | 5 | 2 |
| Converter presentation folder | 2 | 3 | 5 | 3 |
| Converter integration test folder | 2 | 4 after issues #4636 and #4641 | 5 | 23 |
| `proposals/` test package | Absent | 3 | 5 | New |
| `tests/e2e/web_portal/` | 32 | 32 | 5 | 25 |
| `routes.py` top-level classes | 3 | 4 | 5 | 10 |
| `conversion.py` top-level classes | 1 | 2 | 5 | 17 |
| `models.py` top-level classes | 5 | Removed by issue #4636 | 5 | 13 |

## Unmapped Tasks

No task is unmapped. Each task names a requirement, a gate, or a delivery step.

## Constitution Alignment

- The plan's Constitution Check table lists each rule. Three rows are not passes now. Each has a stated remediation:
  - Structured logs: inherited from version 1. The owner decision stays in issue #4636 (item U-2).
  - Inline comments: version 1 debt. Tasks T006 and T007 add comments to each touched block.
  - Class members: `StructuredProposal` declares ten keys. Complexity Tracking records the justification (A-8).
- The export boundary holds. The constitution scopes `DataExporter` to API data (row 39), and FR-015 forbids the call.

## Metrics

- Requirements: 23 (FR-001 to FR-023).
- Success criteria: 7 (SC-001 to SC-007).
- User stories: 5.
- Tasks: 17.
- Test functions: 21. Parametrized cases do not count.
- Remote checks: 78. Seventy-six check GitHub `main`. Two check the local `.venv`.
- Decisions: 20. Human decisions: 1 (D-15).
- Findings: 16. High: 3. Medium: 8. Low: 5.

## Unresolved Items

- Item 1: The credential policy for the portal secret. Owner: issue #4636 (decision D-15, human).
- Item 2: Approval of the three version 2 routes in issue #4648 (A-2). Owner: coordinator.
- Item 3: Field outputs of issues #4637 to #4640 (A-1 and A-15). Owner: those issue owners.
- Item 4: README scope for the converter program (A-7). Owner: program owner.
- Item 5: Placement of the browser test (A-11). Owner: pull request reviewer.
- Item 6: Full-parity test path change (A-5). Owner: full-parity owner.
- Item 7: Confirmation of the 15-minute review lifetime (A-16). Owner: full-parity owner.

## Remediation Actions

- R-1: Add inline comments to each version 1 block that tasks T006 and T007 touch (finding A-9). Owner: the implementer of those tasks.
- R-2: Choose a compliant path before any new browser file enters `tests/e2e/web_portal/` (row 25). Owner: the program owner. This change adds no child to that folder.

## Convergence After Implementation

After tasks T001 to T013 finish, repeat these checks before T-LOCAL-GATES:

1. Read the blob SHAs of `routes.py`, `conversion.py`, `state/proposal.py`, `presentation/converter.html`, and `presentation/converter.js` on the branch.
2. Confirm that the blob SHA of each file changed only in the planned files.
3. Recount each row in the Constrained-Field Coverage table.
4. Replace each planned test name in `tasks.md` with the name that the test run prints.
5. Update the counts in `4641-STATUS.json` and in the summary.
