# Research: Blind except handlers (issue 1794)

## Scope of the research

- Issue: `jmorrison-juniper/MistHelper` #1794. State OPEN, with stateReason REOPENED. Last updated 2026-11-17. Labels: refactor, web-portal, in-progress, frontend, backend, firmware, logging, priority:P1, severity:high. All 62 comments were read.
- Verified commit: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (main, committed 2026-11-26). The local HEAD has the same SHA.
- Local working-tree files count only when their git hash equals the main blob. `src/foundation/support/utils/logger_utils.py` differs from main in the working tree, so this record does not use the local copy.
- Each remote claim cites a `gh api` read of main. Each local count cites `git grep` at the verified commit and carries the label "Local evidence".
- Skills: none loaded. The issue concerns Python exception handling. The Podman and Juniper device skill families do not apply.

## Measured state at main

| Measure | Value | Basis |
| - | - | - |
| Broad handler text matches (`except Exception` or `except BaseException`) | 827 sites in 310 files | Local evidence. Includes re-raise handlers, string literals, tests, and excluded trees. |
| Bare `except:` text matches | 3 sites in 2 files | Local evidence. Ruff BLE001 does not own this form. |
| Ruff in-scope text matches | 678 sites in 261 files | Local evidence. Excludes the four `extend-exclude` prefixes (RC-004). |
| Excluded tree text matches | 149 sites in 49 files | Local evidence. mist-ops-platform 23 in 13, web_portal 26 in 9, scripts 32 in 12, src/interfaces/visualization/maps 68 in 15. |
| Inline `# noqa: BLE001` lines | 16 lines in 4 files | Local evidence. All 16 sit under `src/interfaces/visualization/maps/launcher/`, which ruff excludes. |
| Inline `broad-exception-caught` pylint disables | 57 lines in 20 files | Local evidence. Each kept site that pylint flags uses one of these. |
| Ruff BLE001 count, last reported | 524 | Issue comment 9, 2026-10-29. Not re-measured. Unverified U-1. |
| Pylint W0718 count, recorded | 493 | Stale comment in `pyproject.toml` lines 588 to 593 (RC-002). Unverified U-2. |
| Issue body count, 412 | Stale | Measured on 2026-08-05 with ruff 0.16.0. The pinned ruff is 0.17.6 (RC-008). |

Local counts by ruff scope cluster (text matches, Local evidence):

| Cluster | Files | Sites |
| - | - | - |
| C01 MistHelper.py, wsgi.py | 2 | 10 |
| C02 src/mist/intelligence, src/mist/access | 20 | 34 |
| C03 src/mist/networking, src/mist/resources/inventory, src/mist/resources/org, src/operations/wan | 17 | 38 |
| C04 src/mist/realtime, src/interfaces/monitoring | 16 | 30 |
| C05 src/mist/resources/gateway, src/operations/execution/ssid_consolidation | 11 | 32 |
| C06 src/mist/resources/site, src/foundation/persistence | 9 | 27 |
| C07 src/mist/resources/device | 9 | 40 |
| C08 src/operations/execution/ssh | 13 | 39 |
| C09 src/operations/execution/capture, src/operations/protection | 8 | 25 |
| C10 src/operations/execution/firmware/firmware_manager.py | 1 | 29 |
| C11 src/operations/execution/firmware (other files) | 4 | 24 |
| C12 src/operations/exporting/export | 41 | 94 |
| C13 src/foundation/support/refactors | 18 | 44 |
| C14 src/foundation (other paths) | 9 | 15 |
| C15 src/interfaces/visualization/ui, src/interfaces/portals/licensing_comparison | 5 | 6 |
| C16 src/interfaces/portals/upgrade_portal | 39 | 131 |
| C17 tests | 39 | 60 |

## Decisions

Each decision records alternatives, the chosen option, the reason, and the risk. No decision requires a human (`human_decision_required` is false for all).

D-1. Scope metric. Alternatives: (a) text search of except clauses, (b) pylint W0718, (c) ruff BLE001 with the pinned ruff 0.17.6, with and without `--ignore-noqa`. Chosen: (c). Reason: ruff applies the re-raise and `exc_info` exemptions (RC-095). Text search overcounts re-raise handlers and string literals (Local evidence: 827 against 678 in scope). Pylint uses other roots and reports logged handlers that ruff exempts (issue comment 32, Unverified U-4). Risk: this record does not run ruff. T001 measures the count before the first slice.

D-2. Growth guard until the final gate. Alternatives: (a) select BLE001 now, (b) keep the existing ratchet until the final gate PR, (c) rely on review. Chosen: (b). Reason: enabling BLE001 now fails on several hundred sites at once. Review cannot count growth. The ratchet fails on each new blind handler (RC-032, RC-033). Risk: the ratchet counts only blind handlers, which are broad handlers whose bound name stays unused. A broad handler that logs can grow until the final gate. The ratchet also excludes test directories (RC-033), while ruff includes them.

D-3. Outcome order. Alternatives: (a) narrow every site, (b) keep every site, (c) apply delete, then narrow, then keep. Chosen: (c). Reason: a narrow clause without caller evidence can turn a caught failure into a crash. A keep without a log hides failures. Risk: judgment errors. Each site has one table row and one test (FR-007 to FR-014).

D-4. Narrowing for mistapi calls. Alternatives: (a) narrow to `RuntimeError` (record A, RC-037), (b) narrow to `requests` exceptions, (c) check the returned response and narrow only local parsing. Chosen: (c). Reason: the mistapi retry wrapper catches `ProxyError`, `ConnectionError`, `HTTPError`, and `Exception` itself and returns an `APIResponse` (RC-094). The request module raises `RuntimeError` in one place (RC-093), inside token rotation. The 429 branch of the wrapper catches that case (lines 236 to 239). Record A therefore catches an exception that the REST wrapper path does not raise. Risk: a later mistapi release can change this path. The pin is 0.64.1 (RC-018). Unverified U-15 lists the callers that were not read.

D-5. Log content. Alternatives: (a) full exception text, (b) exception type only, (c) exception type, operation name, redacted message, and `exc_info` through the handlers that carry `SensitiveFilter`. Chosen: (c). Reason: `SensitiveFilter` redacts `exc_text` (RC-060, lines 288 to 293). The console and file handlers install it (RC-061, lines 202 and 208). Issue comments 17, 18, and 20 record traceback leaks in unmerged slices. Risk: a logger that bypasses these handlers has no redaction. Each slice test uses the real handler chain with a synthetic token.

D-6. Held local slices. Alternatives: (a) publish as is, (b) rebase each onto main and check it again, (c) discard. Chosen: (b), and keep each commit until a merged replacement exists. Reason: 16 held commits are not ancestors of main (Local evidence). Their file bases changed (RC-065, RC-067, RC-070, RC-073, RC-074). Risk: rebase conflicts. The owning slice (plan.md, slice map) carries each conflict.

D-7. Tracking. Alternatives: (a) reopen the closed children #2833, #2834, #2835, #2836, and #2926, (b) open one new issue for each slice cluster and link it to #1794, (c) track only in the umbrella. Chosen: (b). Reason: the children closed (GitHub state table), while the local counts still show 53 sites under firmware, 94 under export, and 131 under the upgrade portal. Reopening would reuse a completion record that is false. Risk: duplicate tracking. Each new issue names #1794 and the slice ID.

D-8. Scope and tests. Alternatives: (a) add the four excluded trees to the gate now, (b) keep `extend-exclude` and open follow-up issues for the excluded trees, (c) remove `extend-exclude`. Chosen: (b). Reason: the excluded trees hold 149 sites, and their `noqa` lines are inert (Local evidence). Changing the list is outside the issue. Tests inside the ruff scope follow the same outcome policy (FR-033). Risk: excluded trees keep blind handlers until their follow-up issues close.

D-9. One final gate PR. Alternatives: (a) a PR that selects BLE001 and a PR that removes W0718, (b) one PR for both changes, (c) keep W0718 disabled. Chosen: (b). Reason: the issue requires both changes, and a split leaves a window where the two tools disagree. Risk: pylint can fall below the 9.5 floor (RC-128). The current recorded score is 9.53 (RC-129). The final PR must run the pylint gate before merge.

D-10. Pins and runtime. Alternatives: (a) versions in old records (Python 3.13, ruff 0.16.0, pylint 4.0.6), (b) versions in `pyproject.toml` and `requirements-dev.txt`. Chosen: (b). Reason: `requires-python` is `>=3.15` (RC-005). The ruff target is `py315` (RC-006). Pins are ruff 0.17.6 and pylint 4.1.4 (RC-007, RC-008). Risk: a later upgrade changes counts. T001 records the pinned versions.

D-11. Legacy records. Alternatives: (a) delete the three root-level records, (b) edit them in place, (c) supersede them with this record and keep them. Chosen: (c). Reason: the three folders are grandfathered baseline entries (RC-022). The constitution requires new records under the managed numbered route (RC-019, RC-021). The preservation rule forbids deletion of unmerged history (AGENTS.md, RC-030). Risk: readers may use an old record. T036 records the supersession in `analysis.md` and opens a cleanup issue for a banner in each legacy `spec.md`.

D-12. Closing keyword. Alternatives: (a) a closing keyword in every pull request, (b) a reference keyword in slice pull requests, (c) a closing keyword only in the last pull request. Chosen: (b) for slices and (c) for the final gate PR. For this record PR, the T-PR body follows the brief, which requires `Closes #1794`. Reason: the auto-close workflow closes each issue that a merged pull request names (RC-023). Issue comments 8 and 10 show that a slice merge closed #1794. Risk: this record PR closes #1794 when it merges. The orchestrator must reopen #1794 after the merge if the umbrella must stay open. Analysis A-13 records this risk.

D-13. Pylint on kept sites. Alternatives: (a) one inline `broad-exception-caught` disable with a reason on each kept site that pylint flags, (b) keep the repository-wide disable, (c) narrow every site so no kept site remains. Chosen: (a). Reason: pylint flags logged broad handlers (issue comment 32, Unverified U-4). The issue requires removing W0718 from the disable list (RC-002). Option (c) conflicts with NG-002 of the earlier specification. Risk: suppressions grow. The final PR counts them and runs the pylint gate. Each inline disable needs a reason comment. Inline disables at narrowed or deleted sites are removed in the same slice.

D-14. Labels and size. Alternatives: (a) add the MistHelper.py and tests scope labels, (b) keep the current labels. Chosen: (b). Reason: the issue already carries the type label `refactor` and the scope label `web-portal`. Slice pull requests carry the scope labels that the repository file names (RC-031). Size is XL: 261 candidate files, 678 text sites, 23 slices, and one final gate PR.

## Remote verification

Each row is one check on GitHub main, the local installed mistapi source, or the upstream ruff page. The table has 129 rows. The same 129 rows appear in the `remote_checks` array of `1794-STATUS.json`.

Result counts: present 98, stale 24, partial 2, absent 5.

The existing-record claims are the 35 rows tagged `[A]`, `[B]`, or `[C]`, plus the rows that check record claims without a tag. Their results are: present 18, stale 16 (partial counts as stale), absent 1. Claims A6 and B8 share RC-006.

Records and rows: `[A]` is `specs\1794-blind-except`. `[B]` is `specs\1794-blind-except-handlers`. `[C]` is `specs\1794-blind-except-slice2`.

| ID | Claim | Path | Ref | Blob or commit SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-001 | [B] ruff select list at line 164 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | stale | 209 |
| RC-002 | [B] W0718 in pylint disable at line 475 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | stale | 594 |
| RC-003 | BLE family is outside the ruff select list | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 209 |
| RC-004 | [B] ruff extend-exclude lists four paths | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 206 |
| RC-005 | requires-python is 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RC-006 | [A][B] Python target 3.13 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | stale | 203 |
| RC-007 | [B] pylint 4.0.6 is pinned | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | stale | 313 |
| RC-008 | [B] ruff 0.16.0 is pinned | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | stale | 399 |
| RC-009 | MYPY_PATHS value for the mypy gate | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-010 | [B] vulture minimum confidence 80 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | stale | 127 |
| RC-011 | PYDOCSTYLE and INTERROGATE source roots | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-012 | ruff check . is the lint gate | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 165 |
| RC-013 | [B] pylint reads MistHelper.py and src | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | stale | 78 |
| RC-014 | pylint gate uses SRC_PATH | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 529 |
| RC-015 | bandit form in the local gates table (`-r <package>`) | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | stale | 451 |
| RC-016 | radon gate pipes to complexity-gate | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 549 |
| RC-017 | pytest shards include tests/guardrails | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| RC-018 | mistapi pinned at 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-019 | route digits use base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-020 | numbered route width is 8 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-021 | constitution version 1.9.0 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 562 |
| RC-022 | 1794 record folders are grandfathered | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 87 |
| RC-023 | auto-close workflow closes issues of merged pull requests | .github/workflows/close-linked-issues.yml | main | 42a085ac6240518b028862c290ec9502a5b13b2a | present | 13 |
| RC-024 | pull request template has a spec checklist | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 1 |
| RC-025 | changelog fragment naming rules | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 1 |
| RC-026 | STE writing guide exists | documentation/ASD-STE100_writing-guide.md | main | b464165aae116a17bb3031d3cef9b84a95589c0a | present | 1 |
| RC-027 | quality gate table lists ruff check . | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 50 |
| RC-028 | runtime log is data/script.log | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 753 |
| RC-029 | test and debug container section | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| RC-030 | generic rules for STE, structure, and git | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 1 |
| RC-031 | repository gates table and scope labels | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 1 |
| RC-032 | growth guard for blind handlers | tests/guardrails/test_blind_exception_handler_ratchet.py | main | 3cab97e42178b7b978bcc78eab73d8a0fb3eae27 | present | 1 |
| RC-033 | accepted per-file debt baseline | .github/blind-exception-handler-baseline.json | main | f3a2ee54395a205b422bcbdb0bea9d489a06d951 | present | 1 |
| RC-034 | STE linter configuration | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 1 |
| RC-035 | [B] #1792 must land first, RUF100 already selected | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | stale | 209 |
| RC-036 | [A] firmware resolver file path | src/operations/execution/firmware/running_version.py | main | c25d183e1498e79a6f612a0087f370cf904ba3f8 | present | 122 |
| RC-037 | [A] RuntimeError catch in fetch_site_running_versions | src/operations/execution/firmware/running_version.py | main | c25d183e1498e79a6f612a0087f370cf904ba3f8 | present | 138 |
| RC-038 | [A] resolver test file | tests/unit/firmware/test_running_version.py | main | 0a2ea29e9e33495a415f75471d7f05457dea7eab | present | 1 |
| RC-039 | [A] SSR test file, now at a moved path | tests/unit/firmware/test_firmware_manager_ssr.py | main | none (HTTP 404). Moved blob d168c12d5f6ef04c29246dde5d280fd20ea625ae | stale | 0 |
| RC-040 | [A] release fragment, consumed into CHANGELOG.md line 1091 | changelog.d/issue-1794-blind-except.md | main | none (HTTP 404) | stale | 0 |
| RC-041 | [C] bulk switch handlers narrowed, one broad handler remains | src/operations/execution/firmware/bulk_switch_upgrader.py | main | 0a1b0991f32af5d5358ea7329f1e96c0806fe1b1 | present | 664 |
| RC-042 | [C] site auto-upgrade handlers narrowed, none broad | src/operations/execution/firmware/site_auto_upgrade.py | main | 413de59b844a5f1a9b2699bb695bb0d4cbd029b2 | present | 0 |
| RC-043 | [C] reboot handler narrowed, six broad handlers remain | src/mist/resources/device/device_reboot_manager.py | main | c4a127cb591ff9e7ca47c94550c37f6343b0a5c7 | present | 113 |
| RC-044 | [C] service-ping handler narrowed, three broad handlers remain | src/mist/realtime/websocket/service_ping_manager.py | main | 3d4b4b27bcc724f162085d976ce0af6179f88035 | present | 159 |
| RC-045 | [C] config exporter handlers narrowed, none broad | src/operations/exporting/export/site_config_exporter.py | main | b8aba9cb18c39285321ca8f91242458ebf0f7037 | present | 0 |
| RC-046 | [C] client exporter handlers narrowed, two broad remain | src/operations/exporting/export/site_client_exporter.py | main | c9371a558a8f7d67284dda41b1605beedff35285 | present | 83 |
| RC-047 | [C] bulk switch test file, now at a moved path | tests/unit/test_bulk_switch_upgrader.py | main | none (HTTP 404). Moved blob 6db5c2b226eb2dfb39cbc67043d5d107681052a3 | stale | 0 |
| RC-048 | [C] auto-upgrade test file, now at a moved path | tests/unit/test_site_auto_upgrade.py | main | none (HTTP 404). Moved blob d971668f76f659e16c2d626ca4df2df031d6225c | stale | 0 |
| RC-049 | [C] reboot test file | tests/unit/device/test_device_reboot_manager.py | main | 0b4e6134ec51583263f126ce9f122183d7e406f7 | present | 1 |
| RC-050 | [C] service-ping test file | tests/unit/websocket/test_service_ping_manager.py | main | f092f831dd9012ec919ccf8627a9598da8fa676c | present | 1 |
| RC-051 | [C] config exporter test file | tests/unit/export/test_site_config_exporter.py | main | 5d1d5994f10f9c60eb93e324380cfe3920e21ccd | present | 1 |
| RC-052 | [C] client exporter test file | tests/unit/export/test_site_client_exporter.py | main | 286e492cba883ca2aee042166c5767d6279ae514 | present | 1 |
| RC-053 | [C] release fragment, consumed into CHANGELOG.md line 1057 | changelog.d/issue-1794-blind-except-slice2.md | main | none (HTTP 404) | stale | 0 |
| RC-054 | [B] MistHelper.py holds 33 handlers | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 1822 |
| RC-055 | [B] virtual_chassis.py holds 10 handlers | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 457 |
| RC-056 | [B] bulk_ap_upgrader.py holds 11 handlers | src/operations/execution/firmware/bulk_ap_upgrader.py | main | 99978c5564ea53be21e983c4a8621048c3d88a18 | present | 305 |
| RC-057 | [B] const_definitions_exporter.py holds 11 handlers | src/operations/exporting/export/const_definitions_exporter.py | main | a258912d12796ce244b7a871af80f2ab1f3f0e73 | stale | 0 |
| RC-058 | [B] starlink_dashboard.py at repo root holds 8 handlers | starlink_dashboard.py | main | none (HTTP 404) | absent | 0 |
| RC-059 | [B] firmware_manager.py holds 28 handlers (text count 29) | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | partial | 276 |
| RC-060 | [B] SensitiveFilter class and traceback redaction | src/foundation/support/utils/logger_utils.py | main | 6cb99dc0e3e0a4808391e6953560071b69e36683 | present | 189 |
| RC-061 | root console and file handlers attach SensitiveFilter | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 202 |
| RC-062 | handler at line 106 logs the exception with a message | src/interfaces/visualization/ui/execution/debug_saver.py | main | 1537fa4219c1dd1ac42aac5ef15cdf1635c33442 | present | 106 |
| RC-063 | debug saver test file | tests/unit/ui/test_debug_saver.py | main | e847b19735cfb32fbac28f2924585e6170c2b535 | present | 1 |
| RC-064 | held cache slice target has one broad handler | src/foundation/persistence/cache/cache_utils.py | main | d628806f4b0f32c1059264c82d0722d4e099d0b7 | present | 103 |
| RC-065 | held cache test path | tests/unit/cache/test_cache_utils.py | main | none (HTTP 404). Moved blob ad76ed736f75475ea7134f62f73a10448a7de76f | stale | 0 |
| RC-066 | held time slice target has one broad handler | src/foundation/runtime/time/time_utils.py | main | edbd76dd30df1affcc6095451ce196d829695aa4 | present | 42 |
| RC-067 | held time test path | tests/unit/time/test_time_utils.py | main | none (HTTP 404). Moved blob 25d5874fc64702098bc5bcfbd74944da43d60a47 | stale | 0 |
| RC-068 | held container-detection target | src/foundation/support/utils/environment_utils.py | main | 843aff4bacd8d7dd14391d47cfc3335d7e7c89b8 | present | 155 |
| RC-069 | held anomaly target has one broad handler | src/foundation/support/refactors/anomaly_metrics_discovery.py | main | 2ecbbc2aff1968b0cd6ff9b4efcfbfbef14df8ff | present | 72 |
| RC-070 | held anomaly test path, renamed by PR #4358 | tests/unit/refactors/test_anomaly_metrics_discovery.py | main | none (HTTP 404). Renamed blob b861b6a649620526e9ccf0c6006d9db9ec9de2a3 | stale | 0 |
| RC-071 | held device-fetch target | src/foundation/support/refactors/device_data_fetcher.py | main | b8edb6f2f2da36aad976fb7a7351770a537a146d | present | 134 |
| RC-072 | held SSH CSV target | src/operations/execution/ssh/config/csv_loader.py | main | ac80ed3df60f1362ff11a5b3e38d4dde2cf1decd | present | 54 |
| RC-073 | [held address] claims a broad catch remains in address_utils | src/foundation/support/utils/address_utils.py | main | 1f7bfae7ffcda292274cd691a71bdd791f2f30af | stale | 0 |
| RC-074 | held address test path, moved by PR #4358 | tests/unit/test_address_utils.py | main | none (HTTP 404). Moved blob a1253dd1182df1bfcb82b98f4b677022496d24f1 | stale | 0 |
| RC-075 | held device-stats target has seven broad handlers | src/operations/exporting/export/org_device_stats_exporter.py | main | 7cdd35dafbf5f62c3764bc44749ac3d62c6e096e | present | 82 |
| RC-076 | held inventory target has six broad handlers | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 134 |
| RC-077 | held AP-address target has one broad handler | src/operations/exporting/export/sites_by_ap_model_exporter.py | main | 66d1ccaf05886d89802aa45792977480f73f37c4 | present | 87 |
| RC-078 | held other-device target has one broad handler | src/operations/exporting/export/site_other_device_events_exporter.py | main | 60f1ac7fdd966ef4cd7b38b4e3f6cd314d1fbf3a | present | 83 |
| RC-079 | analytics data collection handlers | src/mist/intelligence/analytics/data_collection_manager.py | main | 9bb8016a27f1e2146af38424725698a73e983389 | present | 64 |
| RC-080 | [comment 7] analytics path, moved to site/ | src/mist/intelligence/analytics/site_analytics_configurator.py | main | none (HTTP 404). Moved blob 5835419f15ef078ebe8cc3e41ef30d880bfd3e3e | stale | 0 |
| RC-081 | [comment 7] analytics path, moved to site/ | src/mist/intelligence/analytics/site_inventory_health_analyzer.py | main | none (HTTP 404). Moved blob 3936d863aedd1800f34c720698b368c31ee528dd | stale | 0 |
| RC-082 | held CSV-template target (uncommitted per comment 61) | src/foundation/support/utils/file_path_utils.py | main | 7e087c4b64feaeada9883518e5678a9ef5fa3777 | present | 66 |
| RC-083 | held CSV-template test path, moved | tests/unit/test_file_path_utils.py | main | none (HTTP 404). Moved blob f1e46ffde221aee80657561c9f1f94f0fbbc0a6d | stale | 0 |
| RC-084 | held catalog target has two broad handlers | src/foundation/support/utils/zscaler_catalogue.py | main | 4ca1d97e1e45ab59711f97988938e9c2162be0d6 | present | 1079 |
| RC-085 | TUI launcher handler (issue 4711 closed) | src/foundation/support/refactors/tui_launcher.py | main | 4bb4eef81ec63bd78051f35b89417df856ec7452 | present | 75 |
| RC-086 | SQLite schema fallback handler (issue 4712 open) | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 62 |
| RC-087 | ping assertion test shared with held branch | tests/unit/websocket/diagnostics/test_ping_executor.py | main | 217ebebf8541ecb80901d811c18a8fbb6fc0daf9 | present | 1 |
| RC-088 | zscaler transport test shared with a held branch | tests/unit/utils/test_zscaler_probe_transport.py | main | c028e21d33d189046b4f91b154f244da2dcd698c | present | 1 |
| RC-089 | held new test file for the AP-address slice | tests/unit/export/test_sites_by_ap_model_address_exceptions.py | main | none (no tree entry) | absent | 0 |
| RC-090 | held new test file for the inventory-address slice | tests/unit/export/test_org_inventory_address_exceptions.py | main | none (no tree entry) | absent | 0 |
| RC-091 | held new test file for address normalization | tests/unit/utils/test_address_normalization_boundaries.py | main | none (no tree entry) | absent | 0 |
| RC-092 | mistapi defines listSiteDevicesStats | .venv\Lib\site-packages\mistapi\api\v1\sites\stats.py | local .venv mistapi 0.64.1 | not applicable (local file) | present | 1051 |
| RC-093 | mistapi raises RuntimeError only for token exhaustion | .venv\Lib\site-packages\mistapi\__api_request.py | local .venv mistapi 0.64.1 | not applicable (local file) | partial | 142 |
| RC-094 | mistapi retry wrapper catches transport errors and returns APIResponse | .venv\Lib\site-packages\mistapi\__api_request.py | local .venv mistapi 0.64.1 | not applicable (local file) | present | 221 |
| RC-095 | ruff exempts re-raise and exc_info logging | https://docs.astral.sh/ruff/rules/blind-except/ | web fetch | not applicable (web page) | present | 0 |
| RC-096 | target record route is free | specs/numbered/0/0/0/2/4/1/3/4 | main | none (no tree entry) | absent | 0 |
| RC-097 | [A] legacy record folder exists | specs/1794-blind-except | main | ae8a28a8532c7a8a14e479701ac767e01ec4bf10 | present | 0 |
| RC-098 | [C] legacy record folder exists | specs/1794-blind-except-slice2 | main | ff4cb5a5e9c46fe7d69ec4d2171c7e1b4aa05c22 | present | 0 |
| RC-099 | [B] legacy record folder exists | specs/1794-blind-except-handlers | main | d8164a74f3889a0f22a60eda2c50076bce55181c | present | 0 |
| RC-100 | [B] B110 spec folder exists | specs/1032-bandit-severity-gate | main | e28faf6349b2f6c720a8ba6a1d3079d9239d72c3 | present | 0 |
| RC-101 | companion unused-noqa spec exists | specs/1792-unused-noqa-directives | main | 4345d82168971d3f44fbdcdef9ae00606dd4fd97 | present | 0 |
| RC-102 | reference record folder exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | main | 00922155516e4f21e34a0bf75613fae7ab481193 | present | 0 |
| RC-103 | PR #4499 squash commit, on main | commit | github commit | ffedf75bcc1473f2ae31eca7c25e42bae27764d8 | present | 0 |
| RC-104 | PR #4499 head commit, not on main, superseded by RC-103 | commit | github commit | c3d0f769cda328d259d7397d2278707845b44b41 | present | 0 |
| RC-105 | PR #4501 squash commit, on main | commit | github commit | 87d74a673d30f6a14f7c4eef9d39de91c2836caa | present | 0 |
| RC-106 | PR #4501 head commit, not on main, superseded by RC-105 | commit | github commit | 8a700b2b518b9d08840087cbd30ff3fc13daa8f4 | present | 0 |
| RC-107 | PR #4500 squash commit, on main | commit | github commit | 68aa4a22d3f23f9a2b087e1c0bdae2699f48ec0e | present | 0 |
| RC-108 | PR #4503 squash commit, on main | commit | github commit | 772fc927761b61dea8beb7f708fbbe78c2a38d86 | present | 0 |
| RC-109 | PR #4524 squash commit, on main | commit | github commit | e0326df393361aa96d17914b7fe37a1c5065ce5b | present | 0 |
| RC-110 | PR #2837 squash commit, on main | commit | github commit | 8dadf3763bcb820d69cad3d65f1329674f05465a | present | 0 |
| RC-111 | PR #2847 squash commit, on main | commit | github commit | b0f7b2f0c7c762a12370ee1acde2ac96a5208834 | present | 0 |
| RC-112 | held cache correction, not on main | commit | github commit | ecdf3fef95b638ee52296cc1db991965cce96c70 | present | 0 |
| RC-113 | held cache slice prior commit, not on main | commit | github commit | 88e8bd4f1ce9e997937513cc8f415085574cf69f | present | 0 |
| RC-114 | held time correction, not on main | commit | github commit | f35a51037b1b4f67cc7b6c53612032cda598fdbb | present | 0 |
| RC-115 | held container-detection commit, not on main | commit | github commit | a2641739600e6e0ee1d0aadbcac8049dd4b4b90f | present | 0 |
| RC-116 | held anomaly commit, not on main | commit | github commit | acdbcb0cb4892eb3220155307f80ab307863ac41 | present | 0 |
| RC-117 | held device-fetch privacy commit, not on main | commit | github commit | 0055f7080a4979fdc33b6ce71dce1c9270d01519 | present | 0 |
| RC-118 | held SSH CSV commit, not on main | commit | github commit | 0157ec13fb7f5eb98564fd65ea4a4b804288e06b | present | 0 |
| RC-119 | held catalog commit, not on main | commit | github commit | 57fd57c8c0aa6ee8407efacb62cc7e06a7bdf159 | present | 0 |
| RC-120 | held device-stats commit, not on main | commit | github commit | 54fc78c46145067f796d9391fcc49cf518b559d6 | present | 0 |
| RC-121 | held AP-address commit, not on main | commit | github commit | f9b33748ce0c7b9039588d544f829bb64a9af380 | present | 0 |
| RC-122 | held inventory-address commit, not on main | commit | github commit | 45ca06d2978a65bfe33900b74585c247cb794ee6 | present | 0 |
| RC-123 | held address-normalization commit, not on main | commit | github commit | 30edc280c9d230129bf148bdd6a215703911f3dc | present | 0 |
| RC-124 | held other-device-events commit, not on main | commit | github commit | 63dd076f7c1d96eda6c68a01237e48d6d29cf59b | present | 0 |
| RC-125 | held ping-assertion commit, not on main | commit | github commit | 49c665d9c1d71c65a2cb5314ae7add702886fb4b | present | 0 |
| RC-126 | main cited in comments on 2026-11-09 | commit | github commit | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | present | 0 |
| RC-127 | main cited in comments on 2026-11-16 | commit | github commit | cc476bbdfaa98c84f1f6e21b5b1fc0e1f32d6c9b | present | 0 |
| RC-128 | pylint score floor is 9.5 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 565 |
| RC-129 | CI records a pylint score of 9.53 against the 9.5 floor | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 526 |

Reachability of RC-103 to RC-127 from main was checked with `git merge-base --is-ancestor` at the verified commit. RC-103, RC-105, RC-107, RC-108, RC-109, RC-110, RC-111, RC-126, and RC-127 are ancestors of main. The other commit rows are not ancestors of main.

Mapping notes for stale rows. RC-006 is the shared Python 3.13 claim of records A and B. RC-059 is partial because the issue reports ruff counts and the text count includes re-raise handlers. RC-093 is partial because mistapi raises `RuntimeError` in one path only, and that path is caught internally.

## GitHub state (not part of the remote verification count)

| Object | State | Date | Note |
| - | - | - | - |
| Issue #1794 | OPEN, stateReason REOPENED | updated 2026-11-17 | Umbrella. |
| Issue #1792 | CLOSED | 2026-08-26 | Unused noqa directives. Its RUF100 change is in `pyproject.toml` line 209. |
| Issue #1709 | CLOSED | 2026-09-15 | MistHelper.py narrowing. Closure reason not read. |
| Issue #887 | CLOSED | 2026-08-03 | Disabled W0718 with the 493 count. |
| Issue #3070 | CLOSED | 2026-10-06 | Growth ratchet. The guard exists at RC-032. |
| Issue #2750 | CLOSED | 2026-09-20 | Duplicate proposal. Not reopened. |
| Issues #2833, #2834, #2835 | CLOSED. #2833 has stateReason COMPLETED | 2026-09-18 | Child issues of #1794. Local counts still show remaining sites. |
| Issue #2836 | CLOSED | 2026-09-17 | Display child issue. |
| Issue #2926 | CLOSED | 2026-10-30 | Upgrade portal child issue. Local count 131 sites remain. |
| Issues #1793, #1796, #1766, #1924 | CLOSED | 2026-08 to 2026-09 | Related lint and logging defects. Named by the earlier specifications. |
| Issue #2711 | OPEN | updated 2026-11-25 | Test assertion review. Owns part of the ping test overlap. |
| Issue #3824 | OPEN | updated 2026-11-09 | Package refactor. Reserves the catalogue source. |
| Issues #4709, #4712, #4713, #4717, #4721, #4746, #4818 | OPEN | 2026-11 | Separate defects found in the audit. Each needs its own fix. |
| Issues #4711, #4715, #4716 | CLOSED | 2026-11 | Separate defects found in the audit. |
| PR #1788 | MERGED | 2026-08-06 | Titled "ci: scope each quality gate to its widest passing set". Diff not read. |
| PR #2837 | MERGED | 2026-09-17 | Record A slice. Squash RC-110. |
| PR #2847 | MERGED | 2026-09-17 | Record C slice. Squash RC-111. |
| PR #4358 | MERGED | 2026-11-13 | Moved the test paths that RC-065, RC-067, RC-070, RC-074, and RC-083 name. |
| PR #4499 | MERGED | 2026-10-29 | UI debug saver slice. Squash RC-103. |
| PR #4500 | MERGED | 2026-10-29 | Visualization UI slice. Squash RC-107. Closed #1794 automatically (issue comment 8). |
| PR #4501 | MERGED | 2026-10-29 | Analytics slice. Squash RC-105. Closed #1794 automatically (issue comment 10). |
| PR #4503 | MERGED | 2026-11-05 | Support utilities slice. Squash RC-108. Changed `address_utils.py`. |
| PR #4524 | MERGED | 2026-10-31 | API fetcher slice. Squash RC-109. |

## Local evidence at the verified commit

These checks read the git object store at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` with read-only commands. They are not remote checks. The counts appear in the measured state table above.

- `git grep -c -E "except[[:space:]]+(Exception|BaseException)[^A-Za-z0-9_]"` at the verified commit: 827 sites in 310 files.
- `git grep -c "pylint: disable=broad-exception-caught"`: 57 lines in 20 files.
- `git grep -c "noqa: BLE001"`: 16 lines in 4 files, all under `src/interfaces/visualization/maps/launcher/`.
- `git ls-tree` for `specs/numbered/0/0/0/2/4/1/` and its ancestors: `specs/numbered/0/` holds 1 child, `specs/numbered/0/0/` holds 2 children, and `specs/numbered/0/0/0/` holds 2 children (`0` and `4`). The directories `specs/numbered/0/0/0/2/` and below hold no entries. The route is free.
- `git hash-object` on the working-tree copies of AGENTS.md, the copilot instructions, the constitution, the four templates, `documentation/quality-gates.md`, `documentation/architecture.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, `documentation/operator-guide.md`, `pyproject.toml`, `ci.yml`, and the ratchet test equals the main blob. The working-tree `logger_utils.py` does not equal the main blob.
- `SensitiveFilter` appears in `src/foundation/support/refactors/main_entrypoint.py` (lines 202 and 208), `src/interfaces/portals/upgrade_portal/app/factory.py` (line 274), and `src/operations/exporting/export/const_definitions_exporter.py` (line 162).

## Sources

| Source | Local path or URL | Supports |
| - | - | - |
| Brief | `files\spec-brief.md` in the session folder | Procedure, schema, and style rules. |
| Repository rules | `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md` | Gates, structure, STE, git flow, constitution checks. Each file matches its main blob (RC-021, RC-030, RC-031). |
| Templates | `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md` | Headings. Each file matches its main blob. |
| Reference record | `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` | Shape only. The root holds spec, plan, tasks, analysis, and design. The design folder holds research, data model, quickstart, contracts (four files), and checklists (three files). |
| Quality gates | `documentation\quality-gates.md` | Gate table and ruff row (RC-027). |
| Operator and deployment docs | `documentation\operator-guide.md`, `documentation\container-deployment.md` | Runtime log path (RC-028) and the test-container rule (RC-029). |
| Route rule | `.specify\scripts\powershell\spec-route.ps1` | Base 5 and width 8 (RC-019, RC-020). Verified on main. |
| Mist SDK | `.venv\Lib\site-packages\mistapi` (version 0.64.1) | `listSiteDevicesStats` (RC-092), the RuntimeError raise (RC-093), and the retry wrapper (RC-094). |
| Ruff rule | https://docs.astral.sh/ruff/rules/blind-except/ | Re-raise and `exc_info` exemptions (RC-095). |
| GitHub | `gh api` reads of `repos/jmorrison-juniper/MistHelper` on `main`, `gh issue view`, `gh pr view`, and `gh label list` | Remote rows and GitHub state. |

## Unverified

- U-1. The current ruff BLE001 count on main. This record cannot run ruff under the repository rules. The last reported value is 524 (issue comment 9). T001 measures the count.
- U-2. The current pylint W0718 count. The recorded 493 is stale. T001 measures the count with pylint 4.1.4.
- U-3. The ruff count for `src/operations/execution/ssh` (14 default and 32 with `--ignore-noqa`, record B). The count requires ruff. The text count is 39 sites (Local evidence).
- U-4. Pylint reports logged broad handlers that ruff exempts (issue comment 32, 80 exception log calls and 8 `exc_info` calls). Pylint was not run.
- U-5. RUF100 reports an inert `# noqa: BLE001` when BLE001 is not selected. The rule text was not fetched. T001 checks the behavior with a temporary file that the implementer deletes.
- U-6. The working-tree `logger_utils.py` differs from main. The diff was not read. This record does not use it.
- U-7. The CSV-template changes in `src/foundation/support/utils/file_path_utils.py` (issue comment 61). The changes are uncommitted, and their availability is not verified. The session was archived.
- U-8. The effect of PR #1788 on the pylint scope (record B). The PR title was read. Its diff was not read.
- U-9. The 7 `B110` sites that spec 1032 covers (record B). The spec folder exists (RC-100). The site count was not read.
- U-10. The body of `listSiteDevicesStats` in `mistapi/api/v1/sites/stats.py` after line 1051. Only its definition line was read. A `RuntimeError` raised inside that body would change D-4.
- U-11. The closure reasons of the child issues and of issue #1709. The state fields were read. The closing comments were not read.
- U-12. The branches that hold the commits in RC-103 to RC-125. The commit objects exist (RC-103 to RC-127). Their branch names were not read.
- U-13. The count of text matches in `tests/` (60 sites). Some matches sit inside string literals, for example in the ratchet test (RC-032).
- U-14. The effect of the final gate on the pylint score. The score was not measured. RC-129 records a score of 9.53 before the change.
- U-15. The callers of `_next_apitoken` in mistapi other than the 429 branch of the retry wrapper. A caller without a catch could raise `RuntimeError` on a REST path. Those callers were not read.
