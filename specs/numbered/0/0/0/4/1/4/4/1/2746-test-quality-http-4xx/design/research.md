# Research: HTTP 4xx Test-Quality Findings

## R1. Decisions

Each decision names the alternatives, the choice, the reason, and the risk. Row references use the table in R2.

### D-1 Scope

- Alternatives: (a) `missing_fm_http_4xx` only. (b) `missing_fm_http_5xx` as the task message states. (c) Both rules.
- Chosen: (a). The issue title and body name 4xx. The triage row for `missing_fm_http_4xx` names issue #2746 (RC-23). Issue #2747 is titled for 5xx.
- Reason: The issue governs the spec. Issue #2747 already owns the 5xx rule. Two owners for one rule cause conflicts.
- Risk: The orchestrator expects 5xx work. The final reply flags this mismatch for routing.

### D-2 Working set

- Alternatives: (a) 71 findings from the issue body. (b) 14 findings from comment 98. (c) 38 baseline entries.
- Chosen: (c). The baseline is the input of the gate (RC-08, RC-16).
- Reason: The body count is outdated (comments 14 and 15). The 14 count is a comment measurement that this phase did not reproduce (R4, U-2).
- Risk: A complete report may differ. Task T002 measures the difference before any removal.

### D-3 Applicability and attribution repairs

- Alternatives: (a) Local opt-in marker. (b) Synthetic status test. (c) Config exclusion. (d) Upstream repair in misthelper-devtools.
- Chosen: (d).
- Reason: The detector treats any imported `mistapi` module as an HTTP risk (RC-74). The detector inspects a whole imported class (RC-75). The local-source gate uses the path form (RC-76). The repository root check uses the nested project (RC-77). Each cause sits in the analyzer, not in a test.
- Risk: Release timing belongs to the misthelper-devtools owner. Class A and class C entries stay in the baseline until then.

### D-4 Removal of class B entries

- Alternatives: (a) `--prune-baseline`. (b) `--write-baseline`. (c) Exact key removal after a complete report.
- Chosen: (c). Use `--write-baseline` only when every removed entry is a class B entry and the gate reports zero new findings.
- Reason: Prune drops absent-file entries only (RC-78, RC-79). The quality-gates text describes prune for missing files (RC-11). Write replaces the whole baseline with current findings (RC-12).
- Risk: A manual key error. The diff check in T004 catches it.

### D-5 Tests

- Alternatives: (a) One new test for each class A, B, or C entry. (b) A guard for unmatched entries in tests. (c) No new test, plus a conditional rule for a real gap.
- Chosen: (c).
- Reason: Class B tests already exist (RC-35, RC-38 to RC-47, RC-54 to RC-57, RC-59, RC-61 to RC-64, RC-68, RC-70 to RC-72). Class C tests already exist (RC-48, RC-53). Class A modules make no HTTP request. A guard for unmatched entries changes the analyzer contract, which is out of scope.
- Risk: A real gap may appear after T002 or T006. Task T007 handles that case.

### D-6 Product defects

- Alternatives: (a) Fix each defect here. (b) Open a separate issue for each defect. (c) Open none.
- Chosen: (c) for the defects named in comments 3, 33, and 71.
- Reason: Main already handles each case. RC-25 logs at ERROR inside the error-status branch. RC-26 rejects non-200 device config. RC-27 accepts only 2xx evidence.
- Risk: An unreported defect. Task T002 records any new finding. Task T007 records any real gap.

### D-7 Closing keyword

- Alternatives: (a) `Closes #2746` in every pull request. (b) `Part of #2746` in interim pull requests and `Closes #2746` in the final pull request.
- Chosen: (b).
- Reason: Automation closed the issue twice after partial pull requests (comments 22 and 39).
- Risk: The final pull request omits the keyword. Task T-PR checks the body.

### D-8 Line-keyed baseline entries

- Alternatives: (a) Insert tests above line-keyed entries. (b) Append tests at the end of each file. (c) Delay until issue #3102 closes.
- Chosen: (b) when a test is needed. No test edit is planned.
- Reason: The five-part key includes the line number (`baseline.py` lines 5 and 49). Issue #3102 is open but not a strict prerequisite (comment 14).
- Risk: Low. Class B, class A, and class C entries use line 1 or a measured line in untouched files.

### D-9 Measure before removal

- Alternatives: (a) Remove entries from the 2026-11-13 list. (b) Measure first.
- Chosen: (b).
- Reason: Comments report 14, 17, 20, and 21 findings at different dates. The installed analyzer is version 0.6.4 (RC-80), not 0.6.3 as comment 81 states.
- Risk: One analyzer run. The cost is small.

## R2. Remote Verification Table

Row count: 80. Each row matches one object in the `remote_checks` array of `2746-STATUS.json`. Ref `main` names the remote branch. Ref `local` names a file in the local checkout. A blob SHA of `none` marks an absent path.

| RC | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | AGENTS.md sets the writing, issue, and pull request rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| RC-02 | Gate row quotes `gate: 0 new findings vs baseline` | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 65 |
| RC-03 | Section Test quality ratchet begins | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| RC-04 | Rule forbids a baseline rewrite that hides a new finding | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 150 |
| RC-05 | Gate row requires a 4xx and a 5xx test for API client modules | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 253 |
| RC-06 | Output scan row requires tmp_path for test output | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 255 |
| RC-07 | Job test_quality_gate runs the analyzer | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 602 |
| RC-08 | Analyzer gate command reads the config and the baseline | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 632 |
| RC-09 | MYPY_PATHS names no test path | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-10 | VULTURE_PATHS names no test path | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-11 | Prune text names missing test files as its target | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 29 |
| RC-12 | Write text names removal of entries that match no finding | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 36 |
| RC-13 | Pin names misthelper-devtools commit 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| RC-14 | Test-quality configuration file exists | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| RC-15 | Guard reads copilot-instructions as a required guide | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 18 |
| RC-16 | Baseline holds 38 missing_fm_http_4xx entries among 733 entries | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 131 |
| RC-17 | Constitution file exists | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| RC-18 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-19 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-20 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-21 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-22 | Reference record folder exists with tree SHA | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | main | 00922155516e4f21e34a0bf75613fae7ab481193 | present | 0 |
| RC-23 | 2700 triage maps missing_fm_http_4xx to issue 2746 | specs/2700-missing-failure-modes/triage.md | main | 018ff20a5d2b121212e7b9e3811344a1182e3d2f | present | 10 |
| RC-24 | 1772 triage row names missing_fm_http_4xx with 38 findings | specs/1772-test-quality/triage.md | main | 4bcc526395514d29c00b3721b0b4b09ceba66a8e | present | 24 |
| RC-25 | CLI shell 4xx path logs ERROR and returns None | src/operations/execution/ssh/cli_shell_manager.py | main | fa0d5ccfe4894b7be85c0ae3c1042c817cbb20db | present | 110 |
| RC-26 | WAN probe device config fetch rejects non-200 status | src/mist/resources/gateway/wan_probe_device_override_manager.py | main | ac94673c2fa4bec31384a10127d9b9e994149b52 | present | 532 |
| RC-27 | Rogue DHCP scanner accepts only 2xx evidence | src/operations/protection/security/rogue_dhcp/scanner.py | main | dd0e76cf5b9c5686ebb154fed29e2e2ae12a8aee | present | 147 |
| RC-28 | Comment path is absent: test_config_utils_wave3 | tests/unit/test_config_utils_wave3.py | main | none | absent | 0 |
| RC-29 | Comment path is absent: test_fast_mode_small_seams | tests/unit/refactors/test_fast_mode_small_seams.py | main | none | absent | 0 |
| RC-30 | Comment path is absent: test_main_entrypoint | tests/unit/refactors/test_main_entrypoint.py | main | none | absent | 0 |
| RC-31 | Comment path is absent: test_reject_unsupported_flag_variants | tests/unit/refactors/test_reject_unsupported_flag_variants.py | main | none | absent | 0 |
| RC-32 | Comment path is absent: test_log_rotation | tests/unit/test_log_rotation.py | main | none | absent | 0 |
| RC-33 | Comment path is absent: test_device_prompt_rename_guard | tests/unit/ui/test_device_prompt_rename_guard.py | main | none | absent | 0 |
| RC-34 | Comment path is absent: test_interactive_display_utils | tests/unit/ui/test_interactive_display_utils.py | main | none | absent | 0 |
| RC-35 | Class B: 401 test at line 161 | mist-ops-platform/tests/unit/api/test_session_security.py | main | f2d951679c3b64ed2022b8879b14052025a40b8f | present | 161 |
| RC-36 | Class A: no HTTP literal | mist-ops-platform/tests/unit/mist/test_final_sdk_verification.py | main | 861cf202545ad90217196966d63446ca6578de64 | present | 0 |
| RC-37 | Class A: no HTTP literal | mist-ops-platform/tests/unit/mist/test_registry_validation.py | main | 634bdf698d15d0af13fb65ee5d9d57bbe8a3fa0c | present | 0 |
| RC-38 | Class B: 4xx test at line 117 | tests/test_upgrade_portal_mist.py | main | a3654ea59009294119375519db5676f3671d9e12 | present | 117 |
| RC-39 | Class B: 403 test at line 211 | tests/unit/firmware/test_bulk_ap_running_version.py | main | 6e4d9cb1e87aa43161ad32718676dd70be9a42e5 | present | 211 |
| RC-40 | Class B: 403 test at line 291 | tests/unit/firmware/test_firmware_manager_config.py | main | 6790f3bbd589b4a5bfcaa0108030544bc726223b | present | 291 |
| RC-41 | Class B: 403 test at line 96 | tests/unit/gateway/test_device_template_cloner_extended.py | main | a6ec61d3e49e8b553c8c46bcbd79600a8fddde63 | present | 96 |
| RC-42 | Class B: 400 test at line 141 | tests/unit/gateway/test_wan2_migration_manager.py | main | 93541f699c5b908ada1c44e9a1d57015d8515469 | present | 141 |
| RC-43 | Class B: 403 test at line 1014 | tests/unit/gateway/test_wan2_migration_manager_extended.py | main | 7a68c25cbc5c1f3a62b47ef8fc5fbec2d6cb6b4d | present | 1014 |
| RC-44 | Class B: 403 test at line 151 | tests/unit/gateway/test_wan_probe_device_override_manager.py | main | fd53499cfaae6d015511b5105b38b1e80a4aa1b9 | present | 151 |
| RC-45 | Class B: 403 test at line 292 | tests/unit/inventory/test_org_device_inventory_summary.py | main | 62f33976f9668d9dca0401bdb508016818cf0bbc | present | 292 |
| RC-46 | Class B: 404 test at line 728 | tests/unit/inventory/test_org_device_inventory_summary_wave8.py | main | 00e25edefd79a9dcf19aa5a8650c338b955837be | present | 728 |
| RC-47 | Class B: 403 test at line 507 | tests/unit/org/test_org_config_migration_conflicts.py | main | d236dbe09d02028d2400235697e251a4d9acc784 | present | 507 |
| RC-48 | Class C: parametrized 401, 403, 404, and 429 at line 122. No test has the name test_an_http_401_response_falls_back | tests/unit/org/test_org_config_migration_workflow.py | main | 6d169157ff1e507919793aac210fd15db29e2856 | present | 122 |
| RC-49 | Class A: no HTTP literal | tests/unit/refactors/test_app_context_session_state.py | main | 6f28712d03b99e60b4405fcef3d95d823efb13f0 | present | 0 |
| RC-50 | Class A: no HTTP literal | tests/unit/config/foundation/support/refactors/runtime/console/test_fast_mode_small_seams.py | main | 64bddd7813edf4f436f99db362f32aaea2625be1 | present | 0 |
| RC-51 | Class A: no HTTP literal | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py | main | 69e663203101a7cb911693fed6e0378120061910 | present | 0 |
| RC-52 | Class A: no HTTP literal | tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py | main | f23fe1c0b84872e42115f70e66020865cb2e0506 | present | 0 |
| RC-53 | Class C: 4xx responses at lines 284, 334, 721, 749, 803, and 874 | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | main | e13bf10b66a6cdf43b9904f9c0eda8fd11eb421c | present | 284 |
| RC-54 | Class B: parametrized 403 and 503 at line 249 | tests/unit/security/rogue_dhcp/test_scanner.py | main | 60ad7070f3308b72a80c3cfa8aa9e3696b0d34aa | present | 249 |
| RC-55 | Class B: parametrized 403 at line 391 | tests/unit/site/address_audit/test_audit_engine.py | main | 56631ee995808bf4665cb3b0793361c7f9f753d9 | present | 391 |
| RC-56 | Class B: 403 test at line 540 | tests/unit/ssh/test_cli_shell_manager.py | main | 02417ebfa5604269dbfac5462b92ca0fd4c7abe5 | present | 540 |
| RC-57 | Class B: 429 test at line 1227 | tests/unit/config/standalone/foundation/support/utilities/network/test_address_utils.py | main | a1253dd1182df1bfcb82b98f4b677022496d24f1 | present | 1227 |
| RC-58 | Class A: no HTTP literal | tests/unit/config/standalone/foundation/runtime/configuration/standalone_config_utils_tests/test_config_utils_wave3.py | main | 8fc547c6f6f6cb1bc651f21ad71a4449a36cd818 | present | 0 |
| RC-59 | Class B: 403 test at line 165 | tests/unit/test_issue_2971_census_repairs.py | main | 2fe6b58bd66a4a04bfae01f5cef3c9205e060d09 | present | 165 |
| RC-60 | Class A: no HTTP literal | tests/unit/config/standalone/foundation/runtime/release/test_log_rotation.py | main | 8dedded2b2c511c1545378a2b2e2e8fac8a8d799 | present | 0 |
| RC-61 | Class B: 403 test at line 1068 | tests/unit/test_prompt_network_device_utils.py | main | f1efb67cfba3d2644a7e2aaa187ad9bd45b6319a | present | 1068 |
| RC-62 | Class B: parametrized 403 and 503 at line 966 | tests/unit/config/standalone/foundation/support/utilities/network/test_rate_limiting.py | main | 8e7250f4aac4e64b7157e86d8f060ba650bf8846 | present | 966 |
| RC-63 | Class B: 403 test at line 733 | tests/unit/prod_readiness/standalone/operations/wan/test_wan_hub_group_manager.py | main | c2581f5e6fa0346386885ea7423f74a254a23d55 | present | 733 |
| RC-64 | Class B: parametrized 403 at line 630 | tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py | main | 362cd3e547907ac7d89357e2c1e369b1a5d749c2 | present | 630 |
| RC-65 | Class A: the only 4xx-range matches are the issue number 431 in text | tests/unit/maps/interfaces/ui/interaction/dispatch/test_device_prompt_rename_guard.py | main | 7b524e94341110b17397341201cf00847843a367 | present | 1 |
| RC-66 | Class A: no HTTP literal | tests/unit/maps/interfaces/ui/interaction/dispatch/test_interactive_display_utils.py | main | ade685530ac749c72ae3afe9e223d730be4708fb | present | 0 |
| RC-67 | Class A: no HTTP literal | tests/unit/ui/test_level_discoverer.py | main | fbb8e044f26366008e047a21ef12fc618b13a6f7 | present | 0 |
| RC-68 | Class B: 403 response at line 958 | tests/unit/ui/test_prompt_utils.py | main | 68f3576ddfc9629efdcbaad627cc691e9a8a2c3a | present | 958 |
| RC-69 | Class A: imports FirmwareManager at line 27 and uses only its classifier | tests/unit/upgrade_portal/test_upgrade_service_classify.py | main | 65d180579bb01dc1ffd2be1ee157487c576c247f | present | 27 |
| RC-70 | Class B: 403 test at line 131 | tests/unit/utils/test_tls_policy.py | main | 0f241554fa76be3aaf15290ab93539ed00878fbb | present | 131 |
| RC-71 | Class B: 403 test at line 244 | tests/unit/web_portal/test_operations_silent_failure.py | main | b6ac562223330ce85075b0a408c664db15f90742 | present | 244 |
| RC-72 | Class B: parametrized 4xx statuses at line 342 | tests/unit/websocket/test_service_ping_discovery.py | main | 4a7e7cad4ec16936ad1f5afa218fd1ce78644363 | present | 342 |
| RC-73 | SDK APIResponse class at line 22 and status_code field at line 43 | .venv\Lib\site-packages\mistapi\__api_response.py | local | 2d878d79295fec79e6409f6243132c53280f15ab | present | 22 |
| RC-74 | Analyzer HTTP status risk from imported SDK modules at lines 370 to 372 | .venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\missing_failure_mode.py | local | 8ab8eb2fea5fcb953ad34247b2cc56203c38c0ea | present | 370 |
| RC-75 | Analyzer inspects the whole imported class segment at lines 323 to 329 | .venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\missing_failure_mode.py | local | 8ab8eb2fea5fcb953ad34247b2cc56203c38c0ea | present | 323 |
| RC-76 | Analyzer local-source gate uses the path form at lines 348 to 354 | .venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\missing_failure_mode.py | local | 8ab8eb2fea5fcb953ad34247b2cc56203c38c0ea | present | 348 |
| RC-77 | Analyzer repository root walks to the nearest project at line 422 | .venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\missing_failure_mode.py | local | 8ab8eb2fea5fcb953ad34247b2cc56203c38c0ea | present | 422 |
| RC-78 | Baseline stale_entries returns absent-file paths only, at line 151 | .venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\baseline.py | local | 7f3f41270313473287c1c677799932ca66aefdf8 | present | 151 |
| RC-79 | Analyzer prune call uses only absent-file entries at line 350 | .venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\__main__.py | local | 66cb242e64251f1f60a6412d733391e54f702336 | present | 350 |
| RC-80 | Installed misthelper-devtools 0.6.4 names commit 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | .venv\Lib\site-packages\misthelper_devtools-0.6.4.dist-info\direct_url.json | local | 25f69f79362e354467dfa92cc1f1e4a183b883b4 | present | 1 |

## R3. Sources

Local files read in this session:

- `AGENTS.md`, in full.
- `.github/copilot-instructions.md`, lines 1 to 330.
- `.specify/memory/constitution.md`, lines 1 to 330.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`, in full.
- `.github/test-quality-baseline.json`, lines 1 to 60, with the entry fields confirmed.
- Headings of `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Reference shape only.
- Named test modules, read by grep for HTTP and status patterns: `tests/unit/refactors/test_app_context_session_state.py`, `tests/unit/ui/test_level_discoverer.py`, `tests/unit/upgrade_portal/test_upgrade_service_classify.py`, `mist-ops-platform/tests/unit/mist/test_final_sdk_verification.py`, and `mist-ops-platform/tests/unit/mist/test_registry_validation.py`.
- `specs/2700-missing-failure-modes/triage.md` and `specs/1772-test-quality/triage.md`, by grep.
- `.venv\Lib\site-packages\mistapi\__api_response.py`, lines 22 to 64.
- `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\missing_failure_mode.py`, lines 1 to 60, 283 to 372, and 420 to 436.
- `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\baseline.py`, lines 1 to 30 and 148 to 185.
- `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\__main__.py`, by grep and lines 328 to 360.

Remote reads (GitHub API, read-only, 2026-11-26):

- Issue #2746: metadata, body, and all 100 comments.
- Pull requests that match `2746`: 43 results with `--limit 300`. Each result read with `gh pr view`.
- Issues and pull requests: 2700, 2703, 2704, 2747, 2971, 3102, 3436, 3736, 3745, 4133, 4358, 4404, 4503, 4514, 4553, 4560, 4604, 4611, 4612, 4614, 4387, 4405, 4732, 4748, 4822, 3994, 3955, and 2711.
- misthelper-devtools issue #67.
- Tree `git/trees/main?recursive=1`: 11,404 entries, not truncated.
- Main commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local `HEAD` matches it.
- Blob bodies read through `git/blobs` with the blob SHA from the tree. The contents API returned HTTP 404 for `.github` paths in this session.

URLs:

- https://github.com/jmorrison-juniper/MistHelper/issues/2746
- https://github.com/jmorrison-juniper/MistHelper/issues/2747
- https://github.com/jmorrison-juniper/misthelper-devtools/issues/67

## R4. Unverified

- U-1: The complete report did not run. Reason: this phase forbids running a repository script. Effect: counts come from comments and static reading. Task T002 confirms them.
- U-2: The 14-finding count from 2026-11-13 is not reproduced. Reason: comment evidence only.
- U-3: The unpublished misthelper-devtools candidates named in comments 79 to 96 are not fetched. Reason: no commit URL was fetched. None is on the pin.
- U-4: The changed files of PR 4604 and PR 4514 are not read. Reason: only titles and merge dates are verified.
- U-5: Mist endpoint behavior for any 4xx status is not claimed. Reason: the tests use simulated responses only.

## R5. Skills and Documents

Skills: No skill was loaded. Reason: the issue concerns Python tests and analyzer gates, with no Podman or Juniper device question.

Documents not read: `documentation/architecture.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, `documentation/operator-guide.md`, `documentation/mist-api-openapi31yaml.yaml`, `documentation/MIST_API_GET_ENDPOINTS.md`, and `documentation/MIST_API_MISSING_ENDPOINTS.md`. Reason: the change alters no architecture, setup, container, operator, or Mist endpoint behavior.
