# Analysis: E2E stall diagnostics

This review compares the specification, the plan, the tasks, the research evidence, and the remote code.
It lists the defects in existing work and the items that stay unresolved.

## 1. Consistency review

### Requirement coverage

| Requirement | Tasks | Planned tests |
| - | - | - |
| FR-001 Arm one watch for each item | T003 | T008, item test |
| FR-002 Write the dump when an item exceeds the threshold | T003 | T008, long-item test |
| FR-003 Threshold default 100, validated override | T003 | T008, invalid-threshold test |
| FR-004 Cancel the watch when the protocol ends | T003 | T008, short-item test |
| FR-005 Boundary records in the trail | T004 | T008, trail-order test |
| FR-006 Diagnostics upload includes both files | T005 | T007, path test |
| FR-007 Cancel message names both causes | T006 | T007, message test |
| FR-008 Guard reads the workflow | T007 | T007 |
| FR-009 Budgets unchanged | T002, T011, T-LOCAL-GATES | Existing guards |
| FR-010 No product file change | T001, T-LOCAL-GATES | Changed-file list |
| FR-011 Changelog fragment | T010, T012 | Changelog policy guard |
| FR-012 Refs, no closing keyword | T-PR, T-MERGE | Pull request body check |

The success criteria map as follows. SC-001 to SC-003 map to the four tests of T008. SC-004 maps to the three tests of T007. SC-005 depends on the post-merge observation in T-REMOTE-CI.

The record has 12 requirements, 16 tasks, and 7 planned tests. The counts match `3736-STATUS.json` and `3736-summary.md`.

### Remote claims

The research record lists 55 remote rows. The STATUS file lists 55 remote checks in the same order. The summary cites the same count.

### Route

The route follows the base-5 rule in `.specify/scripts/powershell/spec-route.ps1`. The function `Get-SpecRadixSegments` converts the number to base 5 and pads it to eight digits.

- Issue 3736 gives base 5 digits 104421, which pad to 00104421. The route is `0\0\1\0\4\4\2\1`, which matches the ROUTE given to this record.
- Issue 4920 gives base 5 digits 124140, which pad to 00124140. The route is `0\0\1\2\4\1\4\0`, which matches the reference record at RC-38.

### Cross-document checks

- Spec clarifications cite research rows RC-17, RC-18, and RC-42. Those rows support the 120-second effective budget.
- Plan Principle IV entry cites UR-4 below.
- Plan Principle I entry cites T012 below.
- The brief template asks for `Closes #3736`. Decision D-7 uses `Refs #3736`. UR-3 records this deviation.

## 2. Defects in existing work

- **DEF-1, issue body counts.** The body reports 429 completed outcomes, 380 passes, 49 skips, and 171 with no result. Comment IC_kwDOQltU8c8AAAABY2yv_A corrects these values to 442, 391, 51, and 158. The local parse in research section 3 agrees with the correction.
- **DEF-2, stale limit in the title.** The title and body name a 15-minute limit. The single job moved to 20 minutes in commit `38d06c48aa01c553ff2fa4d16d819f82dd68dc94` on 2026-10-03. The shards moved to 20 minutes each in commit `0f42cdea6e96b4e5a416e413562a6101aa4f8e37` on 2026-10-16.
- **DEF-3, byte equality claim.** The body says the browser module, the shared fixtures, and the workflow match the granted base byte for byte. That claim holds only at the base commit. On `main`, the workflow blob changed from `cc41c46b8c23d291b73d9137bc78d5765202ded9` to `d51efbc13c0f0a2076680030ed8be7ef7cf64523` (RC-14, RC-04). The harness blob changed from `d8b848ad716fa8ed78ec43cf4d2e542f58044087` to `e450e1855770d2e0ec587935a95233262b118ae1` (RC-21, RC-17). The capture test blob changed from `b8fed6091946f505548c48d34c3ca9b354a8659e` to `b8e5896c26ac04b42579c943b2facbe40d7e9ad7` (RC-25, RC-23).
- **DEF-4, effective budget.** The pytest command sets `--timeout=180` (RC-10, RC-16). The E2E marker sets 120 seconds for each item, and the marker overrides the CLI value (RC-42). The shard guard pins the 180-second value (RC-29). The quality-gate document gives the 120-second budget for coverage shards only (RC-34).
- **DEF-5, misleading cancel message.** The message at line 952 says that every cancellation reached the 20-minute limit (RC-13). Run 44962483189 shows a concurrency cancel with that message. The job ran 11 minutes 12 seconds.
- **DEF-6, diagnostics skipped after the test step.** In job 127446107889, the shard diagnostics step and the cancel message step were both skipped. The cancellation arrived after those steps were skipped. The job had passed all 446 tests. The gap affects only the post-test class of limit events (research section 6.3).
- **DEF-7, stale quality-gate document.** The job list in `documentation/quality-gates.md` is dated 2026-09-26. It omits `playwright_shards` (RC-33).
- **DEF-8, module-level hooks.** `tests/e2e/conftest.py` defines module-level hooks that delegate to classes (RC-19, RC-20, RC-49). Principle II prohibits this pattern for new code. The pattern predates this record (D-10).

## 3. Verification of the issue thread

| Claim | Verdict | Evidence |
| - | - | - |
| Head 6fb9f48, run 37073211456, job 111057821335 | Confirmed | Jobs API and commit API (RC-02) |
| Job cancelled after 15m0s | Confirmed | Check-run annotation |
| 600 collected cases | Confirmed | Log line at 22:38:07.684Z |
| 442 outcomes, 391 passes, 51 skips | Confirmed | Parse in research section 3 |
| Body counts 429, 380, 49, 171 | Corrected | DEF-1 |
| Last pass at 22:44:48.678Z | Confirmed | Parse in research section 3 |
| Cancel at 22:51:56.016Z | Confirmed | Log line |
| Silence longer than 7 minutes | Confirmed | 427.3 seconds |
| Attempt 2: 548 passes and 52 skips | Confirmed | Parse in research section 3 |
| Attempt 2 duration of 489.03 seconds | Not checked | No duration parse was run |
| PR #4236 stop at 581 outcomes, cancel at 07:08:29.654 | Confirmed | Job 116850242205 |
| PR #4403 shard with 414 cases and 272 outcomes | Confirmed | Job 119853643169 |
| PR #4408 APT transfer of 23.9 MB in 10m57s | Not checked | Setup durations in section 6 are consistent, but the transfer figure was not parsed |
| PR #4617 setup budgets of 629 and 573 seconds | Not checked | Pull request body only |

## 4. Unresolved items

- **UR-1, root cause.** The four stall events end at the same test. The cause is unknown (research U-1). The watch and the boundary records gather the evidence for the next event.
- **UR-2, signal delivery.** The signal timer did not produce a report during the stall events (research U-2). D-5 keeps the signal method until the evidence names the blocked call.
- **UR-3, closing keyword.** D-7 uses `Refs #3736`. The orchestrator must confirm this deviation from the brief template.
- **UR-4, deployment pipeline.** Steps 10 to 12 of Principle IV do not run for this change, because no product file changes. The orchestrator must confirm this reading.
- **UR-5, changelog debt.** The `changelog.d/` folder holds 335 children. Task T012 tracks the remediation issue.
- **UR-6, open pull request overlap.** The open pull request #4208 changes web-portal test files. Task T001 checks the overlap before the branch.
- **UR-7, unclassified failures.** The scans did not classify the non-limit E2E failures (research U-6).
- **UR-8, diagnostics gap.** DEF-6 remains. A limit hit after the test step can skip the diagnostics upload.
- **UR-9, CI pytest version.** The attempt-1 log does not show the pytest version (research U-4).
- **UR-10, artifact retention.** The retention period is not checked (research U-5).
- **UR-11, unavailable log.** Job 122682105845 returns HTTP 404 (research U-10).
