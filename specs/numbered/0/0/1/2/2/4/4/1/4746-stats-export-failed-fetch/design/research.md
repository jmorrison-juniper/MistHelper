# Research: Statistics Export Processed Count After Failed Fetch

## Summary

Both statistics exports emit a completion event with processed count 1 after `APIDataFetcher.execute()`. They emit it whatever the return value is. Two issue statements are stale or local only. The reservation claims are local, and the old test paths moved in PR #4358. Remote evidence uses `gh api` on `main`. The head at check time is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Decisions

### D-1 Derive the processed count from the fetch result

- Alternatives: (a) skip the completion event on False. (b) Set `was_stopped` to True on failure. (c) Add a `progress_failed` event type. (d) Count 1 for True and 0 for False.
- Chosen: (d).
- Reason: The start and completion events stay paired (FR-004). The event schema stays unchanged (FR-006, RC-20 to RC-22). `was_stopped` documents user interruption (RC-22), so option (b) misuses it. Option (c) changes the telemetry contract for every consumer.
- Risk: A consumer that reads any completion event as success must read the count. The contract file states the rule. The rate-limit path also returns False and reports 0 (RC-16). The count then matches the disk state.

### D-2 Report 0 for an empty response

- Alternatives: (a) report 1 for an empty response. (b) Change the fetcher to return three states.
- Chosen: 0, by the same rule as D-1.
- Reason: An empty response returns False before any export call (RC-09). No file is written. Option (b) changes the shared fetcher contract, which this issue excludes.
- Risk: The count alone does not separate an empty response from a failure. The fetcher logs a warning for an empty response (RC-09 and the lines 86 to 89 block). It logs an error for an HTTP failure (RC-13).

### D-3 Edit the two methods in place

- Alternatives: (a) add a helper method to `OrgDeviceStatsExporter`. (b) add a module-level helper function. (c) add a helper class in a new module.
- Chosen: edit in place.
- Reason: The class defines 22 methods (RC-07). Principle I forbids a new direct child in a noncompliant parent (RC-50). A module-level helper adds a top-level name to a module that already defines the class. Option (c) adds a file to `src\operations\exporting\export`, which holds 49 direct children (RC-71).
- Risk: The two methods repeat the processed count line. The 25-line debt grows by one line per method (RC-74 to RC-77).

### D-4 Place the new test module in a new `stats` folder

- Alternatives: (a) add tests to `tests\unit\export\test_org_device_stats_exporter.py`. (b) add a file to `tests\unit\prod_readiness\standalone\operations\exporting\inventory\`. (c) add a file to `tests\unit\api\`.
- Chosen: a new `stats` folder under `tests\unit\prod_readiness\standalone\operations\exporting\`. That parent holds three children on main (RC-70). The new folder holds one file.
- Reason: Option (a) edits a reserved file (C-1). The parent `tests\unit\export\` holds 55 direct children (RC-69). Option (b) uses the last free child slot in a folder that already holds the device statistics tests. Option (c) places an exporter test in the API client folder.
- Risk: The folder name and the test basename must stay unique. Both are absent on main (RC-68).

### D-5 Hold publication until the reservation release is recorded

- Alternatives: (a) publish now. (b) wait until issue #1794 merges. (c) add the fix to the #1794 slice.
- Chosen: prepare the branch and the gates now. Open the pull request only after the #1794 owner records a release of the source file. Open it only when the serial publication hold allows a slot (RC-46).
- Reason: The issue asks for coordination with the owner (issue comment of 2026-11-10 16:07:44Z). Option (b) can delay the fix for an unknown period. Option (c) combines two subjects in one issue. AGENTS.md forbids that combination (RC-49).
- Risk: The pull request waits. The coordination checklist makes the wait visible.
- Human decision: No. The hold is a repository process rule. It is not licensing, legal text, data destruction, credential policy, or product priority.

### D-6 Keep the progress labels "13" and "15"

- Alternatives: (a) change the labels to the registry menu numbers 15 and 16. (b) Keep the labels and record the mapping.
- Chosen: (b).
- Reason: The labels are telemetry identifiers (RC-01, RC-04). Consumers match them. Option (a) changes a contract outside this issue. The mismatch is recorded in analysis finding F-1, with the registry rows RC-25 and RC-26 and the handler rows RC-27 and RC-28.
- Risk: Operators see labels that differ from the menu numbers. The contract file and the analysis record the mismatch.

### D-7 Name the fragment for the issue

- Alternatives: (a) `pr-<number>.md`. (b) `<YYYY-MM-DD>-<slug>.md`.
- Chosen: `issue-4746-stats-export-failed-fetch.md`.
- Reason: The pull request does not exist yet. The naming rule uses the issue form when only the issue exists (RC-53). The rule keeps the first name after the pull request opens (RC-54). The change is visible to users, so the fragment is required.
- Risk: None known.

### D-8 Leave the exception path unchanged

- Alternatives: (a) emit a completion event with count 0 in a `finally` block. (b) Convert each exception into False.
- Chosen: leave unchanged.
- Reason: The fetcher re-raises unexpected errors (RC-11). The menu layer owns that failure. The issue asks for the count after a failed request. An exception produces no count, so no false count appears.
- Risk: A progress start can remain without a completion event after an exception (analysis F-6). A follow-up issue records it.

## Remote Verification

Method: `gh api` on `main` at head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Blob SHAs are read from the recursive tree, which lists 11,404 entries and is not truncated. Line numbers are read from the decoded file body. Files that the contents API cannot return in full, and the installed SDK, use a local `git hash-object` comparison. All 1,268 documentation and README blobs matched their remote SHAs. Rows that name the installed SDK use the local hash and say so.

Result meanings: `present` means the claim holds on main. `absent` means the item is not on main, or a search found no text. Line 0 means that no line applies.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Device export emits progress start with label 13 and operation device_stats | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 96 |
| RC-02 | Device export discards the fetch result before the completion event | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 108 |
| RC-03 | Device completion event passes literal processed count 1 | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 111 |
| RC-04 | VPN peer export emits progress start with label 15 and operation vpn_peer_stats | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 486 |
| RC-05 | VPN peer export discards the fetch result before the completion event | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 497 |
| RC-06 | VPN peer completion event passes literal processed count 1 | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 500 |
| RC-07 | Class OrgDeviceStatsExporter starts at line 57 and defines 22 methods | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 57 |
| RC-08 | Fetch returns False when the fetch step returns False | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 84 |
| RC-09 | Fetch returns False when the response holds no rows | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 89 |
| RC-10 | Fetch returns True after the export step | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 93 |
| RC-11 | Fetch re-raises unexpected errors | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 97 |
| RC-12 | Fetch step returns False after an HTTP failure | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 132 |
| RC-13 | HTTP failure check returns True for status 400 or higher | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 160 |
| RC-14 | Pagination call assigns rows inside the try block | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 137 |
| RC-15 | Status 500 or higher is invalid and triggers a retry | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 231 |
| RC-16 | Rate-limit branch saves rows only when rows exist | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 340 |
| RC-17 | SDK call forwards keyword arguments from the exporter | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 178 |
| RC-18 | Retry ceiling default is 3 | src/foundation/runtime/config/runtime_settings.py | main | 4f47d44085d5bddef87f809cfd0ef5879052205f | present | 15 |
| RC-19 | Retry delay default is 5.0 seconds | src/foundation/runtime/config/runtime_settings.py | main | 4f47d44085d5bddef87f809cfd0ef5879052205f | present | 16 |
| RC-20 | Completion event signature takes processed count and was_stopped | src/mist/intelligence/analytics/telemetry_emitter.py | main | 1d8044bea88864fa090989f22f60080b79a5e16f | present | 226 |
| RC-21 | Completion event writes the processed count to items_processed | src/mist/intelligence/analytics/telemetry_emitter.py | main | 1d8044bea88864fa090989f22f60080b79a5e16f | present | 241 |
| RC-22 | The was_stopped field documents user interruption | src/mist/intelligence/analytics/telemetry_emitter.py | main | 1d8044bea88864fa090989f22f60080b79a5e16f | present | 242 |
| RC-23 | ProgressContext is a frozen dataclass | src/foundation/models/dataclasses/progress_event.py | main | f8d908c23e8674c872b538e6e4ac61a78641b2da | present | 22 |
| RC-24 | Response integrity checker defines body_failed_to_parse | src/mist/access/api/response_integrity.py | main | 4a1f25ce501771f2ddf2d6ceaa171ca25b49e4b0 | present | 35 |
| RC-25 | Menu 15 registry entry is safe and names device_stats | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 683 |
| RC-26 | Menu 16 registry entry is safe and names vpn_peer_stats | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 684 |
| RC-27 | Menu 15 handler is OrgDeviceStatsExporter.device_stats | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3796 |
| RC-28 | Menu 16 handler is OrgDeviceStatsExporter.vpn_peer_stats | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3812 |
| RC-29 | Menu 13 handler is OrgDeviceInventorySummary.dispatch | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6389 |
| RC-30 | Data collection runs device_stats as a collection step | src/mist/intelligence/analytics/data_collection_manager.py | main | 9bb8016a27f1e2146af38424725698a73e983389 | present | 82 |
| RC-31 | Exporter test file has a device cache-hit test | tests/unit/export/test_org_device_stats_exporter.py | main | c30a42b548169bc14ee2cadb8a7d80e5da49b8b0 | present | 230 |
| RC-32 | Exporter test file asserts the device completion call without a count | tests/unit/export/test_org_device_stats_exporter.py | main | c30a42b548169bc14ee2cadb8a7d80e5da49b8b0 | present | 247 |
| RC-33 | Menu 13 wiring test stub execute returns nothing | tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py | main | 7f61d0791f4fd8996a636ef03536b69660f08dd9 | present | 146 |
| RC-34 | Menu 13 wiring test asserts processed count 1 | tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py | main | 7f61d0791f4fd8996a636ef03536b69660f08dd9 | present | 170 |
| RC-35 | Menu 13 test file moved to the prod_readiness path by PR 4358 | tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py | PR #4358 merged 2026-11-13 | 7f61d0791f4fd8996a636ef03536b69660f08dd9 | present | 0 |
| RC-36 | Old menu 13 test path is absent on main | tests/unit/test_menu_13_device_stats.py | main | none | absent | 0 |
| RC-37 | API fetcher test file exists | tests/unit/api/test_api_data_fetcher.py | main | aa6178f9cb7dc561c1f99f8c589300bce14a36a8 | present | 1 |
| RC-38 | MYPY_PATHS variable lists the type-check paths | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-39 | VULTURE_PATHS variable lists the dead-code paths | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-40 | PYDOCSTYLE_PATHS variable lists the docstring paths | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-41 | INTERROGATE_PATHS variable lists the coverage paths | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-42 | Local gates table row for Tests | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-43 | Local gates table row for Test quality | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 65 |
| RC-44 | Local gates table row for Symbols | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| RC-45 | Test quality rule requires HTTP 4xx and 5xx tests | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 253 |
| RC-46 | Serial merge slot rule for publication | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 485 |
| RC-47 | Inline comment rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| RC-48 | Action logging rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 104 |
| RC-49 | Issue first rule: one issue holds one subject | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 185 |
| RC-50 | Five-item rule forbids a direct child in a noncompliant parent | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 42 |
| RC-51 | Maximum 25 lines per function | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 85 |
| RC-52 | Principle VII requires action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-53 | Changelog naming row for an issue without a pull request | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-54 | Changelog keeps the first name after the pull request opens | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 32 |
| RC-55 | Changelog guard test exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 1 |
| RC-56 | Spec route width is eight segments | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-57 | Spec route base is five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-58 | listOrgDevicesStats lists HTTP 403 and no HTTP 5xx response | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 21451 |
| RC-59 | searchOrgPeerPathStats lists HTTP 403 and no HTTP 5xx response | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 22492 |
| RC-60 | Missing endpoint document lists searchOrgPeerPathStats | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | present | 896 |
| RC-61 | No Markdown file under documentation or README has progress event text (1,254 files scanned) | documentation/ and README.md | main | none | absent | 0 |
| RC-62 | Installed SDK defines listOrgDevicesStats | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | installed mistapi 0.64.1 (local) | 247e4526005342dc895408519d5974a7aa86aefd | present | 397 |
| RC-63 | Installed SDK defines searchOrgPeerPathStats | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | installed mistapi 0.64.1 (local) | 247e4526005342dc895408519d5974a7aa86aefd | present | 1592 |
| RC-64 | Installed SDK defines the get_all helper | .venv\Lib\site-packages\mistapi\__pagination.py | installed mistapi 0.64.1 (local) | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 39 |
| RC-65 | Installed SDK APIResponse exposes status_code | .venv\Lib\site-packages\mistapi\__api_response.py | installed mistapi 0.64.1 (local) | 2d878d79295fec79e6409f6243132c53280f15ab | present | 43 |
| RC-66 | Route folder for issue 4746 is absent on main | specs/numbered/0/0/1/2/2/4/4/1 | main | none | absent | 0 |
| RC-67 | Changelog fragment for issue 4746 is absent on main | changelog.d/issue-4746-stats-export-failed-fetch.md | main | none | absent | 0 |
| RC-68 | Stats test folder and test basename are absent on main | tests/unit/prod_readiness/standalone/operations/exporting/stats | main | none | absent | 0 |
| RC-69 | Folder tests/unit/export holds 55 direct children on main | tests/unit/export | main | none | present | 0 |
| RC-70 | Folder tests/unit/prod_readiness/standalone/operations/exporting holds 3 direct children on main | tests/unit/prod_readiness/standalone/operations/exporting | main | none | present | 0 |
| RC-71 | Folder src/operations/exporting/export holds 49 direct children on main | src/operations/exporting/export | main | none | present | 0 |
| RC-72 | Commit 0d881744 exists and is an ancestor of main (compare status ahead, behind 0) | commits/0d881744310dc2c1b1be8b47b5b5402504029062 | main | none | present | 0 |
| RC-73 | Commit 57c99870 exists and is not an ancestor of main (compare status diverged, behind 1) | commits/57c998709893ea8db2d3092aaa4b362f8bbab2e7 | main | none | present | 0 |
| RC-74 | device_stats definition starts at line 87 | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 87 |
| RC-75 | device_stats closing parenthesis is at line 112 | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 112 |
| RC-76 | vpn_peer_stats definition starts at line 474 | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 474 |
| RC-77 | vpn_peer_stats closing parenthesis is at line 501 | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 501 |
| RC-78 | Fetch step returns False after an unparsed response body | src/mist/access/api/api_data_fetcher.py | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 134 |
| RC-79 | Container build workflow file exists | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 1 |
| RC-80 | Worktree bootstrap script file exists | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 1 |
| RC-81 | Test quality analyzer settings file exists | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 1 |
| RC-82 | Test quality baseline file exists | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 1 |
| RC-83 | Development requirements file exists | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 1 |
| RC-84 | Preflight test class TestLiveGuides exists | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 771 |
| RC-85 | Project configuration file exists | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 1 |
| RC-86 | Spec STE configuration file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 1 |

## Local Sources

- `AGENTS.md`: writing style, code quality, action logging, git flow, and specifications. Cited rows are RC-47 to RC-49.
- `.github/copilot-instructions.md`: language and environment (lines 18 to 20), local gates (lines 50 to 76), test quality ratchet (line 95), and serial validation (line 483). Cited rows are RC-42 to RC-46.
- `.specify/memory/constitution.md`: Principle I (lines 38 to 43), function limits (lines 78 to 85), and Principle VII (line 235). Cited rows are RC-50 to RC-52.
- `documentation\mist-api-openapi31yaml.yaml`: operation `listOrgDevicesStats` at line 21396 and summary at line 21457. Operation `searchOrgPeerPathStats` at line 22457 and summary at line 22498.
- `.venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py`: `listOrgDevicesStats` parameters include `type`, `duration`, and `limit`. `searchOrgPeerPathStats` parameters include `duration` and `limit`. The signatures end at lines 412 and 1604.
- `.venv\Lib\site-packages\mistapi\__init__.py` line 15 re-exports `get_all` from `mistapi.__pagination`.
- `src\mist\access\api\api_data_fetcher.py` lines 178 and 137 carry the SDK call and the pagination call. Both lines appear in RC-14 and RC-17.
- Pull request and issue data from `gh` reads, which carry no code claim: issue #4746 (open, labels bug and MistHelper.py, comments of 2026-11-10). PR #4358 (merged 2026-11-13). Issues #1794 and #2711 (open, labelled in-progress).
- Open pull request scan: 7 open pull requests on 2026-11-26. PR #4813 changes two other export test files. No open pull request changes the planned files.

## Skills and External Sources

- No skill was loaded. The issue has no Podman or Juniper device behavior.
- No URL was fetched. Local sources answered each question.

## Unverified

- U-1: The "local #1794 device-statistics slice" reserves the source file (issue comment of 2026-11-10 16:07:44Z). Reason: the claim is local only. No remote branch or pull request names the file, and issue #1794 does not name it.
- U-2: An "older local branch" also changes the reserved test file (issue comment of 2026-11-10 16:14:05Z). Reason: the claim is local only, and the issue gives no branch name.
- U-3: The branch that holds commit `57c99870` (RC-73). Reason: the issue does not name the branch. The commit exists remotely and is not on main.
- U-4: Live Mist cloud responses for HTTP 403 and HTTP 503 on these operations. Reason: no live call was made. The OpenAPI document lists no HTTP 5xx response (RC-58, RC-59).
- U-5: Other exporters that emit a literal processed count after a fetch. Examples are `src\operations\exporting\export\org_inventory_exporter.py` (lines 96 and 120), `org_site_exporter.py` (line 74), and `site_device_exporter.py` (line 195). Reason: the evidence is a local search only. The blobs were not checked, and the items are out of scope.
- U-6: Consumers of `items_processed` outside the checked folders. Reason: the search covered the local copies of `src`, `web_portal`, and `scripts`. The search did not check each blob against main.
- U-7: Whether `documentation\MIST_API_MISSING_ENDPOINTS.md` is generated, and by which script. Reason: the generator was not read.
- U-8: Whether the test quality baseline holds entries for the planned test paths. Reason: the research phase runs no tests and no gates. T-LOCAL-GATES resolves this item.
