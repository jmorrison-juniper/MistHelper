# Research: Test quality: repair remaining missing_fm_http_4xx findings

Each decision names the chosen option, the alternatives, the reason, and the risk. Remote claims come from `gh api` reads of the MistHelper default branch and of the pinned misthelper-devtools commit. Local claims come from `.venv` files, and their blob SHAs come from `git hash-object` without a write.

## Decisions

### D-1. Scope is the 4xx rule only

- **Decision**: Repair only `missing_fm_http_4xx`. The 5xx rule stays open under issue #2747.
- **Alternatives considered**: Repair both rules in one record. Repair the 5xx rule under the 4xx title.
- **Rationale**: The orchestrator task names the 4xx rule. The issue body and title name the 5xx rule (issue #2747, read on 2026-11-26). The 4xx title belongs to issue #2746 (open).
- **Risk**: The 5xx findings need a second record. The owner must route that work.

### D-2. Repair detector defects upstream and pin a released commit

- **Decision**: Repair the family F2 applicability defects and the family F3 coverage defects in misthelper-devtools. MistHelper changes only the pin, after a release (T006 to T009).
- **Alternatives considered**: Add `path_globs` exclusions to `.github/test-quality-config.toml`. Add opt-in markers. Add synthetic HTTP tests to registry and local-helper modules. Edit the baseline to hide the entries.
- **Rationale**: The rule code lives in the pinned package (R-61 to R-68). The copilot instructions forbid a baseline edit that hides a finding (R-03). The issue comments reject a synthetic test for a module with no HTTP path. An exclusion hides the finding instead of repairing its cause.
- **Risk**: The release date is unknown (U-2). MistHelper stays blocked until the release.

### D-3. Place a family F1 test in the existing module

- **Decision**: Add each F1 test to the existing test module that the finding names.
- **Alternatives considered**: Add a new test module for each F1 finding.
- **Rationale**: Each baseline entry names one file path and one rule (R-17). A new module leaves the entry in place and adds a file. A test added to the existing module changes that module only.
- **Risk**: The module gains one test function. No directory gains a child.

### D-4. Write the baseline with the documented command, then restore non-4xx entries

- **Decision**: Run `test-quality-analyzer --write-baseline` after the census and the repairs (T012). Restore each removed entry whose rule is not 4xx.
- **Alternatives considered**: `--prune-baseline` only. Hand edits of the JSON.
- **Rationale**: `documentation/quality-gates.md` line 29 (R-82) says the prune command removes entries for test files that no longer exist. Line 37 (R-11) says `--write-baseline` removes each entry that matches no current finding. Line 41 (R-12) warns against `--roots`. A hand edit is error-prone for 733 entries.
- **Risk**: `--write-baseline` removes stale entries for every rule. The restore step is manual (T012).

### D-5. New test code adds no log statement

- **Decision**: New test code carries an inline comment on each executable line. The tests assert the existing log records of the source under test. The tests add no `logging` call.
- **Alternatives considered**: Add `info` and `debug` logs to each test. Exempt tests from Principle VI.
- **Rationale**: Principle VII (R-06, line 235) governs operational actions. A test is not an operator action. An added log would repeat the source log. Principle VI (R-05, line 204) still applies to test code.
- **Risk**: A reviewer may reject D-5. The pull request body records the decision so that the reviewer can decide.

### D-6. Use "Part of" references, not a closing keyword

- **Decision**: The pull request body holds `Part of #2747` and `Part of #2746`. It holds no closing keyword.
- **Alternatives considered**: `Closes #2747`, as the brief template shows.
- **Rationale**: Issue comments of 2026-10-20 and 2026-10-22 record an automatic close and a reopen. Issue #2747 keeps 5xx findings open.
- **Risk**: Both issues stay open after this merge. The owner closes them when the scope completes.

### D-7. Hold the file that open pull request #4208 owns

- **Decision**: Do not change `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` while PR #4208 is open (FR-013).
- **Alternatives considered**: Edit the file on a separate branch.
- **Rationale**: `AGENTS.md` (R-01) says one file cannot carry two open pull requests. The open pull request census shows PR #4208 as the only overlap (R-41, T001).
- **Risk**: One row waits for PR #4208 to close.

### D-8. Add one changelog fragment

- **Decision**: Add `changelog.d/issue-2747-fm-http-4xx.md` with one `### Changed` heading and one bullet that names issue #2747. Follow `changelog.d/README.md` (R-84) for the layout.
- **Alternatives considered**: Add no fragment, because the change is test-only and not visible to a user.
- **Rationale**: The constitution states that each change MUST add one unique fragment (R-83, line 409). The constitution supersedes the other practice documents (constitution Governance section). The copilot instructions and `AGENTS.md` require a fragment only for a user-visible change. The stricter constitution rule applies.
- **Risk**: The release notes list a test-only change. The bullet states that the change is test-only.

### D-9. Run the census in the implementing environment

- **Decision**: The implementing environment runs the census. Its output goes to `test-artifacts/2747/`, which Git ignores.
- **Alternatives considered**: Run the census in this record. Commit the report.
- **Rationale**: The brief forbids running an analyzer in this record (rule 2). The constitution (Data Directory rule) puts generated test evidence in the git-ignored `test-artifacts/` folder.
- **Risk**: The census counts appear only after T003 and T004.

### D-10. Keep the record under issue #2747

- **Decision**: Use issue #2747 as the record key, as the orchestrator instructs. Name issue #2746 in the pull request body.
- **Alternatives considered**: Rename the record to issue #2746.
- **Rationale**: The orchestrator assigns `ISSUE=2747`, and the route folder name depends on that number. The pull request names both issues, so either owner can close its scope.
- **Risk**: The owner may move the 4xx scope to #2746. The record stays valid because the pull request names both issues.

## Remote Verification

Each row is one check. The "Ref" column names the commit or the source of the read:

- `main`: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` (tree listing) or `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`.
- A 40-character SHA: `gh api repos/jmorrison-juniper/misthelper-devtools/contents/<path>?ref=<sha>` in misthelper-devtools.
- `local .venv` rows: the file under `.venv`, with the blob SHA from `git hash-object`.

The tree listing on 2026-11-26 holds 11,404 entries and is not truncated.


| # | Claim | Path | Ref | Blob SHA | Result | Line |
|---|-------|------|-----|----------|--------|------|
| R-01 | Writing, safety, and git rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 1 |
| R-02 | Test-quality row for HTTP 4xx and 5xx tests | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 253 |
| R-03 | Baseline is not rewritten to hide a finding | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 150 |
| R-04 | Constitution Principle IV, full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 148 |
| R-05 | Constitution Principle VI, inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-06 | Constitution Principle VII, action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R-07 | Spec Kit template for the specification | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 1 |
| R-08 | Spec Kit template for the plan | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 1 |
| R-09 | Spec Kit template for the tasks | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 1 |
| R-10 | Spec Kit template for the checklist | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 1 |
| R-11 | Quality gates: baseline write command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 37 |
| R-12 | Quality gates: warning against `--roots` | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 41 |
| R-13 | CI: test quality gate job | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 602 |
| R-14 | CI: analyzer gate command with the scope array | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 632 |
| R-15 | Analyzer config: `missing_http_4xx` rule enabled | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 29 |
| R-16 | Analyzer config: Mist API predicate bans `mistapi` imports | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 66 |
| R-17 | Baseline holds 733 entries, 38 `missing_fm_http_4xx`, and 42 `missing_fm_http_5xx`. First 4xx entry at line 131. | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 131 |
| R-18 | Devtools pin at commit 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| R-19 | 2700 triage row for `missing_fm_http_4xx` (tagged #2746) | specs/2700-missing-failure-modes/triage.md | main | 018ff20a5d2b121212e7b9e3811344a1182e3d2f | present | 10 |
| R-20 | 1772 triage row for `missing_fm_http_4xx` | specs/1772-test-quality/triage.md | main | 4bcc526395514d29c00b3721b0b4b09ceba66a8e | present | 24 |
| R-21 | Reference record shape (spec) | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R-22 | Preflight guard, `TestLiveGuides` | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 1 |
| R-23 | Baseline 4xx entry, module present (session security) | mist-ops-platform/tests/unit/api/test_session_security.py | main | f2d951679c3b64ed2022b8879b14052025a40b8f | present | 1 |
| R-24 | Baseline 4xx entry, module present (final SDK verification) | mist-ops-platform/tests/unit/mist/test_final_sdk_verification.py | main | 861cf202545ad90217196966d63446ca6578de64 | present | 1 |
| R-25 | Baseline 4xx entry, module present (registry validation) | mist-ops-platform/tests/unit/mist/test_registry_validation.py | main | 634bdf698d15d0af13fb65ee5d9d57bbe8a3fa0c | present | 1 |
| R-26 | Baseline 4xx entry, module present (upgrade portal Mist) | tests/test_upgrade_portal_mist.py | main | a3654ea59009294119375519db5676f3671d9e12 | present | 1 |
| R-27 | Baseline 4xx entry, module present (bulk AP running version) | tests/unit/firmware/test_bulk_ap_running_version.py | main | 6e4d9cb1e87aa43161ad32718676dd70be9a42e5 | present | 1 |
| R-28 | Baseline 4xx entry, module present (firmware manager config) | tests/unit/firmware/test_firmware_manager_config.py | main | 6790f3bbd589b4a5bfcaa0108030544bc726223b | present | 1 |
| R-29 | Baseline 4xx entry, module present (device template cloner extended) | tests/unit/gateway/test_device_template_cloner_extended.py | main | a6ec61d3e49e8b553c8c46bcbd79600a8fddde63 | present | 1 |
| R-30 | Baseline 4xx entry, module present (WAN2 migration manager) | tests/unit/gateway/test_wan2_migration_manager.py | main | 93541f699c5b908ada1c44e9a1d57015d8515469 | present | 1 |
| R-31 | Baseline 4xx entry, module present (WAN2 migration manager extended) | tests/unit/gateway/test_wan2_migration_manager_extended.py | main | 7a68c25cbc5c1f3a62b47ef8fc5fbec2d6cb6b4d | present | 1 |
| R-32 | Baseline 4xx entry, module present (WAN probe device override manager) | tests/unit/gateway/test_wan_probe_device_override_manager.py | main | fd53499cfaae6d015511b5105b38b1e80a4aa1b9 | present | 1 |
| R-33 | Baseline 4xx entry, module present (org device inventory summary) | tests/unit/inventory/test_org_device_inventory_summary.py | main | 62f33976f9668d9dca0401bdb508016818cf0bbc | present | 1 |
| R-34 | Baseline 4xx entry, module present (org device inventory summary wave 8) | tests/unit/inventory/test_org_device_inventory_summary_wave8.py | main | 00e25edefd79a9dcf19aa5a8650c338b955837be | present | 1 |
| R-35 | Baseline 4xx entry, module present (org config migration conflicts) | tests/unit/org/test_org_config_migration_conflicts.py | main | d236dbe09d02028d2400235697e251a4d9acc784 | present | 1 |
| R-36 | Baseline 4xx entry, module present (org config migration workflow) | tests/unit/org/test_org_config_migration_workflow.py | main | 6d169157ff1e507919793aac210fd15db29e2856 | present | 1 |
| R-37 | Baseline 4xx entry, module present (app context session state) | tests/unit/refactors/test_app_context_session_state.py | main | 6f28712d03b99e60b4405fcef3d95d823efb13f0 | present | 1 |
| R-38 | Baseline 4xx entry, module present (fast mode small seams) | tests/unit/config/foundation/support/refactors/runtime/console/test_fast_mode_small_seams.py | main | 64bddd7813edf4f436f99db362f32aaea2625be1 | present | 1 |
| R-39 | Baseline 4xx entry, module present (main entrypoint) | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py | main | 69e663203101a7cb911693fed6e0378120061910 | present | 1 |
| R-40 | Baseline 4xx entry, module present (reject unsupported flag variants) | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py | main | f23fe1c0b84872e42115f70e66020865cb2e0506 | present | 1 |
| R-41 | Baseline 4xx entry, module present (WLAN RADIUS timer paths, held by PR #4208) | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | main | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 1 |
| R-42 | Baseline 4xx entry, module present (rogue DHCP scanner) | tests/unit/security/rogue_dhcp/test_scanner.py | main | 60ad7070f3308b72a80c3cfa8aa9e3696b0d34aa | present | 1 |
| R-43 | Baseline 4xx entry, module present (address audit engine) | tests/unit/site/address_audit/test_audit_engine.py | main | 56631ee995808bf4665cb3b0793361c7f9f753d9 | present | 1 |
| R-44 | Baseline 4xx entry, module present (CLI shell manager) | tests/unit/ssh/test_cli_shell_manager.py | main | 02417ebfa5604269dbfac5462b92ca0fd4c7abe5 | present | 1 |
| R-45 | Baseline 4xx entry, module present (address utilities) | tests/unit/config/standalone/foundation/support/utilities/network/test_address_utils.py | main | a1253dd1182df1bfcb82b98f4b677022496d24f1 | present | 1 |
| R-46 | Baseline 4xx entry, module present (config utilities wave 3) | tests/unit/config/standalone/foundation/runtime/configuration/standalone_config_utils_tests/test_config_utils_wave3.py | main | 8fc547c6f6f6cb1bc651f21ad71a4449a36cd818 | present | 1 |
| R-47 | Baseline 4xx entry, module present (issue 2971 census repairs) | tests/unit/test_issue_2971_census_repairs.py | main | 2fe6b58bd66a4a04bfae01f5cef3c9205e060d09 | present | 1 |
| R-48 | Baseline 4xx entry, module present (log rotation) | tests/unit/config/standalone/foundation/runtime/release/test_log_rotation.py | main | 8dedded2b2c511c1545378a2b2e2e8fac8a8d799 | present | 1 |
| R-49 | Baseline 4xx entry, module present (prompt network device utilities) | tests/unit/test_prompt_network_device_utils.py | main | f1efb67cfba3d2644a7e2aaa187ad9bd45b6319a | present | 1 |
| R-50 | Baseline 4xx entry, module present (rate limiting) | tests/unit/config/standalone/foundation/support/utilities/network/test_rate_limiting.py | main | 8e7250f4aac4e64b7157e86d8f060ba650bf8846 | present | 1 |
| R-51 | Baseline 4xx entry, module present (WAN hub group manager) | tests/unit/prod_readiness/standalone/operations/wan/test_wan_hub_group_manager.py | main | c2581f5e6fa0346386885ea7423f74a254a23d55 | present | 1 |
| R-52 | Baseline 4xx entry, module present (WAN VPN builder) | tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py | main | 362cd3e547907ac7d89357e2c1e369b1a5d749c2 | present | 1 |
| R-53 | Baseline 4xx entry, module present (device prompt rename guard) | tests/unit/maps/interfaces/ui/interaction/dispatch/test_device_prompt_rename_guard.py | main | 7b524e94341110b17397341201cf00847843a367 | present | 1 |
| R-54 | Baseline 4xx entry, module present (interactive display utilities) | tests/unit/maps/interfaces/ui/interaction/dispatch/test_interactive_display_utils.py | main | ade685530ac749c72ae3afe9e223d730be4708fb | present | 1 |
| R-55 | Baseline 4xx entry, module present (level discoverer) | tests/unit/ui/test_level_discoverer.py | main | fbb8e044f26366008e047a21ef12fc618b13a6f7 | present | 1 |
| R-56 | Baseline 4xx entry, module present (prompt utilities) | tests/unit/ui/test_prompt_utils.py | main | 68f3576ddfc9629efdcbaad627cc691e9a8a2c3a | present | 1 |
| R-57 | Baseline 4xx entry, module present (upgrade service classify) | tests/unit/upgrade_portal/test_upgrade_service_classify.py | main | 65d180579bb01dc1ffd2be1ee157487c576c247f | present | 1 |
| R-58 | Baseline 4xx entry, module present (TLS policy) | tests/unit/utils/test_tls_policy.py | main | 0f241554fa76be3aaf15290ab93539ed00878fbb | present | 1 |
| R-59 | Baseline 4xx entry, module present (operations silent failure) | tests/unit/web_portal/test_operations_silent_failure.py | main | b6ac562223330ce85075b0a408c664db15f90742 | present | 1 |
| R-60 | Baseline 4xx entry, module present (service ping discovery) | tests/unit/websocket/test_service_ping_discovery.py | main | 4a7e7cad4ec16936ad1f5afa218fd1ce78644363 | present | 1 |
| R-61 | Detector applicability: tests-root rule decides local-source risk (`_allows_local_source`) | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 351 |
| R-62 | Detector applicability: string `mistapi.api.` counts as HTTP status risk | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 378 |
| R-63 | Detector finding: HTTP status risk and no 4xx coverage | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 704 |
| R-64 | Detector rule identifier `missing_fm_http_4xx` | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 708 |
| R-65 | Detector coverage: `SourceDrivenCoverageSlicer` class | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 438 |
| R-66 | Detector coverage: a test drives source when it calls a source root (`_calls_source`) | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 500 |
| R-67 | Detector coverage: local driver helpers (`_collect_source_driver_names`) | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 538 |
| R-68 | Detector coverage: local source names only for analyzer fixtures (`_collect_local_source_names`) | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 587 |
| R-69 | Installed detector is identical to the pinned file (local install recorded at commit 2239e7bd) | .venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\missing_failure_mode.py | local install (commit 2239e7bd468fd27e40c43f2b87fcd35a2e49672b) | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 704 |
| R-70 | mistapi `APIResponse` class (mistapi 0.64.1) | .venv\Lib\site-packages\mistapi\__api_response.py | local .venv (mistapi 0.64.1) | 2d878d79295fec79e6409f6243132c53280f15ab | present | 22 |
| R-71 | mistapi `APIResponse` stores the response status | .venv\Lib\site-packages\mistapi\__api_response.py | local .venv (mistapi 0.64.1) | 2d878d79295fec79e6409f6243132c53280f15ab | present | 48 |
| R-72 | OpenAPI file declares HTTP 403 response entries | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 1614 |
| R-73 | Visualization prompt utilities import `mistapi` and `requests` | src/interfaces/visualization/ui/prompt_utils.py | main | 85298f30dcbc6ed5a6adf01b5801347e2ede7efd | present | 16 |
| R-74 | Interactive display utilities reference `mistapi.api.v1` functions | src/interfaces/visualization/ui/interactive_display_utils.py | main | a763b8fbf97dfdfb5cf5802291a432b42fce2c4f | present | 59 |
| R-75 | Level discoverer builds `mistapi.api.v1` path strings | src/interfaces/visualization/ui/runtime/level_discoverer.py | main | 1e9e492f9d847fb5d3ecc719e6bad8f658db7435 | present | 26 |
| R-76 | Firmware manager imports `mistapi` as a module-level alias | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | present | 62 |
| R-77 | Initialize Mist session imports `requests.adapters` | src/foundation/support/refactors/initialize_mist_session.py | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 26 |
| R-78 | MistHelper loads `requests` at runtime through `__import__` | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 983 |
| R-79 | Config utilities docstring names the `mistapi.APISession` login | src/foundation/runtime/config/config_utils.py | main | b63d83c1cfad322df7442a2241d8e614c1d6fdfa | present | 21 |
| R-80 | Devtools README test command `python -m pytest` at the pin | README.md (misthelper-devtools) | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 36db7c3e49f7700e707fd5b05fd6ca024a3482d0 | present | 24 |
| R-81 | Devtools `testpaths = ["tests"]` at the pin | pyproject.toml (misthelper-devtools) | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 0f52f10c8308a883314489e20970883c62d0943d | present | 81 |
| R-82 | Quality gates: prune command removes entries for test files that no longer exist | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 29 |
| R-83 | Constitution Documentation rule: each change MUST add one unique changelog fragment | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-84 | Changelog fragment rules (layout for fragment files) | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 1 |
| R-85 | STE linter configuration for record checks | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 1 |

The table has 85 rows. Each row matches one entry in `remote_checks` in the STATUS file.

## Sources

- Issue #2747 (MistHelper), read through `gh issue view` on 2026-11-26. It holds the title, body, labels (`chore`, `tests`, `in-progress`, `priority:P3`, `severity:medium`), and 87 comments.
- Issue #2746 (MistHelper), read through `gh issue view`. Open, with the title "Test quality: repair remaining missing_fm_http_4xx findings".
- Closed triage issues #2700, #2703, and #1772 (MistHelper), read through `gh issue view`.
- Closed defect issues #4560 (rogue DHCP scanner) and #4564 (WAN VPN builder), read through `gh issue view`.
- Pull request search for "2747" (MistHelper), read through `gh pr list --state all`. It returned 27 pull requests. 25 are merged. Pull requests #2962 and #3954 are closed.
- Open pull request census (MistHelper), read through `gh pr list --state open --json files`. It returned 7 open pull requests. Only PR #4208 overlaps the 38 test paths.
- Pull requests cited in issue comments as reservations, read through `gh pr view`. PRs #4404, #4619, #4503, #4514, #4497, #4357, #4324, #4312, #4478, #4402, #4385, and #4387 are merged. PR #4133 does not resolve in MistHelper.
- Issue #67 (misthelper-devtools), read through `gh issue view`. Open. Its title is "SourceDrivenCoverageSlicer discards every fixture-driven test".
- Commits `b15d4f913030f984d07088e85f99bddf44ce7d4a` and `66449a34a3f875be4a605a8c7236ac58bd2fb485` (misthelper-devtools), read through `gh api repos/jmorrison-juniper/misthelper-devtools/commits/<sha>`. Both exist. Neither is the pinned commit.
- Pinned misthelper-devtools commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`, read through `gh api contents` (R-61 to R-68, R-80, R-81).
- Local installed packages in `.venv`: `misthelper_devtools` (dist-info records commit 2239e7bd) and `mistapi` 0.64.1 (R-69 to R-71).
- Local documents read with the view tool: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and `documentation/quality-gates.md`.
- The four Spec Kit templates and the reference record were also read with the view tool.
- Local blob SHAs match remote rows R-01 to R-06, R-11 to R-18, R-82, and R-83.
- No `web_fetch` call was made. No external web source was needed.
- The documents `documentation/architecture.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md` hold no test-quality or baseline text (search, 0 matches). They do not apply. The Mist endpoint coverage documents do not apply, because the change touches no endpoint.
- No skill was loaded. The work concerns Python test quality, not Podman or Juniper device behavior.

## Unverified

- **U-1. Census counts on `main`.** The brief forbids running an analyzer. The current count of `missing_fm_http_4xx` findings and of stale baseline entries is not measured. Next step: T003 and T004.
- **U-2. Upstream release.** No misthelper-devtools release contains the F2 and F3 repairs. Issue #67 is open. Next step: T008.
- **U-3. Family labels.** The pre-census families come from static reading of the detector and of each test body. The census may change them. Next step: T005.
- **U-4. Effect of candidate commits.** Commits `b15d4f91` and `66449a34` exist, and their commit messages are verified. Their effect on the findings is reported in issue comments only and was not executed. Next step: the regression cases in T006 and T007.
- **U-5. Pull request #4133.** An issue comment cites this pull request as a held test candidate. A GitHub lookup in MistHelper fails. The reference is treated as unknown.
- **U-6. Live behavior of 4xx responses.** No live Mist call is allowed. R-72 shows that the OpenAPI file documents the response entries. It does not prove endpoint behavior.
- **U-7. Recovery branch.** Issue comments cite `recovery/2747-handoff-20261004` at commit `2d5695fb4ed00411e5dbaf0d2b03539e3aff4863`. This record did not read that branch through the API. The branch covers HTTP 503 and HTTP 200 controls, which belong to the 5xx scope (D-1).
