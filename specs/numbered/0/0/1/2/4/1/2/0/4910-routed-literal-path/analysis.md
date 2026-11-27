# Specification Analysis Report: Restore -LiteralPath in the setup scripts

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/quickstart.md`, `design/contracts/prerequisite-output.md`, and the remote `main` content that the record cites (105 checks in `design/research.md`).

**Method**: A read-only pass compared each requirement with its task, each claim with its remote check, and each constitution rule with the plan. No code and no test ran in this pass.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| A-1 | Defect in existing work | HIGH | `check-prerequisites.ps1` lines 135, 136, 139, 143 | Four optional-document probes lack `-LiteralPath`. Line 139 reads the contracts folder with `Get-ChildItem -Path`. Verified on `main` (RC-01 to RC-04). | Fixed by T004. |
| A-2 | Defect in existing work | HIGH | `setup-tasks.ps1` lines 56, 57, 58, 61 | Four optional-document probes lack `-LiteralPath`. Line 58 reads the contracts folder with `Get-ChildItem -Path`. Verified on `main` (RC-07 to RC-10). | Fixed by T005. |
| A-3 | Defect in existing work | MEDIUM | `create-new-feature.ps1` lines 211, 213 | The spec-file probe and the template probe lack `-LiteralPath`. The spec file is a feature path (RC-12, RC-13, RC-14). Upstream 1.4.3 keeps `-LiteralPath` on the spec file (RC-46). | Fixed by T006. Decision D-3 records the scope. |
| A-4 | Unresolved item | MEDIUM | `update-agent-context.ps1` lines 120, 140, 156 | Three probes on the feature plan path lack `-LiteralPath` (RC-23, RC-58, RC-59). The script updates agent files and sits outside the four scoped scripts. | Open. File a separate issue (U-1). |
| A-5 | Unresolved item | MEDIUM | `common.ps1`, template and override probes (example line 379) | Template and override probes lack `-LiteralPath` (RC-21). The paths are not feature paths. | Open. File a separate issue (U-2). |
| A-6 | Inconsistency | LOW | Issue #4910 body and `spec.md` | The issue names `Test-Path` only. The spec adds `Get-ChildItem -Path` and `create-new-feature.ps1`. | Resolved by decisions D-1 and D-3, recorded in `design/research.md`. |
| A-7 | Process debt | MEDIUM | `tests/guardrails/test_routed_core_port.py`, `tests/guardrails/test_spec_route_contract.py` | Both modules already exceed five top-level names. RC-26 counts 10 names, and RC-64 counts 31 names. The change adds 4 names and 2 names. | Recorded in `plan.md`, Complexity Tracking. Remediation: split both modules by rule (U-5). |
| A-8 | Process debt | LOW | `tests/guardrails` | The folder holds 81 tracked children (RC-38), above the limit of five. The folder is grandfathered. | Resolved by design. FR-015 forbids a new direct child. |
| A-9 | Drift | MEDIUM | `.specify/integrations/speckit.manifest.json` | The hashes for the two check scripts match neither the fetched upstream bytes nor their CRLF-normalized form (RC-48, RC-49). The cause is not verified. | Unresolved (U-3). Decision D-9 leaves the manifest unchanged. Issue #4873 part 2 owns the classification. |
| A-10 | Process gap | LOW | Constitution Principle IV, steps 10 to 12 (RC-76) | Steps 10 and 11 run through the auto-merge dispatch of `container-build.yml` (RC-55). Step 12, deploy and health check, is not part of this change. | Unresolved owner action (U-4). |
| A-11 | Documentation gap | LOW | `documentation/development-setup.md` (RC-96) | The contributor guide names no `pwsh` requirement. The behavior tests need it (RC-65). The gap exists before this change. | Unresolved, out of scope (U-6). |
| A-12 | Limit | LOW | Guard design, `plan.md` Risks | A probe split over two lines escapes the line scan. | Accepted. The spec states the Caution. The examined count fails an empty scan. |
| A-13 | Verification gap | MEDIUM | Behavior tests | The bracket behavior was not executed in this pass, because the brief forbids running code. | Open. Task T003 requires the red result, and T008 requires the green result. |
| A-14 | Coordination | MEDIUM | Issue #4873 (open, labels `in-progress`) | Part 2 of issue #4873 classifies managed-file differences, which include the same scripts. | Accepted. No open pull request overlaps the change map (checked 2026-11-26). T-PR repeats the check. |
| A-15 | Consistency | LOW | `test_routed_core_port.py` module docstring (RC-24) | The docstring names routing rules. The new rule is a hardening rule. | Accepted. The docstring says the module guards rules that the routed layout needs. The literal probe rule fits that purpose. |

## Coverage Summary

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T004 | TC-1 (guard) |
| FR-002 | T004 | TC-1 (guard) |
| FR-003 | T005 | TC-1 (guard) |
| FR-004 | T006 | TC-1 (guard) |
| FR-005 | T004, T005, T006 | TC-4, TC-5 (design document list) |
| FR-006 | T001 | TC-1, TC-3 |
| FR-007 | T001 | TC-1 |
| FR-008 | T001 | TC-2 |
| FR-009 | T001 | TC-3 |
| FR-010 | T002 | TC-4, TC-5, TC-6, TC-7 |
| FR-011 | T008 | Existing tests in both modules (SC-003) |
| FR-012 | T004, T005, T006 | Review in T-PR |
| FR-013 | T007 | Changelog guard |
| FR-014 | T-PR | File list review |
| FR-015 | T001 | File list review in T-PR |

Test cases: TC-1 to TC-3 are the three guard functions in `test_routed_core_port.py`. TC-4 to TC-7 are the four cases of the two bracket functions in `test_spec_route_contract.py`.

| Success criterion | Tasks |
| - | - |
| SC-001 | T003, T008 |
| SC-002 | T003, T008 |
| SC-003 | T008, T-LOCAL-GATES |
| SC-004 | T-LOCAL-GATES, T-PR |
| SC-005 | T-REMOTE-CI, T-MERGE |

## Unmapped Tasks

None. Each of the twelve tasks maps to at least one requirement or success criterion.

## Constitution Alignment

`plan.md`, section Constitution Check, lists each rule with its result. The two results with recorded debt are the top-level name counts (A-7) and the deployment steps (A-10).

## Metrics

- Functional requirements: 15.
- Success criteria: 5.
- Tasks: 12.
- Test cases: 7.
- Decisions: 11, with 0 human decisions.
- Remote checks: 105, with 100 present, 3 absent, and 2 stale.

## Unresolved Items

- **U-1**: File a separate issue for the feature-plan probes in `update-agent-context.ps1` (RC-23, RC-58, RC-59).
- **U-2**: File a separate issue for the template and override probes in `common.ps1` (RC-21).
- **U-3**: Issue #4873 part 2 decides the managed-file hashes (RC-48, RC-49).
- **U-4**: The owner runs the deploy and health check of Principle IV, step 12, after a merge that changes a product file.
- **U-5**: File a separate issue to split `test_routed_core_port.py` and `test_spec_route_contract.py` into rule modules.
- **U-6**: File a separate issue for a `pwsh` note in `documentation/development-setup.md`.
- **U-7**: Run the red and green results in T003 and T008. A missing result leaves A-13 open.

## Convergence After Implementation

After T008, run this review again against the pushed files. Update each finding row with its new state. Record the result in this file before T-PR. Run `speckit.analyze` again when the pull request changes a requirement.
