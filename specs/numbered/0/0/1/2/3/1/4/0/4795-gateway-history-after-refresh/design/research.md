# Research: Gateway History After an Ordinary Refresh

## Method

This research is read-only. No file in the repository changed. No test, linter, build, or repository script ran. GitHub reads used `gh` with the account variable from the brief. Remote file and tree reads used `gh api`. Local SDK files were read with views. Git blob IDs for `.venv` files were computed as SHA-1 over the Git object header and the file bytes, without a write.

## Existing Record and Route

- A local search of `specs\` for folders named `4795-*` found none.
- The remote tree has 11,404 entries, and it is not truncated. No path in it contains `4795`.
- META_DIR holds no file that starts with `4795`.
- Result: no legacy record exists. Nothing is reused, and no record needs verification under brief section 3, steps 3 and 4.
- Route: 4795 in base 5 is `123140`. Padded to eight digits, it is `00123140`, which gives the segments `0 0 1 2 3 1 4 0`.
- Check: the reference record 4920 gives `124140` in base 5, padded to `00124140`. That matches its route `0\0\1\2\4\1\4\0`. The route script uses base 5 and width 8 for numeric records (R78 to R80).
- Record folder: `specs\numbered\0\0\1\2\3\1\4\0\4795-gateway-history-after-refresh`.

## GitHub Facts

| Object | Fact | Read with |
| - | - | - |
| Issue 4795 | OPEN. Labels `bug`, `web-portal`, and `in-progress`. Created 2026-11-13. One owner comment names commit `d7a706d` as the local repair review. The comment says the candidate remains unpublished. | `gh issue view 4795 --json` |
| Pull request 4208 | OPEN and unmerged. Head branch `jmorrison-juniper-4200-migrate-mistwanperformance` at `843be63bc837513b4442dae69da9f0db922e0ed1`. Base `main`. 82 files. Body line 42 reads `Refs #4200, #4793, #4794, #4795, #4797, and #4798. This PR does not close #4200.` | `gh pr view 4208 --json` and `gh pr list --search 4795` |
| Pull request 4208 checks | 42 SUCCESS. 10 SKIPPED: seven from `auto-merge` and three from `close-linked-issues`. | `statusCheckRollup` |
| Commit `d7a706d` | Committed 2026-11-13 at 20:26:55 UTC. Parent `07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc`. Title `fix(wan-performance): make repeated history refreshes safe`. Body `Address #4793, #4794, and #4795 in the #4200 candidate.` 19 files. | `gh api` commit read |
| Comparison from `d7a706d` to `843be63` | The head is 30 commits ahead, and 36 files differ. The blob of `live_routes.py` changed from `acdab416661d6c6ea37bee1eeb10870745ba2543` to `98827fc73a3d241859f539a03451d5cccf4d2e48`. | `gh api` compare read |
| Commit `15c69b1` | HTTP 422, with the message `No commit found for SHA`. | `gh api` commit read |
| Local git | Commit `d7a706d` exists locally. `git merge-base --is-ancestor d7a706d main` returned 1, so `d7a706d` is not on local `main`. | `git cat-file`, `git merge-base` (local only, not counted) |
| `main` | Commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, committed 2026-11-26. The local checkout matches it. | `gh api` commit and tree reads |
| Issues 4200, 4793, 4794, 4797, and 4798 | All OPEN. Issue 4200 is the feature issue, with labels `feature`, `web-portal`, `in-progress`, `networking`, and `observability`. Issues 4793 and 4794 are bugs. Issues 4797 and 4798 are test failures in the WLAN RADIUS area. Pull request 4208 references 4797 and 4798 only. | `gh issue view N --json` |

## Remote Verification Table

Columns: `#` is the row number. `Path` is a repository path, a local `.venv` path, or a GitHub object. `Ref` is the commit or branch that the check reads, or `main`. `Blob SHA` is the Git blob SHA for a file, and it is the commit SHA for a commit row. `Result` is one of `present`, `absent`, `partial`, or `stale`. `Line` is the line number in the file, or 0 when the check tests existence only.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | Repair commit exists on GitHub | commits/d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | present | 0 |
| R02 | Reconstruction commit named in the issue | commits/15c69b1176f7ae7c24e010aba3d29915ef228610 | 15c69b1176f7ae7c24e010aba3d29915ef228610 | none | absent | 0 |
| R03 | Parent of the repair commit | commits/07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | present | 0 |
| R04 | Candidate head contains the repair commit | compare d7a706d71cf13661cf33e5b4a96ddafd79b6b67b to 843be63bc837513b4442dae69da9f0db922e0ed1 | 843be63bc837513b4442dae69da9f0db922e0ed1 | 843be63bc837513b4442dae69da9f0db922e0ed1 | present | 0 |
| R05 | Main commit | commits/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R06 | Live history module absent on main | src/interfaces/wan_performance/presentation/live_routes.py | main | none | absent | 0 |
| R07 | Live service module absent on main | src/interfaces/wan_performance/collection/live_service.py | main | none | absent | 0 |
| R08 | Background refresh module absent on main | src/interfaces/wan_performance/background_refresh.py | main | none | absent | 0 |
| R09 | Pull request changelog fragment absent on main | changelog.d/pr-4208.md | main | none | absent | 0 |
| R10 | WAN performance documentation absent on main | documentation/wan-performance.md | main | none | absent | 0 |
| R11 | Live end-to-end test module absent on main | tests/e2e/web_portal/test_wan_performance_live.py | main | none | absent | 0 |
| R12 | Organization snapshot method on main | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 75 |
| R13 | Organization snapshot sets gateway insights to none on main | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 88 |
| R14 | Gateway insights return empty without a target on main | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 277 |
| R15 | Main worker calls the legacy snapshot method | src/interfaces/portals/wan_dashboard/services/worker.py | main | 084a141c490f3b6bfa4faa8f568fdf3ea090f3c7 | present | 363 |
| R16 | Main identity module defines the gateway identity | src/interfaces/wan_performance/domain/identity.py | main | 437582449d8c3355f71aa35390050cb06be0ddc1 | present | 66 |
| R17 | Parent gateway filter keeps only gateway records | src/interfaces/wan_performance/presentation/live_routes.py | 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | 8664001d056d2896e3300c367d7b84a2e0f24940 | present | 45 |
| R18 | Parent gateway refusal returns the port-or-peer message | src/interfaces/wan_performance/presentation/live_routes.py | 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | 8664001d056d2896e3300c367d7b84a2e0f24940 | present | 47 |
| R19 | Head defines the history class | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 48 |
| R20 | Head method read spans lines 52 to 79 | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 52 |
| R21 | Head method _select_identity starts at line 108 | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 108 |
| R22 | Head gateway set accepts gateway, circuit, and peer records | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 121 |
| R23 | Head returns no identity for two or more gateways | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 123 |
| R24 | Head gateway refusal message text | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 65 |
| R25 | Head port-or-peer refusal message text | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 67 |
| R26 | Head read and _select_identity carry no inline comments | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | absent | 52 |
| R27 | Head read logs nothing before the history read | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | absent | 75 |
| R28 | Head method render spans lines 159 to 222 | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 159 |
| R29 | Head method window resolves the selected identity | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 97 |
| R30 | Retained view refuses a missing identity | src/interfaces/wan_performance/presentation/inspection/windows.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 31fad7b8258b2ad9bdbaf3e80e004c7885577c4d | present | 66 |
| R31 | E1 regression for the scoped-then-ordinary sequence | tests/e2e/web_portal/test_wan_performance_live.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d485c28afb5bf4bd6de20ba9291feb9b267babac | present | 2325 |
| R32 | E2 regression for ambiguous and foreign identity | tests/e2e/web_portal/test_wan_performance_live.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d485c28afb5bf4bd6de20ba9291feb9b267babac | present | 2392 |
| R33 | E2 asserts the gateway refusal message | tests/e2e/web_portal/test_wan_performance_live.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d485c28afb5bf4bd6de20ba9291feb9b267babac | present | 2408 |
| R34 | Unit tests call the history read | tests/unit/wan_performance/test_gateway_insights.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c681280947cda45485faaa16db574e767e681838 | absent | 0 |
| R35 | A test asserts the port-or-peer refusal message | tests/e2e/web_portal/test_wan_performance_live.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d485c28afb5bf4bd6de20ba9291feb9b267babac | absent | 0 |
| R36 | Identity isolation test for history reads | tests/unit/wan_performance/test_history_repository.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 87cdafb890339ee361f0447ae932679ee9d6d93c | present | 749 |
| R37 | Port rows become circuit records | src/interfaces/wan_performance/collection/snapshot_records.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | a4d3d1f9c7407aa37702a4e9a2d7b65ce1e1df33 | present | 154 |
| R38 | Peer rows become peer records | src/interfaces/wan_performance/collection/snapshot_records.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | a4d3d1f9c7407aa37702a4e9a2d7b65ce1e1df33 | present | 168 |
| R39 | Circuit identity holds its gateway | src/interfaces/wan_performance/domain/identity.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c7baea89e2ac50d37237f8e99294c3d1db13c1b6 | present | 90 |
| R40 | Peer identity holds its gateway | src/interfaces/wan_performance/domain/identity.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c7baea89e2ac50d37237f8e99294c3d1db13c1b6 | present | 116 |
| R41 | Refresh accepts an optional gateway target | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 34 |
| R42 | Refresh writes history before publishing | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 46 |
| R43 | Background worker refresh runs without a target | src/interfaces/wan_performance/background_refresh.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | b08895652d7450e24399bed66c3763b46a0fa5c9 | present | 145 |
| R44 | Candidate snapshot method accepts an optional target | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 45 |
| R45 | Documentation states the resolution rule | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 391 |
| R46 | Documentation states the refusal rule | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 392 |
| R47 | Changelog fragment names issue 4795 | changelog.d/pr-4208.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 3d571a370f9cd3b6a7e3367b96dcc652ddf4653e | present | 19 |
| R48 | Pull request body contains the closing keyword for 4795 | pull request 4208 body | 843be63bc837513b4442dae69da9f0db922e0ed1 | 843be63bc837513b4442dae69da9f0db922e0ed1 | absent | 0 |
| R49 | Pull request body names issue 4795 with Refs | pull request 4208 body | 843be63bc837513b4442dae69da9f0db922e0ed1 | 843be63bc837513b4442dae69da9f0db922e0ed1 | present | 42 |
| R50 | Mist search ports function is defined | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | local mistapi 0.64.1 | 247e4526005342dc895408519d5974a7aa86aefd | present | 1157 |
| R51 | Mist search ports URI | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | local mistapi 0.64.1 | 247e4526005342dc895408519d5974a7aa86aefd | present | 1254 |
| R52 | Mist peer path URI | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | local mistapi 0.64.1 | 247e4526005342dc895408519d5974a7aa86aefd | present | 1644 |
| R53 | Mist devices stats URI | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | local mistapi 0.64.1 | 247e4526005342dc895408519d5974a7aa86aefd | present | 458 |
| R54 | Mist gateway insights URI | .venv\Lib\site-packages\mistapi\api\v1\sites\insights.py | local mistapi 0.64.1 | 07bebe3875161acd22eb72554e8b7b5033e2bdd7 | present | 341 |
| R55 | Mist insight metrics URI | .venv\Lib\site-packages\mistapi\api\v1\const\insight_metrics.py | local mistapi 0.64.1 | 8a17928e289a540eb82fc36f51c57598050783b5 | present | 32 |
| R56 | OpenAPI operation searchOrgSwOrGwPorts | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 22023 |
| R57 | OpenAPI operation searchOrgPeerPathStats | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 22454 |
| R58 | OpenAPI operation getSiteInsightMetricsForGateway | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32714 |
| R59 | AGENTS writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R60 | AGENTS one change per pull request | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 223 |
| R61 | AGENTS closing keyword in the body | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| R62 | Copilot instructions local gates section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R63 | Copilot instructions Types row reads MYPY_PATHS | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 60 |
| R64 | Copilot instructions mistapi floor 0.64.0 conflicts with pyproject | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| R65 | Copilot instructions changelog fragment rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R66 | Constitution rule VI inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R67 | Constitution rule VII action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R68 | Constitution function limit of 25 lines | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 85 |
| R69 | Constitution mistapi 0.59 floor conflicts with the pin | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | stale | 279 |
| R70 | Constitution escalation for three files or two classes | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 431 |
| R71 | pyproject mistapi floor 0.64.1 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| R72 | requirements pin mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R73 | CI MYPY_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R74 | CI VULTURE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R75 | CI PYDOCSTYLE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R76 | CI INTERROGATE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R77 | Quality gates require the strict end-to-end environment | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 68 |
| R78 | Spec route base is five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R79 | Spec route numeric width defaults to eight | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| R80 | Numeric route call uses the default width | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 49 |
| R81 | Changelog README names the pull request fragment | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| R82 | Mist GET reference lists searchOrgSwOrGwPorts | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 929 |
| R83 | Mist missing-endpoint report lists searchOrgSwOrGwPorts | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | present | 876 |
| R84 | Changelog fragment guard test exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| R85 | Main snapshot method calls the ports search | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 109 |
| R86 | Main snapshot method calls the peer path search | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 121 |
| R87 | Main gateway insights call the devices stats method | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 283 |
| R88 | Main gateway insights call the gateway insights method | src/interfaces/wan_performance/collection/snapshot_client.py | main | eca7564b5210f211ff8e1464d6720c810086d429 | present | 295 |
| R89 | Repair commit changes no collection file | commits/d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | present | 0 |
| R90 | Head gateway identity natural key | src/interfaces/wan_performance/domain/identity.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c7baea89e2ac50d37237f8e99294c3d1db13c1b6 | present | 69 |
| R91 | Head circuit identity natural key | src/interfaces/wan_performance/domain/identity.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c7baea89e2ac50d37237f8e99294c3d1db13c1b6 | present | 105 |
| R92 | Head peer identity natural key | src/interfaces/wan_performance/domain/identity.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | c7baea89e2ac50d37237f8e99294c3d1db13c1b6 | present | 133 |
| R93 | Head gateway page route | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 282 |
| R94 | Head render selects records by page filters | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 183 |
| R95 | Head render aborts with HTTP 404 when no record matches | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 185 |
| R96 | Head store-missing unavailable message | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 71 |
| R97 | Head store-error unavailable message | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 79 |
| R98 | pyproject requires Python 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R99 | Head organization check returns the gateway only for the service organization | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 126 |
| R100 | Head single-record rule for port and peer kinds | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 113 |

Counts: 100 rows. Present: 86. Stale: 2 (R64 and R69). Absent: 12 (R02, R06, R07, R08, R09, R10, R11, R26, R27, R34, R35, and R48).

Notes:

- R89 checks the file list of commit `d7a706d` from the GitHub commit read. The list has 19 files, and none is under `src/interfaces/wan_performance/collection/`.
- R50 to R55 are local `.venv` files. Their blob SHA is the Git blob ID that was computed for each file. They are not repository paths.
- The candidate snapshot method (R44) differs from the main snapshot method (R12). Rows R85 to R88 describe main only.

## Decisions

Each decision names its alternatives, the chosen option, the reason, and the risk.

### D-1 Repair source

- **Decision**: Use commit `d7a706d` at pull request head `843be63` as the repair. Check its blob before publication.
- **Alternatives**: (a) Write a new repair on `main`. Rejected: the history method is absent on `main` (R06, R07). (b) Use reconstruction commit `15c69b1`. Rejected: GitHub has no such commit (R02).
- **Reason**: The repair is verified at head (R19 to R23), and both regressions exist (R31, R32).
- **Risk**: The file changed after `d7a706d` (GitHub facts). Mitigation: quickstart Scenario 4 checks the blob.

### D-2 Publication vehicle. HUMAN-DECISION-REQUIRED

- **Decision**: Publish the candidate through pull request #4208 after the owner authorizes publication. The recommended option is to publish with the corrected body from D-3.
- **Alternatives**: (a) A new branch from `main` with only the repair. Rejected: the repair needs the candidate modules that `main` lacks (R06 to R08). (b) Split the candidate into one pull request per issue before publishing. Deferred to a separate issue (D-11). (c) Keep the repair unpublished. Rejected: the issue stays open with no path to `main`.
- **Reason**: Pull request #4208 is the only verified path that carries the repair. The issue says it does not authorize publication, so the owner decides.
- **Risk**: One squash commit places 82 files for six issues on `main`. Mitigation: run every applicable gate and require CI success before the merge (T-LOCAL-GATES and T-REMOTE-CI).

### D-3 Closing keyword

- **Decision**: Put `Closes #4795` in the pull request body. Keep `Refs #4200`. Do not close issue #4200.
- **Alternatives**: (a) Keep `Refs #4795` and close the issue by hand after the merge. Rejected: a manual step can be missed. (b) Close the issue before the merge. Rejected: the issue must stay open until `main` has the repair.
- **Reason**: The squash merge reads the body (R61).
- **Risk**: The issue closes before a person checks `main`. Mitigation: T-MERGE reruns E1 and E2 on `main`, and the issue reopens if either fails.

### D-4 Test layering

- **Decision**: Add nine unit tests, N1 to N9. Keep the two end-to-end tests, E1 and E2.
- **Alternatives**: (a) End-to-end tests only. Rejected: slower, and no direct count of history reads. (b) Unit tests only. Rejected: no route proof for the scoped-then-ordinary sequence.
- **Reason**: A unit test checks each read count directly. The end-to-end test checks the page.
- **Risk**: N1 and E1 overlap in part. Mitigation: N1 checks selection, and E1 checks the page output.

### D-5 Refusal rule

- **Decision**: Refuse zero gateways, two or more gateways, and a gateway of another organization. This is a fail-closed rule.
- **Alternatives**: (a) Choose the most frequent gateway. Rejected: a guessed gateway can show another gateway's history. (b) Choose the first record's gateway. Rejected: the result depends on record order.
- **Reason**: The issue asks to reject genuinely ambiguous identities (R22, R23, R99).
- **Risk**: A mixed page refuses. Mitigation: the gateway page filters by gateway and site first (R94).

### D-6 Port and peer rule

- **Decision**: Keep the single-record rule and the port-or-peer message for port and peer kinds (R25, R100).
- **Alternatives**: (a) Use the gateway resolver for port and peer kinds. Rejected: the issue does not ask for it, and it changes working pages.
- **Reason**: Scope. N7 protects this behavior.
- **Risk**: None known.

### D-7 Comments and action logs

- **Decision**: Add an inline comment to each executable line in the touched methods. Add info and debug logs around each action. Log counts only.
- **Alternatives**: (a) Record the violation and defer it. Rejected: Principle VI forbids committing such code (R66). (b) Rewrite the module. Rejected: out of scope.
- **Reason**: Principles VI and VII (R66, R67), and the findings F-03 and F-04.
- **Risk**: A log line can expose data. Mitigation: log counts only, and N8 checks the messages.

### D-8 Extract the history read

- **Decision**: Move the history read, the summary build, and the storage-error handling into `_read_history`. Keep `read` at 25 lines or fewer.
- **Alternatives**: (a) Keep `read` at 28 lines and record the violation. Rejected: the logs in D-7 make it longer. (b) Move the refusal branch too. Rejected: more churn and no gain.
- **Reason**: The function limit of Principle I (R68), and the touched function (R20).
- **Risk**: A signature change. Mitigation: the public signature of `read` stays the same.

### D-9 Documentation and release note

- **Decision**: Reuse documentation lines 391 and 392 (R45, R46) and fragment line 19 (R47). Create no new fragment.
- **Alternatives**: (a) A new `issue-4795-*.md` fragment. Rejected: it duplicates the note in `pr-4208.md`. (b) New documentation text. Rejected: the rule already has one location.
- **Reason**: One release note fragment for each change (R65, R81).
- **Risk**: A split publication must move the note with its change.

### D-10 Labels

- **Decision**: Keep the labels `bug`, `web-portal`, and `in-progress`. Add no label and remove no label.
- **Alternatives**: (a) Remove `in-progress` now. Rejected: the repair is not on `main`.
- **Reason**: The issue stays open and active.
- **Risk**: The status label stays until the repair reaches `main`.

### D-11 Pull request split

- **Decision**: Do not split pull request #4208 in this issue. A separate issue handles the one-change rule.
- **Alternatives**: (a) Split now. Rejected: it needs a new base and an owner choice. (b) Record nothing. Rejected: AGENTS.md requires one change for each pull request (R60).
- **Reason**: The scope of this issue.
- **Risk**: The process defect stays until the separate issue closes.

### D-12 Pre-existing defects

- **Decision**: Record three defects as separate issues, and fix none of them here. The defects are the `render` length (R28), the mistapi floor drift (R64, R69, R71), and the candidate branch name (F-10).
- **Alternatives**: (a) Fix them in this publication. Rejected: they touch unrelated code. (b) Record nothing. Rejected: analysis.md must give each defect an action.
- **Reason**: Scope and review size.
- **Risk**: The known defects ship with the publication.

## Mist API and SDK Notes

- The repaired read path calls the history store. It calls no mistapi function (R20, R27: the history read at line 75).
- The mistapi definitions and URIs that the WAN package reaches are R50 to R55. The OpenAPI operations for the same endpoints are R56 to R58.
- The main snapshot method calls the ports search, the peer path search, the devices stats method, and the gateway insights method (R85 to R88).
- The pinned version is 0.64.1 in `requirements.txt` (R72). The local `.venv` dist-info `METADATA` file reads `Version: 0.64.1`. That local read is not a repository claim.
- The menu reference lists `searchOrgSwOrGwPorts` and `searchOrgPeerPathStats` as GET endpoints (R82). The missing-endpoint report lists them as not used by `MistHelper.py` (R83).

## Sources

Local sources read. They count as local evidence, not as remote checks:

- `AGENTS.md`, `.github/copilot-instructions.md`, and `.specify/memory/constitution.md`, read in full or in ranges.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`.
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`, read for shape only.
- `documentation/quality-gates.md`, the gate table. The development setup and container guides were checked. The container guide applies only when a test starts a container, and these tests start none.
- `documentation/architecture.md` and `documentation/operator-guide.md` were searched for WAN performance terms. Neither holds a WAN performance section. Neither file informed a decision.
- `.venv\Lib\site-packages\mistapi` for function definitions and URIs (read-only).
- `META_DIR\4921-STATUS.json` and `META_DIR\4921-summary.md`, read for format only.
- `META_DIR\validate-drafts.ps1`, read for its checks. It was not run, because brief rule 2 forbids script runs.
- Local git reads: `rev-parse`, `log`, `grep`, `show --stat`, `branch --contains`, `merge-base`, and `cat-file`.
- GitHub reads through `gh`: the issue, the pull request, the search, the commits, the comparison, the tree, and the contents of each file in the table.

No URL was fetched. No upstream check is recorded.

## Skills

No skill was loaded. The issue concerns Python selection logic in a web portal module. It does not concern Podman or Juniper device behavior.

## Unverified

- U-1: The issue says the `LiveHistory` class sits in a committed route module at `15c69b1`. The commit does not exist on GitHub (R02). The claim is unverified.
- U-2: No test ran. The pass or fail state of N1 to N9, E1, and E2 is unknown. Brief rule 2 forbids test runs. The red proof is open (T008).
- U-3: The STE score of this record is not measured. Brief rule 2 forbids linter runs.
- U-4: The ten skipped checks on pull request #4208 have no pass or fail state. They count as unknown under AGENTS.md.
- U-5: The migration safety of the storage changes in commit `d7a706d` is outside this issue. The record does not review them.
- U-6: No upstream mistapi source was fetched. The local `.venv` source is the evidence used.
