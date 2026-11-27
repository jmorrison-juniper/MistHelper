# Specification Analysis Report: Offline Dynamic JVD Labs Preview

This report checks the spec, the plan, and the tasks against each other and against the remote code. It names each defect in existing work. It lists each unresolved item.

## Findings

| ID | Severity | Location | Finding | Action |
| - | - | - | - | - |
| F-1 | HIGH | Task brief, route, issue text | The brief says this issue belongs to the Cisco config converter program. The issue text names no converter component. The route `0/0/1/2/2/0` covers issue numbers 4625 to 4649 by arithmetic (base-5 digits). The route is numeric, not a program group. | Keep the Labs scope. Use the cluster hint "dynamic jvd labs preview". Take shared-file rules from record 4648 (L-11). |
| F-2 | HIGH | PR 4208 | PR 4208 is open and draft. It changes `web_portal/app.py` and `web_portal/templates/base.html` (R-11). Comment 6962287494 names the same block. | T013 and T014 wait for the shared-file handover (D-4). No task edits either file before it. |
| F-3 | HIGH | `tests/e2e` | The copilot rule places web UI tests under `tests/e2e/` (R-42). That folder holds five children (R-29), and guard R-57 forbids more. | D-3 places tests under `tests/integration/web_portal/labs/`. Record 4648 D-4 uses the same pattern (L-11). RA-1 tracks the conflict. |
| F-4 | MEDIUM | `.github/workflows/ci.yml` | The E2E shards run three `tests/e2e` paths (`ci.yml` lines 794 to 798). R-35 cites the web-portal shard. The root shard runs `tests/integration` (R-34). Chromium installs in the E2E job (R-36). The root shard steps after line 310 are not read. | The browser module runs on a developer machine (D-19). The root-shard browser state is unverified (U-9). RA-1 tracks the gap. |
| F-5 | MEDIUM | Local checkout | Local `AGENTS.md` has 265 lines. The remote Specifications section starts at line 345 (R-53). Local `copilot-instructions.md` has 473 lines. Remote "Pull request titles" starts at line 501 (R-44). Local constitution has 462 lines. Remote PR checklist starts at line 516 (R-50). | This record cites remote lines only (L-9). The orchestrator should refresh the local checkout before implementation. |
| F-6 | MEDIUM | Planner framework | The `vmm_topology` package is not in the local `.venv` (L-7). Issue #4504 names the framework. The `plan` call is unknown to this record. | D-15 isolates the call. U-1 records the gap. K-2 covers the risk. |
| F-7 | MEDIUM | Recovered branch | The recovered branch and its tags have no GitHub copy (R-05 to R-10). The owner reports 36 passes and one skip (comment 6961775907). This record does not verify that result (U-2). | D-23. Implementation starts from `main`. |
| F-8 | LOW | Logging | Principle V names structlog or an equivalent (R-46). `web_portal` logs with the stdlib logger (R-17). Record 4636 asks the owner to confirm the stdlib convention (L-13). | D-18 adopts the stdlib convention. U-8 keeps the owner check open. |
| F-9 | LOW | STE gate | The copilot gates table lists fixed Markdown files for the STE gate (R-41). AGENTS requires each Markdown file to pass (R-51). | T-LOCAL-GATES runs `ste-linter` on each changed Markdown file, including the record files. |
| F-10 | LOW | Blueprint precondition | The precondition checks `"csrf" in app.extensions`. Flask-WTF sets that key in `init_app` (L-2). | D-7 keeps the check at registration, not at request time. |
| F-11 | INFO | Record 4822 | Record 4822 plans `specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/` and `src/interfaces/labs/` (L-10). | Consistent. D-1 and D-2 keep both paths. |
| F-12 | INFO | Records 4636 to 4648 | These records share the CSRF answer (4648 D-6), the browser folder (4648 D-4), the handover gate (4648 D-3), and the folder debt (4636 R-2 and R-3, 4646 R-2 and R-3). | Consistent. D-3, D-4, D-8, RA-1, RA-2, and RA-3 follow them. |
| F-13 | INFO | Issue #4504 | The 4504 planning spec exists on main (R-64). Its guard test requires unchecked tasks. The issue body says this issue is separate from 4504. | No conflict. This record adds no task to 4504. |
| F-14 | LOW | Tasks T-PR, T-REMOTE-CI, T-MERGE | The local gates table has no row for pull requests, CI watching, or merges. These tasks verify with the GitHub commands named in the Pull request and Merge sections of AGENTS.md. | Keep the GitHub commands as the verification. The orchestrator reviews the result. |

## Coverage Summary

Each requirement maps to at least one task and at least one test. Test identifiers appear in `tasks.md`.

| Requirement | Tasks | Tests or checks |
| - | - | - |
| FR-001 Labs page route | T011, T013 | TR-03, TB-01 |
| FR-002 Capability route as JSON | T011 | TR-01 |
| FR-003 Authority fields disabled | T011 | TR-01 |
| FR-004 Capability status on page | T010, T011 | TR-03 |
| FR-005 Server example on page | T010, T011 | TR-03 |
| FR-006 Form carries `csrf_token` | T010, T011 | TR-04 |
| FR-007 Shared CSRF answer | T011 | TR-05, TR-06 |
| FR-008 Exactly one run name field | T008, T011 | TR-07 |
| FR-009 Extra and repeated fields rejected | T008, T011 | TR-08, TR-09 |
| FR-010 Run-name pattern enforced | T008, T011 | TU-01, TU-02, TR-10 |
| FR-011 Planner receives server example only | T009, T011 | TU-11 |
| FR-012 Only devices, links, fingerprint shown | T009, T011 | TU-03, TU-06, TR-07 |
| FR-013 Fingerprint definition | T009 | TU-07, TU-08 |
| FR-014 Unavailable when absent or failed | T009, T011 | TU-09, TU-10, TR-11 |
| FR-015 Unexpected key gives unavailable | T009 | TU-04 |
| FR-016 Authority key gives unavailable | T009 | TU-05 |
| FR-017 No private import at load | T009 | TU-12 |
| FR-018 Synthetic fixtures and stubs only | T003, T004, T005 | TU-11, TU-12 |
| FR-019 Three routes only | T011 | TR-12 |
| FR-020 No Mist or provider call | T009 | TU-13, TR-12 |
| FR-021 Stable `data-testid` values | T010, T011 | TR-04, TB-01 |
| FR-022 ASCII logs, no raw values | T009 | TU-14 |
| FR-023 Handover gate for shared files | T013, T014 | TR-03 and TB-01 after registration, diff review in T-PR |
| FR-024 Changelog fragment and operator row | T012, T015 | `test_changelog_fragment_policy.py`, `test_markdown_links.py` |
| FR-025 Five children per directory | T002, T007, T011 | `test_nested_package_structure.py`, `test_src_domain_structure.py`, `test_e2e_package_structure.py` |
| FR-026 Plain page copy | T010 | TR-03 checks plain status words. Review item UI-01 in `design/checklists/ui.md`. |

## Test Inventory

| Identifier | Module | Count |
| - | - | - |
| TR-01 to TR-12 | `test_labs_routes.py` | 12 |
| TU-01 to TU-14 | `test_labs_units.py` | 14 |
| TB-01 to TB-03 | `test_labs_browser.py` | 3 |

## Unmapped Tasks

None. T001 maps to FR-023 as a process task. Each final task maps to every requirement it delivers.

## Metrics

- Requirements: 26 (FR-001 to FR-026).
- Success criteria: 7 (SC-001 to SC-007).
- Tasks: 19 (T001 to T015 and four final tasks).
- Tests planned: 29.
- Decisions: 24, of which 2 are human decisions.
- Remote checks: 82. The same count appears in `STATUS.json` and in `design/research.md`.
- Local reads: 17 (L-1 to L-17).
- Unverified items: 13 (U-1 to U-13).
- Risks: 7 (K-1 to K-7).
- Remediation actions: 3 (RA-1 to RA-3).

## Constitution Alignment

See `plan.md`, section "Constitution Check". No rule fails. Two rules pass with an open owner check: the structlog rule (U-8) and the shared-file handover (D-4).

## Unresolved Items

- HD-1 (D-16): The licensing and delivery of the private framework needs a human answer.
- HD-2 (D-17): The order of the shared-file handover needs a human answer.
- Shared-file handover: Not granted. The status comes from record 4648 (U-6).
- U-1: The `vmm_topology` API is unknown to this record.
- U-8: The owner confirms the stdlib logging convention.
- U-9: The root-shard job steps after line 310 of `ci.yml` are unread.
- RA-1 to RA-3: Folder debt needs separate issues.
