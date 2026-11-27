# Research: Report a missing latest WAN rate

This file holds the decisions, the remote verification table, the sources, and the unverified items. Each code claim cites a path and a line. Each remote check has one row in the table below.

## Decisions

### D-1: Wait for pull request 4208 to release the file

- **Options**: (a) Change main now. (b) Branch from the pull request 4208 head and stack the fix. (c) Transfer the fix to the pull request author. (d) Wait for the merge.
- **Chosen**: (d). If the pull request closes unmerged, open a new record for `GatewayInsightSampleBuilder.build` on main.
- **Reason**: The owner comment on issue 4682 states that the fix stays blocked until pull request 4208 releases the file. AGENTS.md, section "Parallel agents and shared state" (line 242, R-79), states that one file cannot carry two open pull requests. Pull request 4208 is conflicting and changes this file by 658 added lines and 256 deleted lines.
- **Risk**: The fix waits for the merge. The pull request head changed after review (R-70).
- **Human decision required**: No.

### D-2: A missing latest value gives None, never an earlier value

- **Options**: (a) Keep the last valid value and label it stale. (b) Show the last valid value with its timestamp. (c) Show None with a reason.
- **Chosen**: (c).
- **Reason**: The pull request head guide states that missing values remain absent (R-66) and that missing metric values have no points (R-67). The stale label applies to snapshots, not to rate samples (`documentation/wan-performance.md` line 470 on the pull request head, R-80). The value validator requires a reason when the value is None (R-16, lines 16-20).
- **Risk**: Operators lose the earlier number on the page. `raw_values` keeps it for analysis.
- **Human decision required**: No.

### D-3: An absent latest interval counts as missing

- **Options**: (a) Handle null items only, which matches the issue text. (b) Reject the whole response when the latest interval is absent. (c) Treat an absent latest interval like a null item.
- **Chosen**: (c).
- **Reason**: The schema aligns `results` and `rt` by position (R-47). It does not require the latest interval to be present. Without this rule, the builder selects the previous interval as the latest value (R-53).
- **Risk**: Absent and null intervals both report unavailable. A real outage and a missing sample look the same. The reason text does not separate them.
- **Human decision required**: No.

### D-4: Select the latest interval by its expected start time

- **Options**: (a) Use the last array element. (b) Use the latest parsed timestamp. (c) Look up the expected start of the latest interval.
- **Chosen**: (c). The expected start equals `start` plus `interval_seconds` times `maximum_samples` minus one.
- **Reason**: The pull request head already builds the expected starts (R-56) and rejects other timestamps (R-78). The lookup adds no new timestamp assumption.
- **Risk**: If unverified item U-1 is wrong, the lookup finds no interval and reports unavailable. The current code already rejects that input (R-78).
- **Human decision required**: No.

### D-5: Two reasons for missing values

- **Options**: (a) One new reason for every missing case. (b) Keep the old reason only. (c) Two reasons, chosen by whether an earlier valid value exists.
- **Chosen**: (c). The reason is "The latest interval has no value." when an earlier valid value exists. The reason is "The API snapshot has no value." when no valid value exists.
- **Reason**: The pull request head tests assert the old reason (R-81, line 340 of the test file). The new case needs its own text.
- **Risk**: Two strings to maintain. Tests T002 cover both strings.
- **Human decision required**: No.

### D-6: Keep the snapshot partial rule unchanged

- **Options**: (a) Set `partial` when the latest value is missing. (b) Keep the existing rule.
- **Chosen**: (b).
- **Reason**: On the port path, `partial` depends on quality and status events only (R-60). Changing the rule changes the completeness contract for the whole snapshot. The reason text already reports the gap at the metric level.
- **Risk**: A consumer that reads only `partial` misses the gap (analysis item AN-5).
- **Human decision required**: No.

### D-7: Add the tests to the post-merge gateway test file

- **Options**: (a) Add tests to the main path file `tests/unit/wan_dashboard/wan_performance/collection/test_gateway_insights.py` now (R-07). (b) Add a new test module. (c) Add the tests to `tests/unit/wan_performance/test_gateway_insights.py` after the merge.
- **Chosen**: (c).
- **Reason**: Pull request 4208 removes the main path test files, so tests added now would be lost. One test home avoids duplicate cases. The target file already holds a selected-port helper, `responses` (R-65).
- **Risk**: The target file moves if pull request 4208 renames it. Task T001 verifies the path.
- **Human decision required**: No.

### D-8: Update the guide in the same change

- **Options**: (a) Leave the guide unchanged. (b) Add one sentence to the missing-value rule.
- **Chosen**: (b). The sentence goes near line 152 of `documentation/wan-performance.md` (R-67).
- **Reason**: AGENTS.md, section "Documentation" (line 336, R-77), requires the update in the same change. The guide already states the missing-value rule (R-66, R-67).
- **Risk**: None known.
- **Human decision required**: No.

## Remote Verification

Remote checks cover main, pull request head `843be63bc837513b4442dae69da9f0db922e0ed1`, the local `.venv` package, and two GitHub commit facts. Main file blobs equal the local blob hashes (`git hash-object`), so local line numbers match main for those files. The `Result` column uses the values present, absent, partial, or stale.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Main builder selects the last valid value | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 241 |
| R-02 | Main removes null items before selection | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 258 |
| R-03 | Main allows at most one timestamp | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 219 |
| R-04 | Main coverage holds a count | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 244 |
| R-05 | Main reads metric-named arrays | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 251 |
| R-06 | Main partial rule counts samples | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 224 |
| R-07 | Main test file for the builder path | tests/unit/wan_dashboard/wan_performance/collection/test_gateway_insights.py | main | a43cc4479c74747687082b7af65229b1b62aa05c | present | 32 |
| R-08 | Portal registers the WAN dashboard blueprint | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 213 |
| R-09 | Portal insights route | src/interfaces/portals/wan_dashboard/routes.py | main | d58229ce8f0c15998785f88b3cbf5a7009e15f58 | present | 140 |
| R-10 | Portal reads cached insights | src/interfaces/portals/wan_dashboard/services/__init__.py | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 597 |
| R-11 | Portal calls the gateway rate method | src/interfaces/portals/wan_dashboard/services/__init__.py | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 1096 |
| R-12 | Portal hourly series keep index positions | src/interfaces/portals/wan_dashboard/services/__init__.py | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 362 |
| R-13 | Portal traffic series keep index positions | src/interfaces/portals/wan_dashboard/services/__init__.py | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | present | 314 |
| R-14 | Portal has no negative-index selection on insights | src/interfaces/portals/wan_dashboard/services/__init__.py | main | 11fdc93e4740e0a8c083f4f5ed4106448fa42745 | absent | 0 |
| R-15 | Browser reads the last hourly row | src/interfaces/portals/wan_dashboard/static/dashboard.js | main | c0930484b1d20f244e51b64f0076183357f804ec | present | 534 |
| R-16 | Value validator requires a reason when the value is missing | src/interfaces/wan_performance/domain/metric_validation.py | main | 77cfc1da9cbba9ee56e7bc0db4becfa8d2d42f8c | present | 16 |
| R-17 | Measurement rejects a reason when the value is present | src/interfaces/wan_performance/domain/metric_validation.py | main | 77cfc1da9cbba9ee56e7bc0db4becfa8d2d42f8c | present | 28 |
| R-18 | Target test file is absent on main | tests/unit/wan_performance/test_gateway_insights.py | main | none | absent | 0 |
| R-19 | Target guide is absent on main | documentation/wan-performance.md | main | none | absent | 0 |
| R-20 | Route folder 2/2/2 is absent on main | specs/numbered/0/0/1/2/2/2 | main | none | absent | 0 |
| R-21 | Route folder 2 holds five children | specs/numbered/0/0/1/2 | main | none | present | 0 |
| R-22 | Route folder 2/2 holds three children | specs/numbered/0/0/1/2/2 | main | none | present | 0 |
| R-23 | Five-children rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| R-24 | Eight-level base-5 route rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 58 |
| R-25 | Inline comment principle | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-26 | Action logging principle | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R-27 | Repository route rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R-28 | Repository five-children rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 167 |
| R-29 | Tests gate command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R-30 | STE gate row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R-31 | Changelog fragment rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R-32 | Changelog README exists | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| R-33 | Mypy path list | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-34 | Vulture path list | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-35 | Pydocstyle path list | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-36 | Interrogate path list | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-37 | Base-5 radix constant | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-38 | Digit extraction loop | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 28 |
| R-39 | One-file STE writing gate command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 283 |
| R-40 | Test container rule | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| R-41 | Inline comments rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| R-42 | Action logging rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 104 |
| R-43 | Specifications rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 345 |
| R-44 | Operator guide WAN section | documentation/wiki/Web-Portal.md | main | e9dac116b73e6284b46cb6220ec0ca75228fe90c | present | 77 |
| R-45 | Gateway insights operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32717 |
| R-46 | Operation returns the device metric response | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32743 |
| R-47 | Results and timestamps align by position | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94103 |
| R-48 | Result items are string or integer | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94124 |
| R-49 | Example results are integers | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 47779 |
| R-50 | Mistapi gateway insight method | .venv\Lib\site-packages\mistapi\api\v1\sites\insights.py | local-venv | 07bebe3875161acd22eb72554e8b7b5033e2bdd7 | present | 290 |
| R-51 | Mistapi catalog method | .venv\Lib\site-packages\mistapi\api\v1\const\insight_metrics.py | local-venv | 8a17928e289a540eb82fc36f51c57598050783b5 | present | 17 |
| R-52 | Pinned mistapi version directory | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local-venv | none | present | 0 |
| R-53 | Pull request head selects the last valid value | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 282 |
| R-54 | Pull request head coverage uses maximum samples | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 285 |
| R-55 | Builder has six parameters excluding cls | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 271 |
| R-56 | Expected interval starts on the pull request head | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 320 |
| R-57 | Port path selects the ten-minute interval | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 154 |
| R-58 | Port path requests six samples | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 244 |
| R-59 | Pull request head reads results and rt | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 264 |
| R-60 | Port partial flag ignores rate samples | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 182 |
| R-61 | Live route refresh_port on the pull request head | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 327 |
| R-62 | Live service calls collect_for_port | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 63 |
| R-63 | Pull request head registers the WAN performance blueprint | web_portal/app.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | f0d9f5b63eb2f5465a2c5034c7887e7fa32736d3 | present | 214 |
| R-64 | Head test expects None and 12.0 for two metrics | tests/unit/wan_performance/test_gateway_insights.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c681280947cda45485faaa16db574e767e681838 | present | 323 |
| R-65 | Head test helper responses | tests/unit/wan_performance/test_gateway_insights.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c681280947cda45485faaa16db574e767e681838 | present | 687 |
| R-66 | Head guide: missing values remain absent | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 80 |
| R-67 | Head guide: missing metric values have no points | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 152 |
| R-68 | Head parent spec requires explicit missing values | specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery/spec.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 19126c68b5f977bff9d8b09b8d32172c94f0de21 | present | 157 |
| R-69 | Reviewed head commit exists | commit fbb23f8a2348e6840caf479dc10d8841635ea91e | fbb23f8a2348e6840caf479dc10d8841635ea91e | none | present | 0 |
| R-70 | Reviewed head is the current pull request head | compare fbb23f8a2348e6840caf479dc10d8841635ea91e with 843be63bc837513b4442dae69da9f0db922e0ed1 | 843be63bc837513b4442dae69da9f0db922e0ed1 | none | stale | 0 |
| R-71 | Resolve-SpecFeaturePath function | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| R-72 | Python 3.15 requirement | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| R-73 | Pull request section requires gh pr checks watching | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 221 |
| R-74 | Merge section rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 233 |
| R-75 | Symbols gate row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| R-76 | Local gates section heading | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-77 | Documentation section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 336 |
| R-78 | Head rejects timestamps outside expected starts | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 322 |
| R-79 | Parallel agents rule: one file cannot carry two open pull requests | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 242 |
| R-80 | Head guide: snapshots older than five minutes have a stale label | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 470 |
| R-81 | Head test asserts the old no-value reason | tests/unit/wan_performance/test_gateway_insights.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c681280947cda45485faaa16db574e767e681838 | present | 340 |
| R-82 | Head rejects negative, non-finite, or boolean rates | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 345 |
| R-83 | Head rejects misaligned results and timestamps | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 266 |

The table holds 83 rows. Result counts: present 78, absent 4 (R-14, R-18, R-19, R-20), and stale 1 (R-70).

## Sources

- GitHub reads (read-only):
  - `gh issue view 4682` for number, title, body, state, labels, comments, and dates.
  - `gh issue view 4583` for the body and the comments that name issue 4682. Three comments name it. Their URLs are `issues/4583#issuecomment-6726791577`, `issues/4583#issuecomment-6726866382`, and `issues/4583#issuecomment-6727397419`.
  - `gh pr list --search 4682` returned no pull request.
  - `gh pr list --state open` listed the files of each open pull request. Only pull request 4208 changes `snapshot_client.py`. Pull request 4208 changes `snapshot_client.py` by 658 added and 256 deleted lines.
  - `gh pr view 4208` returned state OPEN, head `843be63bc837513b4442dae69da9f0db922e0ed1`, merge state CONFLICTING, and a check roll-up without a failing conclusion.
  - `gh api` on the issues endpoint of jmorrison-juniper/MistHelper for issues 4583, 4681, 4330, and 4200 confirmed the issue types and states. All four are open issues.
  - `gh api` on the commits endpoint for `fbb23f8a2348e6840caf479dc10d8841635ea91e` returned the commit.
  - `gh api` on the compare endpoint with base `fbb23f8` and head `843be63` returned status diverged, ahead 85, behind 42.
  - `gh api` on the git trees endpoint for `main` with recursive output returned 11,404 entries, not truncated.
  - `gh api` on the contents endpoint returned blob SHAs and file bodies for the pull request head files and one spec file.
  - `gh label list` confirmed the label names used in the record.
- Local reads (read-only): AGENTS.md, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four templates in `.specify/templates/` were read in full. The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` was read for its folder shape. The documentation files named in the brief were searched for WAN, gate, and container terms. The cited lines appear in the table above. The code and tests named in this record and the mistapi package in `.venv` were read by line range.
- Coverage documents: `documentation/MIST_API_GET_ENDPOINTS.md` line 1277 and `documentation/MIST_API_MISSING_ENDPOINTS.md` line 1186 both name `getSiteInsightMetricsForGateway`. The missing-endpoints file measures menu usage in `MistHelper.py`. The WAN modules call the method directly, so that list does not change this record.
- Local git (read-only): `rev-parse`, `log -1`, `ls-files`, and `hash-object`. The local main head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- Mist API: `documentation/mist-api-openapi31yaml.yaml` (R-45 to R-49). No live call ran.
- mistapi: `.venv\Lib\site-packages\mistapi` version 0.64.1 (R-50 to R-52).
- Web sources: none. No URL was fetched.
- Skills: none loaded. The issue has no Podman question and no Juniper device behavior question.
- The reference record shape: root files `analysis.md`, `plan.md`, `spec.md`, `tasks.md`, and a `design` folder.

## Unverified

- **U-1**: The `rt` array marks the start of each interval. Reason: OpenAPI does not state it (R-47). The current code assumes it (R-56, R-78). No live response was read.
- **U-2**: Mist sends null items in `results`. Reason: The schema documents string or integer items only (R-48). The current code tolerates null (R-02). No live response was read.
- **U-3**: Mist omits the latest interval in some responses. Reason: The schema does not state this rule. The fix treats it as missing (D-3). No live response was read.
- **U-4**: Which caller fills the main portal insight cache. Reason: Not traced in this pass. The main-path conclusion depends on the index-aligned series (R-12, R-13, R-15), not on the cache writer.
- **U-5**: The final head of pull request 4208. Reason: The head moved between review and this pass (R-70). It may move again before the merge.
- **U-6**: Whether the SQLite and Arango history stores accept None for a rate value. Reason: The store code was not read in this pass.
- **U-7**: The response body shape that mistapi returns to the caller. Reason: Only the method signature was read (R-50). The body handling was not read.
- **U-8**: Later comments on issue 4583. Reason: Only the three comments that name issue 4682 were read.
- **U-9**: No portal route calls the builder on main. Reason: The check used a local search of `src` and `web_portal`, which found no builder reference outside `snapshot_client.py`. A remote code search was not run.
