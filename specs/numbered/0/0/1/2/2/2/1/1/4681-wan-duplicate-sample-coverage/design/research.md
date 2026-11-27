# Research: WAN Duplicate Sample Coverage

## Method

- The check read issue #4681 and issue #4583 with `gh issue view`. It recorded labels, body, and comments.
- The check read PR #4208 with `gh pr view`. It recorded the state, draft flag, merge state, head, base, file list, and checks.
- Open pull requests were listed with `gh pr list --state open`. Seven PRs are open. Only PR #4208 touches a WAN path.
- Remote main was read with one tree call. The tree has 11,404 entries and is not truncated. Main commit: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- The check read the PR #4208 head `843be63bc837513b4442dae69da9f0db922e0ed1` with one tree call. The tree has 11,030 entries and is not truncated.
- The check decoded remote file bodies from `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=<ref>`. Line numbers come from the decoded text.
- The check hashed local governance files and the OpenAPI file with `git hash-object`. Their blob SHAs equal the remote main blob SHAs. Local line numbers therefore equal remote line numbers.
- No test or gate ran in this research. The brief forbids it.

## Issue Facts

- Issue #4681 is open and titled "Runtime: duplicate WAN samples overstate utilization coverage". It was created at 2026-11-08T20:36:01Z and updated at 2026-11-08T20:43:09Z.
- Labels: `bug`, `web-portal`, and `in-progress`.
- Expected behavior, from the issue body: "Expected: count each expected interval once and mark an hour incomplete when any interval is missing."
- Reproduction steps, from the issue body:
  1. Build a controlled utilization response with timestamps from one expected hour.
  2. Repeat one timestamp and omit another expected interval.
  3. Pass the response through the WAN snapshot validation and summary path.
  4. Observe that duplicate samples can inflate coverage and allow the incomplete hour into congestion summaries.
- Logged observation, from the issue body, verbatim:

```text
Observed: timestamp membership is checked without uniqueness or full interval coverage.
Impact: sample_count and coverage_fraction can overstate completeness.
Affected files: src/interfaces/wan_performance/collection/snapshot_client.py and src/interfaces/wan_performance/domain/summary.py.
Live Mist calls: 0.
```

- The issue body says the finding came from a review of PR #4208 at head `fbb23f8a2348e6840caf479dc10d8841635ea91e`. The current head is `843be63bc837513b4442dae69da9f0db922e0ed1`.
- Owner comment `IC_kwDOQltU8c8AAAABkPPVxA`, created at 2026-11-08T20:43:09Z, says: "The fix remains blocked until #4208 releases the files or its owner hands them over."
- Linked pull requests: `gh pr list --search 4681` returned no pull request. PR #4208 appears in the issue body and in the owner comment, so this record reads it directly.
- PR #4208 state: open, draft, merge state CONFLICTING, 82 changed files. Base `2a6a5844698aeb180fea353e0243034890774565`. Created 2026-10-13T21:42:04Z. Updated 2026-11-22T02:10:45Z. The review decision is empty.
- PR #4208 checks at the current head report success for the lint, security, type, coverage, and end-to-end jobs. The auto-merge jobs report skipped.
- Related issue #4583 is open. Its title is "chore(git): a branch holds work with no pull request". Its comments name PR #4208 as the owner of some files. Those comments are stale (finding A-08 in `analysis.md`).

## Decisions

### D-1 Start the fix after PR #4208 releases both files

- Options: (a) Add the fix to PR #4208 now. (b) Fix `main` now. (c) Start after PR #4208 releases both files.
- Chosen: (c).
- Reason: AGENTS.md lines 244 and 245 forbid two open pull requests on one file. The defect exists only on the PR head (RC-02, RC-07 to RC-11). A fix on `main` finds no defect to change (RC-02).
- Risk: The fix waits on a draft PR with merge conflicts.
- Human decision: No. The rule comes from AGENTS.md. No section 6 category applies.

### D-2 Collapse identical duplicates and reject conflicting duplicates

- Options: (a) Reject every duplicate. (b) Keep the first value. (c) Collapse identical duplicates and reject conflicting duplicates.
- Chosen: (c).
- Reason: The issue expects one count for each interval. PR #4208 treats an unchanged replay as a no-op and a changed value at the same time as an abort (RC-18). Keeping the first value guesses which value is true.
- Risk: A conflicting duplicate stops the scheduled refresh until the source corrects it. The refresh logs the failure (RC-20).
- Human decision: No.

### D-3 Mark an hour incomplete for a missing interval

- Options: (a) Drop the hour. (b) Estimate the missing value. (c) Mark the hour incomplete.
- Chosen: (c).
- Reason: The issue expects an incomplete mark. The PR documentation says congestion needs all six samples known (RC-17). Estimation invents data.
- Risk: Some hours show partial coverage. That result is correct.
- Human decision: No.

### D-4 Add a sample-count guard in the summary

- Options: (a) Keep the coverage-only check. (b) Add `sample_count == 6` to the check. (c) Add a new validation step for inconsistent measurements.
- Chosen: (b).
- Reason: The summary trusts coverage alone (RC-14). The guard catches a future writer that sets coverage without six samples. A class attribute adds no top-level name to `summary.py`.
- Risk: None known. The positive test keeps six-sample hours.
- Human decision: No.

### D-5 Place the tests in the existing test modules

- Options: (a) Create a new test module. (b) Add tests to `test_gateway_insights.py` and `test_calendar_summaries.py`. (c) Add tests to `test_snapshot_client.py`.
- Chosen: (b).
- Reason: AGENTS.md prefers existing test files. The insight tests live in `test_gateway_insights.py` (RC-15, RC-16). A new module adds a child to `tests/unit/wan_performance/`, which holds 14 files in the PR #4208 file list.
- Risk: The two files grow.
- Human decision: No.

### D-6 Keep the labels

- Options: (a) Add a `blocked` label. (b) Remove `in-progress`. (c) Keep `bug`, `web-portal`, and `in-progress`.
- Chosen: (c).
- Reason: The repository has no `blocked` label. The owner keeps the claim. Issue comment `IC_kwDOQltU8c8AAAABkPPVxA` says the fix remains blocked by PR #4208.
- Risk: The labels do not show the blocker. The issue comment shows it.
- Human decision: No.

### D-7 Name the changelog fragment for the issue

- Options: (a) `pr-<number>.md`. (b) `issue-4681-wan-duplicate-sample-coverage.md`. (c) `<YYYY-MM-DD>-<slug>.md`.
- Chosen: (b).
- Reason: No pull request exists yet (RC-34). The issue name applies. The first name stays after the pull request opens (RC-35).
- Risk: None.
- Human decision: No.

### D-8 Keep the Mist request and the 10-minute interval

- Options: (a) Switch to the one-hour interval. (b) Change the limit or page size. (c) Keep the request.
- Chosen: (c).
- Reason: The issue scope covers validation and summary. The OpenAPI schema names `10m` as the interval example (RC-46). The SDK accepts `port_id` and `interval` (RC-48).
- Risk: None new.
- Human decision: No.

### D-9 Record the status as complete and name the dependency

- Options: (a) Status `blocked`. (b) Status `complete` with the dependency named.
- Chosen: (b).
- Reason: This record is complete. The blocker is a merge dependency. Task T002 tracks it, and `depends_on_issues` lists PR #4208.
- Risk: The orchestrator may treat the record as ready. The summary names the blocker.
- Human decision: No.

## Remote Verification

Result values are `present`, `absent`, `partial`, or `stale`. `none` means no blob exists. `not applicable` marks local SDK files, which have no git blob.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Main holds the WAN snapshot client module | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 0 |
| RC-02 | Main rejects more than one gateway insight timestamp | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 219 |
| RC-03 | Main requests the one-hour gateway window | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 302 |
| RC-04 | Main has no summary module | src/interfaces/wan_performance/domain/summary.py | main | none | absent | 0 |
| RC-05 | PR head holds the snapshot client module | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 0 |
| RC-06 | PR head selects the 10-minute interval for port samples | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 154 |
| RC-07 | PR head bounds timestamps by six, not by unique intervals | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 266 |
| RC-08 | PR head checks timestamp membership without uniqueness | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 322 |
| RC-09 | PR head sets coverage from the raw count | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 285 |
| RC-10 | PR head sets utilization sample count from the raw count | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 357 |
| RC-11 | PR head sets congestion from a raw count of six | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 435 |
| RC-12 | PR head holds the summary module | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 0 |
| RC-13 | PR head rejects duplicate hours only | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 89 |
| RC-14 | PR head congestion durations check coverage only | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 416 |
| RC-15 | PR head gateway insight tests have no in-response duplicate case | tests/unit/wan_performance/test_gateway_insights.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c681280947cda45485faaa16db574e767e681838 | absent | 0 |
| RC-16 | PR head has a repeated sample time test for persistence | tests/unit/wan_performance/test_gateway_insights.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c681280947cda45485faaa16db574e767e681838 | present | 1014 |
| RC-17 | PR head documentation says all six samples must be known | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 321 |
| RC-18 | PR head documentation says changed sample data aborts at the same time | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 441 |
| RC-19 | PR head live service calls the port insight collection | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 63 |
| RC-20 | PR head scheduled refresh catches ValueError and logs | src/interfaces/wan_performance/background_refresh.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | b08895652d7450e24399bed66c3763b46a0fa5c9 | present | 146 |
| RC-21 | PR head adds a sixth child to collection | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 0 |
| RC-22 | PR head adds a sixth child to domain | src/interfaces/wan_performance/domain/calendar.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88e0598aa66d24086e9dfe0378c374af87ea9305 | present | 0 |
| RC-23 | PR head adds a sixth child to integration | src/interfaces/wan_performance/integration/arango_history.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 0aa4dc6e4d622de6e99b6bcbe7277af69095b56f | present | 0 |
| RC-24 | PR head adds a sixth child to the WAN package | src/interfaces/wan_performance/background_refresh.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | b08895652d7450e24399bed66c3763b46a0fa5c9 | present | 0 |
| RC-25 | AGENTS rule forbids two open pull requests on one file | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 244 |
| RC-26 | AGENTS rule claims the issue before the branch | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 187 |
| RC-27 | copilot-instructions local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-28 | copilot-instructions serial merge slot | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 485 |
| RC-29 | Constitution five-children rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| RC-30 | Constitution function limits | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 78 |
| RC-31 | Constitution inline comment rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 206 |
| RC-32 | Constitution action logging rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 237 |
| RC-33 | Constitution names mistapi as the sole interface | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| RC-34 | Changelog naming table | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| RC-35 | Changelog keeps the first name | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 32 |
| RC-36 | Changelog guard test exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-37 | CI sets the mypy path list | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-38 | CI sets the pylint and interrogate thresholds | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 122 |
| RC-39 | Quality gate table lists test_quality_gate | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 63 |
| RC-40 | README has no WAN text | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| RC-41 | Reference record spec exists on main | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-42 | Route for issue 4681 is absent on main | specs/numbered/0/0/1/2/2/2/1/1 | main | none | absent | 0 |
| RC-43 | OpenAPI defines the gateway stats route | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32714 |
| RC-44 | OpenAPI interval is integer seconds | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94093 |
| RC-45 | OpenAPI results align with rt | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94106 |
| RC-46 | OpenAPI interval example is 10m | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59722 |
| RC-47 | Endpoint inventory maps the route to the SDK module | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1277 |
| RC-48 | SDK gateway insight method accepts port_id and interval | .venv\Lib\site-packages\mistapi\api\v1\sites\insights.py | local | not applicable | present | 290 |
| RC-49 | SDK gateway insight route | .venv\Lib\site-packages\mistapi\api\v1\sites\insights.py | local | not applicable | present | 341 |
| RC-50 | SDK org port search method | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | local | not applicable | present | 1157 |
| RC-51 | SDK insight catalog method | .venv\Lib\site-packages\mistapi\api\v1\const\insight_metrics.py | local | not applicable | present | 17 |
| RC-52 | Installed SDK version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local | not applicable | present | 0 |
| RC-53 | PR head builds the normalized insight sample | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 270 |
| RC-54 | PR head begins the point validation method | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 309 |
| RC-55 | PR head computes congestion metric values | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 429 |
| RC-56 | PR head computes utilization samples | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 350 |
| RC-57 | PR head reads the rt timestamp array | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 265 |
| RC-58 | PR head begins the congestion duration class | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 390 |
| RC-59 | PR head begins the threshold method | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 406 |
| RC-60 | PR head declares the congestion duration summary class | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 54 |
| RC-61 | PR head derives the congestion metric key | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 428 |
| RC-62 | PR head declares the gateway insight class | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 114 |
| RC-63 | PR head declares the first summary class | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 18 |
| RC-64 | PR head calls the gateway insight method with limit six and page one | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 244 |
| RC-65 | PR head builds the expected interval set | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 320 |
| RC-66 | PR head returns validated points | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 325 |
| RC-67 | PR head calls the gateway insight method | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 235 |
| RC-68 | PR head calls the org device stats method | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 140 |
| RC-69 | PR head calls the insight catalog method | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 151 |
| RC-70 | PR head calls the org port search method | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 645 |
| RC-71 | PR head test helper builds rt timestamps | tests/unit/wan_performance/test_gateway_insights.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c681280947cda45485faaa16db574e767e681838 | present | 710 |
| RC-72 | PR head documentation describes ten-minute rate requests | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 431 |
| RC-73 | Development setup document exists | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 0 |
| RC-74 | Copilot instructions language rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 18 |
| RC-75 | OpenAPI device metric response schema starts | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94086 |
| RC-76 | PR head live service collects before publication | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 42 |
| RC-77 | PR head live service writes port history before returning | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 77 |
| RC-78 | PR head live service publishes the snapshot after the history write | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 48 |

Row count: 78. This count matches the `remote_checks` array in `STATUS.json` and the count in `summary.md`.

## Sources

Local paths are relative to the read-only repository root. URLs fetched: none.

- `AGENTS.md`, lines 187 and 244 to 245. Governs the issue claim and file ownership.
- `.github/copilot-instructions.md`, lines 18, 50, and 485. Governs the language, local gates, and the serial merge slot.
- `.specify/memory/constitution.md`, lines 40, 78, 206, 237, and 279. Governs the five-item rule, function limits, comments, logging, and the SDK rule.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`. Governs the headings of each artifact.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`. Governs the shape of the record. I copied its shape only.
- `changelog.d/README.md`, lines 24 to 33. Governs the fragment name.
- `.github/workflows/ci.yml`, lines 78 to 127, 237, 311, 529, 565, 584, and 600. Governs the gate commands and the path lists.
- `documentation/quality-gates.md`, line 63. Governs the test quality gate.
- `documentation/development-setup.md`. Searched for the environment and pytest commands. The search read the venv and pytest sections.
- `documentation/architecture.md`. Read in full. It describes an older `src/` layout.
- `documentation/container-deployment.md`. Searched for test containers. The search found the section at line 141. Not applicable to this fix.
- `documentation/operator-guide.md`, line 63. Menu 279 only. The search found no WAN coverage text.
- `documentation/mist-api-openapi31yaml.yaml`, lines 32714 to 32743, 59715 to 59723, and 94086 to 94123. Governs the Mist request and response shapes.
- `documentation/MIST_API_GET_ENDPOINTS.md`, line 1277. Maps the route to `mistapi.api.v1.sites.insights`.
- `documentation/MIST_API_MISSING_ENDPOINTS.md`, line 1186. Lists the route in the missing-endpoint inventory, which begins at line 212.
- `.venv\Lib\site-packages\mistapi\api\v1\sites\insights.py`, lines 290 to 302 and 341. Governs the SDK gateway insight method.
- `.venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py`, lines 397, 1157, and 1592. Governs the SDK org stats methods.
- `.venv\Lib\site-packages\mistapi\api\v1\const\insight_metrics.py`, lines 17 and 32. Governs the SDK catalog method.
- Remote GitHub reads: issue #4681, issue #4583, PR #4208, open PR list, and label list. Read on 2026-11-26 with `gh`.

Skills used: none. No local skill covers Python SDK response validation.

## Unverified

- U-01: Mist repeats a timestamp in a live response. Reason: this issue makes zero live Mist calls. The OpenAPI text (RC-45) describes alignment and does not state uniqueness.
- U-02: The manual refresh route response to a `ValueError`. Reason: this run did not read `presentation/live_routes.py`.
- U-03: The operator guide has no WAN coverage text. Reason: the check used a local search. This run did not hash the local file against the remote blob.
- U-04: Test and gate results for the fix. Reason: the brief forbids running tests in this run. The fix does not exist yet.
- U-05: The PR #4208 merge date and its final head. Reason: the state changes after this read.
- U-06: The `documentation/architecture.md` drift. Reason: the check used the local file only.
