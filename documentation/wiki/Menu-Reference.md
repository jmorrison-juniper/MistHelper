# Menu Reference

Operation Count: MistHelper currently defines 163 actionable menu entries (0-162) with some gaps for future expansion.

Below is the authoritative list derived directly from `menu_actions` in code. WIP = unstable schema, DESTRUCTIVE = requires explicit user confirmation.

## Important Notes

- Options 14 and 18 are resource-intensive and may take a long time during large exports.
- Options 63-65 are intentionally marked WIP and may evolve as the bulk-history workflows settle.
- Destructive ranges should never be scripted unattended without explicit human review and confirmation.

## Operation Categories

| Range | Category | Summary |
|---|---|---|
| 0 | Exit | Exit and session control |
| 1-4 | Alarms & Definitions | Org alarms, device events, audit logs, and gateway management IPs |
| 5-8 | WebSocket Commands | MAC table, forwarding table, routing table, and SSR/SRX routing tools |
| 9-10 | Packet Capture | Site and org packet capture workflows with WebSocket streaming |
| 11-15 | Org Inventory Core | Sites, inventory, device stats, port stats, and VPN peer stats |
| 16-19 | Gateway Exports | Synthetic tests, device lists, site settings, and test results |
| 20-28 | Location & Enrichment | Sites, gateways, devices, guests, VC stats, combined inventory, and WAN overrides |
| 29-34 | Site-Scoped | Per-site ports, clients, devices, stats, VC, and Wi-Fi clients |
| 35-39 | Template Bundles | All templates plus network, RF, AP, and switch subsets |
| 40-44 | Clients & Security | Wireless and wired clients, security events, rogue clients, and rogue APs |
| 45-53 | Configuration | Licenses, PSKs, webhooks, WLANs, beacons, maps, zones, and insights |
| 54-59 | Admin & Org Mgmt | API tokens, admins, MSP info, SSO, usage, and MX Edge |
| 60-62 | Monitoring / Analytics | Firmware status, inventory comparison, and Marvis troubleshooting |
| 63-65 | WIP Bulk History | 52-week device events, 52-week audit logs, and gateway configs |
| 66-69 | Insights API | Org SLE metrics, site summaries, site insights, and client insights |
| 70-74 | Interactive Views | Site selection, inventory browser, device stats, tests, and config views |
| 75-76 | Continuous Loops | Continuous collection and refresh loops |
| 77-78 | Processing & Support | SFP merge and support package generation |
| 79-80 | CLI / WebSocket | Interactive CLI shell and ARP via WebSocket |
| 81-86 | Advanced Insights | Device insights and anomaly event exports |
| 87-89 | WebSocket Device Commands | Real-time ping, ARP, and service ping streams |
| 90-100 | Destructive Operations | Firmware upgrades, reboots, VC operations, SSH runner, and switch/SSR firmware |
| 101-114 | Advanced Configuration | TUI, RADIUS timers, WAN2 migration, template config, test-site creation, WAN probe, and maps |
| 115-121 | Access / MSP / Health | Interactive login, org firmware, MSP inventory, auto-upgrade, and health analysis |
| 122-160 | Device Utilities & Reports | Bulk WLAN config, device commands, clear actions, DHCP, snapshots, offline reports, SSID consolidation, and E911 |

## Full Menu Table

| Menu ID | Short description | Safety | Callable/Handler |
|---:|---|---|---|
| 0 | Exit MistHelper | Safe | `lambda: sys.exit(0)` |
| 1 | Export all organization alarms from the past day | Safe | `OrgAlarmEventExporter.alarms` |
| 2 | Export all device events from the past 24 hours | Safe | `OrgAlarmEventExporter.device_events` |
| 3 | Export audit logs for the organization (last 24 hours) | Safe | `lambda: OrgExportUtils.audit_logs(full_history=False)` |
| 4 | Export gateway management overlay IPs grouped by template association | Safe | `lambda fast=False: GatewayExportUtils.management_ips(fast=fast)` |
| 5 | Show MAC table on switch device via WebSocket (Layer 2 switching table) | Safe | `WebSocketCommands.show_mac_table` |
| 6 | Show forwarding table on gateway device via WebSocket (Layer 3 routing table) | Safe | `WebSocketCommands.show_forwarding_table` |
| 7 | Show routing table on switches via WebSocket (Switch L3 routing - BGP/OSPF/Static) | Safe | `WebSocketCommands.show_routing_table` |
| 8 | Show SSR/SRX routing table via dedicated API (128T/SRX gateways - Advanced BGP analysis) | Safe | `WebSocketCommands.show_ssr_routes` |
| 9 | Start Site Packet Capture - Wireless/Wired/Gateway/Scan captures with WebSocket streaming | Interactive | `lambda: PacketCaptureManager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).start_site_packet_capture()` |
| 10 | Start Organization Packet Capture - MxEdge captures for org-level Mist Edges only | Safe | `lambda: PacketCaptureManager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).start_org_packet_capture()` |
| 11 | Export a list of all sites in the organization | Safe | `OrgSiteExporter.sites` |
| 12 | Export the full inventory of devices in the organization | Safe | `OrgInventoryExporter.inventory` |
| 13 | Export statistics for all devices in the organization | Safe | `OrgDeviceStatsExporter.device_stats` |
| 14 | Export port-level statistics for switches and gateways | Safe | `OrgDeviceStatsExporter.device_port_stats` |
| 15 | Export VPN peer path statistics for the organization | Safe | `OrgDeviceStatsExporter.vpn_peer_stats` |
| 16 | Export synthetic test results for all gateways | Safe | `GatewayTestExporter.synthetic_tests` |
| 17 | Export a list of all devices in the organization | Safe | `OrgInventoryExporter.devices` |
| 18 | Export configuration settings for all sites | Safe | `SiteConfigExporter.settings` |
| 19 | Export all synthetic test results (including speed tests) for gateways | Safe | `GatewayTestExporter.test_results_by_site` |
| 20 | Export a list of sites with location and timezone info | Safe | `OrgSiteExporter.sites_with_location` |
| 21 | Export a list of gateways with associated site and address info | Safe | `OrgInventoryExporter.gateways_with_site_info` |
| 22 | Export a list of all devices with associated site and address info | Safe | `OrgInventoryExporter.devices_with_site_info` |
| 23 | Export all current guest users and last 7 days of historical guests to CSV | Safe | `lambda: (OrgSiteExporter.current_guests(), OrgSiteExporter.historical_guests())` |
| 24 | Export all switch virtual chassis (VC/stacking) stats to CSV | Safe | `OrgDeviceStatsExporter.switch_vc_stats` |
| 25 | Export combined inventory with site and address info by calendar week | Safe | `OrgInventoryExporter.combined_inventory_with_site_info` |
| 26 | Export gateway templates from the organization | Safe | `GatewayExportUtils.templates` |
| 27 | Export all sites using the 'list' sites API endpoint (to SiteList_ListAPI.csv, only if not already present) | Safe | `OrgSiteExporter.sites_list_api` |
| 28 | Find gateway ports overridden from template (outliers for compliance correction) | Safe | `lambda fast=False: GatewayExportUtils.with_wan_overrides(fast=fast)` |
| 29 | Export port statistics for a selected site | Safe | `SiteDeviceExporter.port_stats` |
| 30 | Export client statistics for a selected site | Safe | `SiteClientExporter.clients` |
| 31 | Export device list for a selected site | Safe | `SiteDeviceExporter.devices` |
| 32 | Export device statistics for a selected site | Safe | `SiteDeviceExporter.device_stats` |
| 33 | Export virtual chassis information for a selected switch device | Safe | `SiteDeviceExporter.device_virtual_chassis` |
| 34 | Export currently connected WiFi clients and session data for a selected site to SiteWiFiClients.CSV | Safe | `SiteClientExporter.wifi_clients` |
| 35 | Export all organization templates (gateway, network, RF, site, AP) | Safe | `OrgTemplateExporter.all_templates` |
| 36 | Export network template information for the organization | Safe | `OrgTemplateExporter.network_templates` |
| 37 | Export RF template information for the organization | Safe | `OrgTemplateExporter.rf_templates` |
| 38 | Export AP template information for the organization | Safe | `OrgTemplateExporter.ap_templates` |
| 39 | Export switch template information for the organization | Safe | `OrgTemplateExporter.switch_templates` |
| 40 | Export wireless client statistics for the organization | Safe | `OrgClientSecurityExporter.wireless_clients` |
| 41 | Export wired client statistics for the organization | Safe | `OrgClientSecurityExporter.wired_clients` |
| 42 | Export security events for the organization | Safe | `OrgClientSecurityExporter.security_events` |
| 43 | Export rogue client detections for the organization | Safe | `OrgClientSecurityExporter.rogue_clients` |
| 44 | Export rogue AP detections for the organization | Safe | `OrgClientSecurityExporter.rogue_aps` |
| 45 | Export license information for the organization | Safe | `OrgAdminExporter.licenses` |
| 46 | Export PSK (Pre-Shared Key) information for the organization | Safe | `OrgConfigExporter.psks` |
| 47 | Export webhook configuration for the organization | Safe | `OrgConfigExporter.webhooks` |
| 48 | Export WLAN configuration for the organization | Safe | `OrgConfigExporter.wlans` |
| 49 | Export WLAN configuration for a selected site | Safe | `SiteConfigExporter.wlans` |
| 50 | Export beacon information for a selected site | Safe | `SiteClientExporter.beacons` |
| 51 | Export map information for a selected site | Safe | `SiteConfigExporter.maps` |
| 52 | Export zone information for a selected site | Safe | `SiteConfigExporter.zones` |
| 53 | Export SLE (Service Level Experience) metrics insights for a selected site | Safe | `SiteExportUtils.insights` |
| 54 | Export API token information for the organization | Safe | `OrgAdminExporter.api_tokens` |
| 55 | Export administrator information for the organization | Safe | `OrgAdminExporter.admins` |
| 56 | MSP (Managed Service Provider) info - Displays guidance only (MSP data requires MSP-level API access, not org-level) | Safe | `OrgConfigExporter.msp` |
| 57 | Export SSO (Single Sign-On) information for the organization | Safe | `OrgAdminExporter.sso` |
| 58 | Export license usage information for the organization | Safe | `OrgAdminExporter.usage` |
| 59 | Export MX Edge information for the organization | Safe | `OrgConfigExporter.mx_edges` |
| 60 | Check current firmware upgrade status across organization with detailed progress monitoring and export to CSV | Safe | `lambda: FirmwareManager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).check_firmware_upgrade_status()` |
| 61 | Compare inventory data with external CSV file using configurable address similarity threshold (ADDRESS_MATCH_THRESHOLD in .env) | Safe | `lambda fast=False, address_check=False, debug=False, skip_ssl_verify=False: InventoryCSVComparator(fast=fast, address_check=address_check, debug=debug, skip_ssl_verify=skip_ssl_verify).execute()` |
| 62 | Interactive Marvis (VNA) AI troubleshooting - guided client, device, and network analysis | Interactive | `TroubleshootUtils.launch_interactive` |
| 63 | Export all org device events from the last 52 weeks (streaming with checkpoint/resume) | Interactive | `OrgAlarmEventExporter.device_events_52w` |
| 64 | Export ALL audit logs for the organization (last 52 weeks) | Safe | `lambda: OrgExportUtils.audit_logs(full_history=True, duration='52w')` |
| 65 | Export configuration details for all gateway devices across all sites | Safe | `GatewayExportUtils.device_configs` |
| 66 | Export Organization SLE Metrics (Service Level Experience) | Safe | `OrgExportUtils.sle_metrics` |
| 67 | Export SLE summary metrics for all sites in the organization | Safe | `OrgExportUtils.sites_sle_summary` |
| 68 | Export general insight metrics for a selected site | Safe | `SiteExportUtils.insight_metrics` |
| 69 | Export client-specific insight metrics for a selected site | Safe | `SiteClientExporter.client_insights` |
| 70 | Select a site (used by other functions) | Safe | `PromptUtils.select_site_with_logging` |
| 71 | View device inventory for a selected site | Interactive | `InteractiveDisplayUtils.site_inventory` |
| 72 | View statistics for a selected device at a site | Interactive | `InteractiveDisplayUtils.device_stats` |
| 73 | View synthetic test stats for a selected gateway device | Interactive | `InteractiveDisplayUtils.device_tests` |
| 74 | View configuration details for a selected device | Interactive | `InteractiveDisplayUtils.device_config` |
| 75 | Loop refresh of core datasets (site list, inventory, stats, ports, VPN) Stop with CTRL+C or create 'stop_loop.txt' | Safe | `DataCollectionManager.continuous_loop` |
| 76 | Run continuous data collection loop (5 core API calls with rate limiting) | Safe | `DataCollectionManager.continuous_loop` |
| 77 | Process and merge CSV files of SFP Module locations into a single CSV file | Safe | `SFPTransceiverDataProcessor.merge_transceiver_data` |
| 78 | Generate support package for each site | Safe | `DataCollectionManager.generate_support_packages` |
| 79 | Interactively execute a CLI command on a gateway or switch (exit with ~) | Interactive | `CLIShellManager.launch` |
| 80 | Run ARP command on an AP and receive output via WebSocket | Safe | `ARPCommandManager.execute` |
| 81 | Export device-specific insight metrics for a selected site | Safe | `SiteExportUtils.device_insights` |
| 82 | Export all available const definitions from the Mist API (comprehensive endpoint coverage) | Safe | `lambda: ConstDefinitionsExporter(apisession).export_all()` |
| 83 | Export Organization Insight Metrics (comprehensive operational insights) | Safe | `OrgExportUtils.insight_metrics` |
| 84 | Export Site Anomaly Events (dynamic discovery of all anomaly-related metrics from Mist API) | Safe | `SiteAnomalyExporter.anomaly_events` |
| 85 | Export Site Device Anomaly Events (device-specific anomaly detection) | Safe | `SiteAnomalyExporter.device_anomaly_events` |
| 86 | Export Site Client Anomaly Events (client-specific anomaly detection: connectivity, roaming, throughput) | Safe | `SiteAnomalyExporter.client_anomaly_events` |
| 87 | WebSocket Device Ping - Execute ping command on device via WebSocket stream (real-time output) | Interactive | `WebSocketNetworkDiagCommands.ping_device` |
| 88 | WebSocket Device ARP - Execute ARP command on device via WebSocket stream (real-time output) | Interactive | `WebSocketNetworkDiagCommands.arp_device` |
| 89 | WebSocket Service Ping - Execute service-specific ping on SSR gateways via WebSocket stream (real-time output) | Interactive | `WebSocketNetworkDiagCommands.service_ping_device` |
| 90 | DESTRUCTIVE: Advanced AP firmware upgrade with mode selection - upgrade by site list/selection or by Gateway Template assignment | Destructive | `lambda: FirmwareManager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).execute_firmware_upgrade_with_mode_selection()` |
| 91 | DESTRUCTIVE: Reboot all devices associated with templates listed in GatewayTemplateRebootList.CSV and log results | Destructive | `DeviceRebootManager.by_gateway_template_list` |
| 92 | DESTRUCTIVE: Convert a virtual chassis switch to virtual MAC (interactive, supports --dry-run) | Destructive | `lambda dry_run=False: VirtualChassisManager.convert_single(dry_run=dry_run)` |
| 93 | DESTRUCTIVE: Convert all virtual chassis switches in sites listed in VCConvert.CSV (bulk operation) | Destructive | `VirtualChassisManager.convert_by_site_list` |
| 94 | Check virtual chassis to virtual MAC conversion status for all switches | Safe | `VirtualChassisManager.check_status` |
| 95 | Export detailed device statistics for all gateways (with freshness check) | Safe | `lambda fast=False: GatewayStatsExporter.device_stats_with_freshness(fast=fast)` |
| 96 | Check and export gateways with duplicate WAN port IP addresses (0/0/0, 0/0/1, 0/0/2) | Safe | `GatewayStatsExporter.wan_port_conflicts` |
| 97 | Enhanced SSH Command Runner - Execute commands on remote network devices via SSH | Interactive | `SSHRunnerManager.interactive` |
| 98 | SSH Runner - Target gateways by template name (online gateways with management IPs only) | Safe | `SSHRunnerManager.by_gateway_template` |
| 99 | DESTRUCTIVE: Advanced Switch firmware upgrade with mode selection - upgrade by site list/selection or by Gateway Template assignment | Destructive | `lambda: FirmwareManager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).execute_switch_firmware_upgrade_with_mode_selection()` |
| 100 | DESTRUCTIVE: Advanced SSR firmware upgrade with mode selection - upgrade by site list/selection or by Gateway Template assignment | Destructive | `lambda: FirmwareManager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).execute_ssr_firmware_upgrade_with_mode_selection()` |
| 101 | Launch Terminal User Interface (TUI) mode - Visual navigation of Mist API library with interactive exploration | Interactive | `lambda: TUILauncher().launch()` |
| 102 | Manage WLAN RADIUS Authentication Timers - Configure auth_servers_timeout, auth_servers_retries, auth_server_selection, and fast_dot1x_timers for site or template WLANs | Safe | `lambda: WLANRadiusTimerManager().manage()` |
| 103 | Set WAN2 Interface Site Variable - Configure 'wan2_interface' site variable for template-based WAN migration (Reports sites with ge-0/0/1 overrides) | Safe | `lambda: WAN2MigrationManager().set_site_variable()` |
| 104 | DESTRUCTIVE: Update Gateway Templates to Use WAN2 Variable - Replace hardcoded 'ge-0/0/1' references with {{wan2_interface}} variable (Requires uppercase 'MIGRATE' confirmation, supports --dry-run) | Destructive | `lambda fast=False, dry_run=False: update_gateway_templates_wan2_variable(fast=fast, dry_run=dry_run)` |
| 105 | Extract Gateway Template Configuration (DIA_Pico, Picocell) - Save specific configs to JSON for replication | Safe | `GatewayTemplateConfigManager.extract` |
| 106 | DESTRUCTIVE: Apply Gateway Template Configuration - Replicate extracted configs to other templates (Requires uppercase 'APPLY' confirmation) | Destructive | `GatewayTemplateConfigManager.apply` |
| 107 | DESTRUCTIVE: Create 137 test sites from NorthAmericanTestSites.csv - Real landmarks across 13 North American countries (Requires uppercase 'CREATE' confirmation) | Destructive | `SiteConfigManager.create_test_sites_from_csv` |
| 108 | DESTRUCTIVE: Create country-specific RF templates and assign sites to matching templates (Requires uppercase 'CREATE' confirmation) | Destructive | `SiteConfigManager.create_country_rf_templates_and_assign` |
| 109 | DESTRUCTIVE: Scan org for AP models and create Device Profile per model with inherit/auto settings (Requires uppercase 'CREATE' confirmation) | Destructive | `SiteConfigManager.create_ap_model_device_profiles` |
| 110 | DESTRUCTIVE: Assign APs to Device Profiles matching their model type (AP-{model}) - Skips APs without matching profiles (Requires uppercase 'ASSIGN' confirmation) | Destructive | `SiteConfigManager.assign_aps_to_matching_device_profiles` |
| 111 | DESTRUCTIVE: Clone Gateway Template by State and Country - Create state/country-specific templates and assign sites (Requires uppercase 'CLONE' confirmation) | Destructive | `GatewayTemplateConfigManager.clone_by_location` |
| 112 | Maps Manager - Interactive site floorplan and map operations (sub-menu) | Interactive | `lambda: MapsManagerLauncher().launch()` |
| 113 | DESTRUCTIVE: Configure WAN Probe Override on Gateway Templates - Set ICMP probe IPs and profile for all WAN interfaces (Requires uppercase 'APPLY' confirmation, supports --dry-run) | Destructive | `lambda dry_run=False: WANProbeConfigManager.configure(dry_run=dry_run)` |
| 114 | DESTRUCTIVE: Configure WAN Probe on Device Port Overrides - Set ICMP probe on device-level WAN overrides only (Requires uppercase 'APPLY' confirmation, supports --dry-run) | Destructive | `lambda dry_run=False: WANProbeDeviceOverrideManager.configure(dry_run=dry_run)` |
| 115 | Switch to interactive login (email/password) - Enables MSP-level API access for current session | Interactive | `switch_to_interactive_login` |
| 116 | DESTRUCTIVE: Org-Level AP Firmware Upgrade - Efficient multi-site upgrade using org-level API (1 call per version vs 1 per site), MSP multi-org support, supports --dry-run | Destructive | `OrgLevelAPFirmwareUpgrader.run` |
| 117 | MSP Inventory Export - Export device inventory across all MSPs and all organizations to CSV (requires MSP privileges via --login) | Safe | `MSPInventoryExporter.execute` |
| 118 | Site Auto-Upgrade Configuration - Configure AP auto-upgrade settings for sites with MSP multi-org support (supports --dry-run) | Safe | `SiteAutoUpgradeConfigurator.execute` |
| 119 | Site Config Analysis - Scan all sites for zone, engagement dwell tag, and occupancy setting deviations | Safe | `ZoneConfigurationAnalyzer.analyze` |
| 120 | DESTRUCTIVE: Site Analytics Configuration - Apply standard RTSA/Rogue/Engagement/Occupancy settings to deviating sites | Destructive | `SiteAnalyticsConfigurator.execute` |
| 121 | Site Inventory Health Analysis - Find sites with APs missing switches/gateways, or with offline infrastructure | Safe | `SiteInventoryHealthAnalyzer.analyze` |
| 122 | Bulk RADIUS WLAN Configuration - Configure auth_servers_timeout, auth_servers_retries, fast_dot1x_timers for org-level RADIUS WLANs | Safe | `lambda dry_run=False: BulkRadiusWLANConfigManager().manage(dry_run=dry_run)` |
| 123 | Traceroute from device to destination host (AP/Switch/Gateway) | Safe | `DeviceUtilityCommands.traceroute` |
| 124 | Show OSPF Neighbors on SSR/SRX Gateway | Safe | `DeviceUtilityCommands.show_ospf_neighbors` |
| 125 | Show OSPF Interfaces on SSR/SRX Gateway | Safe | `DeviceUtilityCommands.show_ospf_interfaces` |
| 126 | Show OSPF Database on SSR/SRX Gateway | Safe | `DeviceUtilityCommands.show_ospf_database` |
| 127 | Show OSPF Summary on SSR/SRX Gateway | Safe | `DeviceUtilityCommands.show_ospf_summary` |
| 128 | Show Sessions on SSR/SRX Gateway | Safe | `DeviceUtilityCommands.show_session` |
| 129 | Show Service Path on SSR Gateway | Safe | `DeviceUtilityCommands.show_service_path` |
| 130 | Show BGP Summary on Switch or Gateway | Safe | `DeviceUtilityCommands.show_bgp_summary` |
| 131 | Show ARP Table on Switch or Gateway | Safe | `DeviceUtilityCommands.show_arp_table` |
| 132 | Show DHCP Leases on Switch or Gateway | Safe | `DeviceUtilityCommands.show_dhcp_leases` |
| 133 | Show 802.1X Table on Switch | Safe | `DeviceUtilityCommands.show_dot1x` |
| 134 | Show EVPN Database on Switch or Gateway | Safe | `DeviceUtilityCommands.show_evpn_database` |
| 135 | Test DNS Resolution on SSR Gateway | Safe | `DeviceUtilityCommands.resolve_dns` |
| 136 | Monitor Traffic on Switch/SRX Port (streaming, Ctrl+C to stop) | Interactive | `DeviceUtilityCommands.monitor_traffic` |
| 137 | Run Top Command on Switch/SRX (streaming, Ctrl+C to stop) | Interactive | `DeviceUtilityCommands.run_top` |
| 138 | Locate Device - Blink LED on AP or Switch | Safe | `DeviceUtilityCommands.locate_device` |
| 139 | Unlocate Device - Stop LED Blinking on AP or Switch | Safe | `DeviceUtilityCommands.unlocate_device` |
| 140 | Bounce Switch/Gateway Port (y/N confirmation) | Safe | `DeviceUtilityCommands.bounce_port` |
| 141 | Cable Test on Switch Port | Safe | `DeviceUtilityCommands.cable_test` |
| 142 | Reprovision Switch/Gateway (y/N confirmation) | Safe | `DeviceUtilityCommands.reprovision_device` |
| 143 | Re-adopt Switch Device | Safe | `DeviceUtilityCommands.readopt_device` |
| 144 | Get ZTP Password for Switch/Gateway (console only) | Safe | `DeviceUtilityCommands.get_ztp_password` |
| 145 | Get Config CLI Commands for Switch Adoption | Safe | `DeviceUtilityCommands.get_config_commands` |
| 146 | Upload Support File from Switch/Gateway | Safe | `DeviceUtilityCommands.upload_support_file` |
| 147 | DESTRUCTIVE: Clear ARP Cache (type CLEAR) | Destructive | `DeviceUtilityCommands.clear_arp_cache` |
| 148 | DESTRUCTIVE: Clear BGP Routes (type CLEAR) | Destructive | `DeviceUtilityCommands.clear_bgp_routes` |
| 149 | DESTRUCTIVE: Clear Session on SSR/SRX (type CLEAR) | Destructive | `DeviceUtilityCommands.clear_session` |
| 150 | DESTRUCTIVE: Clear MAC Table (type CLEAR) | Destructive | `DeviceUtilityCommands.clear_mac_table` |
| 151 | DESTRUCTIVE: Clear BPDU Errors on Switch (type CLEAR) | Destructive | `DeviceUtilityCommands.clear_bpdu_error` |
| 152 | DESTRUCTIVE: Clear Learned MACs from Switch Port (type CLEAR) | Destructive | `DeviceUtilityCommands.clear_learned_macs` |
| 153 | DESTRUCTIVE: Clear Policy Hit Count on SSR (type CLEAR) | Destructive | `DeviceUtilityCommands.clear_policy_hit_count` |
| 154 | Release DHCP Lease on Switch/Gateway (y/N) | Safe | `DeviceUtilityCommands.release_dhcp_lease` |
| 155 | Release DHCP Lease on SSR/SRX (y/N) | Safe | `DeviceUtilityCommands.release_dhcp_ssr` |
| 156 | Poll Fresh Statistics from Switch | Safe | `DeviceUtilityCommands.poll_switch_stats` |
| 157 | Create Device Snapshot on Switch | Safe | `DeviceUtilityCommands.create_device_snapshot` |
| 158 | Offline Device Report | Safe | `OfflineDeviceReporter.execute` |
| 159 | SSID Template Consolidation (5-Phase Guided Workflow) | Safe | `SSIDTemplateConsolidationManager.execute` |
| 160 | E911 BSSID Compliance Report | Safe | `E911BSSIDReportGenerator.execute` |

This page should be regenerated whenever `menu_actions` changes so the wiki stays aligned with `MistHelper.py`.
