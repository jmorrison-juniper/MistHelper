# Specification Analysis Report: Firmware Monitor Treats Failed Stats Pages as Failed Checks

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| A-01 | High | The stats fetch ignores the HTTP status of each page. An HTTP 403 or 503 first page becomes an empty list. The monitor then reports completion. | `firmware_manager.py` lines 637 to 647 (research RC-44). SDK `get_all` lines 39 and 56 to 74 (RC-57). | Fixed by FR-002, FR-003, FR-005, and tasks T011 and T015. |
| A-02 | High | The regression tests that the issue comments describe are not on `main`. The comment of 2026-11-09 says that the test file is local and uncommitted. The file is on `main` with blob `a1352b35`, and it holds no HTTP 403 test (RC-47, RC-48). | The git history lists five commits for the file. The newest is `025ef82ee`. The remote tree and the local index hold the same blob. | Tasks T002 to T009 write the tests. Tests N1 and N2 fail before the change. |
| A-03 | Medium | Coordination with issue #4709 is not evidenced on GitHub. Issue #4709 is open and labeled `in-progress`. Its comment dated 2026-11-09T14:55:03Z names a different owner for its file. | Comments on issue #4709. | Unresolved. This record adds no shared code, so the agreement needed is the file reservation. The orchestrator confirms it before T-PR. This item blocks T-PR only. |
| A-04 | High | The same defect class exists in other flows. The sibling exporter at `site_other_device_events_exporter.py` line 76 and five more `get_all` call sites in `firmware_manager.py` do not check status. | RC-46 and RC-53. The call sites are at lines 3505, 3526, 4055, 4108, and 4164. | Out of scope. Follow-up F-02. |
| A-05 | High | The site branch may not receive firmware update data. The site call passes no `fields` argument. The installed `listSiteDevicesStats` has no `fields` parameter. The OpenAPI describes `fields` as additional fields. If the default site rows lack `fwupdate`, the site branch counts zero active upgrades and reports completion. | RC-61, RC-21, OpenAPI lines 59673 to 59675, and `firmware_manager.py` line 640. | Unverified (research item U-01). Out of scope for this change. Follow-up F-03 runs a read-only check with the owner approval. The human reviewer must read this item. |
| A-06 | Medium | The mistapi pin text disagrees across files. `copilot-instructions.md` line 21 says `>=0.64.0,<0.65`. `pyproject.toml` line 29 says `>=0.64.1,<0.65`. `requirements.txt` line 129 says `==0.64.1`. `constitution.md` line 279 says `0.59+`. | RC-28, RC-29, and research R-10. | Out of scope. The installed 0.64.1 satisfies every statement. Follow-up F-04. |
| A-07 | Medium | `_response_status_code` defaults a missing status to 200 (`firmware_manager.py` lines 73 to 76). Issue #2753 owns the audit of this default. | RC-37. | The monitor does not use the helper (decision D-2). The helper stays unchanged. |
| A-08 | Medium | The five-item rule has no compliant place for the new code. The module and the test module are grandfathered. | Plan, Five-Item Record, and Complexity Tracking. Directory counts are in research item R-06. | Accepted as recorded debt. Remediation R-01 is separate. |
| A-09 | Low | The exit code of continuous monitoring does not reach the menu. `_dispatch_status_scope` drops it (lines 367 to 369), and menu 137 returns no value (`MistHelper.py` lines 5194 to 5196). | RC-32 and RC-25. | The spec states that the operator sees console text only. No change. |
| A-10 | Low | The constitution limit "Max 5 operations per statement block" (`constitution.md` line 83) can count statements or operators. The loop body in task T011 holds six statements. | Plan, Implementation Outline. | Unresolved. The reviewer decides the reading. The method keeps five logical blocks. |
| A-11 | Medium | No live check ran. The issue reproduction used synthetic responses, and the brief forbids live Mist calls. The behavior of `X-Page-Total` and of an empty HTTP 503 body comes from SDK code and synthetic tests only. | Research items U-02 and U-03. | Unverified. The tests use the SDK response classes. The human reviewer decides whether a read-only check is required. |
| A-12 | Info | The `needs-human-review` label stays. The issue requires human review. | Issue labels. | Task T-MERGE and decision D-8. |
| A-13 | Info | A search of pull requests for `4710` returns no result. | `gh pr list --search 4710` returned an empty list. | No linked pull request exists. The record starts a new branch. |
| A-14 | Info | Issue #1910 is closed. Its retry fix is on `main` at lines 52 to 58 and 144 to 186. The baseline commit `3964d21d` is an ancestor of `main`. | RC-02, RC-35, and RC-38. | Consistent with the issue. No change. |

## Coverage Summary

All 12 requirements map to at least one task and at least one test. The traceability table is in `tasks.md`. The table has these results:

- FR-001 to FR-012: each requirement has a task and a test.
- Gate tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover FR-001 to FR-012 as release steps.

## Constitution Alignment

- Principle I, five-item rule: pass with recorded debt (finding A-08).
- Principle III, safety: pass. No confirmation rule changes, and the failure text holds no secret (test N12).
- Principles VI and VII, inline comments and action logging: pass by plan (task T014 and FR-012).
- Mistapi-only rule: pass. The calls use mistapi methods only.

## Unmapped Tasks

None. Every task maps to at least one requirement.

## Metrics

- Requirements: 12.
- Success criteria: 6.
- Tasks: 21.
- New tests: 14.
- Updated tests: 2.
- Remote checks: 61.
- Decisions: 9, with 0 human decisions.
- Unverified items: 4.
- Findings: 14, with 4 High, 5 Medium, 2 Low, and 3 Info.

## Unresolved Items

- U-A (finding A-03): confirm the file reservation with the owner of issue #4709 before T-PR.
- U-B (finding A-05): confirm the site field set before any site-scope claim. Follow-up F-03 covers it.
- U-C (finding A-10): the reviewer decides how to count statements in a block.
- U-D (finding A-11): a read-only live check may confirm the `X-Page-Total` meaning and the empty HTTP 503 behavior.
- U-E (finding A-12): a human completes the review before any merge.

## Follow-Up Issues (not in this pull request)

- F-01: Move the stats page walk into a compliant nested package (remediation R-01).
- F-02: Audit the `get_all` call sites in `firmware_manager.py` (lines 3505, 3526, 4055, 4108, and 4164) and the exporter for issue #4709. Coordinate with #4709.
- F-03: Verify the site stats field set, including `fwupdate`, with one read-only sample approved by the owner.
- F-04: Align the mistapi pin text in `copilot-instructions.md` line 21, `constitution.md` line 279, `pyproject.toml` line 29, and `requirements.txt` line 129.

## Convergence After Implementation

After T-LOCAL-GATES passes, the expected state is:

- Tests N1 to N14 and U1 to U2 pass, and tests N1 to N8, N11, N12, and N13 failed before the change.
- The symbol gate reports `no module-level name changed`.
- The complexity gate reports no block above cyclomatic complexity 10.
- Findings A-01 and A-02 are closed. Findings A-03, A-05, A-10, A-11, and A-12 stay open with the reviewer until the human review completes.
