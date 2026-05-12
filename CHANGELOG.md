# Changelog

All notable changes to MistHelper are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Version format: `YY.MM.DD.HH.MM` (UTC timestamp).

## [Unreleased]

### Refactored

- Reduced cyclomatic complexity of most methods in `src/maps/maps_manager.py` (#251); remaining high-CC methods deferred to dedicated follow-on issues (#293–#296)
  - Extracted `_check_dependencies`, `_configure_logging`, `_setup_api_session`, `_filter_org_privileges`, `_prompt_org_selection`, `_detect_org_from_session`, and `_resolve_org_id` from `main()` (CC 29→7)
  - Extracted `_download_all_site_map_images`, `_select_map_from_site`, `_backup_print_summary`, and other helpers to reduce method-level CC throughout the module
  - `src/maps/*` remains in CI radon exclusion until #293–#296 are resolved (`_launch_plotly_viewer` CC=138, `intelligent_map_replacement_wizard` CC=126, `interactive_map_viewer` CC=43, `launch_viewer_standalone` CC=30)
- Extracted `WebSocketManager`, `WebSocketNetworkDiagCommands`, and `WebSocketCommands` from `MistHelper.py` into `src/websocket/` modules, reducing `MistHelper.py` by ~1,789 lines (#209)
- Added `src/websocket/context.py` with `WebSocketCmdDeps` dataclass for clean dependency injection into extracted WebSocket command classes
- Updated CI radon exclusion to include `src/websocket/manager.py` (contains complex `wait_for_command_result` method)

## [26.05.12.07.25] - 2026-05-12

### Refactored

- Eliminated 3 thin wrapper classes (`SSIDTemplateConsolidationManager`, `E911BSSIDReportGenerator`, `ZoneConfigurationAnalyzer`) and 1 standalone wrapper function (`update_gateway_templates_wan2_variable`) by moving their logic directly into appropriate existing classes: `OrgExportUtils.ssid_template_consolidation`, `OrgExportUtils.e911_bssid_compliance_report`, `SiteExportUtils.zone_config_analysis`, `GatewayExportUtils.wan2_variable_migration`. Updated dispatch entries 104, 119, 159, and 160 accordingly (#287)

## [26.05.12.06.57] - 2026-05-12

### Added

- New menu item 173: `SitesByAPModelExporter.export_sites_by_ap_model` — prompts user to select an AP model from the models present in the organisation, then exports a CSV listing every site that contains APs of that model, including site name, site address, city, state, country, AP count, and individual AP MAC addresses. Uses mistapi's paginated fetch engine for parallel multi-page retrieval (#286)

## [26.05.11.00.00] - 2026-05-11

### Refactored

- Extract `FirmwareManager` class (2327 lines) to `src/firmware/firmware_manager.py` using dependency injection pattern consistent with `BulkAPFirmwareUpgrader`, `OrgLevelAPFirmwareUpgrader`, and other extracted firmware modules. MistHelper.py retains a 50-line thin wrapper (#203)

## [26.05.07.16.34] - 2026-05-07

### Fixed

- FR-001: Renamed `searchOrgBgpPeers` → `searchOrgBgpStats` (mistapi 0.62.0 function rename; line ~16191)
- FR-002: Renamed `searchOrgTunnels` → `searchOrgTunnelsStats` (mistapi 0.62.0 function rename; line ~16198)
- FR-003: Renamed `listOrgSitesStats` → `listOrgSiteStats` (mistapi 0.62.0 function rename; line ~16205)
- All three were confirmed `AttributeError` runtime crashes. No such function names exist in mistapi 0.62.0.

### Security

- FR-004: Attached `LogSanitizer` (mistapi `__logger`) to root logger at startup. Automatically redacts API tokens, passwords, and sensitive field values from all log output. Wrapped in `try/except ImportError` for backward compatibility with pre-0.59.3 mistapi.

### Added

- FR-005: Updated `requirements.txt` to `mistapi>=0.62.0` (was `>=0.61.4`)
- FR-006: New menu 166 — Export E911 Report (`getOrgE911Report`): exports organization E911 data to CSV
- FR-007: New menu 167 — Export JSI PBN Data (`searchOrgJsiPbn`): exports JSI Product Bulletin Notifications
- FR-008: New menu 168 — Export JSI SIRT Advisories (`searchOrgJsiSirt`): exports JSI Security Incident Response Team advisories
- FR-009: New menu 169 — Export Org OSPF Stats (`searchOrgOspfStats`): org-level OSPF adjacency statistics
- New menu 170 — Export Site OSPF Stats (`searchSiteOspfStats`): site-level OSPF adjacency statistics
- FR-010: New menu 171 — Export MxEdge Upgrade Status (`listSiteMxEdgeUpgrades`): site-level MxEdge firmware upgrade records
- FR-011: New menu 172 — Export Auto-Map Assignment Status (`getSiteAutoMapAssignmentStatus`): site auto-map assignment state
- Added `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries for all 5 new API endpoints: `getOrgE911Report`, `listSiteMxEdgeUpgrades`, `getSiteAutoMapAssignmentStatus` (new); `searchOrgOspfStats`, `searchSiteOspfStats` (already present, verified)

## [26.04.26.01.53] - 2026-04-26

### Added

- Bulk Org Data Collection (Menu 165): New external module `src/org_data_collector.py` with `OrgDataCollector` class. Executes 137 org-level read API calls (64 list, 36 search, 6 get, 31 count) in a single pass to populate ArangoDB, Redis, and SQLite backends. Covers admins, API tokens, licenses, SSO/SSO roles, device profiles, network templates, RF templates, site templates, AP templates, security policies/profiles (AAMW, AV, IDP, SecIntel), PSKs, webhooks, VPNs, EVPN topologies, WxLAN rules/tags/tunnels, MxEdge/MxEdge clusters/tunnels, NAC portals/rules/tags, assets/asset filters, alarm templates, site groups, services, service policies, certificates, guest authorizations, PSK portals, tickets, dashboards, SDK invites/templates, Marvis client invites, packet captures, JSI data, firmware versions/upgrades, and 31 count endpoints. Includes per-call error handling (skip on failure, continue with remaining), categorized progress display, pagination support for non-paginated APIs, and collection summary.
- 68 additional ENDPOINT_PRIMARY_KEY_STRATEGIES entries for all new org-level API endpoints (31 count endpoints as auto_increment, entity endpoints as natural_pk, event/search data as composite_pk).

### Fixed

- Fixed `OrgExportUtils.export_data()` to accept optional `limit` parameter (default 1000). When `limit=None`, the limit parameter is omitted from API calls, fixing failures on non-paginated endpoints that reject the `limit` argument.
- Removed 4 broken/parent-dependent operations from org data collector: `listOrgSsoLatestFailures` (requires sso_id), `listOrgNacPortalSsoLatestFailures` (requires nacportal_id), `searchOrgWebhooksDeliveries` (requires webhook_id), `listOrgJsiPastPurchases` (HTTP 400).

## [26.04.23.16.39] - 2026-04-23

### Added

- WAN Hub-Spoke VPN Builder (Menu 164): New external module `src/wan_vpn_builder.py` with `WanVpnBuilder` class. Fetches gateway device profiles, lets the user assign hub/spoke roles and pod values, auto-generates full-mesh hub paths and hub-spoke paths with cross-connects, previews the VPN payload, creates the VPN via API, and optionally writes port_vpn_paths back to each profile. Supports typed CREATE confirmation (FR-007). Includes 61 unit tests covering all pure logic, API helpers, prompts, and the full workflow.

## [26.04.22.20.38] - 2026-04-22

### Added

- WAN Hub Group Number Manager (Menu 163): New external module `src/wan_hub_group_manager.py` with `WanHubGroupNumberManager` class. Lists all gateway device profiles with current pod (group number) values from hub-spoke VPN paths, lets the user select a profile, then set pod (1-128) or clear to default (1). Batch updates all matching VPN paths across multiple VPN objects. Uses trailing-hyphen prefix matching to avoid false collisions (e.g., DC1- vs DC1-BACKUP-). Warns on inconsistent pod values. Follows external module pattern with `execute(apisession, get_org_id_func, safe_input_func)` static method. Includes 33 unit tests covering all four user stories.

## [26.04.22.20.38] - 2026-04-22

### Added

- WAN Hub Group Number Manager (Menu 163): New interactive operation to view, set, and clear pod (group_number) values on WAN hub profile VPN paths. First menu operation extracted into an external module under src/wan_hub_group_manager.py following dependency-injection pattern.
- 33 unit tests for WanHubGroupNumberManager covering profile fetching, path matching, pod set/clear, input validation, and module architecture.

## [26.04.20.20.23] - 2026-04-20

### Added

- Wired Client Manufacturer Report (Menu 162): New WiredClientManufacturerReportGenerator class fetches all org wired clients, displays indexed manufacturer summary with counts sorted by frequency, and lets the user select a manufacturer to export filtered records. Supports "export all" option. Uses existing searchOrgWiredClients API with limit=1000 and standard DataExporter CSV/SQLite output.

## [26.04.09.21.30] - 2026-04-09

### Compatibility Audit

- MistAPI compatibility audit alignment: raised the documented dependency floor to `mistapi>=0.61.4` and `websocket-client>=1.8.0`, updated the site client insights workflow to call `getSiteInsightMetricsForClient(..., metrics=metric)`, and added regression coverage for alarms, device-event pagination, site client stats, site SLE summaries, client insight metrics, and the E911 BSSID report.

## [26.04.08.18.41] - 2026-04-08

### Added

- SSID Template Consolidation (Menu 159): Complete rewrite as SSIDTemplateConsolidationManager with 5-phase guided workflow. Phase 1: read-only audit builds site-template-SSID matrix with cross-cluster deviation analysis. Phase 2: auto-detect site-specific deviations and write MISTHELPER_* site variables. Phase 3: create site groups by Mist Edge cluster affinity. Phase 4: build consolidated WLAN templates with Jinja variable references for deviations. Phase 5: disable old per-site SSIDs. Includes JSON cache/resume, CONFIRM gates on all write phases, and DataExporter dual CSV/SQLite output.

## [26.04.07.22.27] - 2026-04-07

### Fixed

- E911 BSSID Report (Menu 160): Fixed radio band and SSID resolution. Radio stats now fetched from site-level listSiteDevicesStats (not org-level which omits radio_stat). SSID resolution now uses full 3-source chain: site-level WLANs (listSiteWlans), site template WLANs (getOrgSiteTemplate wlans field), and org WLANs via WLAN template assignment (listOrgTemplates applies.site_ids/sitegroup_ids/org_id -> listOrgWlans filtered by template_id). Refactored _fetch_lookups into focused helpers: _fetch_org_wlan_templates, _fetch_org_wlans, _fetch_site_maps, _fetch_site_radio_stats, _resolve_site_ssids, _resolve_site_template_wlans, _get_assigned_template_ids, _add_wlans_to_band_lookup. Site lookup now stores sitegroup_ids and sitetemplate_id for template resolution.

## [26.04.07.22.13] - 2026-04-07

### Changed

- E911 BSSID Report (Menu 160): Enhanced with radio band details and SSID names. Now parses radio_stat from listOrgDevicesStats to resolve each radio MAC to its band (2.4/5/6 GHz), channel, and power. Fetches listSiteWlans per site to build band-to-SSID lookup, mapping WLAN band config (24/5/6/both) to radio bands. New CSV columns: AP MAC, Band, Radio MAC, Channel, Power, SSIDs on Band. Sort order updated to include Band. _fetch_lookups returns dict with radio_bands and wlan_bands lookups; _build_bssid_rows accepts consolidated lookups dict (2 params vs prior 4).

## [26.04.07.21.00] - 2026-04-07

### Added

- E911 BSSID Compliance Report (Menu 160): New E911BSSIDReportGenerator class queries all AP radio MACs via listOrgApsMacs, resolves site name/address via listOrgSites, AP name/site/map via listOrgDevicesStats(type=ap), floor names via listSiteMaps per site, derives 16 BSSIDs per radio MAC (last nibble 0x0-0xF), outputs sorted CSV (Site Name, Site Address, Map Name, AP Name, BSSID) with compliance gap detection for APs missing map assignments. Classified as safe in OperationRegistry for automated --test mode.

## [26.03.28.19.09] - 2026-03-28

### Added

- Offline Device Report (Menu 158): New OfflineDeviceReporter class scans entire org via listOrgDevicesStats (type=all, status=all), filters devices offline beyond user-configurable threshold (default 48h), resolves site names via lookup dict, displays summary stats (total devices, per-type breakdown, top 5 sites) + PrettyTable (max 50 rows), saves human-readable CSV with timestamped filename to data/. Classified as safe in OperationRegistry for automated --test mode.

## [26.03.20.22.31] - 2026-03-20

### Added

- Device Utility Commands: 35 new operations (menus 123-157) covering traceroute, OSPF diagnostics, session/service-path inspection, BGP/ARP/DHCP/802.1X/EVPN show commands, DNS resolution, live traffic monitoring, device locate, port bounce, cable test, reprovision/re-adopt, ZTP password retrieval, config command export, support file upload, 7 clear/reset operations, DHCP lease release, stats polling, and device snapshots
- DeviceUtilityCommands class: Uses mistapi SDK methods (not raw requests) with WebSocket result streaming, device-type validation, port selection from live stats, and three-tier destructive confirmation (none/y-N/typed keyword)
- 14 new ENDPOINT_PRIMARY_KEY_STRATEGIES entries for dual-output (CSV/SQLite) support on all device utility results

## [26.03.05.02.49] - 2026-03-05

### Added

- Web Portal: Flask-based browser interface on port 8055 (--web-portal CLI flag)
- Data Browser: Browse, search, preview, and download CSV/SQLite output files
- Operations: Run data extraction operations (menus 1-89) with real-time SSE progress
- Map Viewer: Interactive Plotly.js floor plan viewer with device markers
- Theme System: Dark, Light, and High Contrast themes with instant switching and localStorage persistence
- Portal Branding: Customizable title, logo, and accent color via ENV variables
- Container Integration: Dual-process startup (Gunicorn + sshd) on ports 8055 and 2200
- Security: CSP headers, CSRF protection, IP allowlist, path traversal guard

### Changed

- Replaced Dash dependency with Flask + Gunicorn for lighter footprint
- Updated Containerfile: EXPOSE 8055, COPY web_portal/, bundled vendor assets
- Updated compose.yml: Port 8055:8055 replaces 8050:8050, WEB_PORT env var
- Container start.sh: Dual-process with SIGTERM trap for clean shutdown

## [26.03.04.22.30] - 2026-03-04

### Changed

- God-class decomposition: All 95 classes now comply with 5-Item Rule (max 5 public methods per class)
- 13 non-compliant classes decomposed via rename-to-private and sub-class extraction
- GlobalImportManager: 13->5 pub (8 renamed private)
- RateLimitingUtils: 6->1 pub (5 renamed private)
- APIFetchUtils: 9->3 pub (extracted APICoreFetchUtils, APITenantFetchUtils)
- AddressUtils: 9->5 pub (4 renamed private)
- WebSocketCommands: 7->4 pub (extracted WebSocketNetworkDiagCommands)
- OrgExportUtils: 51->5 pub (12 renamed private, extracted 7 sub-classes: OrgSiteExporter, OrgInventoryExporter, OrgDeviceStatsExporter, OrgTemplateExporter, OrgClientSecurityExporter, OrgAdminExporter, OrgConfigExporter)
- MapsManager: 28->0 pub (all 28 renamed private - dead/internal-only code)
- EnhancedSSHRunner: 24->5 pub (19 renamed private)
- SiteExportUtils: 22->3 pub (3 renamed private, extracted 4 sub-classes: SiteDeviceExporter, SiteClientExporter, SiteConfigExporter, SiteAnomalyExporter)
- RoutingUtils: 16->3 pub (13 renamed private)
- PromptUtils: 12->5 pub (extracted PromptNetworkDeviceUtils, PromptClientUtils)
- GatewayExportUtils: 12->4 pub (3 renamed private, extracted GatewayTestExporter, GatewayStatsExporter)
- FirmwareManager: 10->4 pub (6 renamed private)
- 16 new sub-classes created following {Scope}{Domain}{Action} naming convention
- Zero functionality changes - all tests pass (49/49) after every decomposition

## [26.03.04.00.55] - 2026-03-04

### Changed

- Extract OrgAlarmEventExporter from OrgExportUtils (5-Item Rule compliance)
- New class contains 5 alarm/event methods: alarms(), alarm_templates(), events(), device_events(), device_events_52w()
- OrgExportUtils reduced from 56 to 51 methods; documented extraction pattern for future decomposition
- Consolidated redundant logging in alarms() (two start messages merged into one)

## [26.03.03.23.35] - 2026-03-03

### Changed

- Menu 122: Show ALL RADIUS WLANs including compliant ones marked '(COMPLIANT)' for full org visibility
- Menu 122: Accept 'q', 'quit', 'cancel', 'back' at selection prompt for safe exit without changes
- Menu 122: Respect --dry-run flag (preview without API calls, DRYRUN_ CSV prefix)
- Menu 122: Respect --debug flag (verbose API response and compliance evaluation logging)
- Menu 122: DRY-RUN and DEBUG mode banners displayed at startup when flags are active

## [26.03.03.22.27] - 2026-03-03

## [26.02.18.19.30] - 2026-02-18

### Added

- Menu 121: Site Inventory Health Analysis - Find sites with APs missing switches/gateways or with offline infrastructure
- Generates two reports: SitesMissingInfrastructure and SitesWithOfflineInfrastructure
- Uses org-level APIs for efficient bulk analysis across all sites

## [26.02.09.00.33] - 2026-02-09

### Changed

- Menu 120: Added engagement hours to standard configuration (all days set to empty string)
- Detects and clears custom operating hours (sun/mon/tue/wed/thu/fri/sat) to defaults

## [26.02.08.23.58] - 2026-02-08

### Changed

- Menu 120: Added WiFi settings to standard configuration (enabled=true, locate_connected=true, locate_unconnected=false)
- SiteAnalyticsConfigurator now checks and applies STANDARD_WIFI settings across all sites

## [26.02.08.23.46] - 2026-02-08

## [26.02.08.23.37] - 2026-02-08

## [26.02.08.23.28] - 2026-02-08

### Changed

- Menu 119: Extended to analyze engagement dwell tags (passerby/bounce/engaged/stationed time ranges)
- Menu 119: Extended to analyze engagement dwell tag custom names
- Menu 119: Extended to analyze occupancy settings (min_duration, clients_enabled, etc.)
- Menu 119: Extended to analyze analytics enabled/disabled status across sites
- Menu 119: Exports 5 CSV files: Summary, AllZones, ZoneFrequency, DwellConfigs, OccupancyConfigs

## [26.02.08.23.20] - 2026-02-08

## [26.02.05.00.25] - 2026-02-05

### Fixed

- Menu 116: Add full pagination support using mistapi.get_all()
- Menu 116: Inventory fetch now retrieves ALL APs (not just first 1000)
- Menu 116: Stats fetch now retrieves ALL device stats with pagination

## [26.02.05.00.20] - 2026-02-05

### Fixed

- Menu 116: Use listOrgAvailableDeviceVersions API (not getOrgDeviceUpgrade)
- Menu 116: Fix 'Unknown' firmware version display - match by MAC address
- Menu 116: Add limit=1000 to listOrgDevicesStats call for proper pagination

## [26.02.05.00.15] - 2026-02-05

### Fixed

- Menu 116: Use getOrgInventory API instead of listOrgDevices (listOrgDevices doesn't support type filter)
- Fixed 'listOrgDevices() got an unexpected keyword argument type' error

## [26.02.04.16.35] - 2026-02-04

### Changed

- Direct interactive login without org selection flow
- Proper inventory fetch with limit=1000 pagination

### Fixed

- Menu 117: Skip MSP/Org selection after login (exports ALL, not selected)
- Menu 117: Use getOrgInventory API instead of listOrgDevices for full inventory
- Fixed device count showing '1 (unknown:1)' for every org

## [26.02.04.16.20] - 2026-02-04

### Changed

- Menu 117: Auto-prompt for interactive login when MSP privileges missing
- No longer requires user to manually run --login or Menu 115 first
- Improved UX: offers to switch authentication in-place if needed

## [26.02.05.06.15] - 2026-02-05

### Changed

- Output includes MSP/Org/Site context columns for each device
- Device type breakdown summary (ap, switch, gateway counts)
- Site name lookup for user-friendly output
- Progress display showing org-by-org processing

## [26.02.05.05.45] - 2026-02-05

### Changed

- Site scope selection: 'All sites' or specific site selection
- Version selection per model with automatic grouping by target version
- Full upgrade strategy support (big_bang, serial, canary, rrm)
- Dry-run mode with --dry-run flag
- API efficiency display showing call savings vs site-level approach

## [26.02.05.04.35] - 2026-02-05

### Changed

- API call estimate now correctly counts unique versions per site
- Upgrade output shows version with list of models being upgraded

## [26.02.05.04.20] - 2026-02-05

### Changed

- Confirmation screen now shows total upgrade API calls
- Per-site breakdown shows device count and call reason
- Note about additional auto-upgrade API calls if step 9 is used

## [26.02.05.04.02] - 2026-02-05

### Changed

- MSP selection now supports selecting multiple MSPs in one workflow
- Organization selection per MSP with consistent selection patterns
- Site selection per org with configurable ranges and pagination
- Upgrade plan summary shows MSPs, orgs, and sites before confirmation
- Dry-run mode skips confirmation and shows simulation banner

## [26.02.05.03.18] - 2026-02-05

### Changed

- FirmwareManager now detects MSP privileges and shows mode [3] when available
- Sequential processing with per-org confirmation and interrupt handling
- Upgrade summary report showing completed/failed/interrupted organizations

## [26.02.02.23.15] - 2026-02-02

### Changed

- Session-based authentication with cookie management for MSP API endpoints
- Two-factor authentication (2FA) support in interactive login flow
- Cloud selection during interactive login (Global, EU, GovCloud, Custom)
- MSP organization export includes msp_id and msp_name context fields

## [26.02.02.21.06] - 2026-02-02

### Changed

- Family-based version selection: Select one version per ap_type family, applies to all models
- AP models grouped by ap_type from /api/v1/const/device_models (ruby, jewel, aphx, etc.)
- Universal version detection aggregates firmware compatibility across all API entries
- Semantic version sorting (0.14.x now correctly sorts above 0.8.x)
- Auto-upgrade scheduling: Added day_of_week and time_of_day options

## [26.01.28.19.03] - 2026-01-28

## [26.01.28.18.55] - 2026-01-28

## [26.01.28.18.51] - 2026-01-28

### Changed

- Menu 90 'All sites' mode: Now displays full site list before confirmation prompt
- AP Discovery Summary: Enhanced to show per-site model breakdown (e.g., 'Site-A: 12 APs (AP45:8, AP34:4)')
- Clarified that sites with no APs or all APs at target will be skipped

## [26.01.28.18.46] - 2026-01-28

## [26.01.28.18.40] - 2026-01-28

## [26.01.28.18.30] - 2026-01-28

## [26.01.18.02.10] - 2026-01-18

## [26.01.17.23.15] - 2026-01-17

## [26.01.17.23.00] - 2026-01-17

## [26.01.17.22.45] - 2026-01-17

## [26.01.17.22.30] - 2026-01-17

## [26.01.17.22.15] - 2026-01-17

## [26.01.17.22.00] - 2026-01-17

## [26.01.17.21.45] - 2026-01-17

## [26.01.17.21.30] - 2026-01-17

## [26.01.17.20.45] - 2026-01-17

## [26.01.17.19.30] - 2026-01-17

## [26.01.17.19.15] - 2026-01-17

## [26.01.17.18.30] - 2026-01-17

## [26.01.17.17.53] - 2026-01-17

## [26.01.17.17.24] - 2026-01-17

## [25.07.10.08.00] - 2025-07-10

## [25.07.10.07.25] - 2025-07-10

## [25.07.10.05.30] - 2025-07-10

## [25.07.10.05.15] - 2025-07-10

## [25.07.10.05.00] - 2025-07-10

## [25.07.09.23.25] - 2025-07-09

## [25.07.09.23.15] - 2025-07-09

## [25.07.09.23.00] - 2025-07-09

## [25.07.09.22.45] - 2025-07-09

## [25.07.09.22.15] - 2025-07-09

## [25.07.09.22.08] - 2025-07-09

## [25.07.09.22.00] - 2025-07-09

## [26.01.16.21.30] - 2026-01-16

## [26.01.16.21.00] - 2026-01-16

## [26.01.16.20.30] - 2026-01-16

## [26.01.16.20.00] - 2026-01-16

## [26.01.16.19.30] - 2026-01-16

## [26.01.16.19.15] - 2026-01-16

## [26.01.16.18.45] - 2026-01-16

## [26.01.16.05.30] - 2026-01-16

## [26.01.15.22.45] - 2026-01-15

### Documentation

- Updated interactive_fetch_device_data_to_csv docstring to support config object pattern

## [26.01.15.21.30] - 2026-01-15

## [26.01.16.00.15] - 2026-01-16

### Documentation

- Added dataclasses import and config classes section near top of MistHelper.py
- Updated function docstrings to mark individual parameters as deprecated in favor of config objects

## [26.01.15.23.56] - 2026-01-15

### Documentation

- Compliance audit: Applied copilot-instructions.md naming and ASCII guidelines

## [26.01.15.16.30] - 2026-01-15

## [26.01.12.16.41] - 2026-01-12

## [26.01.09.18.45] - 2026-01-09

## [26.01.09.17.30] - 2026-01-09

## [25.01.09.19.00] - 2025-01-09

## [26.01.08.15.32] - 2026-01-08

## [25.12.22.20.30] - 2025-12-22

## [25.12.22.19.54] - 2025-12-22

## [25.12.22.19.30] - 2025-12-22

## [25.12.22.18.00] - 2025-12-22

## [25.12.22.17.30] - 2025-12-22

## [25.12.22.13.45] - 2025-12-22

### Documentation

- Added Python 3.13 and mistapi 0.59+ requirements to copilot-instructions.md
- Added Runtime Requirements section to agents.md specifying Python 3.13+ and mistapi 0.59+

## [25.01.21.15.30] - 2025-01-21

### Documentation

- Added Data Directory Permissions section to README troubleshooting
- Updated agents.md with CRITICAL permission requirements in deployment pipeline
- Updated copilot-instructions.md with permission fix between image pull and container restart

## [25.12.15.14.45] - 2025-12-15

### Documentation

- README Section 1 - Updated operation count from 97 to 112 menu entries
- README Section 1 - Updated line count from 22k to 44k lines
- README Section 1 - Updated date to 2025-12-15
- README Section 3 - Removed non-existent run-misthelper.py from directory table
- README Section 6 - Added missing CLI flags: --dry-run, --tui, --testinteractive
- README Section 8 - Fixed menu 40-44 description to mention rogue client/AP detections
- README Section 8 - Added missing menu items 101 (TUI), 111 (Clone Templates), 112 (Maps Manager)
- README Section 14 - Updated container commands to use direct podman commands instead of run-misthelper.py

## [25.12.12.17.10] - 2025-12-12

## [25.12.12.17.03] - 2025-12-12

## [25.12.12.21.55] - 2025-12-12

### Changed

- Zone name input field appears when Zone mode is selected
- Clear All Drawings button with guidance to use eraser tool
- Success/error feedback messages for all save operations

## [25.12.12.21.50] - 2025-12-12

### Changed

- Added coordinate sample logging to verify refresh data
- Added warning log if Clients trace not found during refresh
- Removed visibility toggle override during refresh to preserve user settings

## [25.12.12.21.35] - 2025-12-12

### Changed

- Changed browser tab title from 'Dash' to 'MistHelper Map Viewer'

## [25.12.12.21.30] - 2025-12-12

### Changed

- Set update_title=None on Dash app to prevent tab title flicker from 1-second countdown interval

## [25.12.12.21.20] - 2025-12-12

### Changed

- Upgraded refresh trace logging from debug to info level for visibility

## [25.12.12.17.15] - 2025-12-12

### Changed

- Moved live refresh controls from sidebar to header bar for better visibility
- Added countdown timers showing seconds until next client refresh and minutes:seconds until RF heatmap refresh
- Countdown updates every second when auto-refresh is enabled
- Compact refresh control panel with dark background in header

## [25.12.12.16.45] - 2025-12-12

### Changed

- dcc.Store component: stores site_id, map_id, PPM, and map dimensions for refresh callbacks
- dcc.Interval components: two separate intervals for clients (30s) and coverage (5min) with disabled-by-default state
- Callback architecture: separate callbacks for toggle, client refresh, and coverage refresh with proper state management
- API session reference: refresh callbacks use stored API session for authenticated requests

## [25.12.12.15.35] - 2025-12-12

### Changed

- Explicit warning in console when map_ppm is 0 or missing

## [25.12.12.15.30] - 2025-12-12

### Changed

- Uses first 10 clients with both pixel and meter coordinates to calculate average PPM
- Logs PPM validation results (pass/mismatch) with exact values for debugging

## [25.12.12.14.30] - 2025-12-12

### Changed

- Added heatmap coordinate debug logging to script.log
- Logs coverage X/Y ranges in both pixels and meters for PPM validation

## [25.12.09.14.44] - 2025-12-09

### Documentation

- README and READY_FOR_MIGRATION license references now call out AGPL-3.0-only so downstream consumers see the correct terms immediately.

## [25.12.04.14.15] - 2025-12-04

### Changed

- Heatmap interpolation: zsmooth='best' provides smooth color transitions between grid points
- Gap interpolation: connectgaps=True fills in missing grid cells for complete coverage visualization
- Debug logging: added per-device orientation logging to script.log for troubleshooting
- Coordinate system fix: corrected AP orientation angle conversion (Mist 0°=north to math coordinates with Y-axis flip)

## [25.12.04.13.15] - 2025-12-04

### Changed

- RSSI tooltip: hover over grid cells shows Max RSSI and Avg RSSI in dBm
- Grid size calculation: coverage gridsize (meters) converted to pixels for proper visualization scale
- Error handling: graceful degradation when coverage API unavailable (backend database issues, no data)
- Backend error detection: psycopg2/database errors logged as warnings, not errors (expected transient issues)

## [25.12.04.13.07] - 2025-12-04

### Changed

- Device marker colors: dynamic color array based on individual device status instead of static type-based colors
- Crosshair orientation indicators: now use status-based colors matching device state
- Device labels: border colors match device status for consistent visual feedback
- Type-specific status colors: APs (green/red/orange), Switches (cyan/red/orange), Gateways (magenta/red/orange)

## [25.12.03.17.30] - 2025-12-03

### Changed

- Larger crosshair indicators: increased from 25px to 40px for better visibility of device orientation markers
- Larger orientation dots: increased from 10px to 16px with thicker lines (3px width) for improved visual clarity
- Increased dot distance: orientation direction indicator moved from 35px to 50px from device center
- Annotation toggle control: all text labels (zones, devices, clients, beacons) now hide/show with their parent layers
- Unified visibility management: annotations and traces both controlled by layer toggle callbacks

## [25.12.03.17.15] - 2025-12-03

### Changed

- Multi-checklist architecture: 5 separate checklists for granular layer management
- Client type detection: automatic WiFi/Wired classification based on SSID field presence
- Coverage radius calculation: dynamic radius based on vBeacon power level (-12 to +4 dBm range)
- Client-AP linking: automatic AP lookup by MAC address for association line drawing
- Mesh topology detection: automatic mesh uplink discovery from device mesh_uplink field
- Layer toggle callback: enhanced to handle multiple checklist inputs with combined layer array
- Map statistics: added vBeacon and BLE beacon counts to Map Info panel
- Add vBeacon/Beacon buttons: header toolbar buttons with green/cyan color coding

### Documentation

- Layer controls now match Mist portal Location Settings panel organization
- Client separation provides visual distinction between WiFi and Wired network access

## [25.12.03.16.47] - 2025-12-03

### Changed

- Auto-Zone UI: prominent purple button with robot emoji in header utilities bar
- Zone checklist: all zones checked by default, styled with dark theme
- Zone selection feedback: green highlighted text shows selected zone details
- Edit zone placeholder: guides to Mist API updateSiteMap for vertex modification
- Remove zone warning: red destructive warning for zone deletion operations
- Click handling: detects zone clicks from hovertext and displays zone information

### Documentation

- Added Location Zones panel matching Juniper Mist portal zone management interface
- Auto-Zone feature provides AI-powered automatic zone creation from wall analysis

## [25.12.03.16.44] - 2025-12-03

### Changed

- Drawing Tools UI: color-coded buttons matching element types (magenta/cyan/orange/red)
- Tool guidance: status messages direct users to appropriate toolbar drawing tools
- Destructive warnings: delete buttons highlighted in red with bold warnings
- Sidebar reorganization: Drawing Tools section above Measurement Tools for better workflow
- Compact layout: measurement tools condensed with smaller font for space efficiency

### Documentation

- Added Drawing Tools panel matching Juniper Mist portal map editor interface
- Quick-action buttons provide shortcuts and guidance for common map editing tasks

## [25.12.03.16.41] - 2025-12-03

### Changed

- Validation path styling: magenta color (#ff00ff) with dotted line style for clear differentiation
- Hover information: shows path name and point count on mouseover
- Path naming: displays custom path names or defaults to 'Path 1', 'Path 2', etc.
- Coordinate processing: extracts x,y from path coordinate arrays with validation
- Logging integration: debug messages for path rendering with point counts

### Documentation

- Added validation paths feature matching Juniper Mist portal site survey path capability
- Validation paths used for Wi-Fi coverage testing and performance analysis along routes

## [25.12.03.16.39] - 2025-12-03

### Changed

- Utilities UI redesign: replaced dropdown with horizontal button bar for cleaner interface
- Direct action buttons: Change Image, Remove Image, Rename, Delete as individual buttons in header
- Visual hierarchy: Delete button highlighted in red (#ff4444) for critical action awareness
- Improved spacing: buttons in header bar with inline status messages
- Darker header: #2a2a2a background for better contrast with map area

## [25.12.03.16.38] - 2025-12-03

### Changed

- Utilities UI: dropdown positioned in header top-right matching Mist portal layout
- Action feedback: status messages display warnings for destructive operations
- Color coding: orange for caution (change/rename), red for destructive (remove/delete)
- Logging integration: all utility actions logged with map_id for audit trail
- Header redesign: title and utilities dropdown in flex layout with purple border separator

### Documentation

- Added Utilities dropdown matching Juniper Mist portal map management interface
- Placeholder implementations note required API integrations for full functionality

## [25.12.03.16.35] - 2025-12-03

### Changed

- Set Origin UI: toggle button with mode indicator in sidebar Tools section
- Visual feedback: button highlights in purple when origin-setting mode is active
- Status display: shows current origin coordinates and confirmation when set
- Origin initialization: loads existing origin_x/origin_y from map data if present
- Interactive workflow: click button to activate, click map to set, click button again to exit mode

### Documentation

- Added Set Origin feature matching Juniper Mist portal coordinate system alignment capability

## [25.12.03.16.32] - 2025-12-03

### Changed

- Set Scale UI: input field for length in meters + button in sidebar Tools section
- Workflow guidance: numbered steps (1. Draw line, 2. Enter length) for clear user instructions
- Dynamic PPM: measurement callback reads current PPM from figure metadata instead of static value
- Scale validation: prevents setting scale with invalid/missing length or without drawn line
- Professional styling: scale input and button match dark theme with purple accent (#667eea)

### Documentation

- Added Set Scale feature matching Juniper Mist portal UI/UX for floor plan calibration

## [25.12.03.16.30] - 2025-12-03

### Changed

- Map viewer rotation indicators: replaced triangular wedges with Mist-style crosshair + directional dot
- Crosshair: 25px horizontal and vertical lines at device center (always visible)
- Directional dot: 10px marker positioned 35px from center at orientation angle (only if angle != 0)
- Crosshair color matches device type (green for APs, orange for switches, magenta for gateways)
- Dot shows orientation angle on hover for quick reference

### Documentation

- Updated rotation indicator design to match Juniper Mist portal UI/UX patterns

## [25.12.03.16.22] - 2025-12-03

### Changed

- Map viewer text rendering: switched from mode='markers+text' to mode='markers' + separate annotations
- Annotation-based labels: support bgcolor, bordercolor, borderwidth, and borderpad for professional appearance
- Device labels: positioned 15px above markers with device-type-specific colored borders (green/orange/magenta)
- Client labels: positioned 10px above markers with smaller font and green styling
- Zone labels: automatically positioned at min(x), min(y) coordinates (upper-left bounding box corner)
- Improved label positioning: all labels use xanchor/yanchor for precise placement without overlap

### Documentation

- Added technical note in CSS explaining why text-shadow doesn't work on Plotly SVG elements
- Removed obsolete text-shadow CSS rules that had no effect on map labels

## [25.12.02.20.30] - 2025-12-02

### Changed

- Clone operation uses temporary files for image download/upload to avoid filesystem pollution
- Automatic cleanup of temporary files in all code paths (success, failure, exception)
- Enhanced error handling with separate warnings for download vs upload failures
- User-friendly progress messages at each stage: select, download, create, upload, complete
- Clone confirmation shows full plan before execution including image copy status
- Educational note: zones are site-level objects (not map objects) requiring separate cloning

### Documentation

- Added comprehensive docstring explaining full clone capability including image/walls/paths/zones
- Clone summary clearly shows which elements were successfully copied

## [25.12.02.18.00] - 2025-12-02

### Changed

- Database schema - Added natural primary key strategies for listSiteMaps and getSiteMap with proper indexes
- Interactive sub-menu - Single entry point (Menu 112) with 0 to return to main menu, organized by operation category
- Safety features - Input validation, EOF/interrupt handling, confirmation prompts for destructive operations (placeholders)
- Image handling - JWT token URL support, automatic format detection (png/jpg), organized directory structure by site
- Progress indicators - tqdm progress bars for bulk site/map operations with descriptive labels
- Error handling - Graceful per-site error logging without halting bulk operations, comprehensive exception tracking

### Documentation

- Updated operation count from 111 to 112 total menu entries
- Added Maps Manager category section to menu_actions documentation
- Documented map database strategies in ENDPOINT_PRIMARY_KEY_STRATEGIES configuration

## [25.12.02.17.15] - 2025-12-02

### Documentation

- Updated agents.md Git workflow - clarified that staging alone does not create checkpoints
- Added minimal Git workflow instructions for local commits and rollback procedures
- Removed verbose workflow examples, keeping only essential commands for AI agents

## [25.12.02.16.43] - 2025-12-02

### Documentation

- Added detailed docstrings for clone_gateway_templates_by_state_and_country() explaining address parsing logic
- Documented support for US, CA, MX, CR, PA, HN, GT, and other Central American address formats
- Updated menu option tables with entry 111 for gateway template cloning by geography
- Documented --testinteractive and --dry-run CLI flag usage in help text
- Noted limitations: Multi-word state names (e.g., 'Quintana Roo') may capture last word only

## [25.12.02.11.10] - 2025-12-02

### Documentation

- Added code comments explaining mistapi's expectation of comma-separated token string
- Documented that mistapi handles token rotation internally when configured correctly

## [25.12.02.11.05] - 2025-12-02

## [25.12.02.11.15] - 2025-12-02

### Documentation

- Identified that error occurs when mistapi library validates tokens against Mist API
- Token validation failure suggests tokens need to be refreshed or regenerated
- mistapi library bug: does not handle missing 'privileges' key in API response gracefully

## [25.12.02.11.00] - 2025-12-02

## [25.12.01.17.40] - 2025-12-01

### Changed

- Menu 14 (fast mode): Added extensive debug logging to track data type issues in parallel processing
- Added type validation logging for start_time, end_time, and duration calculations
- Added logging for successful_results and failed_sites return types from execute_with_connection_pool_management
- Added per-result type checking in flattening loop with warnings for unexpected types
- Added site tuple structure validation logging to diagnose dict vs tuple issues

## [25.12.01.17.35] - 2025-12-01

## [25.12.01.17.30] - 2025-12-01

## [25.12.01.17.20] - 2025-12-01

### Changed

- Enhanced error handling in fetch_and_display_api_data with three-layer defense against data loss
- Added response structure validation and logging for debugging unexpected API formats
- Automatic recovery attempts from alternate response structures (response.data['data'], direct lists)
- User-friendly messages explain partial data saves and recovery attempts
- Detailed debug logs capture response types and available keys for troubleshooting

### Documentation

- Updated export_device_port_stats_to_csv docstring with performance optimization notes
- Added fetch_and_display_api_data docstring explaining enhanced error handling layers
- Documented safety features: emergency saves, structure validation, graceful degradation

## [25.11.25.13.49] - 2025-11-25

## [25.11.25.13.40] - 2025-11-25

### Changed

- Pre-flight analysis shows assignment plan before execution
- Exports successful assignments to SuccessfulAPProfileAssignments.csv with AP/profile details
- Exports failed assignments to FailedAPProfileAssignments.csv for troubleshooting
- Exports skipped APs to SkippedAPsNoMatchingProfile.csv for profile creation planning
- Comprehensive summary report showing successful, failed, and skipped counts
- Detailed logging for each AP assignment with full error context
- Gracefully skips APs without model information instead of failing

### Documentation

- Menu 110 marked as DESTRUCTIVE operation requiring 'ASSIGN' confirmation
- Pre-assignment analysis shows counts of APs with/without matching profiles
- Operation count updated from 110 to 111 total menu operations
- Lists APs that will be skipped due to missing matching Device Profiles

### Security

- Requires explicit uppercase 'ASSIGN' confirmation before device assignment
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.3s delay between AP assignments

## [25.11.25.13.23] - 2025-11-25

### Changed

- Progress display shows unique AP models discovered across organization
- Exports successful creations to CreatedAPModelDeviceProfiles.csv with model/profile/ID details
- Exports failures to FailedAPModelDeviceProfiles.csv for troubleshooting
- Comprehensive summary report showing profiles created, failed, and skipped (existing)
- Detailed logging for each profile creation with full error context
- Warns about devices with missing model information for inventory visibility

### Documentation

- Menu 109 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation
- Device Profiles created with minimal payload to ensure all settings inherit/auto by default
- Operation count updated from 109 to 110 total menu operations
- Devices without model information are logged and reported but do not block execution

### Security

- Requires explicit uppercase 'CREATE' confirmation before profile creation
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.5s delay between Device Profile creations

## [25.11.25.12.28] - 2025-11-25

### Changed

- Progress display shows country distribution and site counts per country
- Exports successful assignments to SuccessfulRFTemplateAssignments.csv with site/template details
- Exports failures to FailedRFTemplateAssignments.csv for troubleshooting
- Comprehensive summary report showing templates created, sites assigned, failures, and skipped sites
- Detailed logging for each template creation and site assignment with full error context
- Template reuse logic - skips creation if RF-{country} template already exists

### Documentation

- Menu 108 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation
- RF template configuration uses default/auto settings: band_24 (20MHz auto), band_5 (40MHz auto), band_6 (80MHz auto)
- Operation count updated from 108 to 109 total menu operations
- Sites without country codes are skipped with warning message and logged

### Security

- Requires explicit uppercase 'CREATE' confirmation before template creation and site assignment
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.5s delay between template creations and 0.3s between site assignments

## [25.11.25.14.30] - 2025-11-25

### Changed

- Progress display shows site creation status with index counter
- Exports successful creations to CreatedTestSites.csv with site IDs
- Exports failures to FailedTestSites.csv for troubleshooting
- Comprehensive summary report showing total/success/failure counts
- Detailed logging for each site creation attempt with full error context

### Documentation

- Menu 107 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation
- CSV structure documented: name (required), address, country_code, lat, lng, timezone, notes
- Operation count updated from 107 to 108 total menu operations

### Security

- Requires explicit uppercase 'CREATE' confirmation before execution
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.5s delay between site creations to avoid API throttling

## [25.11.25.09.30] - 2025-11-25

### Documentation

- Menu 25: Updated function docstring to document all three output files (weekly, summary, master)

## [25.11.21.17.00] - 2025-11-21

## [25.11.13.16.15] - 2025-11-13

### Documentation

- Menu 104: Updated docstring explains device override preservation critical safety feature
- Menu 104: Console output clearly shows two-phase migration: templates then device overrides
- Menu 104: Explains risk of static IP loss without device override migration

## [25.11.13.15.45] - 2025-11-13

## [25.11.13.14.30] - 2025-11-13

### Documentation

- Menu 103: CRITICAL overrides (DHCP->Static) clearly flagged for manual review priority
- Menu 103: User guidance explains static IPs will be lost if template DHCP applied without device overrides
- Menu 103: Console output shows breakdown of override severity levels with actionable next steps

## [25.10.30.17.50] - 2025-10-30

## [25.10.30.19.50] - 2025-10-30

## [25.10.29.13.55] - 2025-10-29

## [25.10.29.00.15] - 2025-10-29

### Changed

- Converted remaining progress messages to logging (only user-facing data remains as print)
- Debug logs now show template assignment determination before WLAN fetching
- Added logging for org WLAN filtering process with template_id matching

### Documentation

- Clarified architecture: WLAN templates are configuration containers, not WLAN collections
- Org WLANs exist independently and optionally reference templates for config inheritance
- Templates define what configuration to apply; WLANs reference them via template_id

## [25.10.28.23.15] - 2025-10-28

### Changed

- Debug output written to log file instead of console for cleaner user experience
- Detailed logging shows applies.site_ids, applies.sitegroup_ids, applies.wxtag_ids, applies.org_id
- Shows WLAN structure type (list vs dict) and WLAN count per template in debug logs

## [25.10.28.22.30] - 2025-10-28

### Documentation

- Site Templates (/sitetemplates): Full site configs with embedded WLANs
- WLAN Templates (/templates): WLAN-specific templates assignable to sites
- Org WLANs (/wlans): Standalone org-level WLANs (not template-based)

## [25.10.28.22.09] - 2025-10-28

## [25.10.28.21.00] - 2025-10-28

### Changed

- Enhanced WLAN inheritance detection across three levels: site, site_template, org_template
- Org WLAN template modifications now show clear impact scope (which sites affected)
- Improved warning messages distinguish between site template and org template changes
- API routing automatically selects correct update endpoint based on WLAN source level

## [25.10.21.15.00] - 2025-10-21

### Changed

- Results grid uses Rich Table with DOUBLE box style for prominence
- Columns auto-detected from first result item keys
- Scroll position tracked with results_scroll_offset state variable
- Help text dynamically shows grid controls when viewing results
- Grid appears automatically after successful API call with tabular data
- Execution state now includes 'viewing_results' for grid display mode

## [25.10.21.14.55] - 2025-10-21

### Changed

- Parameter submission logic clarified with explicit handling for required vs optional
- Debug logging differentiates between 'stored' and 'skipped' parameters
- API calls now only include parameters explicitly provided by user or auto-filled from .env

## [25.10.21.14.50] - 2025-10-21

### Changed

- Debug JSON files now include both raw_response (complete) and parsed_data (extracted)
- Object introspection via dir() and getattr() captures all non-private attributes
- Handles nested objects recursively to preserve full response hierarchy
- Graceful fallback to string representation for non-serializable types

## [25.10.21.14.45] - 2025-10-21

### Changed

- Results show structure depth with indentation (dict keys, list items, nested objects)
- Dictionary items display with type and count header (e.g., 'results: dict (5 keys)')
- List items show count and preview first N items with key-value pairs
- Nested structures recursively formatted up to 3 levels deep
- Sample item display shows first 3 key-value pairs per dict in list
- Value strings truncated to 60 chars in nested views, 200 chars at top level

## [25.10.21.14.30] - 2025-10-21

## [25.10.21.12.18] - 2025-10-21

### Changed

- Improved result display - shows sample keys and values for dict items in lists
- Better preview formatting - displays first 3 items with key-value pairs for API results
- Result metadata - shows function name, parameters (redacted), timestamp, and parsed data structure
- Debug file notifications - output panel shows where debug results were saved
- Tip messages - suggests viewing debug logs for large datasets

## [25.10.21.12.12] - 2025-10-21

### Changed

- Parameter prompts now display in prominent input boxes with clear headers
- Box-style input prompts show parameter name, requirement status, and default value
- Current input highlighted with white-on-gray background for visibility
- Previously entered parameters shown below with checkmarks
- Progress indicator shows N/M parameters completed
- Visual hierarchy: Current prompt (bold yellow box) → Previous inputs (dim with checkmarks)

## [25.10.21.12.09] - 2025-10-21

### Changed

- TUI stays active during function execution - no screen clearing or context switches
- Output panel shows execution progress (prompting → executing → completed)
- Previously entered parameters visible while prompting for next parameter
- Backspace support for editing input inline
- Escape cancels execution and returns to navigation mode
- Help text changes based on mode (navigation vs input)
- Smart result formatting in output panel (type, count, preview)
- Input mode clearly indicated with magenta Output panel border

## [25.10.21.12.04] - 2025-10-21

### Changed

- TUI now automatically uses values from .env file for function parameters
- Parameters like org_id, site_id, device_id automatically filled from environment variables
- No need to manually enter org_id when executing functions if configured in .env
- Environment values displayed with [from .env] indicator for transparency

## [25.10.21.11.58] - 2025-10-21

### Changed

- Function execution no longer interferes with TUI display refresh cycle
- Ctrl+C during execution properly returns to TUI without freezing
- Terminal mode properly managed across Live() context transitions

## [25.10.21.11.52] - 2025-10-21

### Changed

- Smart result preview system - shows type, count, and sample items without converting entire result to string
- Lists/tuples: Shows item count and first 3 items with truncation indicators
- Dicts: Shows key count and first 5 keys for large dictionaries
- Strings: Truncates at 200 characters with length indicator
- Memory-safe handling: Never converts full result to string, uses repr() with limits
- Helpful tip displayed for large results (>10 items) suggesting use of main menu CSV/SQLite export options

### Security

- Result preview limits prevent memory exhaustion attacks from malformed API responses
- Safe repr() usage with character limits prevents infinite recursion or excessive memory use

## [25.10.21.11.49] - 2025-10-21

### Changed

- Added intelligent viewport scrolling - visible window follows cursor through item list
- Viewport height automatically calculated based on available panel height (minus borders)
- Selection stays centered in viewport when possible, adjusts near top/bottom boundaries
- Debug logging for viewport calculations when --debug flag is set (selection position, scroll range, visible items)

## [25.10.21.11.43] - 2025-10-21

## [25.10.21.17.30] - 2025-10-21

### Changed

- MistHelperTUI class redesigned with hierarchical navigation state (current_path, breadcrumb)
- Dynamic discovery using Python inspect and importlib for package introspection
- Parameter prompting system with required/optional detection and default value support
- Result display with formatted preview and error handling
- Automatic apisession initialization and injection for API call execution
- Drill-down navigation (Enter on modules) and back navigation (Escape key)
- Real-time function signature and documentation display
- Educational design - learn API structure by exploring

## [25.10.14.17.00] - 2025-10-14

### Fixed

- Downloads now complete reliably without threading complexity

### Removed

- Queue-based background downloader (replaced with simpler synchronous approach)

## [25.10.07.16.15] - 2025-10-07

### Fixed

- Wired client API module - Corrected import path to mistapi.api.v1.sites.wired_clients (separate module from wireless clients)
- AttributeError on wired client fetch - Resolved 'module has no attribute searchSiteWiredClients' error
- Verified: Wireless clients use mistapi.api.v1.sites.clients.searchSiteWirelessClients
- Verified: Wired clients use mistapi.api.v1.sites.wired_clients.searchSiteWiredClients

## [25.10.06.18.30] - 2025-10-06

### Fixed

- Corrected session attribute in PCAP polling functions
- Site PCAP polling used self.apisession instead of self.mist_session (PacketCaptureManager attribute)
- Org PCAP polling used self.apisession instead of self.mist_session (PacketCaptureManager attribute)
- Changed self.apisession to self.mist_session in _wait_and_download_pcap() (line 4072)
- Changed self.apisession to self.mist_session in _wait_and_download_pcap_org() (line 4212)
- PCAP downloads now work correctly - polling no longer throws AttributeError
- Root cause: PacketCaptureManager.__init__ stores session as self.mist_session, not self.apisession

## [25.10.06.18.25] - 2025-10-06

### Changed

- Added comprehensive debug logging to PCAP download polling functions
- Site-level PCAP polling now logs every poll attempt with detailed capture state
- Org-level PCAP polling now logs every poll attempt with detailed capture state
- Logs response status code, number of captures returned, and capture found/not found status
- When capture found, logs all relevant fields: enabled, format, type, duration, expiry, timestamp, pcap_url
- Logs when pcap_url is NOT SET YET vs when it becomes available
- Logs available capture IDs when our capture is not found in the list
- Exception handling now uses exc_info=True for full traceback in logs
- Debug logs will reveal why PCAP downloads timeout (capture not found, pcap_url never set, API errors)
- Run with --debug flag to see detailed polling behavior in script.log

## [25.10.06.18.20] - 2025-10-06

### Fixed

- Corrected mistapi function names for listing packet captures
- Changed listSitePcapCaptures to correct listSitePacketCaptures (3 occurrences)
- Changed listOrgPcapCaptures to correct listOrgPacketCaptures (1 occurrence)
- Previous function names caused AttributeError when checking for existing captures
- Pre-check for existing captures now works correctly before launching new ones
- Locations: Single AP pre-check, multi-AP pre-check, site PCAP polling, org PCAP polling
- Function names now match mistapi SDK and Mist API operationId values
- operationId: listSitePacketCaptures and listOrgPacketCaptures per OpenAPI spec

