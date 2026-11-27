# Specification Analysis Report: SSR optic and Mist cloud path lab tests

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, the contracts, the checklists, and the remote code on main at head f03c6c9b36d612a48d7b9652998c2fd87dd777ca.

**Method**: A read-only pass compared the issue thread, the merged pull requests, the remote tree, and the remote blobs. The pass recorded each defect and each unresolved item below. No gate or test ran.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A1 | Stale thread | LOW | Issue #3960 comments of 2026-10-07 | The comments call pull request #4114 a draft. Pull request #4114 merged on 2026-10-10. | This record uses the merged state (C-29, C-65). See D-1. |
| A2 | Stale coordination | LOW | Issue #3960 body, first read-first step | The body asks for a comment on #3959. Issue #3959 closed on 2026-10-21. | The claim comment goes on #3960. See D-5. |
| A3 | Lapsed ownership | LOW | Issue #3960 body, read-first step 4 | The body says pull request #3953 owns scripts/verify_ssr_commands.py. Pull request #3953 merged on 2026-10-06. | The verifier stays unchanged. See D-4 and FR-008. |
| A4 | Claim mismatch | MEDIUM | Issue #3960 body, verifier note | The body says the verifier reports Junos commands in GW_PORT_DOWN.md and _shared_common.md. The main block reads only the console health check runbook (C-22). | Treat the claim as unsupported. Open a separate issue (U-4). |
| A5 | Claim mismatch | LOW | Issue #3960 body, verifier note | The body says the verifier reads text after each code fence. The code removes fenced blocks (C-20). | Record the code behavior. Make no change here. |
| A6 | Detection gap | MEDIUM | scripts/verify_ssr_commands.py, lines 58 to 61 (C-21) | A parent command match passes a command with an invalid subcommand. The verifier cannot prove H-1 or H-2. | Use the lab outputs as proof. Open a separate issue (U-4). |
| A7 | Missing input | MEDIUM | documentation/references/ssr/cli_reference.md (C-23, C-24, C-26) | Git ignores the verifier input. The file is absent from main. A clean checkout cannot run the verifier. | The verifier is not a gate for this change. Open a separate issue (U-4). |
| A8 | Naming mismatch | MEDIUM | Runbook lines 104 and 125 (C-02, C-69). Skill file 02-ports.md, lines 10 and 11 | The runbook uses names such as xe-0-1. The local hardware reference names the 10GbE SFP+ ports 0/0 to 0/3 on SSR1300 and SSR1400. | H-3 records the device port names (T006). See U-2. |
| A9 | Unsourced claim | MEDIUM | Runbook line 149 (C-06) | The 2026-10-05 observation has no source in the repository or the issue. | H-7 (T010) and FR-017. See U-1. |
| A10 | Coverage gap | LOW | Runbook rows 360 to 365 (C-17). Runbook lines 123, 125, and 153 (C-07, C-69) | Six statements have rows. Other vendor-sourced statements have no row. | D-6. See U-3. |
| A11 | Rule conflict | LOW | Runbook lines 367 to 370 (C-18) and the issue text for H-2 | The runbook rule names step C2 for row 361. The issue names the section 11 table for H-2. | D-7 follows the issue for H-2 only. |
| A12 | Unverifiable source | MEDIUM | Runbook section 14 rows and links (C-13, C-14, C-15) | The vendor hosts return a blocked address in this run. The release note claim for item I95-44742 has no check. | See U-5. H-2 and H-4 test the release note claim. H-6 tests the Testing Tools claim. |
| A13 | Public repository | LOW | copilot-instructions.md, line 478 (C-39) | The repository is public. A committed address stays public. | Warning in T012 and the sanitization checklist. |
| A14 | Workflow scope | LOW | copilot-instructions.md, line 473 (C-38) | The container build runs only for a push that changes a product file. | The plan records no container build for this change. |
| A15 | Local and remote agreement | LOW | Local HEAD, blob hash checks, and a local search of specs | The local HEAD equals remote main head f03c6c9b. Local blob hashes equal remote shas for each checked file. No local 3960 record exists. | No conflict. Remote evidence governs. |
| A16 | Skill scope | LOW | Local skill juniper-hw-ssr1000, SKILL.md answer rule 3 | Optic qualification belongs to juniper-optical-transceivers. This run did not load that skill. | The optic claims stay unverified. See U-7. |
| A17 | Historical counts | LOW | Issue #3960 body, check counts for pull request #3951 | The body reports 33 passed checks and 7 skipped checks. This run did not query those checks. Pull request #4114 reports 34 successful, 10 skipped, 1 cancelled, and 0 failed check runs. | Record the counts as sources only. |

## Requirement and Success Criteria Coverage

| Requirement | Tasks | Tests | Notes |
|-------------|-------|-------|-------|
| FR-001 | T003 to T011 | TEST-08 to TEST-14 | Owner-only steps. |
| FR-002 | T003 | TEST-06 | Credential word scan. |
| FR-003 | T012 | TEST-08 to TEST-13 | Targets follow the lab output contract. |
| FR-004 | T012 | TEST-06 | Sanitization scan. |
| FR-005 | T013 | TEST-07 | Release string in each cell. |
| FR-006 | T001, T013 | TEST-07 | No second table. |
| FR-007 | T-PR, T-MERGE | TEST-17 | Closing keyword. |
| FR-008 | T-LOCAL-GATES | TEST-06 | Changed path list. |
| FR-009 | T-LOCAL-GATES | TEST-06 | Changed path list. |
| FR-010 | T-LOCAL-GATES | TEST-01, TEST-02 | STE gate. |
| FR-011 | T-LOCAL-GATES | TEST-03, TEST-04 | Link check. |
| FR-012 | T009 | TEST-13 | Typed confirmation. |
| FR-013 | T002 | TEST-17 | Claim and overlap check. |
| FR-014 | T014 | TEST-02, TEST-05 | Fragment name rule. |
| FR-015 | T001 | TEST-18 | Unverified list in design/research.md. |
| FR-016 | T012, T013 | TEST-07 | No result without output. |
| FR-017 | T010 | TEST-14 | Source or removal. |
| FR-018 | T011 | TEST-19 | Clean status and branch comparison. |
| SC-001 | T004 to T009 | TEST-08 to TEST-13 | Six outputs. |
| SC-002 | T013 | TEST-07 | Zero Not run cells. |
| SC-003 | T-LOCAL-GATES | TEST-01, TEST-02 | STE scores. |
| SC-004 | T-LOCAL-GATES | TEST-06 | Verifier files unchanged. |
| SC-005 | T-PR, T-MERGE | TEST-17 | Closing keyword rule. |
| SC-006 | T-REMOTE-CI | TEST-15 | Required checks. |

## Unresolved Items

| ID | Item | Owner of the next step | Next step |
|----|------|------------------------|-----------|
| U-1 | The 2026-10-05 observation at runbook line 149 has no source. | Owner | H-7 (T010). |
| U-2 | The runbook port names (xe-0-x) differ from the local hardware reference names (0/x). | Owner | H-3 records the names that the device prints (T006). |
| U-3 | Vendor-sourced statements at lines 123, 125, and 153 have no lab row. | Owner | Decide on a separate issue (D-6). |
| U-4 | Verifier defects A4 to A7 need evidence and a fix. | Owner | Open a separate issue. This issue keeps the verifier unchanged (D-4). |
| U-5 | Vendor sources in section 14 (lines 339 to 345) and the Testing Tools sentence (line 166) were not fetched in this run. | Owner or a later run with vendor access | Confirm each source. H-2 and H-4 test the release note claim (C-15). H-6 tests the Testing Tools claim (C-08). |
| U-6 | The command `show device-interface name <name> extended-statistics` (line 246) has no lab test. | Owner | Decide whether to add a lab test. `show mist detail` is covered by H-5. |
| U-7 | The optic qualification claim for part 740-021309 (line 125) belongs to juniper-optical-transceivers. | Later run | Load that skill and check the claim. |

## Remote Consistency

- The remote check count is 69. The rows in design/research.md, the `remote_checks` array in STATUS.json, and the count in summary.md match this value (TEST-18).
- The record path in STATUS.json equals the route in plan.md and the slug in spec.md.
- The task count is 18 in tasks.md, STATUS.json, and summary.md. The requirement count is 18 in spec.md and STATUS.json. The test count is 19 in quickstart.md, tasks.md, and STATUS.json. The decision count is 8 in research.md, STATUS.json, and summary.md.
