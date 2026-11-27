# Research: API Fetch Failures

## Method

- Issue facts came from `gh issue view` on issue 4762. The issue has 24 comments. Each comment was read.
- Linked pull requests came from `gh pr list --search "4762"`. The list returned pull requests 4767 and 4853. Both are merged.
- One call fetched the `main` tree. Blob SHAs and line numbers came from `gh api` contents and blob reads on `main`. Each cited line was decoded from the remote body.
- Local reads were read-only. The mistapi and misthelper_devtools sources came from `.venv\Lib\site-packages`. The rows that cite them use the ref `local-venv`.
- No build, test, linter, install, container, or repository script ran. No GitHub write happened.
- No skill was loaded. No question in this issue concerns Podman or Juniper device behavior.
- `web_fetch` was not used. Local and remote sources answered every question.

## Decisions

### D-1 Nested error class

- Decision: define `APICoreFetchUtils.APIFetchError(RuntimeError)` inside the class body.
- Alternatives: (a) a module-level class in the same file, (b) a class in a new module, (c) a `None` return on failure.
- Rationale: the comparator counts module-level imports and definitions (rows R102, R103, and R105). A module-level class or import fails the Symbols gate. A `RuntimeError` base keeps the existing `except RuntimeError` fallbacks (rows R31 and R46).
- Risk: callers must reference the nested name. The name is longer but explicit.

### D-2 Paging with `get_next`

- Decision: walk later pages with `mistapi.get_next` and check every page.
- Alternatives: (a) keep `mistapi.get_all` and check only the first page, (b) send HTTP requests with `requests`.
- Rationale: `get_all` reads no later status (row R95). It stops without an error (row R96). `get_next` is the SDK page step (row R94). The constitution forbids direct HTTP (row R121).
- Risk: the helper repeats the shape handling of `get_all`. Tests U-3 and U-9 cover both shapes.

### D-3 Status rule

- Decision: fail on each page whose status is missing or outside 200 to 299.
- Alternatives: (a) fail at 400 and above only, as `APIResponse` does (row R100), (b) accept a missing status.
- Rationale: the SDK sets no status after a connection or proxy failure (row R99). A missing status treated as success returns an empty list again.
- Risk: a 3xx response raises. The OpenAPI operations list error codes and the success code 200 only (rows R85 and R89).

### D-4 Payload rule

- Decision: fail on a 2xx payload that is neither a list nor a dict with a `results` list. Return an empty list for a 2xx read with no items.
- Alternatives: (a) treat an unknown payload as empty, (b) treat an empty list as a failure.
- Rationale: an unknown 2xx payload is the same defect class (rows R95 and R97). An empty list is the normal answer for an organization with no items.
- Risk: an unexpected valid payload raises. The error names the cause, so the operator can report it.

### D-5 Scope

- Decision: change the two helpers and the optional lookups in the contract. Track the other direct readers in a follow-up issue.
- Alternatives: (a) repair every `mistapi.get_all` reader in this change, (b) change the helpers and leave every caller unchanged.
- Rationale: AGENTS requires one concern for each issue. The direct readers (rows R29 and R39) span more files. Option (b) lets optional lookups stop reports that produced data before (issue comments 8 and 12).
- Risk: the direct readers keep the empty-result defect until the follow-up issue lands.

### D-6 Required reads propagate

- Decision: do not catch `APIFetchError` in a required read.
- Alternatives: (a) catch the error, print a message, and return an empty result, (b) return `None` on the error.
- Rationale: an empty return repeats the defect. The menu dispatcher already logs an unexpected exception and applies the policy in D-13 (rows R59 to R61). The existing org AP upgrader handler reports a site read error and returns `None` (rows R43 and R44).
- Risk: direct-mode sessions end on the error (D-13).

### D-7 Optional lookups

- Decision: catch only `APIFetchError` in each optional lookup. Log one warning, keep the empty lookup, and continue.
- Alternatives: (a) catch `Exception`, (b) propagate the error, (c) remove the lookup from the output.
- Rationale: a broad catch hides unrelated defects. Propagation stops reports that produced data before (issue comments 8 and 12). Removing the lookup changes output columns, which is out of scope.
- Risk: the output shows fallback site names. One warning names the cause.

### D-8 Class reference

- Decision: a module that calls `APICoreFetchUtils` by bare name (rows R20 and R10) uses that name in its `except` clause. Other modules use `mh.APICoreFetchUtils.APIFetchError`.
- Alternatives: (a) add a module-level import to each module, (b) add a wrapper function around each call.
- Rationale: a new module-level import adds a name and fails the Symbols gate (row R102). A wrapper function breaks the class rule (row R115).
- Risk: a test that replaces `APICoreFetchUtils` with a non-class object raises a `TypeError` only when a read raises. Unverified item U-10 records the search-only review of the affected tests.

### D-9 MSP broad catch

- Decision: keep `except Exception`. Raise the log level to warning.
- Alternatives: (a) narrow the catch to `APIFetchError`, (b) keep debug level.
- Rationale: narrowing turns an unrelated error into an exception that reaches the caller. Debug level hides the failure from the operator (row R28).
- Risk: the broad catch still hides unrelated errors at warning level. The warning includes the error text.

### D-10 Test placement

- Decision: `tests/integration/export/test_api_fetch_enrichment.py`.
- Alternatives: (a) the reserved path `tests/integration/test_api_fetch_enrichment.py`, (b) a new folder directly under `tests/integration/`.
- Rationale: `tests/integration/` holds 26 children on `main` (row R125). A new direct child breaks the five-item rule (row R114). `tests/integration/export/` holds 2 children on `main` (row R126). One more child stays within the limit.
- Risk: the owner comment names the other path. No other owner holds the new path (A-004).

### D-11 Owned test

- Decision: leave `tests/unit/export/test_site_device_exporter.py` unchanged.
- Alternatives: add the site-device regression to that file.
- Rationale: session 79a9bb52 owns the file (issue comment 9). The integration module covers the same path.
- Risk: the owned tests run in T-LOCAL-GATES. A failure needs the owner review.

### D-12 Release note name

- Decision: `changelog.d/issue-4762-api-fetch-failures.md`.
- Alternatives: (a) `pr-<number>.md` before a pull request exists, (b) a date-based name.
- Rationale: the issue exists and no pull request exists. Row R122 states the naming rule. The first name stays after the pull request opens.
- Risk: none.

### D-13 Dispatcher policy

- Decision: keep the menu dispatcher unchanged. Direct mode exits with code 1 after a required read fails. Container mode returns to the menu.
- Alternatives: (a) print a message and return to the menu in every mode, (b) catch `APIFetchError` in each required caller.
- Rationale: the dispatcher already logs unexpected menu exceptions and applies this policy (rows R59 to R61). A dispatcher change edits a shared entry file. Option (b) adds catches to about ten call sites.
- Risk: direct-mode operators lose the session after an API error. Unresolved item U-B in `analysis.md` records the owner review.

## Caller Inventory

The full checklist is in `design/checklists/callers.md`. Each caller has one class.

| Caller | Location | Class | Behavior after the change | Rows |
| - | - | - | - | - |
| `SiteNameLookup.fetch` | `src/mist/intelligence/reports/switch_scorecard/site_lookup.py` line 23 | Optional | Catch, warn, empty lookup | R10 |
| WAN scorecard | `src/mist/intelligence/reports/wan_edge_scorecard/scorecard.py` line 85 | Optional | Warning from the lookup | R11 |
| Switch scorecard | `src/mist/intelligence/reports/switch_scorecard/operation.py` line 41 | Optional | Warning from the lookup | R12 |
| AP scorecard | `src/mist/intelligence/reports/ap_scorecard/operation.py` line 49 | Optional | Warning from the lookup | R13 |
| Offline device report | `src/mist/intelligence/reports/offline_device_reporter.py` line 107 | Optional | Catch, warn, `Unknown Site` fallback | R14, R15 |
| Site device statistics name | `src/operations/exporting/export/site_device_exporter.py` line 141 | Optional | Catch, warn, site ID as name | R16, R17 |
| AP model export sites | `src/operations/exporting/export/sites_by_ap_model_exporter.py` line 173 | Optional | Catch, warn, empty site map | R18, R19 |
| AP model inventory | `src/operations/exporting/export/sites_by_ap_model_exporter.py` line 36 | Required | Propagate | R33 |
| Devices site lookup | `src/operations/exporting/export/org_inventory_exporter.py` lines 509, 530, and 557 | Optional | Catch inside `_build_site_lookup_from_api` | R21, R22, R23 |
| Devices inventory | `src/operations/exporting/export/org_inventory_exporter.py` lines 544 and 558 | Required | Propagate | R34, R35 |
| Gateways site lookup | `src/operations/exporting/export/org_inventory_exporter.py` line 688 | Optional | Through `_build_site_lookup_from_api` | R24 |
| Gateways inventory | `src/operations/exporting/export/org_inventory_exporter.py` line 692 | Required | Propagate | R36 |
| MSP site lookup | `src/operations/exporting/export/msp_inventory_exporter.py` line 358 | Optional | Broad catch kept, warning level | R27, R28 |
| MSP organization inventory | `src/operations/exporting/export/msp_inventory_exporter.py` line 275 | Direct reader, out of scope | Unchanged | R29 |
| Prompt site cache | `src/interfaces/visualization/ui/prompt_utils.py` line 394 | Optional | `RuntimeError` fallback unchanged | R30, R31 |
| Prompt client | `src/foundation/runtime/input/prompt_client_utils.py` line 229 | Optional through the prompt cache | Unchanged | R32 |
| Gateway export inventory | `src/mist/resources/gateway/gateway_export_utils.py` lines 561 and 572 | Required | Propagate | R37, R38 |
| Gateway export sites | `src/mist/resources/gateway/gateway_export_utils.py` line 282 | Direct reader, out of scope | Unchanged | R39 |
| Firmware site seam | `src/operations/execution/firmware/firmware_manager.py` line 1901 | Required, consumer inferred (U-5) | Existing handlers unchanged | R40 |
| Firmware site lookup | `src/operations/execution/firmware/firmware_manager.py` line 3542 | Optional | Existing warning | R41 |
| Bulk upgrader sites | `src/operations/execution/firmware/bulk_ap_upgrader.py` line 313 | Required | Propagate to the menu | R42 |
| Org AP upgrader sites | `src/operations/execution/firmware/org_ap_upgrader.py` line 1016 | Required | Existing handler at line 1023 | R43, R44 |
| Site auto upgrade sites | `src/operations/execution/firmware/site_auto_upgrade.py` line 333 | Required | Existing `RuntimeError` handler at line 340 | R45, R46 |
| Organization site export | `src/operations/exporting/export/org_site_exporter.py` lines 90 and 115 | Required | Propagate | R47, R48 |
| Zone analysis wiring | `src/operations/exporting/export/site_export_utils.py` line 553 | Required | Propagate | R49 |
| Zone analyzer | `src/mist/intelligence/analytics/site/zone_analyzer.py` line 561 | Required | Propagate | R50 |
| Zone script | `scripts/replace_zone.py` line 30 | Required | Propagate | R51 |
| Zone menu wiring | `MistHelper.py` line 5771 | Required | Propagate | R64 |
| Site settings | `src/mist/access/api/api_fetch_utils.py` line 154 | Required | Propagate | R52 |
| Site settings export | `src/operations/exporting/export/site_config_exporter.py` line 168 | Required | Propagate | R53 |
| SSID gap report | `src/mist/intelligence/reports/ssid_broadcast_gap_report.py` line 41 | Required | Propagate | R54 |
| CLI `--site` resolver | `MistHelper.py` line 7886 | Required | Top-level handler logs and exits 1 | R55, R56, R57, R58 |
| Firmware configuration | `MistHelper.py` line 3621 | Required, consumer inferred (U-5) | Existing handlers | R62 |
| Org upgrade configuration | `MistHelper.py` line 5732 | Required, consumer inferred (U-5) | Existing handler | R63 |
| Fast-path CSV generator | `src/foundation/persistence/cache/cache_utils.py` line 103 | Optional by design | Generator failure returns `False` | R65 |

## Remote Verification

The table lists 126 checks. Ref `main` means a remote read on `main`. Ref `local-venv` means a read-only file in `.venv`. Line 0 means a file-level or absence check.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | APICoreFetchUtils class defined | src/mist/access/api/api_core_fetch_utils.py | main | 2d63aa95a11d5b8707a7a3cb478c2d4e00110dce | present | 30 |
| R02 | all_sites_with_limit defined | src/mist/access/api/api_core_fetch_utils.py | main | 2d63aa95a11d5b8707a7a3cb478c2d4e00110dce | present | 38 |
| R03 | all_sites_with_limit returns mistapi.get_all result | src/mist/access/api/api_core_fetch_utils.py | main | 2d63aa95a11d5b8707a7a3cb478c2d4e00110dce | present | 53 |
| R04 | all_inventory_with_limit defined | src/mist/access/api/api_core_fetch_utils.py | main | 2d63aa95a11d5b8707a7a3cb478c2d4e00110dce | present | 56 |
| R05 | getOrgInventory call passes vc=True | src/mist/access/api/api_core_fetch_utils.py | main | 2d63aa95a11d5b8707a7a3cb478c2d4e00110dce | present | 69 |
| R06 | all_inventory_with_limit returns mistapi.get_all result | src/mist/access/api/api_core_fetch_utils.py | main | 2d63aa95a11d5b8707a7a3cb478c2d4e00110dce | present | 71 |
| R07 | APIFetchError exists on main | src/mist/access/api/api_core_fetch_utils.py | main | 2d63aa95a11d5b8707a7a3cb478c2d4e00110dce | absent | 0 |
| R08 | Unit test for all_sites_with_limit exists | tests/unit/api/test_api_core_fetch_utils.py | main | 04eda0bb9fe4a912013ddc80f06747c272e949e7 | present | 19 |
| R09 | Unit test for all_inventory_with_limit exists | tests/unit/api/test_api_core_fetch_utils.py | main | 04eda0bb9fe4a912013ddc80f06747c272e949e7 | present | 43 |
| R10 | SiteNameLookup.fetch calls all_sites_with_limit | src/mist/intelligence/reports/switch_scorecard/site_lookup.py | main | a0b6edda2b59616f345889448f9e21e4e87c6dfc | present | 23 |
| R11 | WAN scorecard calls SiteNameLookup.fetch | src/mist/intelligence/reports/wan_edge_scorecard/scorecard.py | main | a30148647b045bb39cd087bca1039150c0c58151 | present | 85 |
| R12 | Switch scorecard calls SiteNameLookup.fetch | src/mist/intelligence/reports/switch_scorecard/operation.py | main | 1eee8b619423eb037f602ef0f2604bedfa5d9374 | present | 41 |
| R13 | AP scorecard calls SiteNameLookup.fetch | src/mist/intelligence/reports/ap_scorecard/operation.py | main | 944166728319f9c3e55f4bab547e9bb0764a76c6 | present | 49 |
| R14 | Offline report _fetch_data calls all_sites_with_limit | src/mist/intelligence/reports/offline_device_reporter.py | main | 4909db33d24ae6cd52f02dcbd9450608ae716b99 | present | 107 |
| R15 | Offline report maps a missing site name to Unknown Site | src/mist/intelligence/reports/offline_device_reporter.py | main | 4909db33d24ae6cd52f02dcbd9450608ae716b99 | present | 154 |
| R16 | _resolve_site_for_stats calls all_sites_with_limit | src/operations/exporting/export/site_device_exporter.py | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 141 |
| R17 | _resolve_site_for_stats uses the site ID as a fallback | src/operations/exporting/export/site_device_exporter.py | main | f9fd54c69b9458df6182b6142c63bf15b012bb1a | present | 143 |
| R18 | export_sites_by_ap_model calls all_sites_with_limit | src/operations/exporting/export/sites_by_ap_model_exporter.py | main | 66d1ccaf05886d89802aa45792977480f73f37c4 | present | 173 |
| R19 | Site map lookup returns an empty default for a missing site | src/operations/exporting/export/sites_by_ap_model_exporter.py | main | 66d1ccaf05886d89802aa45792977480f73f37c4 | present | 113 |
| R20 | org_inventory_exporter imports APICoreFetchUtils at module level | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 43 |
| R21 | _build_site_lookup_from_api calls all_sites_with_limit | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 509 |
| R22 | Cache-miss fallback calls _build_site_lookup_from_api | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 530 |
| R23 | Non-fast devices path calls _build_site_lookup_from_api | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 557 |
| R24 | gateways_with_site_info calls all_sites_with_limit | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 688 |
| R25 | Device site fallback text is Unknown | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 590 |
| R26 | Gateway site fallback text is Unknown | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 734 |
| R27 | MSP _build_site_lookup calls all_sites_with_limit inside a broad catch | src/operations/exporting/export/msp_inventory_exporter.py | main | 4b2aa3ab42ebac86ecdf43be224fa4df07385895 | present | 358 |
| R28 | MSP _build_site_lookup logs its failure at debug level | src/operations/exporting/export/msp_inventory_exporter.py | main | 4b2aa3ab42ebac86ecdf43be224fa4df07385895 | present | 361 |
| R29 | MSP organization inventory calls mistapi.get_all directly | src/operations/exporting/export/msp_inventory_exporter.py | main | 4b2aa3ab42ebac86ecdf43be224fa4df07385895 | present | 275 |
| R30 | _load_sites_cache calls all_sites_with_limit | src/interfaces/visualization/ui/prompt_utils.py | main | 85298f30dcbc6ed5a6adf01b5801347e2ede7efd | present | 394 |
| R31 | _load_sites_cache catches RuntimeError | src/interfaces/visualization/ui/prompt_utils.py | main | 85298f30dcbc6ed5a6adf01b5801347e2ede7efd | present | 398 |
| R32 | Prompt client calls _load_sites_cache | src/foundation/runtime/input/prompt_client_utils.py | main | a8d6d1cc0758a097953af09506f97a5267c917ce | present | 229 |
| R33 | AP model read calls all_inventory_with_limit | src/operations/exporting/export/sites_by_ap_model_exporter.py | main | 66d1ccaf05886d89802aa45792977480f73f37c4 | present | 36 |
| R34 | Inventory cache fallback calls all_inventory_with_limit | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 544 |
| R35 | Non-fast devices path calls all_inventory_with_limit | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 558 |
| R36 | gateways_with_site_info calls all_inventory_with_limit | src/operations/exporting/export/org_inventory_exporter.py | main | 938e2d9265146cf3c35081574cbf479e23988ee0 | present | 692 |
| R37 | Gateway export calls all_inventory_with_limit | src/mist/resources/gateway/gateway_export_utils.py | main | 5ea396219ddc3791f8fdf45720dc4a28c961b21a | present | 561 |
| R38 | Gateway export calls all_inventory_with_limit again | src/mist/resources/gateway/gateway_export_utils.py | main | 5ea396219ddc3791f8fdf45720dc4a28c961b21a | present | 572 |
| R39 | Gateway export reads sites through mistapi.get_all directly | src/mist/resources/gateway/gateway_export_utils.py | main | 5ea396219ddc3791f8fdf45720dc4a28c961b21a | present | 282 |
| R40 | Firmware manager passes all_sites_with_limit as a fetch seam | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | present | 1901 |
| R41 | Firmware site lookup catches Exception and warns | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | present | 3549 |
| R42 | Bulk upgrader reads sites through the seam | src/operations/execution/firmware/bulk_ap_upgrader.py | main | 99978c5564ea53be21e983c4a8621048c3d88a18 | present | 313 |
| R43 | Org AP upgrader reads sites through the seam | src/operations/execution/firmware/org_ap_upgrader.py | main | 079a0db1a003abe30e7c7a666c6e9d6892b04f68 | present | 1016 |
| R44 | Org AP upgrader catches Exception and reports the error | src/operations/execution/firmware/org_ap_upgrader.py | main | 079a0db1a003abe30e7c7a666c6e9d6892b04f68 | present | 1023 |
| R45 | Site auto upgrade reads sites through the seam | src/operations/execution/firmware/site_auto_upgrade.py | main | 413de59b844a5f1a9b2699bb695bb0d4cbd029b2 | present | 333 |
| R46 | Site auto upgrade catches RuntimeError | src/operations/execution/firmware/site_auto_upgrade.py | main | 413de59b844a5f1a9b2699bb695bb0d4cbd029b2 | present | 340 |
| R47 | Organization site export reads sites | src/operations/exporting/export/org_site_exporter.py | main | 062a920885a3a45e5c89e605a3e12b8c3fa45f10 | present | 90 |
| R48 | Site location export reads sites | src/operations/exporting/export/org_site_exporter.py | main | 062a920885a3a45e5c89e605a3e12b8c3fa45f10 | present | 115 |
| R49 | Zone analysis wiring in site export utilities | src/operations/exporting/export/site_export_utils.py | main | de9b901f90ad43af86688bc41d39df68fbff2153 | present | 553 |
| R50 | Zone analyzer calls the injected site fetch | src/mist/intelligence/analytics/site/zone_analyzer.py | main | 819d02d9a4a86bf84ebcb0854c01592c8755e472 | present | 561 |
| R51 | Zone script wires all_sites_with_limit | scripts/replace_zone.py | main | 10e3a35d82c0421077790250b6a292f6f3c7676d | present | 30 |
| R52 | all_site_settings reads sites through all_sites_with_limit | src/mist/access/api/api_fetch_utils.py | main | 373f1166028c2e52392cc80a38b6fc27458e2124 | present | 154 |
| R53 | Site configuration export calls all_site_settings | src/operations/exporting/export/site_config_exporter.py | main | b8aba9cb18c39285321ca8f91242458ebf0f7037 | present | 168 |
| R54 | SSID gap report reads all sites | src/mist/intelligence/reports/ssid_broadcast_gap_report.py | main | 31a1d88bceab2f7e7b5636128037d88b7c3e724c | present | 41 |
| R55 | CLI --site resolver reads all sites | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7886 |
| R56 | CLI run mode defines the run path | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7817 |
| R57 | Top-level entry logs an unhandled exception | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8346 |
| R58 | Top-level entry exits with code 1 | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8367 |
| R59 | Menu dispatcher calls the selected function | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8089 |
| R60 | Menu dispatcher catches Exception | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8096 |
| R61 | Direct mode exits with code 1 after a menu exception | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 8155 |
| R62 | Firmware configuration wires all_sites_with_limit | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3621 |
| R63 | Org upgrade configuration wires all_sites_with_limit | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5732 |
| R64 | Zone analyzer configuration wires all_sites_with_limit | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5771 |
| R65 | CSV generator catches Exception | src/foundation/persistence/cache/cache_utils.py | main | d628806f4b0f32c1059264c82d0722d4e099d0b7 | present | 103 |
| R66 | mistapi is pinned to 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R67 | MYPY_PATHS includes src/ | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R68 | VULTURE_PATHS is defined | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R69 | PYDOCSTYLE_PATHS is defined | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R70 | INTERROGATE_PATHS is defined | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R71 | Ruff check command | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 165 |
| R72 | Black check command | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 196 |
| R73 | Mypy command | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 237 |
| R74 | Radix segment function | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| R75 | Feature path resolver function | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| R76 | SDK guard copies re-exports such as get_all | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | present | 276 |
| R77 | Test-quality configuration exists | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| R78 | Test-quality baseline exists | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 |
| R79 | Full-gate requirements file exists | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 0 |
| R80 | Changelog fragment guard exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| R81 | Test-quality preflight module exists | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| R82 | OpenAPI inventory path defined | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10639 |
| R83 | getOrgInventory operationId | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10660 |
| R84 | getOrgInventory limit and page parameters | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10745 |
| R85 | getOrgInventory response codes 400, 401, 403, 404, and 429 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10750 |
| R86 | OpenAPI sites path defined | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20018 |
| R87 | listOrgSites operationId | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20022 |
| R88 | listOrgSites limit and page parameters | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20024 |
| R89 | listOrgSites response codes 400, 401, 403, 404, and 429 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20029 |
| R90 | OpenAPI file has no HTTP 503 response | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 0 |
| R91 | MIST_API_GET_ENDPOINTS getOrgInventory row | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 607 |
| R92 | MIST_API_GET_ENDPOINTS listOrgSites row | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 867 |
| R93 | mistapi re-exports get_next | .venv\Lib\site-packages\mistapi\__init__.py | local-venv | not applicable | present | 16 |
| R94 | get_next returns the next page or None | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | not applicable | present | 33 |
| R95 | get_all list branch extends without a status check | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | not applicable | present | 62 |
| R96 | get_all stops without an error when the next page is missing | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | not applicable | present | 64 |
| R97 | get_all dict branch returns results only | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | not applicable | present | 65 |
| R98 | APIResponse default data is an empty dict | .venv\Lib\site-packages\mistapi\__api_response.py | local-venv | not applicable | present | 39 |
| R99 | APIResponse default status code is None | .venv\Lib\site-packages\mistapi\__api_response.py | local-venv | not applicable | present | 43 |
| R100 | APIResponse flags status 400 or higher | .venv\Lib\site-packages\mistapi\__api_response.py | local-venv | not applicable | present | 60 |
| R101 | APIRequest returns the response after a failure | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | not applicable | present | 258 |
| R102 | Installed mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-venv | not applicable | present | 3 |
| R103 | Symbol gate counts import names | .venv\Lib\site-packages\misthelper_devtools\symbol_diff\comparator.py | local-venv | not applicable | present | 165 |
| R104 | Symbol gate counts class and function names | .venv\Lib\site-packages\misthelper_devtools\symbol_diff\comparator.py | local-venv | not applicable | present | 164 |
| R105 | Symbol gate returns 1 when a name changes | .venv\Lib\site-packages\misthelper_devtools\symbol_diff\comparator.py | local-venv | not applicable | present | 129 |
| R106 | Merge commit message contains Refs #4762 | commit aa8d12e90fd68b5b22a44471b0606443e6ab9338 | main | aa8d12e90fd68b5b22a44471b0606443e6ab9338 | present | 0 |
| R107 | Pull request 4853 body says it does not resolve #4762 | pull request 4853 body | main | not applicable | present | 0 |
| R108 | Pull request 4767 changed msp_inventory_exporter.py | pull request 4767 file list | main | 4b2aa3ab42ebac86ecdf43be224fa4df07385895 | present | 0 |
| R109 | No 4762 record exists on main | specs directory tree | main | not applicable | absent | 0 |
| R110 | AGENTS.md writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R111 | AGENTS.md tests section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 133 |
| R112 | Copilot instructions local gates section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R113 | Copilot instructions test quality row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 253 |
| R114 | Constitution Principle I five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R115 | Constitution Principle II class-based architecture | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| R116 | Constitution Principle III safety-first | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R117 | Constitution Principle IV full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R118 | Constitution Principle V observability | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| R119 | Constitution Principle VI inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R120 | Constitution Principle VII action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R121 | Constitution mistapi-only rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| R122 | Changelog naming table | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| R123 | STE gate file list | .github/workflows/ste-lint.yml | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 44 |
| R124 | Architecture table row for the access API | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 270 |
| R125 | tests/integration directory holds 26 children | tests/integration | main | not applicable | present | 0 |
| R126 | tests/integration/export directory holds 2 children | tests/integration/export | main | not applicable | present | 0 |

## Sources

- Issue 4762: `gh issue view 4762 -R jmorrison-juniper/MistHelper --json` with state OPEN, labels `bug`, `MistHelper.py`, and `in-progress`, and 24 comments.
- Pull requests 4767 and 4853: `gh pr view` for the file list, the body, and the merge data. Merge commit `aa8d12e90fd68b5b22a44471b0606443e6ab9338`: commits API on `main`.
- Remote tree and contents: one `git/trees/main` call. Contents and blob reads for the rows in the table above.
- Local repository, read-only: `AGENTS.md` (full), `.github/copilot-instructions.md` (full), `.specify/memory/constitution.md` (full), and the four templates under `.specify/templates/` (full).
- Local repository, read-only: `.specify/scripts/powershell/spec-route.ps1` (full), `changelog.d/README.md` (full), `src/mist/access/api/api_core_fetch_utils.py` (full), and `tests/unit/api/test_api_core_fetch_utils.py` (full).
- Local repository, read-only: `src/mist/intelligence/reports/switch_scorecard/site_lookup.py` (full), and the callers in the caller inventory (ranges and searches).
- Reference record: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv\spec.md` lines 1 to 60, and `tasks.md` lines 1 to 50. The shape was copied: a feature root with spec, plan, tasks, and analysis, plus a `design` folder. No content was copied.
- Documentation: `documentation/quality-gates.md` and `documentation/architecture.md` were searched for the terms that apply. `documentation/operator-guide.md` was searched for site, warning, and fallback text, and it has none. `documentation/container-deployment.md` applies only when a test container starts. This change starts none.
- mistapi 0.64.1 source: `.venv\Lib\site-packages\mistapi\` (read-only). The misthelper_devtools source: `.venv\Lib\site-packages\misthelper_devtools\symbol_diff\comparator.py` (read-only).
- No URL was fetched. No skill was loaded.

## Unverified

- U-1: Live Mist responses for HTTP 403, 429, and 503. Reason: no network request is allowed. The behavior comes from the SDK source (rows R94 to R101) and the OpenAPI text (rows R82 to R92).
- U-2: A hosted CI result for any candidate patch. Reason: no candidate exists on `main` or on a remote branch.
- U-3: The candidate patch hashes, the owner gate results, and the owner symbol-diff exit code from issue comments 11 to 23. Reason: the candidate is not in the repository, and no script run is allowed.
- U-4: Session 79a9bb52 ownership and the file-only handoffs from the owners of issue 1794. Reason: the coordination exists only in issue comments 9 and 13.
- U-5: The consumers of the `fetch_sites_fn` wiring at rows R40, R62, and R63. Reason: the consumers are inferred from keyword names and configuration fields. The full consumer bodies were not read.
- U-6: The menu numbers 10, 11, 12, 26, 61, 88, and 144. Reason: taken from local reads of `MistHelper.py` and `operation_registry.py`. The lines were not decoded from `main`.
- U-7: The issue closing reference after pull request 4853. Reason: the closing reference was not queried. The issue state OPEN was verified.
- U-8: The closure of issue 4765. Reason: the issue is closed on `main`, and the owner comment predates the closure. The gate result must rerun in T-LOCAL-GATES.
- U-9: The Python version statement. Reason: the statement is cited by section name only.
- U-10: Existing tests that replace `APICoreFetchUtils` with a fake. Reason: reviewed by search only. No test run is allowed. T-LOCAL-GATES runs them.
- U-11: The `symbol-diff` exit behavior. Reason: read from the comparator source (rows R103 to R105). No run is allowed.
- U-12: HTTP 429 handling after the SDK retries. Reason: read from `__api_request.py` (row R101). No run is allowed.
- U-13: The development setup document was searched, not read in full. Its bootstrap, activation, and `python -m pytest` lines (local lines 32 to 40, 136, and 183 to 184) match the commands in `design/quickstart.md`. The remote copy has no row in this table.
