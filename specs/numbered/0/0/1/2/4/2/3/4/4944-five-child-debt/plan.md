# Implementation Plan: Remediate the five-child debt of three folders

**Input**: `spec.md` in this folder. Decisions D-1 to D-14 are in `design/research.md`. The remote evidence is in the same file.

## Summary

Move the tracked children of three debt folders into category folders. Ship six pull requests, one move group each. PR-1 adds the guard. Each later pull request moves one group, updates every active reference, lowers its baseline, and adds one changelog fragment. The behavior of every module stays the same.

## Technical Context

- **Language/Version**: Python 3.15 (`pyproject.toml` requires `>=3.15`). PowerShell 7 for the `.ps1` files.
- **Primary Dependencies**: None added. Existing tools: pytest 9.2.0 (`pyproject.toml` line 109), ruff, black, mypy, radon, bandit, pydocstyle, interrogate, ste-linter, and `misthelper-devtools`.
- **Storage**: None. The change adds no data file and moves no data file.
- **Testing**: The guard cases and the path-depth cases. Existing tests of each moved module, updated in the same pull request.
- **Target Platform**: Windows 11, macOS, and Linux.
- **Project Type**: Command-line tool with web portals.
- **Performance Goals**: None. The change alters no runtime path.
- **Constraints**: Code uses `pathlib.Path` or `os.path`. This record uses read-only `gh` and `git` commands. Each pull request uses a squash merge.
- **Scale/Scope**: 80 debt children, 60 reference files, six pull requests, 14 decisions, 24 path-depth cases.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, hierarchy limit | Pass with recorded exception | Each pull request replaces removed children with one category folder, so each debt count falls. `compose.ps1` stays at the top level (D-1). |
| I. No new direct child in a noncompliant parent | Pass | The guard cases and the path-depth cases extend existing files (D-4, D-13). No new file enters `tests/guardrails/`, `tests/unit/scripts/`, or `scripts/`. |
| I. Record touched violations and the remediation action | Pass | Section "Touched debt" lists the violations. Issue 4944 is the remediation action. |
| I. Function limits | Pass | Moved code keeps its functions. New test functions stay under 25 lines. |
| I. Specs record route | Pass | The record uses the numbered route `specs/numbered/0/0/1/2/4/2/3/4`, computed from `spec-route.ps1`. |
| II. Class-based architecture, no wrappers | Pass | No wrapper function is added. No shim is kept at an old path (D-8). |
| III. Safety-first input | Pass | No input handling changes. Moved scripts keep their `safe_input` calls. |
| IV. Full deployment pipeline | Pass with steps | Each pull request runs T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. PR-6 changes `src/` docstrings, so Principle IV steps 10 to 12 apply after its merge. |
| V. ASCII log output | Pass | The guard prints ASCII only. Moved modules keep their logs. |
| VI. Inline comments | Pass with requirement | Each changed code line in the path-depth edits and the new test cases carries an inline comment. |
| VII. Action logging | Pass | The guard and the test cases add no runtime action. Moved modules keep their logging. |
| Mist Cloud REST through mistapi | Not applicable | No Mist request changes. |
| Package manager | Pass | No dependency or requirements file changes. |
| Container runtime and test containers | Not applicable | No container command changes. Documents keep `scripts\compose.ps1`. |
| File paths | Pass with requirement | Path edits use `pathlib.Path` or `os.path`. No new separator literal is added. |
| Output backends, operational store, database keys | Not applicable | No export, store, or key change. |
| Data directory | Pass with check | `debug_html.py` and `mist_scraper_receiver.py` keep writes under `data/`. Their root depth changes (path-depth rows 23 and 24). |
| Container security and Zscaler | Not applicable | No change. |
| Security findings, fix over suppress | Pass | No suppression comment is added. |
| Documentation | Pass | Each pull request updates its documents and regenerates its generated pages. |
| Release notes | Pass | Each pull request adds one changelog fragment (D-14). |
| Complexity-driven SpecKit escalation | Pass | The change touches more than three files and two packages, so this record exists. |
| Multi-agent git workflow | Pass | Issue 4944 exists. Each branch uses the `chore/4944-<slug>` name. Staging uses explicit paths. |

## Touched Debt

| Folder | Main now | Baseline after PR-1 | Final count | Remediation action |
| - | - | - | - | - |
| `scripts/` | 53 | 53 | 5 | Issue 4944 |
| `tests/unit/scripts/` | 10 | 10 | 4 | Issue 4944 |
| `documentation/noc-runbooks/` | 17 | 17 | 5 | Issue 4944 |
| `tests/guardrails/` | 80 or more direct children, noncompliant | Not changed | Not changed | No new child is added (D-4). |

## Pull Request Sequence

| PR | Move group | `scripts/` after | `tests/unit/scripts/` after | `noc-runbooks/` after | Baselines set |
| - | - | - | - | - | - |
| PR-1 | Guard and baseline | 53 | 10 | 17 | 53, 10, 17 |
| PR-2 | Runbooks by platform | 53 | 10 | 5 | 53, 10, 5 |
| PR-3 | `verification_tools/` | 47 | 9 | 5 | 47, 9, 5 |
| PR-4 | `repository_tools/` | 40 | 4 | 5 | 40, 4, 5 |
| PR-5 | `reference_tools/` | 37 | 4 | 5 | 37, 4, 5 |
| PR-6 | `one_time_scans/` | 5 | 4 | 5 | 5, 4, 5 |

The count after PR-3 is 53 minus 7 moved items plus 1 category folder. The count after PR-4 is 47 minus 8 plus 1. The count after PR-5 is 40 minus 4 plus 1. The count after PR-6 is 37 minus 33 plus 1.

## Target Layout After PR-6

```text
documentation/noc-runbooks/
  SSR_ALARM_INDEX.md
  gateway/      GATEWAY_DOWN.md, GW_BGP_NEIGHBOR_DOWN.md, GW_PORT_DOWN.md, GW_VPN_PATH_DOWN.md, GW_VPN_PEER_DOWN.md
  switch/       SW_ALARM_CHASSIS_MGMT_LINK_DOWN.md, SW_CRITICAL_PORT_DOWN.md, SW_VC_PORT_DOWN.md
  ssr/          SSR_APPLICATION_PERFORMANCE.md, SSR_CONSOLE_HEALTH_CHECK.md, SSR_EVIDENCE_CAPTURE.md, SSR_FIRMWARE_HEALTH.md
  integration/  AP_WARNING_REPORT_MENU_307.md, MIST_NETCOOL_ALARM_INTEGRATION.md, NODE_DOWN.md, _shared_common.md

scripts/
  compose.ps1
  reference_tools/       generate_api_docs.py, generate_menu_wiki.py, generate_portal_menu_registry.py, menu_api_map/
  repository_tools/
    ci_support/          compare_test_runs.py, release_body.py, run_repository_analyzers.py
    guards/              check_top5_complexity.py, pr_title_guard/, rrm_dry_run_read_guard.py
    worktree/            bootstrap_worktree.ps1, bootstrap_worktree.py
  verification_tools/
    benchmarks/          five files
    netcool_runbook_smoke/
    source_checks/       scrape_mist_ideas_test.py, test_ssr.py, verify_ssr_commands.py
    test_stop_signal.py
    wave1/               run_wave1_gate.ps1, verify_wave1_scope_boundaries.py
  one_time_scans/
    data_audits/         analyze_marvis_pcap.py, audit_csv.py, check_vpn_flags.py, filter_orgaudit.py, scan_2753.py
    debug_and_runners/
      device_checks/     check_device_profiles.py, check_device_profiles_orig.py, extract_page_strings.py
      debug_tools/       debug_auth.py, debug_html.py
      runners/           e2e_store_reset.py, observium_discovery.ps1, run_ssid_phase1.py
    migrations/          _migrate_viewer_wave.py, menu_regroup.py, migrate_sqlite_to_polyglot.py, replace_zone.py
    mist_ideas/
      analysis/          mist_ideas_analyzer.py, mist_ideas_analyzer_pkg/, mist_ideas_distiller_v2.py, mist_ideas_distiller_v2_pkg/
      scrapers/          mist_ideas_scraper_auth.py, mist_ideas_scraper_ssr.py, mist_ideas_scraper_standalone.py, mist_scraper_receiver.py
    probes_and_sources/
      external_sources/  build_zen_city_metadata.py, crawl_jvd.py, fetch_ssr_docs.py, pdf_to_markdown.py, probe_zscaler_endpoints.py
      pk_strategy/       _diff_pk.py, pk_strategy_suggestions.py, probe_pk_strategy.py

tests/unit/scripts/
  test_script_imports.py
  reference_tools/       test_menu_api_map.py
  repository_tools/
    ci_support/          test_compare_test_runs.py
    guards/              test_pr_title_guard.py
    worktree/            test_bootstrap_worktree_uv.py, test_browser_download_certificates.py, test_browser_driver_bootstrap.py, test_stale_source_sweep.py
  verification_tools/
    netcool_runbook_smoke/  five test files
    source_checks/       test_verify_ssr_commands.py
```

Each folder in the layout holds five children or fewer. The deepest folder holds five files.

## Project Structure (this record)

```text
spec-drafts/4944/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/child-count-guard.md
    checklists/requirements.md
```

## Change Map

Each row names a path in this repository. "Move" changes the path only. "Modify" changes the named lines. "Regenerate" runs the tool and commits its output.

### PR-1: Guard and baseline

| Path | Action | Detail |
| - | - | - |
| `tests/guardrails/test_process_folder_structure.py` | Modify | Add `DEBT_FOLDER_BASELINE` with 53, 10, and 17, and add the guard cases. Add no file. |

### PR-2: Runbooks by platform

| Old path | New path |
| - | - |
| `documentation/noc-runbooks/GATEWAY_DOWN.md` | `documentation/noc-runbooks/gateway/GATEWAY_DOWN.md` |
| `documentation/noc-runbooks/GW_BGP_NEIGHBOR_DOWN.md` | `documentation/noc-runbooks/gateway/GW_BGP_NEIGHBOR_DOWN.md` |
| `documentation/noc-runbooks/GW_PORT_DOWN.md` | `documentation/noc-runbooks/gateway/GW_PORT_DOWN.md` |
| `documentation/noc-runbooks/GW_VPN_PATH_DOWN.md` | `documentation/noc-runbooks/gateway/GW_VPN_PATH_DOWN.md` |
| `documentation/noc-runbooks/GW_VPN_PEER_DOWN.md` | `documentation/noc-runbooks/gateway/GW_VPN_PEER_DOWN.md` |
| `documentation/noc-runbooks/SW_ALARM_CHASSIS_MGMT_LINK_DOWN.md` | `documentation/noc-runbooks/switch/SW_ALARM_CHASSIS_MGMT_LINK_DOWN.md` |
| `documentation/noc-runbooks/SW_CRITICAL_PORT_DOWN.md` | `documentation/noc-runbooks/switch/SW_CRITICAL_PORT_DOWN.md` |
| `documentation/noc-runbooks/SW_VC_PORT_DOWN.md` | `documentation/noc-runbooks/switch/SW_VC_PORT_DOWN.md` |
| `documentation/noc-runbooks/SSR_APPLICATION_PERFORMANCE.md` | `documentation/noc-runbooks/ssr/SSR_APPLICATION_PERFORMANCE.md` |
| `documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md` | `documentation/noc-runbooks/ssr/SSR_CONSOLE_HEALTH_CHECK.md` |
| `documentation/noc-runbooks/SSR_EVIDENCE_CAPTURE.md` | `documentation/noc-runbooks/ssr/SSR_EVIDENCE_CAPTURE.md` |
| `documentation/noc-runbooks/SSR_FIRMWARE_HEALTH.md` | `documentation/noc-runbooks/ssr/SSR_FIRMWARE_HEALTH.md` |
| `documentation/noc-runbooks/AP_WARNING_REPORT_MENU_307.md` | `documentation/noc-runbooks/integration/AP_WARNING_REPORT_MENU_307.md` |
| `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md` | `documentation/noc-runbooks/integration/MIST_NETCOOL_ALARM_INTEGRATION.md` |
| `documentation/noc-runbooks/NODE_DOWN.md` | `documentation/noc-runbooks/integration/NODE_DOWN.md` |
| `documentation/noc-runbooks/_shared_common.md` | `documentation/noc-runbooks/integration/_shared_common.md` |

`documentation/noc-runbooks/SSR_ALARM_INDEX.md` stays at the top level.

| Path | Action | Lines | Detail |
| - | - | - | - |
| `documentation/noc-runbooks/*.md` | Modify | Relative links | Rewrite each link to a moved file. Research U-2 lists the link work. |
| `documentation/noc-runbooks/SSR_ALARM_INDEX.md` | Modify | Index links | Point to the `ssr/` and `gateway/` paths. |
| `scripts/netcool_runbook_smoke/__main__.py` | Modify | 230 | `RUNBOOK_DEFAULT` names the integration path. |
| `scripts/verify_ssr_commands.py` | Modify | 67 | Path names `ssr/SSR_CONSOLE_HEALTH_CHECK.md`. |
| `tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py` | Modify | 27 | `RUNBOOK_FILE` names the integration path. |

### PR-3: `verification_tools/`

| Old path | New path |
| - | - |
| `scripts/benchmarks/` | `scripts/verification_tools/benchmarks/` |
| `scripts/netcool_runbook_smoke/` | `scripts/verification_tools/netcool_runbook_smoke/` |
| `scripts/wave1/` | `scripts/verification_tools/wave1/` |
| `scripts/verify_ssr_commands.py` | `scripts/verification_tools/source_checks/verify_ssr_commands.py` |
| `scripts/test_ssr.py` | `scripts/verification_tools/source_checks/test_ssr.py` |
| `scripts/scrape_mist_ideas_test.py` | `scripts/verification_tools/source_checks/scrape_mist_ideas_test.py` |
| `scripts/test_stop_signal.py` | `scripts/verification_tools/test_stop_signal.py` |
| `tests/unit/scripts/netcool_runbook_smoke/` | `tests/unit/scripts/verification_tools/netcool_runbook_smoke/` |
| `tests/unit/scripts/test_verify_ssr_commands.py` | `tests/unit/scripts/verification_tools/source_checks/test_verify_ssr_commands.py` |

| Path | Action | Lines | Detail |
| - | - | - | - |
| `scripts/netcool_runbook_smoke/__main__.py` | Modify | 25, 32, 33, 36, 40, 43, 48, 106, 583 | Module path, prog name, and root depth 2 to 3. |
| `scripts/netcool_runbook_smoke/checks/__init__.py` | Modify | 22, 23, 24, 25, 33, 628 | Module path and the string at 628. |
| `scripts/netcool_runbook_smoke/checks/catalogs.py` | Modify | 15, 20 | Module path. |
| `scripts/netcool_runbook_smoke/checks/identity.py` | Modify | 16, 22, 28, 29 | Module path. |
| `scripts/netcool_runbook_smoke/checks/scope.py` | Modify | 18, 23 | Module path. |
| `scripts/netcool_runbook_smoke/checks/searches.py` | Modify | 16, 21, 25 | Module path. |
| `scripts/netcool_runbook_smoke/checks/support.py` | Modify | 18 | Module path. |
| `scripts/netcool_runbook_smoke/command.py` | Modify | 20, 26, 63 | Module path and logger package names. |
| `scripts/benchmarks/bench_capture_concurrency.py` | Modify | 18, 100 | Root depth 2 to 3. Label string. |
| `scripts/benchmarks/bench_performance_overhead.py` | Modify | 24, 29 | Root depth 2 to 3. Label string. |
| `scripts/benchmarks/bench_e2e_hook_overhead.py` | Modify | 27 | Root depth 2 to 3. |
| `scripts/benchmarks/bench_flatten_dict.py` | Modify | 17, 18, 30 | Usage text and root depth 2 to 3. |
| `scripts/benchmarks/performance_memory.py` | Modify | 40 | Label string. |
| `scripts/wave1/verify_wave1_scope_boundaries.py` | Modify | 13, 30, 31 | Usage text, comment, and root depth 2 to 3. |
| `scripts/wave1/run_wave1_gate.ps1` | Modify | 7 | Two `Split-Path -Parent` calls become three. |
| `scripts/test_stop_signal.py` | Modify | 7 | Usage path. |
| `tests/test_performance_memory.py` | Modify | 11 | Import path. |
| `tests/unit/config/foundation/support/benchmarks/test_capture_concurrency_benchmark.py` | Modify | 10 | Import path. |
| `tests/unit/utils/test_tls_policy.py` | Modify | 27 | String path to `verification_tools/source_checks/test_ssr.py`. |
| `tests/guardrails/test_wave1_gate_runner.py` | Modify | 3, 18, 19 | Path to `verification_tools/wave1/run_wave1_gate.ps1`. |
| `tests/unit/scripts/verification_tools/netcool_runbook_smoke/*.py` | Modify | Import lines | Module path. Lines are in research rows 57 onward. |
| `tests/unit/scripts/verification_tools/source_checks/test_verify_ssr_commands.py` | Modify | 7 | Import path. |
| `documentation/noc-runbooks/integration/MIST_NETCOOL_ALARM_INTEGRATION.md` | Modify | 1982, 2057 | Module path in command and version lines. |
| `tests/unit/scripts/test_script_imports.py` | Modify | Add | Create the path-depth test with 6 cases (benchmarks 4, netcool 1, wave1 1). |

### PR-4: `repository_tools/`

| Old path | New path |
| - | - |
| `scripts/pr_title_guard/` | `scripts/repository_tools/guards/pr_title_guard/` |
| `scripts/check_top5_complexity.py` | `scripts/repository_tools/guards/check_top5_complexity.py` |
| `scripts/rrm_dry_run_read_guard.py` | `scripts/repository_tools/guards/rrm_dry_run_read_guard.py` |
| `scripts/release_body.py` | `scripts/repository_tools/ci_support/release_body.py` |
| `scripts/run_repository_analyzers.py` | `scripts/repository_tools/ci_support/run_repository_analyzers.py` |
| `scripts/compare_test_runs.py` | `scripts/repository_tools/ci_support/compare_test_runs.py` |
| `scripts/bootstrap_worktree.py` | `scripts/repository_tools/worktree/bootstrap_worktree.py` |
| `scripts/bootstrap_worktree.ps1` | `scripts/repository_tools/worktree/bootstrap_worktree.ps1` |
| `tests/unit/scripts/test_pr_title_guard.py` | `tests/unit/scripts/repository_tools/guards/test_pr_title_guard.py` |
| `tests/unit/scripts/test_compare_test_runs.py` | `tests/unit/scripts/repository_tools/ci_support/test_compare_test_runs.py` |
| `tests/unit/scripts/test_bootstrap_worktree_uv.py` | `tests/unit/scripts/repository_tools/worktree/test_bootstrap_worktree_uv.py` |
| `tests/unit/scripts/test_browser_download_certificates.py` | `tests/unit/scripts/repository_tools/worktree/test_browser_download_certificates.py` |
| `tests/unit/scripts/test_browser_driver_bootstrap.py` | `tests/unit/scripts/repository_tools/worktree/test_browser_driver_bootstrap.py` |
| `tests/unit/scripts/test_stale_source_sweep.py` | `tests/unit/scripts/repository_tools/worktree/test_stale_source_sweep.py` |

`bootstrap_worktree.ps1` finds its Python sibling with `Join-Path $scriptDir` (line 42). Both files move together, so that lookup holds.

| Path | Action | Lines | Detail |
| - | - | - | - |
| `.github/workflows/pull-request-title.yml` | Modify | 27 | `python -m scripts.repository_tools.guards.pr_title_guard`. |
| `.github/workflows/release.yml` | Modify | 144 | `python -m scripts.repository_tools.ci_support.release_body`. |
| `.github/copilot-instructions.md` | Modify | 29, 543 | Bootstrap command path. |
| `documentation/development-setup.md` | Modify | 32, 33, 183, 355 | Bootstrap command and `.ps1` path. |
| `documentation/quality-gates.md` | Modify | 263 | Bootstrap path. |
| `documentation/wiki/Testing.md` | Modify | 43 | `compare_test_runs.py` path. |
| `tests/conftest.py` | Modify | 48 | `_BOOTSTRAP_COMMAND` text. |
| `tests/e2e/upgrade_portal/conftest.py` | Modify | 555 | Message text. |
| `tests/e2e/web_portal/test_map_site_selection_race_journey.py` | Modify | 42 | Message text. |
| `tests/contract/packaging/test_bootstrap_compose_provider.py` | Modify | 21, 89 to 95 | Module path and patch targets. |
| `tests/contract/test_release_body_workflow.py` | Modify | 131, 189 | Module path strings. |
| `tests/unit/config/standalone/foundation/runtime/release/test_release_body.py` | Modify | 16, 422 | Import and module argument. |
| `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` | Modify | 21 | Import path. |
| `tests/unit/config/foundation/runtime/startup/bootstrap/preflight/test_github_account_checker.py` | Modify | 10, 20, 22, 44, 46 | Import and patch targets. |
| `tests/guardrails/test_pr_title_workflow.py` | Modify | 80, 126, 227 | Module path in workflow expectations. |
| `tests/guardrails/test_rrm_dry_run_read_sites.py` | Modify | 7 | Import path. |
| `src/mist/resources/site/rrm_reset/dry_run_policy.py` | Modify | 20 | Docstring path. |
| `scripts/repository_tools/worktree/bootstrap_worktree.py` | Modify | 52 | Root depth 1 to 3. |
| `scripts/repository_tools/guards/rrm_dry_run_read_guard.py` | Modify | 172 | Root depth 1 to 3. |
| `scripts/repository_tools/guards/pr_title_guard/__main__.py` | Modify | 3 | Import path. |
| Moved test modules in this group | Modify | Import and patch lines | Research rows 58 to 66 list the lines. |
| `tests/unit/scripts/test_script_imports.py` | Modify | Add | Add 2 path-depth cases. |

### PR-5: `reference_tools/`

| Old path | New path |
| - | - |
| `scripts/generate_api_docs.py` | `scripts/reference_tools/generate_api_docs.py` |
| `scripts/generate_menu_wiki.py` | `scripts/reference_tools/generate_menu_wiki.py` |
| `scripts/generate_portal_menu_registry.py` | `scripts/reference_tools/generate_portal_menu_registry.py` |
| `scripts/menu_api_map/` | `scripts/reference_tools/menu_api_map/` |
| `tests/unit/scripts/test_menu_api_map.py` | `tests/unit/scripts/reference_tools/test_menu_api_map.py` |

| Path | Action | Lines | Detail |
| - | - | - | - |
| `.github/workflows/ci.yml` | Modify | 718, 724, 732 | Generator and check commands and the message at 724. |
| `tests/guardrails/test_move_module_guidance.py` | Modify | 47, 211, 212 | Expected commands must match the CI lines. |
| `tests/guardrails/test_portal_operation_coverage.py` | Modify | 164, 172 | Message text. |
| `tests/guardrails/test_markdown_links.py` | Modify | 93 | Docstring path. |
| `.github/copilot-instructions.md` | Modify | 72, 243, 272, 585 | Menu commands. |
| `documentation/quality-gates.md` | Modify | 67 | Menu drift command. |
| `documentation/architecture.md` | Modify | 166 | Menu API folder path. |
| `documentation/menu-highlights.md` | Modify | 6 | Generator command. |
| `documentation/api/ENRICHMENT_GUIDE.md` | Modify | 104 | Generator command. |
| `documentation/menu_reference.md` | Regenerate | 3 | `generate_menu_wiki.py` output. |
| `documentation/wiki/Menu-Reference.md` | Regenerate | 3 | `generate_menu_wiki.py` output. |
| `documentation/menu-api/*.md` (8 files) | Regenerate | 1 (README also 14, 17) | `menu_api_map` output. |
| `documentation/wiki/Menu-API-Endpoints*.md` (8 files) | Regenerate | 1 (main page also 14, 17) | `menu_api_map` output. |
| `web_portal/menu_registry.py` | Regenerate | 8 | Generated docstring. |
| `scripts/reference_tools/menu_api_map/__main__.py` | Modify | 1, 23, 24, 28, 121 | Command text, logger name, and root depth 2 to 3. |
| `scripts/reference_tools/menu_api_map/render/pages.py` | Modify | 20, 199, 202 | Notice and command text. |
| `scripts/reference_tools/menu_api_map/analysis/reference_data.py` | Modify | 28, 30 | Command and file text. |
| `scripts/reference_tools/menu_api_map/README.md` | Modify | 15 to 19, 78, 79 | Command text. |
| `scripts/reference_tools/generate_api_docs.py` | Modify | 16, 43 | Usage text and root depth 2. |
| `scripts/reference_tools/generate_menu_wiki.py` | Modify | 61, 188 | Root depth 2 and generated text. |
| `scripts/reference_tools/generate_portal_menu_registry.py` | Modify | 16, 29, 39 | Usage text and root depth 2. |
| `tests/unit/scripts/reference_tools/test_menu_api_map.py` | Modify | 3, 24 to 35, 43, 50, 341, 565 | Import and text. |
| `tests/unit/scripts/test_script_imports.py` | Modify | Add | Add 4 path-depth cases. |

### PR-6: `one_time_scans/`

| Old path | New path |
| - | - |
| `scripts/_diff_pk.py` | `scripts/one_time_scans/probes_and_sources/pk_strategy/_diff_pk.py` |
| `scripts/pk_strategy_suggestions.py` | `scripts/one_time_scans/probes_and_sources/pk_strategy/pk_strategy_suggestions.py` |
| `scripts/probe_pk_strategy.py` | `scripts/one_time_scans/probes_and_sources/pk_strategy/probe_pk_strategy.py` |
| `scripts/build_zen_city_metadata.py` | `scripts/one_time_scans/probes_and_sources/external_sources/build_zen_city_metadata.py` |
| `scripts/crawl_jvd.py` | `scripts/one_time_scans/probes_and_sources/external_sources/crawl_jvd.py` |
| `scripts/fetch_ssr_docs.py` | `scripts/one_time_scans/probes_and_sources/external_sources/fetch_ssr_docs.py` |
| `scripts/pdf_to_markdown.py` | `scripts/one_time_scans/probes_and_sources/external_sources/pdf_to_markdown.py` |
| `scripts/probe_zscaler_endpoints.py` | `scripts/one_time_scans/probes_and_sources/external_sources/probe_zscaler_endpoints.py` |
| `scripts/mist_ideas_analyzer.py` | `scripts/one_time_scans/mist_ideas/analysis/mist_ideas_analyzer.py` |
| `scripts/mist_ideas_analyzer_pkg/` | `scripts/one_time_scans/mist_ideas/analysis/mist_ideas_analyzer_pkg/` |
| `scripts/mist_ideas_distiller_v2.py` | `scripts/one_time_scans/mist_ideas/analysis/mist_ideas_distiller_v2.py` |
| `scripts/mist_ideas_distiller_v2_pkg/` | `scripts/one_time_scans/mist_ideas/analysis/mist_ideas_distiller_v2_pkg/` |
| `scripts/mist_ideas_scraper_auth.py` | `scripts/one_time_scans/mist_ideas/scrapers/mist_ideas_scraper_auth.py` |
| `scripts/mist_ideas_scraper_ssr.py` | `scripts/one_time_scans/mist_ideas/scrapers/mist_ideas_scraper_ssr.py` |
| `scripts/mist_ideas_scraper_standalone.py` | `scripts/one_time_scans/mist_ideas/scrapers/mist_ideas_scraper_standalone.py` |
| `scripts/mist_scraper_receiver.py` | `scripts/one_time_scans/mist_ideas/scrapers/mist_scraper_receiver.py` |
| `scripts/analyze_marvis_pcap.py` | `scripts/one_time_scans/data_audits/analyze_marvis_pcap.py` |
| `scripts/audit_csv.py` | `scripts/one_time_scans/data_audits/audit_csv.py` |
| `scripts/check_vpn_flags.py` | `scripts/one_time_scans/data_audits/check_vpn_flags.py` |
| `scripts/filter_orgaudit.py` | `scripts/one_time_scans/data_audits/filter_orgaudit.py` |
| `scripts/scan_2753.py` | `scripts/one_time_scans/data_audits/scan_2753.py` |
| `scripts/_migrate_viewer_wave.py` | `scripts/one_time_scans/migrations/_migrate_viewer_wave.py` |
| `scripts/menu_regroup.py` | `scripts/one_time_scans/migrations/menu_regroup.py` |
| `scripts/migrate_sqlite_to_polyglot.py` | `scripts/one_time_scans/migrations/migrate_sqlite_to_polyglot.py` |
| `scripts/replace_zone.py` | `scripts/one_time_scans/migrations/replace_zone.py` |
| `scripts/check_device_profiles.py` | `scripts/one_time_scans/debug_and_runners/device_checks/check_device_profiles.py` |
| `scripts/check_device_profiles_orig.py` | `scripts/one_time_scans/debug_and_runners/device_checks/check_device_profiles_orig.py` |
| `scripts/extract_page_strings.py` | `scripts/one_time_scans/debug_and_runners/device_checks/extract_page_strings.py` |
| `scripts/debug_auth.py` | `scripts/one_time_scans/debug_and_runners/debug_tools/debug_auth.py` |
| `scripts/debug_html.py` | `scripts/one_time_scans/debug_and_runners/debug_tools/debug_html.py` |
| `scripts/e2e_store_reset.py` | `scripts/one_time_scans/debug_and_runners/runners/e2e_store_reset.py` |
| `scripts/run_ssid_phase1.py` | `scripts/one_time_scans/debug_and_runners/runners/run_ssid_phase1.py` |
| `scripts/observium_discovery.ps1` | `scripts/one_time_scans/debug_and_runners/runners/observium_discovery.ps1` |

| Path | Action | Lines | Detail |
| - | - | - | - |
| `.github/workflows/ci.yml` | Modify | 93, 95, 99 | `MYPY_PATHS`, its comment, and `RADON_PATHS` name the new paths. |
| `pyproject.toml` | Modify | 143, 402, 403, 410, 411 | Comments and mypy module names. |
| `tests/guardrails/test_mypy_paths_openai_scripts.py` | Modify | 6, 26, 27 | Expected MYPY paths. |
| `tests/unit/scripts/test_script_imports.py` | Modify | 24, 34, 49, 53, 57, 63, 67, 71 | Module names and messages. |
| `tests/guardrails/test_issue_2753_csv_device_id_scan.py` | Modify | 9 | Import path. |
| `tests/test_pdf_to_markdown.py` | Modify | 1, 19 | Docstring and import path. |
| `tests/unit/utils/test_tls_policy.py` | Modify | 28, 29 | String paths. |
| `compose.yml` | Modify | 45 | Comment about the Mist Ideas tools. |
| `.gitignore` | Modify | 24, 26, 27, 37 | Comments that name `fetch_ssr_docs.py` and `pdf_to_markdown.py`. |
| `documentation/architecture.md` | Modify | 166 | The `scripts/` row names the four category folders. |
| `documentation/noc-runbooks/SSR_ALARM_INDEX.md` | Modify | 167 | Fetch command. |
| `documentation/noc-runbooks/ssr/SSR_APPLICATION_PERFORMANCE.md` | Modify | 183 | Fetch command. |
| `documentation/noc-runbooks/ssr/SSR_CONSOLE_HEALTH_CHECK.md` | Modify | 328, 329 | Fetch and PDF commands. |
| `documentation/noc-runbooks/ssr/SSR_EVIDENCE_CAPTURE.md` | Modify | 242 | Fetch command. |
| `documentation/noc-runbooks/ssr/SSR_FIRMWARE_HEALTH.md` | Modify | 140 | Fetch command. |
| `documentation/noc-runbooks/integration/_shared_common.md` | Modify | 116 | Fetch command. |
| `src/foundation/support/utils/zen_city_metadata.py` | Modify | 9, 15 | Docstring paths. |
| `src/foundation/support/utils/zscaler_catalogue.py` | Modify | 37, 39 | Comment paths. |
| `src/foundation/support/utils/zscaler_probe.py` | Modify | 15, 87 | Docstring paths. |
| `src/mist/intelligence/juniper_docs/acquire/downloader.py` | Modify | 3 | Docstring path. |
| `src/mist/intelligence/juniper_docs/acquire/pdf_resolver.py` | Modify | 3 | Docstring path. |
| Moved modules in this group | Modify | Root expressions and usage text | Table "Path-depth edits" lists them. |
| `tests/unit/scripts/test_script_imports.py` | Modify | Add | Add 12 path-depth cases. |

PR-6 also sets the final baselines to 5, 4, and 5 in `tests/guardrails/test_process_folder_structure.py`.

### Path-depth edits

Each row changes a repository-root expression. The path-depth test checks the expected text in each source file.

| # | File after move | Old expression | New expression | PR |
| - | - | - | - | - |
| 1 | `scripts/reference_tools/generate_api_docs.py` | `Path(__file__).resolve().parent.parent` | `Path(__file__).resolve().parents[2]` | PR-5 |
| 2 | `scripts/reference_tools/generate_menu_wiki.py` | `parents[1]` | `parents[2]` | PR-5 |
| 3 | `scripts/reference_tools/generate_portal_menu_registry.py` | `parents[1]` | `parents[2]` | PR-5 |
| 4 | `scripts/reference_tools/menu_api_map/__main__.py` | `parents[2]` | `parents[3]` | PR-5 |
| 5 | `scripts/repository_tools/worktree/bootstrap_worktree.py` | `parents[1]` | `parents[3]` | PR-4 |
| 6 | `scripts/repository_tools/guards/rrm_dry_run_read_guard.py` | `parents[1]` | `parents[3]` | PR-4 |
| 7 | `scripts/verification_tools/benchmarks/bench_capture_concurrency.py` | `parents[2]` | `parents[3]` | PR-3 |
| 8 | `scripts/verification_tools/benchmarks/bench_performance_overhead.py` | `parents[2]` | `parents[3]` | PR-3 |
| 9 | `scripts/verification_tools/benchmarks/bench_e2e_hook_overhead.py` | `parents[2]` | `parents[3]` | PR-3 |
| 10 | `scripts/verification_tools/benchmarks/bench_flatten_dict.py` | `parents[2]` | `parents[3]` | PR-3 |
| 11 | `scripts/verification_tools/netcool_runbook_smoke/__main__.py` | `parents[2]` | `parents[3]` | PR-3 |
| 12 | `scripts/verification_tools/wave1/verify_wave1_scope_boundaries.py` | `parents[2]` | `parents[3]` | PR-3 |
| 13 | `scripts/one_time_scans/probes_and_sources/pk_strategy/probe_pk_strategy.py` | `parent.parent` | `parents[4]` | PR-6 |
| 14 | `scripts/one_time_scans/probes_and_sources/external_sources/build_zen_city_metadata.py` | `parent.parent` | `parents[4]` | PR-6 |
| 15 | `scripts/one_time_scans/probes_and_sources/external_sources/crawl_jvd.py` | `parent.parent` | `parents[4]` | PR-6 |
| 16 | `scripts/one_time_scans/probes_and_sources/external_sources/probe_zscaler_endpoints.py` | `parent.parent` | `parents[4]` | PR-6 |
| 17 | `scripts/one_time_scans/migrations/migrate_sqlite_to_polyglot.py` | `parent.parent` | `parents[3]` | PR-6 |
| 18 | `scripts/one_time_scans/migrations/menu_regroup.py` | `os.path.dirname(SCRIPT_DIR)` | `os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))` | PR-6 |
| 19 | `scripts/one_time_scans/data_audits/scan_2753.py` | `parents[1]` | `parents[3]` | PR-6 |
| 20 | `scripts/one_time_scans/mist_ideas/scrapers/mist_ideas_scraper_auth.py` | `parent.parent` | `parents[4]` | PR-6 |
| 21 | `scripts/one_time_scans/mist_ideas/scrapers/mist_ideas_scraper_ssr.py` | `parent.parent` | `parents[4]` | PR-6 |
| 22 | `scripts/one_time_scans/mist_ideas/scrapers/mist_ideas_scraper_standalone.py` | `parent.parent` | `parents[4]` | PR-6 |
| 23 | `scripts/one_time_scans/mist_ideas/scrapers/mist_scraper_receiver.py` | `Path(__file__).parent.parent / "data"` | `Path(__file__).resolve().parents[4] / "data"` | PR-6 |
| 24 | `scripts/one_time_scans/debug_and_runners/debug_tools/debug_html.py` | `Path(__file__).resolve().parent.parent / "data"` | `Path(__file__).resolve().parents[4] / "data"` | PR-6 |

Two more edits do not compute a root. `scripts/one_time_scans/probes_and_sources/pk_strategy/_diff_pk.py` (research row 4, line 20) opens a path relative to the working directory, so it names the new path. `scripts/one_time_scans/mist_ideas/analysis/` keeps its `sys.path` insert. The CLI and its package move together, so `Path(__file__).resolve().parent` still finds the package.

Case count: PR-3 adds 6 cases (rows 7 to 12). PR-4 adds 2 cases (rows 5 and 6). PR-5 adds 4 cases (rows 1 to 4). PR-6 adds 12 cases (rows 13 to 24). The total is 24.

### Regenerated outputs

The generator text changes in PR-5. These files change only through their tools, then CI checks them with `--check`:
- `documentation/menu-api/` (8 files) and `documentation/wiki/Menu-API-Endpoints*.md` (8 files) from `menu_api_map`.
- `documentation/menu_reference.md` and `documentation/wiki/Menu-Reference.md` from `generate_menu_wiki.py`.
- `web_portal/menu_registry.py` from `generate_portal_menu_registry.py`.

## Dependencies

- Tools: `gh` for reads and for PR steps. `git` for reads in this record. The implementer uses `git` write commands only in the PR steps. Python 3.15.2 through `uv`. pytest, ruff, black, mypy, radon, bandit, ste-linter, `test-quality-analyzer`, `symbol-diff`, and `pytest-chunks` from `requirements-dev.txt`.
- Packages: none added. No requirements file changes.
- Issues: Issue 4934 is closed. Its feature, merged through PR #4941, added one child to two debt folders. No open issue blocks this work.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A moved module fails to import. | Compile each changed file with `python -m py_compile`. Run the affected tests in the same pull request. |
| A repository-root depth stays wrong. | The path-depth test checks each expression. The sweep greps `parents[` and `parent.parent` in `scripts/` each pull request. |
| A runbook link breaks. | Run `tests/guardrails/test_markdown_links.py` in PR-2. Check the link list from research unverified item U-2. |
| A generated page keeps old text. | Regenerate in PR-5. Run the `--check` command. The drift gate must pass. |
| A CI workflow path breaks. | Watch each run with `gh pr checks <number> --watch` (T-REMOTE-CI). Repair the cause in the same pull request. |
| Operators run an old command. | Each pull request updates the documents. Each changelog fragment names the new path. No alias is added (D-8). |
| Parallel pull requests edit the same lines. | Check open pull requests with `gh pr list --json number,headRefName,files` before each PR. Rebase before the push. |
| Issue 4934 or another pull request adds a child first. | The guard fails. The author rebases and records the new count in the same pull request. |
| A staged local file leaks into a pull request. | Stage by explicit path. Run `git status` before each commit. Do not stage `ci`, `issues`, `juniper_skills`, `mermaid`, or `__pycache__`. |
| Full test shards take about 25 minutes. | Run the shards for each pull request that changes test files, and rely on CI otherwise. Record the choice in the pull request body. |
| A duplicate basename causes a pytest import mismatch. | Main has no duplicate basename for the moved test files. Each pull request repeats the check with `git ls-files` (quickstart step 7). |

## Rollback Steps

1. Revert the pull requests in reverse order, starting with PR-6. Use `git revert <squash-sha>` on a new branch, then open a pull request that uses `Refs #4944`.
2. Each revert restores the old paths and the old baseline in the same commit.
3. Caution: a revert can conflict with a later pull request that edits the same lines. Resolve each conflict before the revert merges.
4. Warning: a force push to `main` removes commits. Never force push to `main` to undo a merge.
