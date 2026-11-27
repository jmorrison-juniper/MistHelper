# Specification Analysis Report: Statistics Export Processed Count After Failed Fetch

## Findings

| ID | Severity | Finding | Evidence | Action |
| - | - | - | - | - |
| F-1 | High | The issue names menu 13 and menu 15 for two progress labels. The registry menu numbers for the same exports are 15 and 16. Menu 13 is the org device inventory summary. | RC-01, RC-04, RC-25 to RC-29 | Keep the labels (D-6). Record the mismatch for a follow-up issue. |
| F-2 | High | The reservations named in the issue are local claims. No open pull request touches the planned files. The issue names no remote branch for the reservation. | RC-72, RC-73, Unverified U-1 to U-3 | Hold publication until the release is recorded (D-5). |
| F-3 | Medium | The issue says PR #4358 reserves the old test paths. PR #4358 merged on 2026-11-13 and moved both files. The old paths are absent on main. | RC-35, RC-36 | Use the new path. The reserved-path statement in the issue is stale. |
| F-4 | Medium | The menu 13 stub returns nothing. Its count assertion passes only with the old behavior. | RC-33, RC-34 | Update the stub in T003 in the same commit as T002. |
| F-5 | Medium | Both statistics exports exceed the 25-line limit before the change. | RC-74 to RC-77, Complexity Tracking in `plan.md` | Record the debt. File a follow-up issue for the split. |
| F-6 | Medium | When the fetcher re-raises an exception, the progress start has no matching completion event. | RC-11 | Out of scope (D-8). Record a follow-up issue. |
| F-7 | Low | The missing endpoint document lists `searchOrgPeerPathStats`, which menu 16 calls. | RC-60, RC-28 | Record a documentation follow-up. This change does not edit the document. |
| F-8 | Low | Mock return values are truthy. The old exporter tests keep processed count 1 without any change. | RC-31, RC-32 | No edit to the reserved file. The new tests use the real fetcher. |
| F-9 | Low | The HTTP 429 path writes no partial rows. The rate-limit branch needs rows, and the pagination call raises before it assigns them. The count 0 matches the disk state. | RC-14, RC-16 | No action. |
| F-10 | Low | The fetcher forwards keyword arguments from the exporter into the SDK call. This pattern predates the change. | RC-17 | No action in this change. Record for a separate review. |
| F-11 | Low | Other exporters emit a literal processed count as well. | Unverified U-5 | Out of scope. Verify and record in a follow-up issue. |

## Coverage Summary

| Requirement | Tasks | Tests or checks |
| - | - | - |
| FR-001 | T002 | Tests 4 and 6 |
| FR-002 | T002 | Tests 1, 2, 3, and 5 |
| FR-003 | T002 | Tests 5 and 6 |
| FR-004 | T002 | Tests 4 and 6, each with one completion call |
| FR-005 | T002 | Tests 1 and 5, which assert labels "13" and "15" |
| FR-006 | T005 | Existing `tests\unit\api\test_api_data_fetcher.py` (unchanged file, run in T-LOCAL-GATES) |
| FR-007 | T002 | Existing cache-hit test `test_cache_hit_returns_early` (`tests\unit\export\test_org_device_stats_exporter.py`, line 230) |
| FR-008 | T002 | Test 4 asserts the DEBUG record. The inline comments are checked at T-PR. |
| FR-009 | T001 | Tests 1 to 6 |
| FR-010 | T003 | `test_emits_start_and_complete` in `tests\unit\prod_readiness\standalone\operations\exporting\inventory\test_menu_13_device_stats.py` |
| FR-011 | T004 | `tests\guardrails\test_changelog_fragment_policy.py` |
| C-1 to C-5 | T-PR, T-LOCAL-GATES, and the coordination checklist | Checklist items in `design\checklists\coordination.md` |

## Constrained-Field Coverage

- The processed count takes only the values 0 and 1. Tests 1 to 6 check both values.
- The progress labels are "13" and "15". Tests 1 and 5 check the label values.
- The test quality rule requires HTTP 4xx and HTTP 5xx tests (RC-45). Test 1 and test 5 cover HTTP 403. Test 2 covers HTTP 503. No test uses a bare `assert result`.

## Constitution Alignment

- Principle I: The change adds no direct child to a noncompliant parent (RC-50). The two methods exceed 25 lines before the change (F-5). The debt has a remediation action.
- Principle I unique-record exception: The fragment and this record are unique records for this change.
- Principle VI and Principle VII: Each touched line has an inline comment, and the debug log follows the fetch (FR-008).

## Unmapped Tasks

None. Each task maps to a requirement, a coordination constraint, or a gate:

- T001 to T005 map to FR-001 to FR-011.
- T-LOCAL-GATES maps to SC-005 and C-5.
- T-PR maps to C-2, C-3, and FR-011.
- T-REMOTE-CI maps to SC-005.
- T-MERGE maps to Principle IV and C-3.

## Metrics

- Functional requirements: 11
- Coordination constraints: 5
- Tasks: 9
- New tests: 6. Updated tests: 1.
- Remote checks: 86 (see `design\research.md`)
- Decisions: 8. Human decisions: 0.
- Unverified items: 8 (see `design\research.md`)

## Unresolved Items

1. The #1794 owner must record a release of `org_device_stats_exporter.py`. T-PR cannot start until the release is recorded.
2. The branch of the #2711 owner's commit `57c99870` is unknown (Unverified U-3). The branch does not change this change.
3. Follow-up issue: the label mismatch between progress labels and registry menu numbers (F-1).
4. Follow-up issue: the 25-line split of both methods (F-5).
5. Follow-up issue: the completion event after a re-raised exception (F-6).
6. Follow-up issue: the missing endpoint document entry (F-7).
7. Follow-up issue after verification: the other exporters that emit a literal processed count (F-11).

## Convergence After Implementation

- Run `quickstart.md` Scenario 1 before the fix. Five tests must fail and one must pass.
- Run `quickstart.md` Scenario 2 after the fix. All six tests must pass.
- Run the symbol check (T005) after each edit to the exporter file. The check must report no module-level name changed.
