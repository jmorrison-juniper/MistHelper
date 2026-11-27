# Analysis: Gated Converter Apply and Reconciliation

This review compares `spec.md`, `plan.md`, `tasks.md`, the remote state on `main`, and the sibling drafts of issues 4636, 4646, 4647, and 4648. Remote evidence appears in `design/research.md`, section Remote Verification.

## Requirement Coverage

| Requirement | Tasks | Tests |
| --- | --- | --- |
| FR-001 scope view | T004, T012, T016 | TST-26 |
| FR-002 approval binding | T005 | TST-03, TST-04, TST-05 |
| FR-003 exact `APPLY` | T012 | TST-02, TST-24 |
| FR-004 verified operator | T005 | TST-03 |
| FR-005 approval checks | T005 | TST-01, TST-04, TST-07 |
| FR-006 backup gate | T006 | TST-06 |
| FR-007 invalidation | T009 | TST-10 |
| FR-008 single use under lock | T005, T009 | TST-07 |
| FR-009 scope lock | T009 | TST-27 |
| FR-010 preflight and re-read | T009 | TST-10 |
| FR-011 allow-list | T003, T004, T007 | TST-11 |
| FR-012 body from current object | T009 | TST-11 |
| FR-013 explicit SDK arguments | T007 | TST-12 |
| FR-014 disabled families | T007 | TST-09 |
| FR-015 no code retry | T007 | TST-14 |
| FR-016 bounded waits | T007 | TST-16 |
| FR-017 outcome classes | T008 | TST-13, TST-15 |
| FR-018 stop after non-verified outcome | T009 | TST-13, TST-15, TST-23 |
| FR-019 reconciliation | T010 | TST-21, TST-22 |
| FR-020 verified after read-back | T010 | TST-20 |
| FR-021 create without ID | T008 | TST-17 |
| FR-022 cancel | T005, T012 | TST-08 |
| FR-023 redaction | T011 | TST-18, TST-26 |
| FR-024 action logging | T011 | TST-18 |
| FR-025 unchanged behavior | T014, T015, T017, T018 | Existing converter tests |

Each requirement maps to at least one task and one test. Each task names exact paths and one verification command.

## Findings

| ID | Area | Severity | Evidence | Finding | Action |
| --- | --- | --- | --- | --- | --- |
| F-01 | Parent task T021 | High | Parent `tasks.md` line 76 | The path `tests/contract/cisco_config_converter/test_apply.py` adds a child to `tests/contract/`, which holds 17 children. | Decision D-15 moves the tests to `apply/`. |
| F-02 | Parent task T022 | High | Parent `tasks.md` line 77, research row R27 | The task names `models.py`. Issue 4636 deletes that file. | Tasks T004 to T011 name the `state/` modules. |
| F-03 | Parent tasks T021 and T022 | Medium | Parent `tasks.md` lines 76 and 77 | Neither task names a browser file, but the issue requires the scope view and the cancel control. | Decision D-16 assigns the browser controls to issue 4647. |
| F-04 | Constitution | Medium | `.specify/memory/constitution.md` line 279, research row R20 | The constitution says `mistapi` 0.59 or newer. The pin is 0.64.1. | The pin governs. The constitution text needs a separate amendment. |
| F-05 | Parent research C24 | High | `mistapi/__api_request.py` lines 59, 229, 300, 324, 343 | The SDK repeats HTTP 429 for writes and sets no timeout on writes. The parent assumed the SDK bounds retries. | Decisions D-7 and D-8. Tests TST-14 and TST-16. |
| F-06 | Issue 4636 dependency | High | Research row R38 | Issue 4636 exists only as a draft. Its types are absent from `main`. | Task T002 blocks every code task. |
| F-07 | Capacity | High | `plan.md`, capacity table | After issue 4636, `state/` and `state/lifecycle/` hold five children each. No slot remains for `execution.py`. | Amendment X-1 and decision D-14. |
| F-08 | Overlap with issue 4646 | High | Issue 4646 `plan.md` line 149 | Issue 4646 defines `OutcomeReconciler`, which repeats this record's reconciliation. | Amendment X-5. |
| F-09 | Overlap with issue 4646 | Medium | Issue 4646 `plan.md` lines 147, 151, 152 | Issue 4646 moves `backup.py` and edits `operation.py` and `transitions.py`. | Amendment X-9. This record edits none of those modules beyond issue 4636. |
| F-10 | Capacity | High | Issue 4648 `plan.md` lines 87 and 88 | Issue 4648 adds two test files to the converter test root. With issues 4636, 4644, and 4646, the root holds seven children. | Amendment X-7. |
| F-11 | Shared file | Medium | Issue 4647 `plan.md` line 94 | Issue 4647 and this record both need `converter.js`. | Decision D-16. Issue 4647 edits the file after this record lands its contract. |
| F-12 | Outcome term | Medium | Issue 4636 `data-model.md`, issue 4646 `spec.md` line 125 | Issue 4636 lists four outcomes. Issue 4646 uses `not-applied`. | Amendment X-2 adds `not-applied` to issue 4636. |
| F-13 | Transition table | Medium | Issue 4636 `data-model.md`, Transition Table | The table has no edge from `approved` to `reviewed`, which cancel needs. | Amendment X-3. |
| F-14 | Scope digest | Medium | Issue 4636 `data-model.md`, ProposalRecord | The scope digest omits the change set. | Amendment X-4. |
| F-15 | Route reachability | Medium | Research row R08 | `web_portal/app.py` registers no converter blueprint. The apply route cannot run in the portal. | Parent task T032 and gate G3 own the registration. |
| F-16 | Ownership status | Low | Issue 4633 comments, PR #4208, PR #4615 | Issue 4633 closed. PR #4208 is open. PR #4615 merged on 2026-11-13. | Recorded in the spec dependency table. G3 is partly cleared. |
| F-17 | Local drift | Low | Local blob check | Local `.gitignore` and `spec-route.ps1` differ from `main`. | Remote values are cited for both files. |
| F-18 | Document twin | Low | Parent `contracts/mist-apply.md` line 5 | The parent cites the JSON OpenAPI twin. This record cites the YAML twin. | Both twins name the same operation IDs. This record cites the YAML line numbers. |
| F-19 | Device assignment scope | Medium | Parent research row C22 | The parent names device assignments. No registered family covers `updateSiteDevice` or `updateOrgInventoryAssignment`. | Decision D-1 excludes both until issue 4634 supplies evidence. Family F-08 covers profile assignment. |

## Residual Risks

- R-1: Mist offers no compare-and-set in the SDK. A change between the re-read and the write can go undetected. The risk stays open until Mist documents a concurrency control.
- R-2: The Mist PUT semantics are unverified. The executor sends the complete body, so the risk affects only omitted fields. Unverified item U-1 tracks it.
- R-3: The OpenAPI file documents no HTTP 500 response for the families in scope. The executor treats a 500 as indeterminate. Unverified item U-3 tracks it.

## Unresolved Items

| Item | Owner | Blocks |
| --- | --- | --- |
| Gate G1, licensing and authorship (issue 4635) | Owner and legal review | Release |
| Gate G2, field evidence (issue 4634) | Owner and API review | Each family allow-list |
| Gate G3, shared-file handover (PR #4208) | Integration owner | Route registration |
| Gate G4, store and retention policy | Cloud owner | Any production write |
| Gate G5, per-operation approval | Operator | Each write |
| Decision D-5, identity provider | Human | Any approval |
| Decision D-17, family enablement | Human | Any production write |
| Decision D-18, shared secret policy | Human | Approval sealing |
| Amendments X-1 to X-9 | Owners of issues 4636, 4646, 4647, and 4648 | Code tasks T004 to T011 |

Warning: Until decisions D-5 and D-17 close, no approval can run a live write. This record enforces that rule in code.
