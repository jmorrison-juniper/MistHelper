# Analysis: Integrate Mist Cisco Config Converter

**Feature**: [Spec](spec.md) | **Plan**: [plan](plan.md) | **Tasks**: [tasks](tasks.md) | **Research**: [design/research.md](design/research.md)

**Scope**: This review checks the spec, plan, tasks, and child records 4634 to 4649. It also checks the legacy record and the remote code on `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Each finding cites a remote row (R-##) or a source (S-##) from research.md.

## Consistency Review

| ID | Area | Finding | Evidence | Severity | Action |
|---|---|---|---|---|---|
| A-01 | License | The DNS slice merged to `main` before the license decision. The issue comment of 2026-10-16 blocks source work until approval. PR #4226 lists six source files and four test files. | S-1, S-2, R-81 | High | D-17 (human). Keep the code unregistered (D-2). |
| A-02 | Process | The PR #4226 body says "Do not merge". The PR merged on 2026-10-26. | S-2 | High | The owner records the override in the issue. The reviewer confirms it. |
| A-03 | Records | The issue comment of 2026-10-16 calls PR #4226 a planning PR. The PR title is "feat(web-portal): add isolated offline Cisco DNS converter". | S-1, S-2 | Medium | The owner corrects the comment. |
| A-04 | Records | Issue comments on child issues describe PR #4596 as open. Issue 4634 says so on 2026-11-08. Issue 4642 says so on 2026-11-09. PR #4596 merged on 2026-11-13. | S-7, S-14 | Low | The issue authors correct the comments. This record edits no issue. |
| A-05 | Scope | The legacy record defers cloud apply. The issue requires an apply path with typed confirmation. | Legacy spec, S-1 | Medium | D-3 replaces the deferral with gated apply. |
| A-06 | Version | The legacy plan and quickstart name Python 3.13. `pyproject.toml` requires 3.15. | R-32, R-67 | Medium | This record uses 3.15. The legacy text is replaced (D-1). |
| A-07 | Path | The legacy record names `tests/unit/gateway/overrides`. The path is absent. The file sits under `tests/unit/marvis/mist/resources/gateway/overrides/`. | R-16, R-17 | Medium | D-9 keeps the file at its path on `main`. |
| A-08 | Path | The legacy plan names `test_sdk_contract.py`. The file is absent. | R-19 | Low | The legacy text is replaced. Child records own their test files. |
| A-09 | IDs | Legacy T017 and T018 (export) collide with parity T017 and T018 (proposal review). Child 4641 reports the same collision. | Legacy tasks, parity tasks | Medium | D-13. Legacy IDs appear only as `L-T###`. The legacy IDs map by content to parity T005 and T007 to T014. No ID maps one to one. |
| A-10 | Dependencies | The mistapi pin differs in three files. The copilot text says `>=0.64.0,<0.65`. `pyproject.toml` says `>=0.64.1,<0.65`. `requirements.txt` says `==0.64.1`. | R-49, R-69, R-68 | Low | The owner corrects the repository text in a separate change. |
| A-11 | Secrets | `PORTAL_SECRET_KEY` falls back to a random UUID at each start. Stored review records break after a restart. | R-46 | High | D-16 (human). |
| A-12 | Identity | `web_portal/app.py` defines no login route. Its only auth-pattern match is a comment about a webhook signature (line 242). The search covered `app.py` only. | R-44, S-9 | High | D-16 (human). The search of other portal files is open (U-12). |
| A-13 | Data | The data browser excludes only the firmware `BACKUP_DIRECTORY` name (R-47). Private converter files under `data/` would appear in the browser. | R-47 | High | D-7. Add the exclusion before production retention, in a separate change (G3). |
| A-14 | Structure | `tests/contract` holds 17 children (R-92). Child 4634 D-9 places contract tests under `tests/contract/web_portal/cisco_config_converter`. | R-92, R-89 | Medium | D-9. Child 4634 amends its path. |
| A-15 | Structure | `tests/e2e/web_portal` holds 32 children (R-93). Children 4642 and 4645 name `tests/e2e/cisco_config_converter/`. Children 4647 to 4649 name `tests/e2e/web_portal/test_cisco_parity.py` (R-91 absent). Child 4647 D-1 forbids new files there. | R-93, R-91 | Medium | D-9. T029 extends the existing module. Children 4642, 4645, 4648, and 4649 amend their paths. |
| A-16 | Structure | Child 4645 names `src/interfaces/portals/cisco_config_converter/engine/`. The converter root holds five children today (R-94). A sixth child breaks the rule. | R-94, child 4645 D-6 | Medium | D-10. The engine moves under `state/administration/`. |
| A-17 | Structure | `presentation/` would hold six files after the child additions. These are converter.html, converter.js, converter.css, proposal_review.js, administration.html, and administration.js. | Child 4641, 4645, 4647 | Medium | D-10. Administration files move to `presentation/administration/`. |
| A-18 | Sequence | Child 4639 edits `conversion.py`. Child 4640 replaces that file with a package. Child 4638 adds files under `conversion/` before 4640 creates it. | Child 4638, 4639, 4640 | High | D-14. The skeleton lands with T012 and T014 in one change. Child 4639 writes under `conversion/management/` after 4640. |
| A-19 | Counts | Child 4636 states 60 remote checks in its summary. Its STATUS file lists 24. | Child 4636 STATUS and summary | Low | Child 4636 corrects its summary. |
| A-20 | Child claim | Child 4642 says the `ConverterRoutes` class is full and that discovery code belongs elsewhere. This record did not verify the class size. | Child 4642 summary | Low | Open. The discovery code moves to `src/mist/access/targets/` (T020). |
| A-21 | Scope | The gateway template type enum lists `spoke` and `standalone` only (R-75). Parity T012 expects a Hub selection. | R-75 | Medium | The hub role stays out of scope. The owner decides under D-18. |
| A-22 | Deletion | Child 4634 D-4 excludes `deleteOrgServicePolicy` (R-74). Child 4645 D-13 excludes service-policy deletion. The issue 4224 comment of 2026-11-13 says the service-policy deletion scope remains unresolved. Parity FR-023 requires scoped service, network, and template deletion (R-100). It does not name service policies. | R-74, R-100, S-1 | High | D-15 (human). |
| A-23 | Unassignment | Child 4634 D-8 and child 4645 D-3 ask the owner about site-template unassignment. | Child 4634 and 4645 | Medium | D-15 (human). |
| A-24 | Counts | Child 4635 counts nine converter files. PR #4226 lists six source files and four test files. | Child 4635, S-2 | Low | D-17 uses the PR list. Child 4635 corrects its count. |
| A-25 | Shared files | PR #4208 is an open draft, updated 2026-11-22. It lists `web_portal/app.py` and `web_portal/templates/base.html`. No handover is recorded. | S-4, S-1 | High | D-11. Gate G3 blocks both files. |
| A-26 | Tracking | The issue closure keyword is required in the record PR body (T-PR). The 2026-10-16 comment asks to keep #4224 open. The 2026-11-13 comment says it remains open. | S-1, T-PR | Medium | Open. The orchestrator confirms the keyword before T-PR. The owner can reopen the issue. |
| A-27 | Child claim | Child 4634 says the SDK sets no write timeout and logs write bodies at DEBUG level. This record did not verify either claim. | Child 4634 defects | Medium | Open (U-02, U-03). The record sets its own bounds (D-6). |
| A-28 | Limit | The legacy contract attributes the 16 MiB limit to observed source behavior. The source user guide and mapping reference contain no size statement in the keyword search. | Legacy contract, S-8 | Medium | Open (U-08). The owner confirms the limit under D-18 or with a source. |
| A-29 | Source gap | The source mapping reference lists flow export as a feature that needs workarounds (R-82). | R-82 | Low | FR-036 keeps flow export visible as a display-only limit. |

## Defects in Existing Work

- The merged DNS slice lacks a license decision (A-01).
- The merged PR body says "Do not merge" (A-02).
- The legacy record names an absent test path (A-07) and an absent test file (A-08).
- The legacy record names Python 3.13 (A-06).
- The portal secret falls back to a random UUID (A-11).
- The data browser lists files under `data/` (A-13).
- Child 4636 reports two different remote-check counts (A-19).

## Cross-Record Conflicts

- Test locations conflict across children 4634, 4639, 4640, 4642, 4645, 4647, 4648, and 4649 (A-14, A-15). D-9 resolves the layout.
- The administration engine and the presentation files conflict with the root and folder limits (A-16, A-17). D-10 resolves the layout.
- Conversion file edits conflict between children 4638, 4639, and 4640 (A-18). D-14 resolves the sequence.
- Service deletion scope conflicts between children 4634 and 4645 (A-22). D-15 asks the owner.

## Issue Acceptance Status

| Acceptance criterion (issue #4224) | Status on `main` | Evidence |
|---|---|---|
| Conversion workflow is available in a portal tab | Not met | R-22 and R-23 |
| Operator parses a Cisco configuration and reviews the source | Partly met for DNS only | R-13, R-34, R-41 |
| Operator reviews proposed Mist settings before any cloud change | Partly met for DNS only | R-34, R-40 |
| Preview does not require Mist credentials | Met for the isolated host | R-36 (no SDK import) and T029 |
| Apply requires valid credentials and typed confirmation | Not met | R-42 (no apply route) |
| Input, output, logging, and secrets follow the security rules | Partly met | R-35, R-37, R-38, R-46 |
| Existing portal workflows remain unchanged | Met | R-22 and R-23 (no shared file changed) |
| Unit, integration, edge-case, and browser tests cover the workflow | Partly met for DNS only | R-17, R-18, R-20 |
| License compatibility resolved before any copy | Not met | A-01 and D-17 |
| Integration uses the existing Compose group and shared services | Not verified in full | R-64 and R-65 (no compose change in this record) |

## Unresolved Items

- D-15 to D-18 need human decisions (A-01, A-11, A-12, A-22, A-23, A-21).
- Gate G1 (legal) is open (A-01).
- Gate G3 (shared files) is open (A-25).
- Gates G2, G4, and G5 are open for each write family.
- The record PR keyword question in A-26 needs the orchestrator decision.
- The upload limit source question in A-28 needs an owner decision.
