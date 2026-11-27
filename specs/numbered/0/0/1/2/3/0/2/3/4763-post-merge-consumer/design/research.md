# Research: Main workflow recovery

## R1. Route and scope

The route for issue 4763 is `0/0/1/2/3/0/2/3`. The width is eight base-5 digits. The value is 4763 in base 5:

```text
4763 = 1 x 5^5 + 2 x 5^4 + 3 x 5^3 + 0 x 5^2 + 2 x 5^1 + 3 x 5^0
```

The leading zeros fill 5^7 and 5^6. The route function is `python_route` in `tests/guardrails/test_spec_route_contract.py` (RC-79).

Scope: the consumer workflow, the shared workflow at `d63a120`, the three guard test files, the changelog fragment, the legacy record, and open pull request #4886.

## R2. Consumer state on main

- The pin is `d63a120487cecf750184cb178387cdc25c0a7635` at line 61 (RC-01).
- The list names four main workflows at line 65 (RC-02).
- The trigger and permission block is at lines 25 to 60 (RC-03 to RC-05). The close job is at lines 79 and 85 (RC-06, RC-07).
- Pull request #4815 changed the pin from `0fdcf610c87a281bd4e952486d6154b2bf45fec4`, added `ste-lint.yml` to the list, and changed the guard constant and its assertion (RC-47, RC-08, RC-09). Its merge commit is `11569e461fc6f025e502d54bf00b40213fae9654` (RC-48).
- The tip at check time is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (RC-66).

## R3. Shared logic at d63a120

- The enable step requests auto-merge and records a confirmed merge with `merged=true` at line 234 (RC-25).
- The enable step leaves a pending request without merged output at lines 238 to 241 (RC-26).
- A workflow-file change blocks the merge call and posts a notice (RC-27).
- The dispatch job starts for a merged closed event at lines 265 and 266 (RC-29). It starts for a non-closed event only after a confirmed merge at line 274 (RC-28). It skips a canceled run at line 258 (RC-30).
- The dispatch job checks the current tip at line 311. It counts runs on that tip, not the newest run, at lines 321 to 326 (RC-31). It allows five checks spaced 20 seconds apart (RC-32). It serializes dispatch with a concurrency group (RC-33). It starts each missed workflow with `gh workflow run` at line 365 and exits 1 after a failed start at lines 385 to 389 (RC-34).
- The shared header states that a workflow-token event starts no run (RC-23, lines 7 to 12).

## R4. Hosted evidence

| Path | Evidence | Rows |
| - | - | - |
| Immediate | Eight labeled runs. Each logs one confirmed merge and four `Started` lines. Each merge is by `app/github-actions`. | RC-56 to RC-63 |
| Merged-close | Run 43793516716 covered ci, codeql, and ste-lint, and started container-build. | RC-49 |
| Merged-close, human merge | Closed run 44952654909 completed its dispatch job after the merge of pull request 4871. | RC-64 |
| Container dispatch | Run 43793676817 ran on commit 11569e4. | RC-50 |
| Scheduled coverage | Run 45786075135 logged coverage for four workflows on the current tip. | RC-65 |
| Workflow-file block | Run 43800244711 logged the block for pull request 4816. Pull request 4816 merged by a person with the owner account. | RC-54, RC-55 |
| Baseline | Run 42920503087 ran the enable step and skipped the dispatch job. The old pin is not inspected here (U-a). | RC-53 |
| No coverage | Commit c9aa2bb had no main workflow run. Commit ac046837 had zero runs. | RC-51, RC-52 |

The list of the 100 most recent merged pull requests holds eight pull requests with the `auto-merge` label, merged after 2026-11-16. Each has one labeled run with a successful enable job and a successful dispatch job. GitHub created each run 7 to 14 seconds before its merge. The first dispatch start came about 100 seconds after the merge.

## R5. Delayed-path survey

Method: list the 400 most recent Auto-merge runs. Keep the `pull_request` runs with conclusion `success`. Read each run's jobs. The survey returned 11 runs. It found five closed-event runs for human merges, with the enable job skipped and the dispatch job successful. It found six labeled runs for token merges, and each had a confirmed merge. No run had an enable job that succeeded while its dispatch job reported skipped (RC-68).

The survey does not reach runs before 2026-11-21. RC-56 and RC-57 cover pull requests 4864 and 4865 (2026-11-20) only. The survey does not include their closed runs (U-b).

## R6. Scheduled survey

Method: list the scheduled Auto-merge runs. The query returned 21 runs created after 2026-11-16T04:00Z. Each log was read for `Started` lines. None logged a start (RC-67). Run 45786075135 logged four `already covers the tip.` lines (RC-65).

## R7. Open pull request #4886

Pull request #4886 is a Dependabot bump. It moves the pin from `d63a120` to `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (RC-70). Its only changed file is `auto-merge.yml`. Its Quality Gates run fails the assertion in `test_merge_recovery_uses_the_verified_shared_commit` at line 145 (RC-71). The shared reusable workflow blob is the same at both commits (RC-35). The upstream commit `2239e7bd` changes other files, which this record does not compare (U-d).

## R8. Push workflows on main and the wiki decision

Five workflows start on a push to `main`: `ci.yml` (RC-36), `codeql.yml` (RC-37), `container-build.yml` for listed paths (RC-38), `ste-lint.yml` (RC-39), and `wiki-publish.yml` for wiki paths (RC-40). The main-workflow list names the first four. The workflows `close-linked-issues.yml`, `windows-audit-report.yml`, `windows-timeout-budget.yml`, and `release.yml` do not start on a push to `main` (RC-43 to RC-46).

## R9. Legacy record verification

The legacy record is at `specs\numbered\0\0\1\2\3\0\2\3\4763-post-merge-consumer`. It has five files. Its content is a draft to verify.

| ID | Legacy claim | Result | Rows |
| - | - | - | - |
| L-01 | spec.md line 7 says `Local implementation` | stale | RC-16 |
| L-02 | FR-001 pins the reviewed revision | verified | RC-01, RC-08 |
| L-03 | FR-002 lists the four workflows | verified | RC-02, RC-09 |
| L-04 | FR-003 keeps triggers, permissions, guard, and close job | verified | RC-03 to RC-07 |
| L-05 | FR-004 treats a pending request as not merged | verified | RC-26, RC-28 |
| L-06 | FR-005 keeps manual, scheduled, and merged-close recovery | verified | RC-05, RC-29, RC-49, RC-65 |
| L-07 | FR-006 creates no test merge | verified | RC-47 |
| L-08 | SC-001 accepts manual start and push to main | verified | RC-36 to RC-39 |
| L-09 | SC-002 guard rejects the old revision and a missing workflow | verified | RC-08, RC-09 |
| L-10 | SC-003 keeps hosted acceptance open | stale | RC-56 to RC-63, RC-68 |
| L-11 | plan.md line 24 says a guard class exceeds five members | stale | RC-13 |
| L-12 | plan.md says each workflow accepts dispatch and push to main | verified | RC-36 to RC-38 |
| L-13 | tasks T001 to T004 are delivered | verified | RC-01, RC-08, RC-14, RC-18 |
| L-14 | tasks T005 is open | stale | RC-19 |
| L-15 | analysis.md describes the shared gates | verified | RC-25 to RC-30 |
| L-16 | checklist says hosted acceptance is separate | verified | RC-21 |

Totals: 12 verified, 4 stale, 0 absent.

## R10. Gate applicability

The changed files are Markdown record files under `specs/`. No Python, YAML, or instruction file changes. The local gates table therefore has no applicable row except the guard tests that read `specs/` (RC-79, RC-80). The STE command names five other files (RC-73 mentions the wider rule). The CI jobs for citation lint (RC-84) read `src` and `tests` only. The bandit job scans the repository root (RC-85). The SpecKit task audit is advisory (RC-86). The `tests/guardrails/test_auto_merge_issue_close.py` file reads the consumer workflow, so it stays in the gate set as a regression check.

## R11. Decisions

Each decision names the options, the choice, the reason, the risk, and the human flag. No decision requires a human (`human_decision_required` is false for each).

### D-1 Recovery by dispatch after a confirmed merge

- Options: (a) dispatch after a confirmed merge. (b) A GitHub App token for the merge. (c) A merge queue. (d) Dispatch on every accepted request.
- Choice: (a). The shared workflow at `d63a120` already implements it (RC-25, RC-28).
- Reason: Option (a) needs no new credential. GitHub honors `workflow_dispatch`. The confirmed-merge gate prevents duplicate starts.
- Risk: A delayed merge depends on the closed path or the schedule. The schedule adds up to six hours.

### D-2 A pending request does not start recovery

- Options: (a) start only after a confirmed merge, a closed merged event, a scheduled run, or a manual start. (b) Start on each accepted request. (c) Start only on closed events.
- Choice: (a).
- Reason: Option (b) can start before the merge. Option (c) misses the eight immediate-path merges. Those merges started no closed run in the survey (RC-58 to RC-63, RC-68).
- Risk: A delayed merge waits for the closed path or the schedule.

### D-3 Coverage check before each start

- Options: (a) five coverage checks spaced 20 seconds apart. (b) Start without a check. (c) Check only the newest run.
- Choice: (a) (RC-31, RC-32).
- Reason: Option (b) duplicates runs. Option (c) reads run lists that can be stale.
- Risk: The coverage checks add about 100 seconds. A failed lookup starts nothing (RC-31).

### D-4 Keep four main workflows and exclude wiki-publish.yml

- Options: (a) keep four workflows. (b) Add `wiki-publish.yml`.
- Choice: (a).
- Reason: The wiki workflow header gives token-merge recovery to its daily schedule and states the trade-off (RC-41). The wiki workflow commits nothing when its pages match (RC-42). Option (b) adds one run for each token merge for a read surface.
- Risk: The wiki can lag up to 24 hours after a token merge that changes `documentation/wiki/`. The daily schedule and a maintainer start cover the lag.

### D-5 Count logged ordinary merges as acceptance evidence

- Options: (a) count logged ordinary merges whose pull request has the `auto-merge` label. (b) Require a formal review decision. (c) Require a new test merge.
- Choice: (a).
- Reason: AGENTS.md makes the label the approval step after green checks (RC-72). The eight pull requests have no review decision, so option (b) has no data. The owner forbids option (c) (RC-93).
- Risk: The owner can reject the label as approval. The immediate evidence would then need a new review.

### D-6 Close issue 4763 only after delayed-path evidence

- Options: (a) close after SC-003 and orchestrator approval. (b) Close now on immediate evidence. (c) Close after a fixed time.
- Choice: (a).
- Reason: The owner states that acceptance needs both paths (RC-93, RC-94). Option (b) contradicts that rule. Option (c) has no evidence basis.
- Risk: The issue can stay open for a long time. A delayed case needs a late label or a new commit on a labeled pull request.

### D-7 The record pull request uses `Refs #4763`

- Options: (a) `Refs #4763`. (b) `Closes #4763`, the default in the brief.
- Choice: (a).
- Reason: A merge with a closing keyword closes the issue before D-6 passes.
- Risk: Someone must close the issue by hand after D-6 passes.

### D-8 Keep the pin at d63a120 and do not merge pull request #4886 as is

- Options: (a) keep `d63a120` and leave #4886 to its owner. (b) Merge #4886 as is. (c) Move the pin and the guard constant in one manual pull request.
- Choice: (a) now. Option (c) is the route for a future bump.
- Reason: Option (b) fails the guard test (RC-71). The shared reusable workflow blob stays the same (RC-35), but the record does not compare other shared files (U-d). Option (c) changes a workflow file, so it needs a manual merge (D-10).
- Risk: Dependabot can keep opening bump pull requests until the owner changes the pin.

### D-9 Reuse the legacy slug at the same route

- Options: (a) reuse `post-merge-consumer` at `specs\numbered\0\0\1\2\3\0\2\3`. (b) Use a new slug.
- Choice: (a).
- Reason: The route and the issue number stay fixed. The slug names the same body of work (RC-15). A second folder would split one issue across two records.
- Risk: T-PR must replace each legacy file. A partial replacement leaves a mixed record.

### D-10 Manual merge for workflow-file changes

- Options: (a) one manual protected squash merge by an owner account. (b) A GitHub App token. (c) Remove the guard.
- Choice: (a).
- Reason: The guard blocks a token merge of a workflow file (RC-27). Pull request 4816 used the manual route (RC-55). Option (b) needs credential provisioning. Option (c) removes a safety control.
- Risk: The merge depends on one account.

## R12. Remote verification table

Method: each row is one check. Results: `present` means the claim holds. `stale` means a legacy statement no longer holds. `absent` means the expected evidence does not exist in the surveyed window. The `Blob or commit` column holds a file blob SHA, a commit SHA, or a run head SHA. The upstream rows name `jmorrison-juniper/misthelper-devtools` in the path. Each row names a GitHub REST or CLI read.

| ID | Claim | Path | Ref | Blob or commit | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Consumer pins upstream commit d63a120 | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 61 |
| RC-02 | Consumer lists four main workflows at line 65 and sets report-orphaned-push at line 67 | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 65 |
| RC-03 | Consumer enables pull_request types labeled and closed | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 25 |
| RC-04 | Consumer push trigger skips main | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 35 |
| RC-05 | Consumer schedule at line 44, workflow_dispatch at line 46, empty top-level permissions at line 50, job scopes at lines 56 to 60 | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 44 |
| RC-06 | Consumer close job requires a merged closed event or a schedule | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 79 |
| RC-07 | Consumer close job calls a shared close workflow pinned to a full commit | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 85 |
| RC-08 | Guard test pins commit d63a120 | tests/guardrails/test_auto_merge_issue_close.py | main | 54dfdc345dcd492a7df80fc243cf36a354b4556a | present | 46 |
| RC-09 | Guard test expects exactly four main workflows | tests/guardrails/test_auto_merge_issue_close.py | main | 54dfdc345dcd492a7df80fc243cf36a354b4556a | present | 159 |
| RC-10 | Guard test requires a push to main for each main workflow | tests/guardrails/test_auto_merge_issue_close.py | main | 54dfdc345dcd492a7df80fc243cf36a354b4556a | present | 166 |
| RC-11 | Guard test defines 17 test functions, the first at line 90 | tests/guardrails/test_auto_merge_issue_close.py | main | 54dfdc345dcd492a7df80fc243cf36a354b4556a | present | 90 |
| RC-12 | Guard test module defines 18 top-level names, the first at line 27 | tests/guardrails/test_auto_merge_issue_close.py | main | 54dfdc345dcd492a7df80fc243cf36a354b4556a | present | 27 |
| RC-13 | Legacy plan line 24 says a guard class exceeds five members. The largest class holds five test functions. | specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/plan.md | main | 5621478a7cd2534ef5892a73bd6b41cce2c4af73 | stale | 24 |
| RC-14 | Release-note fragment for the consumer change exists | changelog.d/issue-4763-post-merge-consumer.md | main | 1ac1fce1900535ab082a3911661ad50004373103 | present | 1 |
| RC-15 | Legacy spec.md exists on main | specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/spec.md | main | 2f429c7ec34078c1ee07dc121a105b46a75f874c | present | 0 |
| RC-16 | Legacy spec.md line 7 says Local implementation | specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/spec.md | main | 2f429c7ec34078c1ee07dc121a105b46a75f874c | stale | 7 |
| RC-17 | Legacy plan.md exists on main | specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/plan.md | main | 5621478a7cd2534ef5892a73bd6b41cce2c4af73 | present | 0 |
| RC-18 | Legacy tasks.md marks T004 delivered | specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/tasks.md | main | cd17213c2fcc8438a023d5c88261119f9dc1c1ee | present | 8 |
| RC-19 | Legacy tasks.md keeps T005 open | specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/tasks.md | main | cd17213c2fcc8438a023d5c88261119f9dc1c1ee | stale | 12 |
| RC-20 | Legacy analysis.md exists on main | specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/analysis.md | main | 04a18f3a17f243596d05c54d3734074b492686ce | present | 0 |
| RC-21 | Legacy requirements checklist exists and has the hosted acceptance item | specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/design/checklists/requirements.md | main | 86f5e3515b7556b07f7c9711887a75c163f8a002 | present | 17 |
| RC-22 | Upstream commit d63a120 exists in misthelper-devtools | jmorrison-juniper/misthelper-devtools commits | d63a120487cecf750184cb178387cdc25c0a7635 | d63a120487cecf750184cb178387cdc25c0a7635 | present | 0 |
| RC-23 | Upstream reusable workflow exists at d63a120, its header states the token rule at lines 7 to 12, and its inputs sit at lines 48 to 75 | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 7 |
| RC-24 | Upstream pull request 87 merged with merge commit d63a120 | jmorrison-juniper/misthelper-devtools pulls/87 | main | d63a120487cecf750184cb178387cdc25c0a7635 | present | 0 |
| RC-25 | Upstream logs acceptance at line 194, writes merged output at line 234, and logs verification at line 235 only after a confirmed merge | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 234 |
| RC-26 | Upstream enable job runs only for labeled non-closed events (lines 84 to 87) and leaves a pending request without merged output (log at line 239, branch at lines 238 to 241) | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 238 |
| RC-27 | Upstream blocks a token merge of a workflow file | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 116 |
| RC-28 | Upstream dispatch for non-closed events needs a successful enable job and a confirmed merge (lines 273 and 274), and also runs for schedule and workflow_dispatch events (lines 261 and 262) | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 274 |
| RC-29 | Upstream dispatch accepts a merged closed event | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 265 |
| RC-30 | Upstream dispatch skips canceled runs with !cancelled() | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 258 |
| RC-31 | Upstream reads the current tip once at line 311, stops before any start when the lookup fails (lines 311 to 314), and counts runs on that tip, not the newest run, at lines 321 to 326 | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 311 |
| RC-32 | Upstream allows five coverage checks spaced 20 seconds apart | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 301 |
| RC-33 | Upstream serializes dispatch with a concurrency group | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 284 |
| RC-34 | Upstream logs coverage at lines 339 and 363, counts queued runs at lines 335 and 336, starts a missed workflow with gh workflow run at line 365, logs the start at line 366, logs the final coverage line at line 390, and exits 1 after a failed start at lines 385 to 389 | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | d63a120487cecf750184cb178387cdc25c0a7635 | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 365 |
| RC-35 | Upstream reusable workflow blob at 2239e7bd equals the blob at d63a120 | jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8 | present | 0 |
| RC-36 | ci.yml is named Quality Gates and pushes to main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 23 |
| RC-37 | codeql.yml pushes to main | .github/workflows/codeql.yml | main | 2ef072fbddd473f841c5877f4d89b7c7760aeaf0 | present | 14 |
| RC-38 | container-build.yml pushes to main for listed paths | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| RC-39 | ste-lint.yml pushes to main | .github/workflows/ste-lint.yml | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 25 |
| RC-40 | wiki-publish.yml pushes to main for wiki paths and runs daily | .github/workflows/wiki-publish.yml | main | 212707cfe8b7c7809f4a7992fe96ea8dd71e171b | present | 22 |
| RC-41 | wiki-publish.yml header says the schedule catches token-merged pull requests | .github/workflows/wiki-publish.yml | main | 212707cfe8b7c7809f4a7992fe96ea8dd71e171b | present | 6 |
| RC-42 | wiki-publish.yml reports a no-op run without a commit | .github/workflows/wiki-publish.yml | main | 212707cfe8b7c7809f4a7992fe96ea8dd71e171b | present | 88 |
| RC-43 | close-linked-issues.yml has no push trigger | .github/workflows/close-linked-issues.yml | main | 42a085ac6240518b028862c290ec9502a5b13b2a | present | 20 |
| RC-44 | windows-audit-report.yml pushes to branches other than main | .github/workflows/windows-audit-report.yml | main | 2d4e608b038dbe20f522bd296f707126a0ad37bb | present | 5 |
| RC-45 | windows-timeout-budget.yml pushes to branches other than main | .github/workflows/windows-timeout-budget.yml | main | 1caf671d77b9a4462a7cd06aa4c3fe481023aaa0 | present | 5 |
| RC-46 | release.yml runs on version tags only | .github/workflows/release.yml | main | e81c05798c7609344d2d59b94114d7d9f76263be | present | 5 |
| RC-47 | Pull request 4815 changed the pin from 0fdcf610 to d63a120 and added ste-lint.yml to the list | pulls/4815 | main | 11569e461fc6f025e502d54bf00b40213fae9654 | present | 61 |
| RC-48 | Commit 11569e4 exists and four main workflows ran on it | commits/11569e461fc6f025e502d54bf00b40213fae9654 | main | 11569e461fc6f025e502d54bf00b40213fae9654 | present | 0 |
| RC-49 | Merged-close run 43793516716 covered three workflows and started container-build | actions/runs/43793516716 | jmorrison-juniper-post-merge-consumer-integration | 829aaa08c5a8e2f7560e36281e85435b08ba5c01 | present | 0 |
| RC-50 | Container dispatch run 43793676817 ran on commit 11569e4 | actions/runs/43793676817 | main | 11569e461fc6f025e502d54bf00b40213fae9654 | present | 0 |
| RC-51 | Commit c9aa2bb exists and no main workflow ran on it | commits/c9aa2bbc01893a07bb7eec1a6462026a6e70b41b | main | c9aa2bbc01893a07bb7eec1a6462026a6e70b41b | present | 0 |
| RC-52 | Commit ac046837 exists with zero workflow runs | commits/ac046837b2bef943f0edbcd3298456265d7014fe | main | ac046837b2bef943f0edbcd3298456265d7014fe | present | 0 |
| RC-53 | Baseline run 42920503087 ran the enable step and skipped the dispatch job | actions/runs/42920503087 | fix/4755-2fa-login-credentials | 3d09862c340d9fa86416fdf3f4ef31d3c0216745 | present | 0 |
| RC-54 | Blocked run 43800244711 reported a workflow-file change and posted the notice | actions/runs/43800244711 | jmorrison-juniper-windows-audit-report-portability | 362c797b178ca980dba162b3230a4effd3e2ad8f | present | 0 |
| RC-55 | Pull request 4816 was merged by jmorrison-juniper at commit 114dd21 | pulls/4816 | main | 114dd21a9561134530769cd282990d770515d4a1 | present | 0 |
| RC-56 | Immediate path on pull request 4864 with run 44817305047 | pulls/4864 | main | 6eca11b88566bb1428ab3ddcdf5df92850c8af67 | present | 0 |
| RC-57 | Immediate path on pull request 4865 with run 44828207234 | pulls/4865 | main | b2828ffb439714c5cfc697dbf8ca207dc3e9a7f2 | present | 0 |
| RC-58 | Immediate path on pull request 4880 with run 44968350716 | pulls/4880 | main | b1360b31674a3e9082c2d4103953bfc01941e786 | present | 0 |
| RC-59 | Immediate path on pull request 4913 with run 45474446529 | pulls/4913 | main | 24f2eb8c14c6ff274bf880d150105a9d4045c2aa | present | 0 |
| RC-60 | Immediate path on pull request 4918 with run 45491725974 | pulls/4918 | main | 0788b975ea45df840d003dd997c684dbe847c448 | present | 0 |
| RC-61 | Immediate path on pull request 4924 with run 45729141283 | pulls/4924 | main | 4e81b2a4a724e29476270564be927f797def82be | present | 0 |
| RC-62 | Immediate path on pull request 4940 with run 45743063874 | pulls/4940 | main | ccff03e05a686ac3f7c14fddb0828cd373c6e822 | present | 0 |
| RC-63 | Immediate path on pull request 4941 with run 45773895615 | pulls/4941 | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-64 | Closed-event run 44952654909 completed its dispatch job after the merge of pull request 4871 | pulls/4871 | main | 23379f0e075557cd5c0761a79f23ad8d3583e296 | present | 0 |
| RC-65 | Scheduled run 45786075135 logged coverage for all four workflows on tip f03c6c9 | actions/runs/45786075135 | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-66 | Tip of main is f03c6c9 at 2026-11-26T07:15:01Z | commits/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-67 | None of the 21 scheduled Auto-merge runs created after 2026-11-16T04:00Z logged a start | actions/workflows/auto-merge.yml/runs?event=schedule | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| RC-68 | None of the 11 successful pull_request runs in the 400 most recent Auto-merge runs shows a pending request | actions/workflows/auto-merge.yml/runs?event=pull_request | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| RC-69 | Issues 4769 and 4770 closed on 2026-11-12, about 10.5 hours after the token merge of pull request 4772 | issues/4769 | main | ac046837b2bef943f0edbcd3298456265d7014fe | present | 0 |
| RC-70 | Open pull request 4886 changes only auto-merge.yml and moves the pin to 2239e7bd | pulls/4886 | dependabot/github_actions/jmorrison-juniper/misthelper-devtools/dot-github/workflows/reusable-auto-merge.yml-2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | present | 0 |
| RC-71 | Quality Gates run of pull request 4886 fails the pin assertion in the guard test | actions/runs/45064239338 | dependabot branch of pull request 4886 | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | present | 145 |
| RC-72 | AGENTS.md requires the auto-merge label only after green checks | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 230 |
| RC-73 | AGENTS.md asks for the STE gate on each Markdown file | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| RC-74 | Copilot instructions list the Tests gate command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-75 | Copilot instructions describe wiki-publish as a push or a daily schedule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 476 |
| RC-76 | Constitution Principle I states the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-77 | Constitution Principle IV states the deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| RC-78 | Spec route script exists | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 0 |
| RC-79 | Route guard defines 23 test functions, computes routes at line 33, and needs pwsh at line 64 | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 33 |
| RC-80 | Folder guard limits each managed group to five children | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 33 |
| RC-81 | Folder guard reads 792 grandfathered legacy children | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 136 |
| RC-82 | Folder guard defines 9 test functions, the first at line 133 | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 133 |
| RC-83 | Baseline manifest exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| RC-84 | CI citation lint reads src and tests only | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 702 |
| RC-85 | CI bandit scans the repository root | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| RC-86 | CI SpecKit task audit is advisory | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 750 |
| RC-87 | Quality gates documentation names the post-merge dispatch check | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 139 |
| RC-88 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-89 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-90 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-91 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-92 | Close linked issues on merge runs with event workflow_dispatch exist on commits 4e81b2a, ccff03e, and f03c6c9 | actions/runs (close linked issues dispatch runs) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-93 | Issue 4763 comment 12 says no test-only merge and no held pull request release for acceptance | issues/4763 comment IC_kwDOQltU8c8AAAABm6x4og | main | IC_kwDOQltU8c8AAAABm6x4og | present | 0 |
| RC-94 | Issue 4763 is open after comment 10 reopened it for hosted acceptance | issues/4763 comment IC_kwDOQltU8c8AAAABm53wiQ | main | IC_kwDOQltU8c8AAAABm53wiQ | present | 0 |
| RC-95 | No open pull request touches the record route. Pull request 4886 touches auto-merge.yml only | pulls (7 open pull requests) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |

## R13. Sources

- Local: `AGENTS.md` (lines 230, 340, 345) and `.github/copilot-instructions.md` (lines 50, 61, 471, 476, 478).
- Local: `.specify/memory/constitution.md` (lines 38, 143, 175, 235) and the four templates under `.specify/templates/` (headings).
- Local: the reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` (shape only).
- Remote: GitHub REST and CLI reads for the paths named in the table. The record fetches no URL. The shared workflow header (RC-23) and the issue history state the platform rule in A-1.
- Not applicable: the Mist API file `documentation/mist-api-openapi31yaml.yaml`, the mistapi SDK, and the container or operator guides. This change calls no Mist endpoint and changes no container or operator behavior.
- Skills: none loaded. The issue concerns GitHub Actions dispatch, not Podman or Juniper device behavior.

## R14. Unverified

- **U-a**: The pin in effect for run 42920503087. The issue states the cause. This record did not read the old file at that run's head.
- **U-b**: Closed runs for pull requests 4864 and 4865. They fall before the survey window.
- **U-c**: Whether a closed run starts after a delayed merge (A-3). Delayed-path evidence is absent (RC-68).
- **U-d**: The record does not check other shared files at commit `2239e7bd`. It compares only the reusable workflow blob (RC-35).
- **U-e**: Whether the `auto-merge` label is an approval. D-5 decides yes. The owner may decide otherwise.
- **U-f**: The source of the close-linked-issues dispatch runs (RC-92).
