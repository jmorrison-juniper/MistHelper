# Research: Remediate the five-child debt of three folders

## Method

- Remote truth: The recursive tree of `main` was fetched twice on 2026-11-26. Both fetches returned 11404 entries and no truncation. The `main` ref holds commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca.
- Local HEAD equals `origin/main`. The working tree has five modified tracked files outside this scope. None of them is a claim row.
- Line claims: Each reference file hashes to the same blob SHA locally (`git hash-object`) and on main. Equal SHAs mean equal bytes, so the cited line numbers hold on main.
- Directory claims: The tree SHA of each debt folder equals the tree SHA of local HEAD.
- Counts: A tracked child is a distinct first path segment under the folder in the recursive tree. Local-only folders are not tracked children.

## Decisions

### D-1 Category layout

- Alternatives: (a) Move `compose.ps1` into a category folder. (b) Keep a flat folder with name prefixes.
- Choice: Four category folders and `compose.ps1` at the top level of `scripts/`.
- Reason: Operator and developer documents name `scripts\compose.ps1` in more than ten files. Moving it adds churn and risk. The four category names follow the issue's examples.
- Risk: One file stays at the top level. This is a recorded exception to a pure purpose layout.

### D-2 Mirror the categories in `tests/unit/scripts/`

- Alternatives: (a) Keep the test modules flat. (b) Move them into a separate test tree.
- Choice: Mirror the category folders. `test_script_imports.py` stays at the top level, because CI names it at `.github/workflows/ci.yml` line 303.
- Reason: A developer finds a test from the path of its tool.
- Risk: More test modules move. Basenames stay unique. The duplicate check on main found no shared basename.

### D-3 Runbook layout

- Alternatives: (a) Add a `README.md` index beside `_shared_common.md` and four folders. That makes six children. (b) Give `_shared_common.md` its own fifth folder. That makes six children.
- Choice: `SSR_ALARM_INDEX.md` stays at the top level as the one index file. The platform folders are `gateway/`, `switch/`, `ssr/`, and `integration/`. The integration folder holds `_shared_common.md`, `NODE_DOWN.md`, `AP_WARNING_REPORT_MENU_307.md`, and `MIST_NETCOOL_ALARM_INTEGRATION.md`.
- Reason: The issue asks to keep one index file. Five children fit only with this layout.
- Risk: The index covers SSR alarms only. Operators find other runbooks through the folder names.

### D-4 Guard location and form

- Alternatives: (a) A new test file in `tests/guardrails/`. That adds a child to a noncompliant parent. Principle I forbids it. (b) A new JSON baseline file in `tests/guardrails/`. Same rule. (c) A count of filesystem children. That counts `__pycache__` and local-only folders. (d) A baseline file inside each debt folder. That makes the folder count itself.
- Choice: Add the guard cases to `tests/guardrails/test_process_folder_structure.py`. Store the baseline as the constant `DEBT_FOLDER_BASELINE`. Count tracked children with `git ls-files`.
- Reason: The guard adds no child. The count matches the issue's definition.
- Risk: Git must exist in CI and in local runs. The guard fails when `git ls-files` fails. It never skips.

### D-5 Six pull requests, one move group each

- Alternatives: (a) One pull request for all groups. (b) Group by file type.
- Choice: PR-1 guard. PR-2 runbooks. PR-3 verification tools. PR-4 repository tools. PR-5 reference tools. PR-6 one-time scans.
- Reason: The issue asks for one move group per pull request. Runbooks change no code import except two paths. The one-time scans have the most files and the most mypy entries, so they go last.
- Risk: Six reviews. Each review stays small.

### D-6 Closing keyword

- Alternatives: (a) `Closes #4944` in each pull request. (b) `Refs #4944` in each pull request, and no closing keyword.
- Choice: `Refs #4944` in PR-1 to PR-5. `Closes #4944` in PR-6.
- Reason: The first merge would close the issue while later groups stay open work. The brief's T-PR wording assumes one pull request. This choice deviates from that wording for the reason given here.
- Risk: None for the merge. The issue closes at the final merge.

### D-7 Historical records

- Alternatives: (a) Rewrite the historical files to the new paths. (b) Leave every historical file unchanged and exclude it from the sweep.
- Choice: The old-path sweep excludes `specs/`, `changelog.d/`, `CHANGELOG.md`, `documentation/release-notes.md`, `documentation/development-tooling-migration.md`, and `.specify/bugs/menu-93-inventory-output/fix.md`.
- Reason: These files record past facts with dates. Rewriting them changes history and creates a large conflict set. A targeted grep found moved paths in three historical files outside `specs/` and `changelog.d/`. The other files that name moved items are active. Each pull request updates them.
- Risk: A reader can follow an old path in a historical file. Each historical file states its date. This choice deviates from the issue's literal criterion, and the deviation is recorded here.

### D-8 No alias, shim, or wrapper at an old path

- Alternatives: (a) Keep a stub module at each old path. (b) Keep a symbolic link at each old path.
- Choice: Each pull request changes every caller in the same pull request.
- Reason: AGENTS.md and the constitution forbid compatibility shims. A stub adds a child to a debt folder.
- Risk: A developer who runs an old command sees a missing file. The documents, the changelog fragment, and the commit message name the new path.

### D-9 Repository-root expressions

- Alternatives: (a) Keep the old depth and add a link to the root. (b) Read the root from an environment variable.
- Choice: Update each expression to the new depth. Test each one with the path-depth cases in `tests/unit/scripts/test_script_imports.py`.
- Reason: The change is explicit and cheap to test. A test fails when a file moves and its depth stays old.
- Risk: A new file copies an old expression. Each pull request runs the sweep for `parents[` and `parent.parent` under `scripts/`.

### D-10 Baseline counts from main

- Alternatives: (a) Use the issue's counts 52, 10, and 16. (b) Use the counts of local HEAD with local-only folders.
- Choice: Use 53, 10, and 17, measured on commit f03c6c9b.
- Reason: The issue counts for `scripts/` and `documentation/noc-runbooks/` predate PR #4941. The issue count for `tests/unit/scripts/` was never correct. Main is the truth order in this record.
- Risk: Main moves before PR-1 merges. The implementer rebases and recounts.

### D-11 Generated pages

- Alternatives: (a) Edit the pages by hand. (b) Remove the command text from the pages.
- Choice: Regenerate each page with its tool in PR-5. Run each `--check` command.
- Reason: The menu reference drift gate compares the output of the generator. Hand edits drift.
- Risk: The generator needs the moved modules at their new paths in the same pull request.

### D-12 Local-only folders and untracked files

- Alternatives: (a) Delete the local-only folders. (b) Commit them.
- Choice: Leave them unchanged. Stage each file by explicit path. Do not stage the local-only folders.
- Reason: Deletion is destructive. The folders are not repository content. AGENTS.md requires explicit staging.
- Risk: A local-only file can remain on disk. The guard does not count it.

### D-13 Location of the path-depth cases

- Alternatives: (a) A new test file under `tests/unit/scripts/`. That adds a child to a debt folder. (b) A new file in `tests/guardrails/`. That adds a child to a noncompliant parent.
- Choice: Add the test function and its cases to `tests/unit/scripts/test_script_imports.py`.
- Reason: The file exists. The change adds no child.
- Risk: The file grows by 24 cases over six pull requests. Each case stays one line.

### D-14 Changelog fragment per pull request

- Alternatives: (a) One fragment for the issue. (b) No fragment, because the change is internal.
- Choice: One fragment per pull request. Name it `changelog.d/pr-<number>.md` after the pull request exists. Use one `### Changed` heading and one bullet that names issue 4944.
- Reason: The repository rule names one fragment per user-visible change. Each pull request changes the paths that operators and developers run.
- Risk: None known.

## Remote Verification

Each row is one remote check. The result column uses `present` for a path that exists on main with the stated SHA. It uses `stale` for an issue claim that main no longer matches. The total is 143 rows, and `design/research.md`, `plan.md`, and `META STATUS` use the same rows.

| # | Claim | Path | Blob or tree SHA | Result | Line |
| - | - | - | - | - | - |
| 1 | Debt folder holds 53 children. Issue states 52. | scripts | e773ca4fb588b3b46bb86346ea9f4c9802ee97fe | stale | 0 |
| 2 | Debt folder holds 10 children. Issue states 10. Main held 9 before f03c6c9b. | tests/unit/scripts | f97045862321977f2401dfea353224afa0423c86 | stale | 0 |
| 3 | Debt folder holds 17 children. Issue states 16. | documentation/noc-runbooks | ebef9a186ecf9e618dab5d48f9ddaaabd1bccaa8 | stale | 0 |
| 4 | _diff_pk.py moves to one_time_scans/probes_and_sources/pk_strategy (PR-6). Path string. | scripts/_diff_pk.py | 40ceaebb2c77f9c680561a07deb5841a503ceed3 | present | 20 |
| 5 | _migrate_viewer_wave.py moves to one_time_scans/migrations (PR-6). Usage text. | scripts/_migrate_viewer_wave.py | 8d3b1d8724b67cfb30f416da2cd161c8b0deff2e | present | 3 |
| 6 | analyze_marvis_pcap.py moves to one_time_scans/data_audits (PR-6). Named in RADON_PATHS. | scripts/analyze_marvis_pcap.py | 7ddeb4c537967db241b0b4a2aec4eb2efa341440 | present | 0 |
| 7 | audit_csv.py moves to one_time_scans/data_audits (PR-6). Comment. | scripts/audit_csv.py | cfbafc27b190ab86aeb7aa757f7f0bdd341b58ef | present | 176 |
| 8 | benchmarks folder moves to verification_tools/benchmarks (PR-3). Root depth. | scripts/benchmarks | a5baf14f932ac09659c4eb0d6db10f86a73b730a | present | 18 |
| 9 | bootstrap_worktree.ps1 moves to repository_tools/worktree (PR-4). Usage text. | scripts/bootstrap_worktree.ps1 | 36db3250f4183110584f4bd6d69d1f47ea89aefa | present | 13 |
| 10 | bootstrap_worktree.py moves to repository_tools/worktree (PR-4). Root depth. | scripts/bootstrap_worktree.py | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 52 |
| 11 | build_zen_city_metadata.py moves to one_time_scans/probes_and_sources/external_sources (PR-6). Root depth. | scripts/build_zen_city_metadata.py | 6dbc2aaceedfccf55e74f49a5b0804f262c69e93 | present | 35 |
| 12 | check_device_profiles_orig.py moves to one_time_scans/debug_and_runners/device_checks (PR-6). | scripts/check_device_profiles_orig.py | c97a8dd4b226c0f62e96d6fb4f42f2411ca632ff | present | 0 |
| 13 | check_device_profiles.py moves to one_time_scans/debug_and_runners/device_checks (PR-6). | scripts/check_device_profiles.py | ff88bff0b210682504e47db42cd0193c59c27663 | present | 0 |
| 14 | check_top5_complexity.py moves to repository_tools/guards (PR-4). | scripts/check_top5_complexity.py | 7e13d7f70518c21621535e7732b901ab800af765 | present | 0 |
| 15 | check_vpn_flags.py moves to one_time_scans/data_audits (PR-6). | scripts/check_vpn_flags.py | 2ccd3345f7846babe9093baad3e4eb0293d41660 | present | 0 |
| 16 | compare_test_runs.py moves to repository_tools/ci_support (PR-4). Test import. | scripts/compare_test_runs.py | f0cfe6a90f8938ab11e67572d9e7552898deadfe | present | 0 |
| 17 | compose.ps1 stays at the top level of scripts. | scripts/compose.ps1 | d58a2b1065d53ce9ae971a733e09aec3cbbcc6a5 | present | 0 |
| 18 | crawl_jvd.py moves to one_time_scans/probes_and_sources/external_sources (PR-6). Root depth. | scripts/crawl_jvd.py | 855bd6005bccf8fbecc3576485e7c9aa6491b1f9 | present | 19 |
| 19 | debug_auth.py moves to one_time_scans/debug_and_runners/debug_tools (PR-6). | scripts/debug_auth.py | 9e8fb6392e02f00050773d3c442980aa495b83ef | present | 0 |
| 20 | debug_html.py moves to one_time_scans/debug_and_runners/debug_tools (PR-6). Root depth and data path. | scripts/debug_html.py | 15e2280a6d1d5ef1d3b44bd8214144f6860ac904 | present | 23 |
| 21 | e2e_store_reset.py moves to one_time_scans/debug_and_runners/runners (PR-6). Usage text. | scripts/e2e_store_reset.py | d15e0fc156d53055777c679f616a9d53a62e2d81 | present | 11 |
| 22 | extract_page_strings.py moves to one_time_scans/debug_and_runners/device_checks (PR-6). | scripts/extract_page_strings.py | 6d9ce2e072f5e5b55e8f08385238a840f9671279 | present | 0 |
| 23 | fetch_ssr_docs.py moves to one_time_scans/probes_and_sources/external_sources (PR-6). Runbook commands name it. | scripts/fetch_ssr_docs.py | 8cda26884a8a17b02cf1f7c1c7132a340d1e6283 | present | 0 |
| 24 | filter_orgaudit.py moves to one_time_scans/data_audits (PR-6). | scripts/filter_orgaudit.py | 468f57c082c4e09ae112b874fdb4adea9077666b | present | 0 |
| 25 | generate_api_docs.py moves to reference_tools (PR-5). Root depth. | scripts/generate_api_docs.py | 444df852b47769047e9e38beb266de93951a05d4 | present | 43 |
| 26 | generate_menu_wiki.py moves to reference_tools (PR-5). Root depth and generated text. | scripts/generate_menu_wiki.py | f959225275536743e93bc95d37cb015865a73d53 | present | 61 |
| 27 | generate_portal_menu_registry.py moves to reference_tools (PR-5). Root depth. | scripts/generate_portal_menu_registry.py | 4138c89540abc453c4f6fe420f66ef57ccf5662b | present | 29 |
| 28 | menu_api_map folder moves to reference_tools/menu_api_map (PR-5). Root depth. | scripts/menu_api_map | 02ab424ea291a237000554b4c3f9d2427c3e25a9 | present | 24 |
| 29 | menu_regroup.py moves to one_time_scans/migrations (PR-6). Directory chain. | scripts/menu_regroup.py | c4c9251e5a8ddf6f0a2f10ba744da7754c9c87c0 | present | 265 |
| 30 | migrate_sqlite_to_polyglot.py moves to one_time_scans/migrations (PR-6). Root depth. | scripts/migrate_sqlite_to_polyglot.py | c8e22bc74d0d0fbf87220bbfb3da106e65ff5fc1 | present | 23 |
| 31 | mist_ideas_analyzer_pkg folder moves to one_time_scans/mist_ideas/analysis (PR-6). | scripts/mist_ideas_analyzer_pkg | b1cf11fdf5a945c40183358e2c5705e3a7645625 | present | 0 |
| 32 | mist_ideas_analyzer.py moves to one_time_scans/mist_ideas/analysis (PR-6). Path insert. | scripts/mist_ideas_analyzer.py | 5bdf404d345af79387ff5a173600bcd05671b6be | present | 20 |
| 33 | mist_ideas_distiller_v2_pkg folder moves to one_time_scans/mist_ideas/analysis (PR-6). | scripts/mist_ideas_distiller_v2_pkg | d1d156f511fbc101287ebe9c8586360c0107f07d | present | 0 |
| 34 | mist_ideas_distiller_v2.py moves to one_time_scans/mist_ideas/analysis (PR-6). Path insert. | scripts/mist_ideas_distiller_v2.py | 329fef4f8919979136c8e8efa8f7e551916060f3 | present | 21 |
| 35 | mist_ideas_scraper_auth.py moves to one_time_scans/mist_ideas/scrapers (PR-6). Root depth. | scripts/mist_ideas_scraper_auth.py | 1578b9b1b1441f3cd0e1f6dbe0ae709e5bd767e9 | present | 37 |
| 36 | mist_ideas_scraper_ssr.py moves to one_time_scans/mist_ideas/scrapers (PR-6). Root depth. | scripts/mist_ideas_scraper_ssr.py | 870ae645b5efe6ed80a9aa8c064536a33223fde2 | present | 39 |
| 37 | mist_ideas_scraper_standalone.py moves to one_time_scans/mist_ideas/scrapers (PR-6). Root depth. | scripts/mist_ideas_scraper_standalone.py | eed81fb4049d8bae3c21a09bca31237d87e6ad8c | present | 32 |
| 38 | mist_scraper_receiver.py moves to one_time_scans/mist_ideas/scrapers (PR-6). Data path. | scripts/mist_scraper_receiver.py | d501d918a4fa5437243c5bb4c4c4f0a6630bd3b4 | present | 58 |
| 39 | netcool_runbook_smoke folder moves to verification_tools (PR-3). Runbook default path and root depth. | scripts/netcool_runbook_smoke | b178eed8d5f9d0867cd1a5cc592ee92f891213d4 | present | 230 |
| 40 | observium_discovery.ps1 moves to one_time_scans/debug_and_runners/runners (PR-6). | scripts/observium_discovery.ps1 | 6147020a5c33f8fa7549e0cb43929fb81dbc88c5 | present | 0 |
| 41 | pdf_to_markdown.py moves to one_time_scans/probes_and_sources/external_sources (PR-6). Usage text. | scripts/pdf_to_markdown.py | 558e96a13de42cf5a82e0ab5b6c4d25ff1e2f94a | present | 17 |
| 42 | pk_strategy_suggestions.py moves to one_time_scans/probes_and_sources/pk_strategy (PR-6). | scripts/pk_strategy_suggestions.py | 619e2cd03aca82128ce70a0264a7ec65b61244ca | present | 0 |
| 43 | pr_title_guard folder moves to repository_tools/guards (PR-4). Module import. | scripts/pr_title_guard | 0b4c289dc91f1246c5a8bcc80c47eaa2ec20a921 | present | 3 |
| 44 | probe_pk_strategy.py moves to one_time_scans/probes_and_sources/pk_strategy (PR-6). Root depth. | scripts/probe_pk_strategy.py | 991e56c43e381c2cb655387261b68bb6a6222198 | present | 40 |
| 45 | probe_zscaler_endpoints.py moves to one_time_scans/probes_and_sources/external_sources (PR-6). Root depth. | scripts/probe_zscaler_endpoints.py | 06316499f25f788f9075c85df791fd058bf30d13 | present | 43 |
| 46 | release_body.py moves to repository_tools/ci_support (PR-4). Release workflow calls it. | scripts/release_body.py | 714052b2a0f3f0aa4a59d0f09c9dbefb343fb274 | present | 0 |
| 47 | replace_zone.py moves to one_time_scans/migrations (PR-6). Usage text. | scripts/replace_zone.py | 10e3a35d82c0421077790250b6a292f6f3c7676d | present | 4 |
| 48 | rrm_dry_run_read_guard.py moves to repository_tools/guards (PR-4). Root depth. | scripts/rrm_dry_run_read_guard.py | 512ee100b6ac7d17b23454ce586b8349ce464a6b | present | 172 |
| 49 | run_repository_analyzers.py moves to repository_tools/ci_support (PR-4). | scripts/run_repository_analyzers.py | 08ea5c3ba734e494716336943142528e79f4df8d | present | 0 |
| 50 | run_ssid_phase1.py moves to one_time_scans/debug_and_runners/runners (PR-6). | scripts/run_ssid_phase1.py | 86f08b781bd762f8983f44e0f6ba5f2100df167f | present | 0 |
| 51 | scan_2753.py moves to one_time_scans/data_audits (PR-6). Root depth. Test import. | scripts/scan_2753.py | cb9eff89c7255419d1c563ba54312e6bada1c5f7 | present | 13 |
| 52 | scrape_mist_ideas_test.py moves to verification_tools/source_checks (PR-3). | scripts/scrape_mist_ideas_test.py | 934c26d9911910772e293e3cdfea6599a5798e53 | present | 0 |
| 53 | test_ssr.py moves to verification_tools/source_checks (PR-3). Test policy names it. | scripts/test_ssr.py | 6aa8b451a550d7179d350a9c05012e787a325008 | present | 27 |
| 54 | test_stop_signal.py moves to verification_tools (PR-3). Usage text. | scripts/test_stop_signal.py | 9cbfdaef109457fa72b58e9c425b58d959400b23 | present | 7 |
| 55 | verify_ssr_commands.py moves to verification_tools/source_checks (PR-3). Runbook path. Test import. | scripts/verify_ssr_commands.py | d6d4041fcc7f7e0f0adc677a11debfadbbb305e0 | present | 67 |
| 56 | wave1 folder moves to verification_tools/wave1 (PR-3). Root depth. | scripts/wave1 | b9305416d6e20b2bb37ea0ad81ddf04de072350d | present | 31 |
| 57 | Test folder moves to tests/unit/scripts/verification_tools (PR-3). Runbook path. | tests/unit/scripts/netcool_runbook_smoke | dc2187f65cd957dfed16e29d5f9204c016ebfc22 | present | 27 |
| 58 | test_bootstrap_worktree_uv.py moves to tests/unit/scripts/repository_tools/worktree (PR-4). Import. | tests/unit/scripts/test_bootstrap_worktree_uv.py | 568a790c7491684a486010c5bc46c53623f1342f | present | 23 |
| 59 | test_browser_download_certificates.py moves to repository_tools/worktree (PR-4). Imports and patch targets. | tests/unit/scripts/test_browser_download_certificates.py | f1a2f7e16034872f9a01eee4816dff3f4e2ee500 | present | 21 |
| 60 | test_browser_driver_bootstrap.py moves to repository_tools/worktree (PR-4). Imports and patch targets. | tests/unit/scripts/test_browser_driver_bootstrap.py | b6710a724f0283b3f7a38cbd0e340a771188d851 | present | 19 |
| 61 | test_compare_test_runs.py moves to repository_tools/ci_support (PR-4). Import. | tests/unit/scripts/test_compare_test_runs.py | cf4282d00835b1c55e7f1f2e54bf716c78d22f2f | present | 9 |
| 62 | test_menu_api_map.py moves to tests/unit/scripts/reference_tools (PR-5). Imports and text. | tests/unit/scripts/test_menu_api_map.py | be8d0487974b4a18b33f3045df9a4840696a5b8c | present | 24 |
| 63 | test_pr_title_guard.py moves to repository_tools/guards (PR-4). Import and module argument. | tests/unit/scripts/test_pr_title_guard.py | 98aaae908ef46575f83dd5ec63aa3b764caf0636 | present | 15 |
| 64 | test_script_imports.py stays at the top level. PR-3 to PR-6 add path-depth cases here. | tests/unit/scripts/test_script_imports.py | df2c2a7f978cc54d6719ebdf73cf8efe0ff5139d | present | 53 |
| 65 | test_stale_source_sweep.py moves to repository_tools/worktree (PR-4). Import. | tests/unit/scripts/test_stale_source_sweep.py | 9c2ed4cb3177e200c8b2f85680501908109690f0 | present | 21 |
| 66 | test_verify_ssr_commands.py moves to tests/unit/scripts/verification_tools/source_checks (PR-3). Import. | tests/unit/scripts/test_verify_ssr_commands.py | 08843e3c358c8da874b7ae76f0bf50996528b7e6 | present | 7 |
| 67 | _shared_common.md moves to integration (PR-2). Fetch command text. | documentation/noc-runbooks/_shared_common.md | 1b2d4f584bc4a217418926cfecc02dc8a1ffcc45 | present | 116 |
| 68 | AP_WARNING_REPORT_MENU_307.md moves to integration (PR-2). | documentation/noc-runbooks/AP_WARNING_REPORT_MENU_307.md | f66f542fbfe09deb7d1271518332924404a1fa63 | present | 0 |
| 69 | GATEWAY_DOWN.md moves to gateway (PR-2). | documentation/noc-runbooks/GATEWAY_DOWN.md | 451a771d2755516e59d6f7bdc169dce9cf7fc52d | present | 0 |
| 70 | GW_BGP_NEIGHBOR_DOWN.md moves to gateway (PR-2). | documentation/noc-runbooks/GW_BGP_NEIGHBOR_DOWN.md | e576f1c41d38d1360c6ea839ef46b0b9b6ed47d0 | present | 0 |
| 71 | GW_PORT_DOWN.md moves to gateway (PR-2). | documentation/noc-runbooks/GW_PORT_DOWN.md | df79e601daa3bffbff40a715a13c95bc6a6b8ef7 | present | 0 |
| 72 | GW_VPN_PATH_DOWN.md moves to gateway (PR-2). | documentation/noc-runbooks/GW_VPN_PATH_DOWN.md | d63d995080c0f5526c5e6b8a1f48c6d5e7fc011c | present | 0 |
| 73 | GW_VPN_PEER_DOWN.md moves to gateway (PR-2). | documentation/noc-runbooks/GW_VPN_PEER_DOWN.md | 7a2f0079363ca1969b261c0414b90dc6763adfa2 | present | 0 |
| 74 | MIST_NETCOOL_ALARM_INTEGRATION.md moves to integration (PR-2). Module path lines (PR-3). | documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md | f53313e142d735290a15f821962782e4c80dc9ef | present | 1982 |
| 75 | NODE_DOWN.md moves to integration (PR-2). | documentation/noc-runbooks/NODE_DOWN.md | 524a133e61cc26d012df0a41e93f70da73c72b42 | present | 0 |
| 76 | SSR_ALARM_INDEX.md stays as the index. Fetch command text. | documentation/noc-runbooks/SSR_ALARM_INDEX.md | df77ec9364561763f7200f2fac819211d05138e8 | present | 167 |
| 77 | SSR_APPLICATION_PERFORMANCE.md moves to ssr (PR-2). Fetch command text. | documentation/noc-runbooks/SSR_APPLICATION_PERFORMANCE.md | 57937af2bb22f79e43e77f5f52a0fa8c445ab848 | present | 183 |
| 78 | SSR_CONSOLE_HEALTH_CHECK.md moves to ssr (PR-2). Fetch and PDF command text. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 328 |
| 79 | SSR_EVIDENCE_CAPTURE.md moves to ssr (PR-2). Fetch command text. | documentation/noc-runbooks/SSR_EVIDENCE_CAPTURE.md | 3be1f557a400a3a16d5022cbb6418896a6de1036 | present | 242 |
| 80 | SSR_FIRMWARE_HEALTH.md moves to ssr (PR-2). Fetch command text. | documentation/noc-runbooks/SSR_FIRMWARE_HEALTH.md | 710430e7b2b9df26cf3192d620f6431f5f950a39 | present | 140 |
| 81 | SW_ALARM_CHASSIS_MGMT_LINK_DOWN.md moves to switch (PR-2). | documentation/noc-runbooks/SW_ALARM_CHASSIS_MGMT_LINK_DOWN.md | d9bf382ced9c3d75dda78ed0f662fa28ac1b3bb2 | present | 0 |
| 82 | SW_CRITICAL_PORT_DOWN.md moves to switch (PR-2). | documentation/noc-runbooks/SW_CRITICAL_PORT_DOWN.md | 10db7849ad69cb610d46aa140b93a3428bbfa6bc | present | 0 |
| 83 | SW_VC_PORT_DOWN.md moves to switch (PR-2). | documentation/noc-runbooks/SW_VC_PORT_DOWN.md | 0fc77eb9a5593eb2ac847a5c2b58b541e248f7b3 | present | 0 |
| 84 | CI names the MYPY and RADON paths, a comment, and the menu commands (PR-5, PR-6). | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 85 | Title workflow runs the title guard module (PR-4). | .github/workflows/pull-request-title.yml | 6b161b5a7dd71a0f0c9c0f38b750a7322ae8704e | present | 27 |
| 86 | Release workflow runs the release body module (PR-4). | .github/workflows/release.yml | e81c05798c7609344d2d59b94114d7d9f76263be | present | 144 |
| 87 | Agent instructions name the bootstrap and menu commands (PR-4, PR-5). | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 29 |
| 88 | Ignore file comments name the fetch and PDF scripts (PR-6). | .gitignore | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 24 |
| 89 | Pyproject comments and mypy module names (PR-6). | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 143 |
| 90 | Compose comment names the Mist Ideas tools (PR-6). | compose.yml | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 45 |
| 91 | Development setup names the bootstrap commands (PR-4). | documentation/development-setup.md | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 32 |
| 92 | Quality gates name the menu drift command (PR-5) and the bootstrap path (PR-4). | documentation/quality-gates.md | 6776d334cca5d9b43273473a06da367a65605c6d | present | 67 |
| 93 | Architecture names the menu API folder (PR-5) and the scripts row (PR-6). | documentation/architecture.md | b4cab54be36d223b7eba879ca99b838f508938ce | present | 166 |
| 94 | Menu API README is generated and names the command (PR-5). | documentation/menu-api/README.md | e2d5dfb117f4e60c7b4c888c5dd5222b14f1be45 | present | 1 |
| 95 | Menu API continuous-loop page is generated (PR-5). | documentation/menu-api/continuous-loop.md | 08b7ecb60c0e25ade4b415cb3336ef1c988bd803 | present | 1 |
| 96 | Menu API destructive page is generated (PR-5). | documentation/menu-api/destructive.md | 643ff157e818944a0e4d7fbd208b282c4a1c0113 | present | 1 |
| 97 | Menu API interactive-safe page is generated (PR-5). | documentation/menu-api/interactive-safe.md | 57b580ddc1c4b9fe4971c72fb26a592764e7ac53 | present | 1 |
| 98 | Menu API interactive page is generated (PR-5). | documentation/menu-api/interactive.md | ec5402f333e691cb9a490177932603df1b38bc7d | present | 1 |
| 99 | Menu API resource-intensive page is generated (PR-5). | documentation/menu-api/resource-intensive.md | dd1ec5195bab0c92c673007942a16774aed4104f | present | 1 |
| 100 | Menu API safe page is generated (PR-5). | documentation/menu-api/safe.md | c4c10e2ed30aeb6617716a6d0a90de7f36ed7ad1 | present | 1 |
| 101 | Menu API websocket page is generated (PR-5). | documentation/menu-api/websocket.md | 7d8601a1fdfa8c307cb0a78e9b967e72e0c79852 | present | 1 |
| 102 | Wiki menu API endpoints page is generated and names the command (PR-5). | documentation/wiki/Menu-API-Endpoints.md | 9c9b33ae1bda8bf91ddad097912f903fce0ceb5d | present | 1 |
| 103 | Wiki continuous-loop page is generated (PR-5). | documentation/wiki/Menu-API-Endpoints-Continuous-Loop.md | 169e4c341e63624f886375ffe29cf112934b2dce | present | 1 |
| 104 | Wiki destructive page is generated (PR-5). | documentation/wiki/Menu-API-Endpoints-Destructive.md | d1d23a9bfada852eb4af62eab341e2f7f9672e40 | present | 1 |
| 105 | Wiki interactive-safe page is generated (PR-5). | documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md | 4a8af3e00177b136124c62e47bb0fb87caebeb96 | present | 1 |
| 106 | Wiki interactive page is generated (PR-5). | documentation/wiki/Menu-API-Endpoints-Interactive.md | 53daac8f6d62b0b15a8d55d871398706480ab7bb | present | 1 |
| 107 | Wiki resource-intensive page is generated (PR-5). | documentation/wiki/Menu-API-Endpoints-Resource-Intensive.md | f3c05b9624d5993fa42c9fba9b2b91a6cc40dc43 | present | 1 |
| 108 | Wiki safe page is generated (PR-5). | documentation/wiki/Menu-API-Endpoints-Safe.md | 0b1fb0a6cb52e47d0aa16950cb40abce24ba41e3 | present | 1 |
| 109 | Wiki websocket page is generated (PR-5). | documentation/wiki/Menu-API-Endpoints-Websocket.md | f31684b8be0c8630f1ac8c954f9223b38013d2ab | present | 1 |
| 110 | Wiki menu reference is generated and names the command (PR-5). | documentation/wiki/Menu-Reference.md | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 3 |
| 111 | Wiki testing page names the compare command (PR-4). | documentation/wiki/Testing.md | 648485e70449ca0c3f8e9d9f676930bb932be3b0 | present | 43 |
| 112 | Menu reference page is generated and names the command (PR-5). | documentation/menu_reference.md | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 3 |
| 113 | Menu highlights names the generator command (PR-5). | documentation/menu-highlights.md | 232c974edd45362ed9398876b63d4790f8c2a605 | present | 6 |
| 114 | API enrichment guide names the API docs generator (PR-5). | documentation/api/ENRICHMENT_GUIDE.md | 56442596847d203e8855d7dac3be8e1b844a96a3 | present | 104 |
| 115 | Zen city metadata docstring names the moved script (PR-6). | src/foundation/support/utils/zen_city_metadata.py | 174a130ba03b8bbe5c5672df6491db9616762bc4 | present | 9 |
| 116 | Zscaler catalogue comment names the moved script (PR-6). | src/foundation/support/utils/zscaler_catalogue.py | 4ca1d97e1e45ab59711f97988938e9c2162be0d6 | present | 37 |
| 117 | Zscaler probe docstring names the moved script (PR-6). | src/foundation/support/utils/zscaler_probe.py | b2ccdbde88089a97f0c3f54013f1f33253dfdf13 | present | 15 |
| 118 | Juniper docs downloader docstring names the moved script (PR-6). | src/mist/intelligence/juniper_docs/acquire/downloader.py | cb3242a24988f39e317d490eaa4bd70444740471 | present | 3 |
| 119 | Juniper docs PDF resolver docstring names the moved script (PR-6). | src/mist/intelligence/juniper_docs/acquire/pdf_resolver.py | c87fbcfd779f968c8a4e9f2ff59adf65e9c7fd31 | present | 3 |
| 120 | RRM policy docstring names the guard module (PR-4). | src/mist/resources/site/rrm_reset/dry_run_policy.py | 4ef590483160e50c95c211946a008627b5d7615b | present | 20 |
| 121 | Web portal menu registry docstring is generated (PR-5). | web_portal/menu_registry.py | ad7b102a62949be55e553b71fc4f24b8b261cc65 | present | 8 |
| 122 | Shared test configuration holds the bootstrap command constant (PR-4). | tests/conftest.py | f55885cafab8f4c346ee7d7a813835bab300e45d | present | 48 |
| 123 | Compose bootstrap provider test imports and patches the bootstrap module (PR-4). | tests/contract/packaging/test_bootstrap_compose_provider.py | 7a9e1e3f96062006fd4c7a49c6eb763d5c48fdaf | present | 21 |
| 124 | Release body workflow test names the module (PR-4). | tests/contract/test_release_body_workflow.py | 1cc8f57837685ff5a4de8ce8baffa9a8213a4ad0 | present | 131 |
| 125 | Upgrade portal e2e conftest holds a bootstrap message (PR-4). | tests/e2e/upgrade_portal/conftest.py | d14fda9f0a4cf69dc3c1ec60efa5adb863b73840 | present | 555 |
| 126 | Map race journey test holds a bootstrap message (PR-4). | tests/e2e/web_portal/test_map_site_selection_race_journey.py | 51b658421cc74ee53a1c28ce1ca0e11b0d2a9e96 | present | 42 |
| 127 | CSV device ID guard test imports the scan module (PR-6). | tests/guardrails/test_issue_2753_csv_device_id_scan.py | ccdd01e96f472f2171dff1b347498b6117e0e3b0 | present | 9 |
| 128 | Markdown link guard docstring names the API docs generator (PR-5). | tests/guardrails/test_markdown_links.py | cafefdac69006ddf7544e5a57a101f0f63fbcc38 | present | 93 |
| 129 | Move module guard expects the menu commands and CI lines (PR-5). | tests/guardrails/test_move_module_guidance.py | ae163b792b330285dba7a8c32cc957a78c3838d4 | present | 47 |
| 130 | Mypy paths guard expects the Mist Ideas package paths (PR-6). | tests/guardrails/test_mypy_paths_openai_scripts.py | e3cb489eeef54d4d115da4c782335ace04b62d75 | present | 6 |
| 131 | Portal coverage guard expects the registry generator message (PR-5). | tests/guardrails/test_portal_operation_coverage.py | bb1732f9a4af05ab586d7b3241fd2e86982cf5fb | present | 164 |
| 132 | PR title workflow guard expects the title module command (PR-4). | tests/guardrails/test_pr_title_workflow.py | e44002451d8b50e059b4aa414b0633320af1ce7e | present | 80 |
| 133 | RRM sites guard imports the guard module (PR-4). | tests/guardrails/test_rrm_dry_run_read_sites.py | db50dc30940fcb11be434e1105a63edccb21a45f | present | 7 |
| 134 | Wave1 gate runner test builds the path to the gate runner (PR-3). | tests/guardrails/test_wave1_gate_runner.py | 983c73ded2227eea74d21fb0d7792acbfef0fd41 | present | 3 |
| 135 | Process folder guard file is the host of the child-count guard (PR-1). | tests/guardrails/test_process_folder_structure.py | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| 136 | PDF converter test imports the converter module (PR-6). | tests/test_pdf_to_markdown.py | dad1bfc79f0e015dc6f601a92a8dde7feafe929e | present | 1 |
| 137 | Performance memory test imports the moved benchmark module (PR-3). | tests/test_performance_memory.py | 0c67d73569774252ebfeb239d6df38f47aac8509 | present | 11 |
| 138 | Uv locked sync test imports the bootstrap module (PR-4). | tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py | 678632eec13c5673cbc453210d47a09bacf8b431 | present | 21 |
| 139 | GitHub account checker test patches the bootstrap module (PR-4). | tests/unit/config/foundation/runtime/startup/bootstrap/preflight/test_github_account_checker.py | feda724caff35c4e7313a060248aa43542fa4787 | present | 10 |
| 140 | Capture concurrency benchmark test imports the moved module (PR-3). | tests/unit/config/foundation/support/benchmarks/test_capture_concurrency_benchmark.py | b7ba53646ac4b9471be588a2cf040b243c74db3c | present | 10 |
| 141 | Release body unit test imports the release body module (PR-4). | tests/unit/config/standalone/foundation/runtime/release/test_release_body.py | 4b5b4ae4c3d5161a8007d66d82190a8823bd6ec1 | present | 16 |
| 142 | TLS policy test lists script paths (PR-3 and PR-6). | tests/unit/utils/test_tls_policy.py | 0f241554fa76be3aaf15290ab93539ed00878fbb | present | 27 |
| 143 | Menu API page generator writes the notice and the commands (PR-5). | scripts/menu_api_map/render/pages.py | be8f67ae41c93986360357c8f04a2309b6848a21 | present | 20 |

## Sources

- Local, read in full: `AGENTS.md`. `.github/copilot-instructions.md` (473 lines). `.specify/memory/constitution.md` (462 lines). `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`.
- Local, read in part: `.specify/scripts/powershell/spec-route.ps1` (route formula, lines 1 to 60). `tests/guardrails/test_process_folder_structure.py` (lines 1 to 70). `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` (headings and file list only, as the shape reference).
- Local, located by grep and read at the cited lines: `documentation/quality-gates.md` (67, 263). `documentation/architecture.md` (166). `documentation/development-setup.md` (32, 33, 183, 355). `documentation/operator-guide.md` (420). `documentation/container-deployment.md` (78, 248, 265, 281). These lines name `compose.ps1` only, or name a moved item.
- Local, checked by grep for moved names: `tests/guardrails/process_folder_baseline.json` (no moved name). `tests/conftest.py`. `src/foundation/support/utils/operation_registry.py` and `documentation/ap-warning-report.md` (no `scripts` text, so no change).
- GitHub, read-only: issue 4944 (`gh issue view`). Issue 4934 (CLOSED, `gh issue view`). Pull request list for 4944 (empty). Commit f03c6c9b, which is PR #4941 (`gh api commits`, `git diff --name-status`). The `main` ref (`gh api git/ref/heads/main`). The recursive `main` tree (`gh api git/trees/main?recursive=1`, fetched twice).
- No `web_fetch` call. No skill loaded: no Podman, Juniper device, or Mist API behavior is in scope.
- Mist OpenAPI and mistapi: not read. The change alters no Mist API call, so no Mist claim exists in this record.

## Unverified

- U-1: Runtime behavior of each moved tool. Reason: Rule 2 forbids running scripts in this record. Each pull request runs compile checks and pytest instead.
- U-2: The full list of relative links in the 17 runbooks. Reason: The count needs a full read of 17 long files. PR-2 lists the links with grep before it moves them.
- U-3: Every reference inside a moved file beyond the cited lines. Reason: The path-depth cases and the sweep catch the rest in each pull request.
- U-4: The contents of the local-only folders `ci`, `issues`, `juniper_skills`, and `mermaid`. They exist on disk and do not appear in the main tree. Reason: They are not repository content and are out of scope.
- U-5: The output of `symbol-diff` for renamed files. Reason: The tool was not run in this record. Each pull request records its output. If the tool does not pair the old and new files, the implementer compares the module-level names by hand and records the result.
- U-6: The regenerated page content. Reason: Generation happens in PR-5, after this record.
- U-7: The results of the full `pytest-chunks` shards. Reason: Not run in this record. CI runs the shards.
