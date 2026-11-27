# Specification Analysis Report: Laptop Branch Archive Verification

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, and the remote state of origin on 2026-11-26.

**Method**: The review is read-only. Counts come from GitHub GET responses and read-only local git commands. The review checked the requirement map, the task map, and the remote state. Each finding has a resolution.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| F-1 | Inconsistency | HIGH | Issue body, reference count | The issue calls 497 names archive refs. Origin holds 491 archive refs and 6 rescue branches. | Fixed in the record (D-2, TC-05). The issue owner must correct the issue body. The summary reports this to the orchestrator. |
| F-2 | Inconsistency | MEDIUM | Issue body, rescue names | The issue lists rescue branches with the archive list. Their names carry no archive prefix. | Fixed. The record gives them the counterpart state `self` (RC-31). |
| F-3 | Inconsistency | MEDIUM | Issue body, `jmorrison-juniper-4200-migrate-mistwanperformance` | The issue calls the laptop branches local-only. A same-name branch exists on origin at another tip. The archive tip diverges from it (48 commits ahead, 85 behind). | Accepted. The local-only claim concerns commits, not names. The record reports the state (RC-36, RC-37). |
| F-4 | Coverage | LOW | Stash source branch | The stash names `jmorrison-juniper-documented-trend-object-export`. Origin lacks that branch, and the issue lists no archive ref for it. | Accepted. The record marks the absence (RC-38). The stash base commit stays unverified. |
| F-5 | Redundancy | LOW | Archive tips | The 491 archive refs point to 475 distinct commits. Twelve groups share a tip. One group of six names shares a tip, and each of the six claims 41 unpushed commits. | Accepted. The shared tip groups appear below. A human decides which name to keep (D-8). |
| F-6 | Drift | MEDIUM | Local checkout | Six of the ten local branches that carry archived names have tips that differ from the archive tips. | Accepted. The archive tip is the record value. Local state is a cross-check only (D-1). |
| F-7 | Debt | LOW | `changelog.d/` | The folder holds 335 direct children on main (RC-28). The five-children rule does not hold there. | Tracked as T013. The constitution permits unique records in this folder. |
| F-8 | Unverified | MEDIUM | Issue claims | The claims of no secret, no force push, no merge, no deletion, and the claimed unpushed counts cannot be verified from origin alone. | Listed in the Unverified list of `design/research.md` (FR-010). |
| F-9 | Process | LOW | Changelog rule | The constitution requires a fragment for each change. The changelog README exempts internal-only changes. | Resolved. The constitution governs. The change adds one fragment (D-6). |
| F-10 | Coverage | LOW | Search hit #4870 | A search hit matches the title only. Its body does not mention 4868. | Accepted. The record does not list #4870 as related. Issue #4911 is related, because its body names archive refs. |

## Shared Tip Groups

Each row lists archive refs that point to one commit. The first column is the first seven characters of the tip.

| Tip | Refs | Archived names |
| - | - | - |
| 79bae83 | 2 | 3998-fix-wan-vpn-http-503, fix/4564-wan-vpn-http-503 |
| 51603bf | 2 | chore/2708-next-behavior-assertion, jmorrison-juniper-publish-test-quality-slice |
| d2f5acd | 2 | jmorrison-jnpr-fix-4051-rrm-dry-run-precedence, pr-4107-remote |
| f8ff543 | 2 | jmorrison-juniper-3200-upgrade-portal-e2e-parity, pr/4541/jmorrison-juniper-3200-upgrade-portal-e2e-parity |
| b7f4f79 | 2 | jmorrison-juniper-4340-menu-reference-drift, jmorrison-juniper-potential-meme |
| b4d61b8 | 2 | jmorrison-juniper-cisco-converter-full-parity-spec, pr-4596 |
| ae11a1b | 2 | jmorrison-juniper-device-metric-cancellation-test, preserved/issue2711-device-original |
| fb7a7d1 | 6 | jmorrison-juniper-fix-4585-dependency-lock-rejects-devel, jmorrison-juniper-issue-4036-json-preview-file-not-found, jmorrison-juniper-issue-4168-split-juniper-rma-and-export-packages-b2bbe4, jmorrison-juniper-menu-209-http-errors, jmorrison-juniper-pending-paste-race-investigation, jmorrison-juniper-verify-4584-main-resolution |
| 9b94803 | 2 | jmorrison-juniper-publish-firmware-403-test, jmorrison-juniper-test-quality-http-4xx-slice-6ce |
| a5b1b2c | 2 | jmorrison-juniper-strict-pyright-repairs, preserve/strict-a5b1b2c |
| b485fa0 | 2 | jmorrison-juniper-test-quality-2708-redis-json-writer, jmorrison-juniper-test-redis-json-writer-assertion |
| 4f71aa5 | 2 | jmorrison-juniper-test-quality-2747-http-503-pr, jmorrison-juniper-test-quality-second-http-5xx-slice |

## Coverage Summary

| Requirement | Has task | Task IDs | Tests | Notes |
| - | - | - | - | - |
| FR-001 | Yes | T001, T014 | TC-01 | |
| FR-002 | Yes | T002 | TC-02 | |
| FR-003 | Yes | T001, T011 | TC-03 | |
| FR-004 | Yes | T003, T010 | TC-04 | |
| FR-005 | Yes | T004 | TC-05 | |
| FR-006 | Yes | T004 | TC-05 | |
| FR-007 | Yes | T005 | TC-06 | |
| FR-008 | Yes | T005 | TC-06 | |
| FR-009 | Yes | T006 | TC-07 | |
| FR-010 | Yes | T007, T010 | TC-15 | |
| FR-011 | Yes | T008, T014, T-MERGE | TC-11 | |
| FR-012 | Yes | T009, T011, T013 | TC-08, TC-09 | |
| FR-013 | Yes | T010, T011, T-LOCAL-GATES | TC-13 | |
| FR-014 | Yes | T012 | TC-14 | |
| FR-015 | Yes | T010, T-LOCAL-GATES | TC-12 | |
| SC-001 | Yes | T001, T014 | TC-01 | |
| SC-002 | Yes | T002 | TC-02 | |
| SC-003 | Yes | T003, T004 | TC-04, TC-05 | |
| SC-004 | Yes | T007 | TC-10 | |
| SC-005 | Yes | T005 | TC-06 | |
| SC-006 | Yes | T-LOCAL-GATES, T-REMOTE-CI | TC-13 | |

## Metrics

| Measure | Value |
| - | - |
| Listed names in the issue | 497 |
| Archived names (archive refs) | 491, including the stash ref |
| Rescue branches | 6 |
| Remote checks in `design/research.md` | 39 |
| Requirements | 15 |
| Tasks | 18 |
| Tests | 15 |
| Decisions | 10 |
| Human decisions | 1 (D-8) |

## Unresolved Items

- D-8 needs a human decision before any deletion of an archive ref.
- F-1 needs the issue owner to correct the count in the issue body.
- The claims listed under Unverified in `design/research.md` remain unverified.
