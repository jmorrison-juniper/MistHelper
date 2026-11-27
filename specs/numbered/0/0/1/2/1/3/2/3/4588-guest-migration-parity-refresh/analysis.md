# Specification Analysis Report

**Date**: 2026-11-26
**Scope**: Refresh of the guest migration parity planning for #4588. Context issues: #4231 and #4278. Shared-file owner: PR 4208.
**Inputs**: [spec](spec.md), [plan](plan.md), [tasks](tasks.md), [research](design/research.md), and the contracts in `design/contracts/`.

This report checks consistency across the planning artifacts and the remote evidence. It changes no product behavior and no constitution rule. Implementation stays blocked by the gates in the [decision register](design/research.md#7-decision-register).

## Findings

| ID | Category | Severity | Location | Finding and required action |
| --- | --- | --- | --- | --- |
| F01 | Evidence | HIGH | Legacy spec, research, and analysis. R11. | The legacy record says issue #4278 is closed. GitHub reports it open, updated 2026-11-08. Action: this record uses GitHub state. The owner reconciles the comment and the state (D-2). |
| F02 | Pin | MEDIUM | Legacy research. R13, R50, R51. | The legacy record pins the target at 772fc927. Main is 117 commits ahead. Compose and requirements changed. Action: re-pin to `f03c6c9b` (D-4). |
| F03 | Record | MEDIUM | `specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity/` | The legacy folder remains at the same route. This refresh supersedes it for planning. Action: keep the legacy folder unchanged (D-1). The owner decides whether to retire it. |
| F04 | Citation | LOW | Legacy research S16 and S18 | The legacy LICENSE citation L1 to L26 and the development Compose citation L1 to L16 are wrong. The files have 39 and 17 lines. Action: corrected in research S04 and S07. |
| F05 | Stack | MEDIUM | Legacy plan, Technical Context | The legacy plan states Python 3.13 for the target. The repository requires Python 3.15 (T17 L20). Action: the plan states 3.15. |
| F06 | Inventory | MEDIUM | Legacy parity note | The legacy record says only P063 is existing guest functionality. Menu 200 is an existing per-site guest CSV export (T06 L118). Action: row P073 records it as existing adjacent. |
| F07 | API | HIGH | Source UI and schema. P027, P028. | The source allows 2628000 minutes. The checked schema allows 259200 at most (T11). Action: D-7. |
| F08 | API | HIGH | Source guide. P028. | The source guide promises up to five years (S09 L27). Action: D-7 applies, and T036 corrects the operator guide. |
| F09 | API | HIGH | Source code and guide. P037. | The source revokes with PUT and `minutes` set to 0 (S02 L649 to L652). The guide says DELETE does not remove the guest (S09 L238). Action: D-8 keeps revoke unavailable until verified. |
| F10 | API | HIGH | Source payloads. P023, P035. | The source sends `name` (S03 L1639) and `wlan_id` (S02 L558). The schema marks both read-only (T11). Action: D-9 removes them from writes. |
| F11 | Data | MEDIUM | Source CSV. P046. | The source defaults invalid row minutes to 1440 (S03 L1409). Action: D-11 rejects the row. |
| F12 | Process | MEDIUM | Owner comment of 2026-11-08 and the orchestrator brief | The owner asks to keep #4588 open for review. The orchestrator requires the closing keyword in the PR body. A merge closes the issue. Action: T-PR keeps the keyword as the orchestrator requires. The orchestrator confirms owner acceptance before T-MERGE. Open item. |
| F13 | Governance | MEDIUM | Constitution L279 and repository instructions L20 | The constitution states mistapi 0.59 or newer. The repository instructions require mistapi 0.64. The requirements file pins 0.64.1 (T10 L129). Action: the plan uses 0.64.1. The owner aligns the constitution text in a separate change. |
| F14 | Governance | MEDIUM | Constitution L315 to L316. U07. | The constitution names a declared operational store. No document in the checked tree names it. Action: D-12 selects the SQLite store. The owner names the declared store. |
| F15 | Metric | LOW | Legacy analysis | The legacy analysis reports 42 of 42 requirements. The spec defines 35 requirements. Action: this record reports 35. |
| F16 | Evidence | HIGH | Visual parity. Research U02 and U03. | No source or target screenshot was captured in this run. Action: visual parity stays UNVERIFIED. T034 holds the paired captures. |
| F17 | Process | HIGH | Local gates. Research U13. | The STE, citation, link, and task-audit gates did not run. The brief forbids repository scripts. Action: T-LOCAL-GATES stays open. |
| F18 | Ownership | MEDIUM | PR 4208. R08. | PR 4208 is open. It changes `web_portal/app.py` and `web_portal/templates/base.html`. Action: D-4 and T007 block shared edits until handover. |
| F19 | Source | MEDIUM | Source `field4`. P025. | The source sets `field4` from the API token name (S02 L550 to L552). The token name is not an operator identity. Action: P025 is an intentional deviation. D-6 defines the identity model. |
| F20 | Privacy | LOW | Source LICENSE. S04 L3. | The source copyright line includes a contact address. This record cites line 3 but does not repeat the address. |
| F21 | Context | LOW | Request for records 4231 and 4278 | The spec-drafts folder holds no 4231 or 4278 record. Repository search found record 4231 on main (R27, R28). Repository search found no record 4278. Action: this record uses record 4231 for context. |
| F22 | Evidence | MEDIUM | Legacy ledger L34 to L40 | Seven legacy claims are absent from this run. They concern pyproject, official pages, session screenshots, validation results, PR 4290 files, and upstream mistapi. Action: each stays on the research unverified list. |
| F23 | Target | LOW | Projection docstring. T01 L6. | The projection docstring says write workflows wait for license, access, and API approvals. Action: update the wording when D-5 and D-6 close. |
| F24 | Source | LOW | Source failed reads. P060. | A failed guest read writes to the console and shows the empty state (S03 L1122 to L1125 and L666). Action: P060 is an intentional deviation. |
| F25 | Scope | LOW | Source menus and operator guide | Menu 284 tests a guest portal SMS provider (T23 L72 to L73). Action: it stays outside this migration and is not in the inventory. |

## Coverage summary

Each functional requirement maps to at least one task and at least one test family. The coverage table is in [tasks](tasks.md#requirement-coverage).

| Success criterion | Task IDs | Acceptance |
| --- | --- | --- |
| SC-001 | T001, T037, T038 | TEST-030 accounts for each inventory row and its disposition. |
| SC-002 | T002, T018, T024, T028, T033 | TEST-020, TEST-021, and TEST-022 prove zero writes for invalid submissions. |
| SC-003 | T025, T026, T028 | TEST-016, TEST-018, and TEST-019 account for each CSV row. |
| SC-004 | T006, T032, T034, T038 | TEST-027 and TEST-028 require approved visual differences. |
| SC-005 | T013, T024, T029, T030 | TEST-005, TEST-006, TEST-023, and TEST-029 keep unknown values and truthful outcomes. |
| SC-006 | T008, T031, T035 | TEST-025, TEST-026, and TEST-035 keep one application and the existing stores. |
| SC-007 | T001, T035, T037 | TEST-030 maps the remaining requirements before implementation. |

No task lacks a requirement or an acceptance purpose. Each task names a primary destination and its prerequisites.

## Constitution alignment

- The feature root holds five children. The design directory holds five children. The contracts directory holds five files. The checklists directory holds two files.
- The route uses the base-5 radix of 4588 (T19 L4). The route parent holds two children after this record.
- The plan records the existing folder debt and a separate remediation action (plan, Complexity Tracking).
- The future code uses named classes and direct imports from the defining module (T18 L91 to L112).
- The future writes need validated input, exact scope, approved access, a typed word, durable intent, and no ambiguous retry (T18 L113 to L141).
- The planning PR changes Markdown only. Steps 10 to 12 of principle IV do not run for this change (T17 L473).

## Metrics

| Measure | Result |
| --- | --- |
| Functional requirements | 35 |
| Success criteria | 7 |
| User stories | 5 |
| Tasks | 44: 40 migration tasks and 4 planning tasks |
| Migration task status | 0 verified-present, 9 partial (T001, T003, T004, T005, T006, T008, T009, T013, T037), and 31 open or absent |
| Test families | 35 |
| Paired visual families | 15 |
| Inventory rows | 73: 1 existing, 1 existing adjacent, 39 missing, 19 intentional deviations, and 13 decision required |
| Remote checks | 71 |
| Legacy ledger | 40: 26 verified, 7 stale, and 7 absent |
| Decisions | 15: 2 require a human decision (D-5 and D-6) |
| Open items | F12 (closing keyword), F17 (local gates), and F16 (visual evidence) |

Each count in this table reads from the tasks file, the parity inventory, the research ledger, and the decision register.

## Unresolved items

- HUMAN-DECISION-REQUIRED (D-5): confirm the noncommercial reading and approve the attribution text.
- HUMAN-DECISION-REQUIRED (D-6): approve the operator identity and role model for writes.
- F12: the owner and the orchestrator decide whether the planning PR may close #4588 at merge.
- F17: the local gates are not run. T-LOCAL-GATES runs them.
- F16: visual parity needs captures. T034 holds the captures.
- F14: the owner names the declared operational store.

## Next actions

1. Run T-LOCAL-GATES on the record files and the changelog fragment.
2. Create the planning branch and commit the files. Open one pull request with the body that the orchestrator requires.
3. Watch the remote checks with T-REMOTE-CI.
4. Wait for owner and orchestrator authorization before T-MERGE.
5. Keep issues #4231 and #4278 open. Keep the implementation paused until D-5 and D-6 close.
