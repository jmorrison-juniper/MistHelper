# Specification Analysis Report: Reviewed Restore and Partial-Operation Recovery

## Result

The record covers the restore and recovery scope of issue 4646 and parity tasks T027 and T028. Each functional requirement maps to at least one task and one test. Each success criterion maps to at least one test or guard.

The record has no code change. It is an offline design. Two open gates block implementation: the layout revision R-4636-1 in issue 4636, and the operator identity decision D-14. Two decisions are marked HUMAN-DECISION-REQUIRED: D-14 and D-20.

## Findings

| ID | Category | Severity | Location | Summary | Disposition |
| --- | --- | --- | --- | --- | --- |
| F-1 | Layout | HIGH | `plan.md`, section Layout Dependency R-4636-1 | Issue 4636 holds `state/lifecycle/` at five children, so no child fits the recovery package. | Issue 4636 adopts R-4636-1 before T008. Implementation waits. Authoring is not blocked. |
| F-2 | Test path | HIGH | Parity `tasks.md` line 92, remote checks 44 and 45 | The parity path `tests/contract/cisco_config_converter/test_recovery.py` adds a child to a noncompliant parent. `tests/contract/` holds 17 children. | Decision D-3 places the tests under the integration folder. The parity owner must accept the path change. |
| F-3 | Stale module name | HIGH | Parity `tasks.md` line 93, remote check 58 | Task T028 names `models.py`. Issue 4636 replaces that file with the `state/` package. | This record names the `state/` paths. |
| F-4 | Confirmation word | HIGH | `.github/copilot-instructions.md` line 324 (remote check 7), parity `spec.md` line 130 (remote check 64) | Menu 306 uses `RESTORE`. Parity FR-024 uses `CONFIRM` for administrative writes. | Decision D-6 uses `CONFIRM`. The owner should align both features. |
| F-5 | SDK timeout | HIGH | `.venv\Lib\site-packages\mistapi\__api_request.py` (remote check 102) | The installed SDK sets no timeout on write calls. A wait can block without a bound. | Decisions D-16 and test E11 bound each wait and treat a missed bound as indeterminate. |
| F-6 | SDK retry | HIGH | `.venv\Lib\site-packages\mistapi\__api_request.py` line 59 (remote check 100) | The SDK repeats POST and PUT after HTTP 429, up to three times. | Decision D-17 treats a final 429 as indeterminate. Test E12 proves reconciliation before the next write. |
| F-7 | Operator identity | HIGH | Issue 4636 decision D-10 | No verified operator identity exists in the portal. | Approvals are refused (decision D-14). The decision is HUMAN-DECISION-REQUIRED. |
| F-8 | Reference semantics | MEDIUM | OpenAPI `strings` schema (remote check 95), `network` schema (remote check 88) | Service policy `services` values are plain strings. The meaning, name or ID, is not stated. | Decision D-11 blocks unresolved references. Unverified item U-1. |
| F-9 | UI ownership | MEDIUM | Issue 4646 section UI Behavior, issue 4224 comment of 2026-11-09 | The issue asks for a restore view. Presentation files belong to issues 4637, 4638, and 4647. | Decision D-23 assigns the view to issue 4647. The UI acceptance stays open until that issue merges. |
| F-10 | Route capacity | MEDIUM | `routes.py` (remote checks 37 and 38) | `routes.py` holds four top-level names. | The restore route adds one function. The module reaches five names. |
| F-11 | Backup format | MEDIUM | Issue 4643 (open) | Restore needs the full backup body of each object. Issue 4636 stores only digests. | Decision D-27 adds a private `objects` mapping. Issue 4643 must store the bodies. |
| F-12 | Sibling records | MEDIUM | `spec-drafts` folders 4647, 4648, and 4649 | The three sibling records had no files when this record was written. | Unverified item U-12. Review each sibling record before T005. |
| F-13 | Shared files | MEDIUM | Pull request 4208 (open, draft), files `web_portal/app.py` and `web_portal/templates/base.html` | Portal integration needs an owner handover. | This record edits neither file. Parity task T032 stays blocked. |
| F-14 | Merge order | MEDIUM | Parity overlap comment of 2026-11-09 | Issues 4637 and 4641 to 4646 list `routes.py` as a shared file. | Merge these pull requests in series. Rebase before each push. |
| F-15 | Labels | LOW | Issue 4646 labels | The issue lacks the `feature-spec` label that its parent and siblings carry. | STATUS adds `feature-spec`. |
| F-16 | Structured logs | MEDIUM | Issue 4636 open item U-2 | Principle V asks for structlog or an equivalent. | Standard logging with key and value fields stays until the owner confirms equivalence. |
| F-17 | Store policy | MEDIUM | Constitution Operational Store rule (remote check 17) | The store needs owner approval for retention and backup (issue 4636 open item U-3). | Open gate for T012. |
| F-18 | Grandfathered debt | MEDIUM | `src/interfaces/portals/` (remote check 43), `tests/contract/` (remote check 44) | Two noncompliant parents already exist. | Neither is touched. Remediation actions R-2 and R-3 remain. |
| F-19 | Gate inputs | LOW | `.github/copilot-instructions.md`, section Test quality ratchet | The test-quality config and baseline files are not in the remote check list. | Unverified item U-13. T-LOCAL-GATES names the procedure only. |
| F-20 | Evidence method | LOW | SDK rows 97 to 104 | SDK files are local, so their remote checks use the local path and the Git blob hash. | Recorded with ref `local-venv-0.64.1`. |
| F-21 | Route folders | LOW | Remote checks 54 and 55 | The route folders for issues 4646 and 4636 do not exist on `main`. | Expected. The orchestrator creates the folders at merge time. |
| F-22 | Restore scope | LOW | Parity `research.md` rows C28 and C31 (remote checks 66 and 67) | The parity rows name policy, service, and network restore. They name no template restore. | Decision D-1 limits the scope to those three families. |
| F-23 | Sibling count | MEDIUM | Issue 4636 summary in `spec-drafts\_meta\4636-summary.md` and its STATUS file | The summary states 60 remote checks. The STATUS file lists 24. | Recorded as a defect in issue 4636. This record counts its own 108 checks in each file. |

## Defects in Existing Work

- Issue 4636 leaves no free child in `state/lifecycle/`. The recovery package needs one. (F-1)
- The parity task list names two paths that no longer fit the repository: `tests/contract/cisco_config_converter/` and `models.py`. (F-2, F-3)
- The parity contract and menu 306 use different typed words for restores. (F-4)
- The installed SDK sets no timeout on writes and repeats writes after HTTP 429. (F-5, F-6)
- The portal has no converter blueprint registration and no converter navigation. Remote checks 49 and 50 record both facts. Integration remains a separate task.
- Issue 4636 summary states 60 remote checks, but its STATUS file lists 24 (F-23).

## Coverage Summary

| Requirement | Tasks | Tests or guards |
| --- | --- | --- |
| FR-001 | T005, T009 | D1 |
| FR-002 | T005, T009 | D2, D3, D4, D5 |
| FR-003 | T005, T008, T010 | D6, D7, D13 |
| FR-004 | T005, T010 | D6 |
| FR-005 | T005, T010 | D9 |
| FR-006 | T005, T010 | D8, D10, D11, D12 |
| FR-007 | T006, T007, T010, T012 | D13, E14, R7 |
| FR-008 | T006, T012 | E8 |
| FR-009 | T006, T012, T013 | E1, E2, E6 |
| FR-010 | T006, T013 | E4, E5 |
| FR-011 | T006, T012 | E3 |
| FR-012 | T006, T012 | E1, E2, E5 |
| FR-013 | T006, T012 | E9 |
| FR-014 | T006, T012 | E8 |
| FR-015 | T006, T012 | E8 |
| FR-016 | T006, T012 | E10 |
| FR-017 | T006, T012 | E11, E12, E13 |
| FR-018 | T006, T007, T012 | E10, R5 |
| FR-019 | T007, T010 | R1, R2 |
| FR-020 | T007, T013 | R6 |
| FR-021 | T007, T010, T013 | R3, R4 |
| FR-022 | T005, T013 | D14 |
| FR-023 | T006, T009, T014 | E15 |
| FR-024 | T002, T004, T011 | `tests/integration/test_mistapi_sdk_compatibility.py` |
| FR-025 | T006, T014 | E7 |
| FR-026 | T014, T016 | `tests/integration/web_portal/cisco_config_converter/test_routes.py` |
| FR-027 | T015, T016 | `tests/guardrails/test_nested_package_structure.py` |
| FR-028 | T006, T012, T015 | E15 |

Test identifiers D1 to D14 are the decision tests. Identifiers E1 to E15 are the execution tests. Identifiers R1 to R7 are the recovery tests. The order follows the task list.

## Success Criteria Coverage

| Criterion | Evidence |
| --- | --- |
| SC-001 | E1 to E6 assert zero writes for each refusal. |
| SC-002 | D6 to D13 assert one decision for each object. |
| SC-003 | E11 and E12 assert an indeterminate outcome and zero repeats. |
| SC-004 | E14 asserts unchanged digests for unrelated objects. |
| SC-005 | R1 and R2 assert ownership before a reverse update. |
| SC-006 | Every module uses `FakeMistGateway` from `fakes.py`. |
| SC-007 | E15 asserts no backup body in responses or logs. |
| SC-008 | `tests/guardrails/test_nested_package_structure.py` counts each directory. |

## Consistency Review

| Check | Result |
| --- | --- |
| Each FR appears in at least one task and at least one test. | Pass. The coverage table lists each FR. |
| Each task names exact repository paths. | Pass. Every task lists its paths. |
| Each task names one verification command from the Local gates table. | Pass. Each command starts with `python -m`, `radon`, or another gate command from the table. |
| The test count agrees across documents. | Pass. The plan, tasks, and STATUS file state 36. |
| The plan file map matches the task paths. | Pass. Each path in the file map appears in one task. |
| The capacity counts in the plan match the remote tree. | Pass. Remote checks 39, 42, 43, 44, 46, 48, and 38 support each count. |
| Decision IDs agree in the plan, the research, and the STATUS file. | Pass. Decisions D-1 to D-27 appear in each place. |
| The remote check count matches the research table and the summary. | Pass. The count is 108 in each place. |

## Constitution Alignment

The constitution check in `plan.md` lists each rule with its result. Two rules fail until open items close: structured logs (F-16) and the Mist write evidence (T002). Action logging and inline comments fail until the implementation tasks finish. No rule forbids the change.

## Unresolved Items

- HUMAN-DECISION-REQUIRED decision D-14: the operator identity design for write-capable approvals.
- HUMAN-DECISION-REQUIRED decision D-20: owner permission for deletion of objects that a restore created.
- External gate R-4636-1: issue 4636 must move `lifecycle/backup.py` into `lifecycle/recovery/`.
- External gate issue 4634: payload evidence for each write (unverified items U-1 to U-5).
- External gate issue 4635: licensing decision. This record reuses no source expression.
- External gate issue 4643: backup bodies stored in the private store (decision D-27).
- External gate issue 4644: the gated apply path and the reconciliation contract.
- External gate issue 4645: the administrative gate and the delete path.
- External gate issue 4647: the restore view (decision D-23).
- Unverified items U-6 to U-13 remain open as listed in `design/research.md`.

## Remediation Actions

- R-1: Split `routes.py` into a package with one module for each route family. Open a separate issue.
- R-2: Reduce `src/interfaces/portals/` to five children. Open a separate issue.
- R-3: Reduce `tests/contract/` to five children. Open a separate issue.

## Validation Commands and Results

This drafting pass ran no build, test, linter, formatter, install, container, or repository script. Each check used read-only commands.

| Command | Result |
| --- | --- |
| `gh issue view 4646` and related issue reads | Run. Results are in `design/research.md`, section R1. |
| `gh pr list` and `gh pr view` for pull requests 4596 and 4208 | Run. Results are in `design/research.md`, section R2. |
| `gh api` tree read for `main` | Run once. Results are in `design/research.md`, section Remote verification. |
| `gh api` contents and blob reads for cited lines | Run. Results are in `design/research.md`, section Remote verification. |
| `git hash-object` on the installed SDK files | Run. The command does not write an object. |
| `Select-String` on the installed SDK files | Run. Results are in `design/research.md`, section R5. |
| `python -m pytest` and the other repository gates | Not run. Reason: the drafting rules forbid tests and gates in this pass. |
