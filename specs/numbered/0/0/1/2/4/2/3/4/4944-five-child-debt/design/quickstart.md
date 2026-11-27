# Quickstart: Remediate the five-child debt of three folders

Use these steps to reproduce the baseline and to verify each pull request. Each code block runs in PowerShell from the repository root unless it names another folder.

## Prerequisites

- A local clone of `jmorrison-juniper/MistHelper` at `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`, on `main` at commit f03c6c9b or later.
- `gh` authenticated with the account in `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`.
- Python 3.15.2 and the project environment. Before PR-4, the bootstrap command is `scripts\bootstrap_worktree.py`. From PR-4, it is `scripts\repository_tools\worktree\bootstrap_worktree.py`.

## Scenario 1: Confirm the remote baseline (read-only)

Set the `gh` environment before each `gh` command. Then count the direct children of the three debt folders on `main`.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$tree = ConvertFrom-Json -InputObject ([string]::Join("`n", (gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1")))
$tree.tree | Where-Object { $_.path -match '^(scripts|tests/unit/scripts|documentation/noc-runbooks)/[^/]+$' } | ForEach-Object { ($_.path -split '/')[0..($_.path.Split('/').Count - 2)] -join '/' } | Group-Object | Select-Object Name, Count
```

Expected: `scripts` 53, `tests/unit/scripts` 10, and `documentation/noc-runbooks` 17 at commit f03c6c9b. After PR-6, the expected values are 5, 4, and 5.

## Scenario 2: Count tracked children locally (read-only)

Each line counts the distinct direct children of one debt folder in the local index.

```powershell
$repo = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
rtk proxy git -C $repo ls-files -- scripts | ForEach-Object { ($_ -split '/')[1] } | Sort-Object -Unique | Measure-Object | Select-Object -ExpandProperty Count
rtk proxy git -C $repo ls-files -- tests/unit/scripts | ForEach-Object { ($_ -split '/')[3] } | Sort-Object -Unique | Measure-Object | Select-Object -ExpandProperty Count
rtk proxy git -C $repo ls-files -- documentation/noc-runbooks | ForEach-Object { ($_ -split '/')[2] } | Sort-Object -Unique | Measure-Object | Select-Object -ExpandProperty Count
```

Expected: 53, 10, and 17 at the start. The local count equals the remote count, because local HEAD equals `origin/main`.

## Scenario 3: Run the guard (from PR-1)

```powershell
python -m pytest tests/guardrails/test_process_folder_structure.py -q -s
```

Expected: three lines that start with `five-child debt:`, one for each folder, and a pass result. The growth case also passes, because it uses a temporary count.

## Scenario 4: Run the path-depth cases (from PR-3)

```powershell
python -m pytest tests/unit/scripts/test_script_imports.py -q
```

Expected: pass results for the path-depth cases. The case count is 6 after PR-3, 8 after PR-4, 12 after PR-5, and 24 after PR-6.

## Scenario 5: Run the old-path sweep (after each PR)

The sweep prints each line that names a moved path. The historical files are excluded. Expected output after PR-6: no line.

```powershell
$repo = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
$oldPattern = 'scripts/(_diff_pk|_migrate_viewer_wave|analyze_marvis_pcap|audit_csv|benchmarks|bootstrap_worktree|build_zen_city_metadata|check_device_profiles|check_top5_complexity|check_vpn_flags|compare_test_runs|crawl_jvd|debug_auth|debug_html|e2e_store_reset|extract_page_strings|fetch_ssr_docs|filter_orgaudit|generate_api_docs|generate_menu_wiki|generate_portal_menu_registry|menu_api_map|menu_regroup|migrate_sqlite_to_polyglot|mist_ideas_|mist_scraper_receiver|netcool_runbook_smoke|observium_discovery|pdf_to_markdown|pk_strategy_suggestions|pr_title_guard|probe_pk_strategy|probe_zscaler_endpoints|release_body|replace_zone|rrm_dry_run_read_guard|run_repository_analyzers|run_ssid_phase1|scan_2753|scrape_mist_ideas_test|test_ssr|test_stop_signal|verify_ssr_commands|wave1)|scripts\.(menu_api_map|pr_title_guard|netcool_runbook_smoke|benchmarks|wave1|mist_ideas_|release_body|bootstrap_worktree|scan_2753|pdf_to_markdown|verify_ssr_commands|compare_test_runs|rrm_dry_run_read_guard|generate_|audit_csv|performance_memory)|noc-runbooks/(GATEWAY_DOWN|GW_|SW_|SSR_APPLICATION|SSR_CONSOLE|SSR_EVIDENCE|SSR_FIRMWARE|AP_WARNING|MIST_NETCOOL|NODE_DOWN|_shared_common)'
rtk proxy git -C $repo grep -n -E -e $oldPattern -- . ':(exclude)specs' ':(exclude)changelog.d' ':(exclude)CHANGELOG.md' ':(exclude)documentation/release-notes.md' ':(exclude)documentation/development-tooling-migration.md' ':(exclude).specify/bugs/menu-93-inventory-output/fix.md'
```

Expected: no output. Git returns exit code 1 when no line matches.

## Scenario 6: Check the generated menu pages (PR-5)

```powershell
python scripts/reference_tools/generate_menu_wiki.py
python -m scripts.reference_tools.menu_api_map --check
rtk proxy git -C $repo status --porcelain -- documentation web_portal
python -m pytest tests/guardrails/test_menu_number_uniqueness.py tests/guardrails/test_operation_registry_menu_coverage.py -q
```

Expected: the generator leaves no changed file. The `--check` command exits 0. The status command prints no line for the generated pages. The two guard files pass, which confirms 308 registered menu operations with unique numbers.

## Scenario 7: Check the moved test basenames (each PR)

```powershell
$movedTests = @('test_bootstrap_worktree_uv.py', 'test_browser_download_certificates.py', 'test_browser_driver_bootstrap.py', 'test_compare_test_runs.py', 'test_menu_api_map.py', 'test_pr_title_guard.py', 'test_stale_source_sweep.py', 'test_verify_ssr_commands.py')
rtk proxy git -C $repo ls-files -- tests | Where-Object { $movedTests -contains (Split-Path -Leaf $_) }
```

Expected: exactly one path for each name. A second path for any name means that the basename is no longer unique. Stop and rename the module before the pull request continues.

## Scenario 8: Compile each changed Python file (each PR)

Run this command for each Python file that the pull request changes. The example names one file.

```powershell
python -m py_compile scripts/reference_tools/generate_menu_wiki.py
```

Expected: no output and exit code 0.

## Scenario 9: Roll back one pull request (implementer only)

```powershell
git -C $repo switch -c revert/4944-<number>
git -C $repo revert --no-edit <squash-sha>
```

Expected: a revert commit on the new branch. Open a pull request with `Refs #4944`. Revert the pull requests in reverse order, starting with PR-6. Never force push to `main`.
