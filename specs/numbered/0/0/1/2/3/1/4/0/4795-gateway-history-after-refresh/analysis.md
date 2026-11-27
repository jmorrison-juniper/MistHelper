# Specification Analysis Report: Gateway History After an Ordinary Refresh

## Findings

| ID | Severity | Finding | Evidence | Action |
| - | - | - | - | - |
| F-01 | High | The repair is absent from `main`. `main` has no `LiveHistory` method, no live route, and no WAN live tests. | R06 to R11 | D-2. The publication decides when the repair reaches `main`. |
| F-02 | High | The issue cites reconstruction commit `15c69b1`. GitHub has no such commit, and the local checkout lacks it. | R02 | This record does not use it. The owner summary notes it. No GitHub write occurs here. |
| F-03 | High | The changed methods carry no inline comments. Constitution Principle VI forbids committing such code. | R26 | T003 and T004 (D-7). |
| F-04 | High | The history read logs nothing before its action. Constitution Principle VII requires a log before and after each action. | R27 | T004 (D-7). |
| F-05 | Medium | `LiveHistory.read` spans 28 lines. The limit is 25. | R20 | T003 (D-8). |
| F-06 | Medium | `LivePages.render` spans 64 lines. The limit is 25. This change does not touch it. | R28 | D-12. A separate issue. |
| F-07 | Medium | No unit test calls `LiveHistory.read`. The port-or-peer message has no test. | R34, R35 | T005 to T007. |
| F-08 | Medium | Pull request #4208 says `Refs #4795`. Its merge does not close the issue. | R48, R49 | D-3 and T-PR. |
| F-09 | Medium | Pull request #4208 changes 82 files for six issues: #4200, #4793, #4794, #4795, #4797, and #4798. AGENTS.md line 223 requires one change for each pull request. | R49, R60 | D-11, a separate issue. D-2 is the owner decision. |
| F-10 | Medium | The candidate branch `jmorrison-juniper-4200-migrate-mistwanperformance` does not follow the `<type>/<ISSUE>-<slug>` pattern. | GitHub facts in research.md | Accepted for publication only (D-2). |
| F-11 | Medium | The mistapi floor differs by document. `copilot-instructions.md` line 21 says 0.64.0. `pyproject.toml` line 29 says 0.64.1. The constitution line 279 says 0.59. | R64, R69, R71 | D-12, a separate issue. This change edits no text. |
| F-12 | Medium | Ten checks on pull request #4208 are skipped: seven from `auto-merge` and three from `close-linked-issues`. A skipped check counts as unknown. | GitHub facts in research.md | T-REMOTE-CI reruns them. |
| F-13 | Low | `LiveHistory.window` refuses the same ambiguity with a different message. | R29, R30 | No change. FR-009 keeps the quoted text. |
| F-14 | Low | `LiveHistory.read` has two extra parameters at head, `cache_only` and `window`. The three-argument calls in N1 to N9 stay valid. | R20 | None. |
| F-15 | Low | Commit `d7a706d` changes no collection file. Mist calls in the collection layer are outside this issue. | R89 | None. |
| F-16 | Info | Issues #4797 and #4798 are test failures outside this defect. Pull request #4208 references them. | GitHub facts in research.md | None. They are not dependencies. |
| F-17 | Info | The changelog fragment already names issue 4795. | R47 | T010. |
| F-18 | Info | The record route equals the base-5 digits of 4795, padded to eight places. | R78 to R80 | None. |
| F-19 | Low | FR-010 has no automated content test. The changelog guard and the STE gate cover the release note and the document. | T009, T010 | Accepted. The document text is reviewed under AGENTS.md. |

## Coverage Summary

| Requirement | Tasks | Tests | Notes |
| - | - | - | - |
| FR-001 | T001, T005 | N1, N2, N3, E1 | Resolution from gateway, circuit, and peer records. |
| FR-002 | T002, T006 | N4, N6, E2 | Zero or many gateways refuse. |
| FR-003 | T002, T006 | N5, E2 | Foreign organization refuses. |
| FR-004 | T005 | N1, N2 | One history read for the resolved gateway. |
| FR-005 | T001, T002, T-MERGE | E1, E2 on `main` | Visibility after the sequence. |
| FR-006 | T007 | N7 | Port and peer rule and message. |
| FR-007 | T005, T006 | N1, N4, N5 | No publish and no read on refusal. |
| FR-008 | T003, T004 | N8 | Comments and logs. |
| FR-009 | T003, T006 | N4, N6, N9, E2 | Exact message text. |
| FR-010 | T009, T010 | Changelog guard and STE gate | No content test (F-19). |

## Constitution Alignment

- The fail rows in plan.md map to tasks or to decisions. Principle VI maps to T003 and T004. Principle VII maps to T004. The function limit maps to T003 and D-8.
- The multi-agent rules map to D-2, D-3, and D-11. The branch name stays accepted for publication only.
- Principle IV maps to T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. T-MERGE covers the container build, the revision label, the deployment, and the health check.
- Principle V passes. The new log text is ASCII.

## Unmapped Tasks

None. Each task maps to at least one requirement.

## Metrics

- Requirements: 10 (FR-001 to FR-010).
- Tasks: 14 (T001 to T010, and four delivery tasks).
- Planned tests: 9 test functions (N1 to N9). Existing end-to-end tests: 2 (E1 and E2).
- Success criteria: 6 (SC-001 to SC-006).
- Remote checks: 100. Present: 86. Stale: 2. Absent: 12.
- Decisions: 12 (D-1 to D-12). Human decisions: 1 (D-2).

## Unresolved Items

- Owner decision D-2: publication of the #4200 candidate through pull request #4208.
- Separate issues recommended by D-11 and D-12: the one-change rule for pull request #4208, the `LivePages.render` length, and the mistapi floor drift. A GitHub write creates each issue, so the owner or the orchestrator files them.
- The reconstruction commit `15c69b1` named in the issue (F-02).
- The ten skipped checks on pull request #4208 (F-12).
