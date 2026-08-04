# Menu Reference

This page is generated. Run `python scripts/generate_menu_wiki.py` after any
change to `menu_actions` in `MistHelper.py` or to `src/utils/operation_registry.py`.

MistHelper defines **209 actionable menu entries**, numbered
1 to 209 with no gaps.
Menu 0 is Exit, so the registry holds 210 entries in total.

The Safety column reads from `src/utils/operation_registry.py`, which is the
single source of truth. The classifier fails closed, so an unregistered option
never runs in an automated test pass.

## Important Notes

- Options 14, 18-19, 59, 97-101, 153 are resource intensive. They can run for a long time on a large org.
- Options 154-187, 189-191, 194, 206-208 are destructive. They change the Mist cloud configuration.
- Warning: Do not script a destructive option unattended. Each one needs a typed
  confirmation from a human operator.

## Operation Categories

| Menu numbers | Category | Summary |
|---|---|---|
| 1-13, 15-17, 20-58, 188, 193, 195-196, 204-205 | Safe org exports | 61 operations. Read-only org exports. The --test run includes them. |
| 60-96, 197-203, 209 | Interactive safe | 45 operations. Read-only, but they prompt for a site or a device. The --testinteractive run includes them. |
| 154-187, 189-191, 194, 206-208 | Destructive | 41 operations. They change the Mist cloud configuration. Each one needs a typed confirmation. |
| 0, 124-150, 192 | Interactive | 29 operations. They prompt the operator, so no automated run includes them. |
| 102-123 | WebSocket | 22 operations. They open a WebSocket stream to a device. |
| 14, 18-19, 59, 97-101, 153 | Resource intensive | 10 operations. They run long or fetch a large payload. |
| 151-152 | Continuous loop | 2 operations. They loop until the operator stops them. |

## Full Menu Table

| Menu ID | Short description | Safety | Callable/Handler |
|---:|---|---|---|
| 0 | Exit MistHelper | Interactive | `lambda: sys.exit(0)` |
| 1 | Export a list of all sites in the organization | Safe org exports | `OrgSiteExporter.sites` |
| 2 | Export a list of sites with location and timezone info | Safe org exports | `OrgSiteExporter.sites_with_location` |
| 3 | Export all sites using the 'list' sites API endpoint (to SiteList_ListAPI.csv, only if not already present) | Safe org exports | `OrgSiteExporter.sites_list_api` |
| 4 | Export all current guest users and last 7 days of historical guests to CSV | Safe org exports | `lambda: (OrgSiteExporter.current_guests(), OrgSiteExporter.historical_guests())` |
| 5 | Export E911 report for the organization | Safe org exports | `OrgExportUtils.e911_report` |
| 6 | Site Config Analysis - Scan all sites for zone, engagement dwell tag, and occupancy setting deviations | Safe org exports | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).zone_config_analysis()` |
| 7 | Site Inventory Health Analysis - Find sites with APs missing switches/gateways, or with offline infrastructure | Safe org exports | `lambda: ExtractedSiteInventoryHealthAnalyzer.analyze(SiteInventoryHealthAnalyzerDeps(apisession=apisession, mistapi=mistapi, get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id, all_sites_fn=APICoreFetchUtils.all_sites_with_limit, save_data_fn=DataExporter.write_with_format_selection))` |
| 8 | Export the full inventory of devices in the organization | Safe org exports | `OrgInventoryExporter.inventory` |
| 9 | Export a list of all devices in the organization | Safe org exports | `OrgInventoryExporter.devices` |
| 10 | Export a list of all devices with associated site and address info | Safe org exports | `OrgInventoryExporter.devices_with_site_info` |
| 11 | Export a list of gateways with associated site and address info | Safe org exports | `OrgInventoryExporter.gateways_with_site_info` |
| 12 | Export combined inventory with site and address info by calendar week | Safe org exports | `OrgInventoryExporter.combined_inventory_with_site_info` |
| 13 | Export org device model counts, firmware version distribution, and versions per model (MSP-aware) | Safe org exports | `OrgDeviceInventorySummary.dispatch` |
| 14 | Check virtual chassis to virtual MAC conversion status for all switches | Resource intensive | `lambda: _configure_virtual_chassis_manager().launch_check_status()` |
| 15 | Export statistics for all devices in the organization | Safe org exports | `OrgDeviceStatsExporter.device_stats` |
| 16 | Export VPN peer path statistics for the organization | Safe org exports | `OrgDeviceStatsExporter.vpn_peer_stats` |
| 17 | Export all switch virtual chassis (VC/stacking) stats to CSV | Safe org exports | `OrgDeviceStatsExporter.switch_vc_stats` |
| 18 | Export detailed device statistics for all gateways (with freshness check) | Resource intensive | `lambda fast=False: _dispatch_gateway_stats_device_stats_with_freshness(fast=fast)` |
| 19 | Export port-level statistics for switches and gateways | Resource intensive | `OrgDeviceStatsExporter.device_port_stats` |
| 20 | Export all organization alarms from the past day | Safe org exports | `OrgAlarmEventExporter.alarms` |
| 21 | Export all device events from the past 24 hours | Safe org exports | `OrgAlarmEventExporter.device_events` |
| 22 | Export audit logs for the organization (last 24 hours) | Safe org exports | `lambda: OrgExportUtils.audit_logs(full_history=False)` |
| 23 | Export self (admin account) audit log | Safe org exports | `SelfExportUtils.audit_logs` |
| 24 | Export security events for the organization | Safe org exports | `OrgClientSecurityExporter.security_events` |
| 25 | Audit Log Analysis - Mermaid timeline + interactive HTML report | Safe org exports | `AuditAnalysisOps.audit_log_analysis` |
| 26 | Offline Device Report | Safe org exports | `OfflineDeviceReporter.execute` |
| 27 | Export wireless client statistics for the organization | Safe org exports | `OrgClientSecurityExporter.wireless_clients` |
| 28 | Export wired client statistics for the organization | Safe org exports | `OrgClientSecurityExporter.wired_clients` |
| 29 | Export rogue client detections for the organization | Safe org exports | `OrgClientSecurityExporter.rogue_clients` |
| 30 | Export rogue AP detections for the organization | Safe org exports | `OrgClientSecurityExporter.rogue_aps` |
| 31 | Export gateway management overlay IPs grouped by template association | Safe org exports | `_dispatch_gateway_management_ips` |
| 32 | Export gateway templates from the organization | Safe org exports | `_dispatch_gateway_templates` |
| 33 | Export synthetic test results for all gateways | Safe org exports | `GatewayTestExporter.synthetic_tests` |
| 34 | Export all synthetic test results (including speed tests) for gateways | Safe org exports | `GatewayTestExporter.test_results_by_site` |
| 35 | Find gateway ports overridden from template (outliers for compliance correction) | Safe org exports | `_dispatch_gateway_with_wan_overrides` |
| 36 | Check and export gateways with duplicate WAN port IP addresses (0/0/0, 0/0/1, 0/0/2) | Safe org exports | `_dispatch_gateway_stats_wan_port_conflicts` |
| 37 | Export all organization templates (gateway, network, RF, site, AP) | Safe org exports | `OrgTemplateExporter.all_templates` |
| 38 | Export network template information for the organization | Safe org exports | `OrgTemplateExporter.network_templates` |
| 39 | Export RF template information for the organization | Safe org exports | `OrgTemplateExporter.rf_templates` |
| 40 | Export AP template information for the organization | Safe org exports | `OrgTemplateExporter.ap_templates` |
| 41 | Export switch template information for the organization | Safe org exports | `OrgTemplateExporter.switch_templates` |
| 42 | Export license information for the organization | Safe org exports | `OrgAdminExporter.licenses` |
| 43 | Export license usage information for the organization | Safe org exports | `OrgAdminExporter.usage` |
| 44 | Export PSK (Pre-Shared Key) information for the organization | Safe org exports | `OrgConfigExporter.psks` |
| 45 | Export webhook configuration for the organization | Safe org exports | `OrgConfigExporter.webhooks` |
| 46 | Export WLAN configuration for the organization | Safe org exports | `OrgConfigExporter.wlans` |
| 47 | Export API token information for the organization | Safe org exports | `OrgAdminExporter.api_tokens` |
| 48 | Export administrator information for the organization | Safe org exports | `OrgAdminExporter.admins` |
| 49 | Export SSO (Single Sign-On) information for the organization | Safe org exports | `OrgAdminExporter.sso` |
| 50 | Export MX Edge information for the organization | Safe org exports | `OrgConfigExporter.mx_edges` |
| 51 | Export Organization SLE Metrics (Service Level Experience) | Safe org exports | `OrgExportUtils.sle_metrics` |
| 52 | Export SLE summary metrics for all sites in the organization | Safe org exports | `OrgExportUtils.sites_sle_summary` |
| 53 | Export Organization Insight Metrics (comprehensive operational insights) | Safe org exports | `OrgExportUtils.insight_metrics` |
| 54 | Export all available const definitions from the Mist API (comprehensive endpoint coverage) | Safe org exports | `lambda: ConstDefinitionsExporter(apisession).export_all()` |
| 55 | Export OSPF adjacency statistics for the organization | Safe org exports | `OrgExportUtils.ospf_stats` |
| 56 | Export JSI PBN (Product Bulletin Notifications) data | Safe org exports | `OrgExportUtils.jsi_pbn` |
| 57 | Export JSI SIRT (Security Incident Response) advisories | Safe org exports | `OrgExportUtils.jsi_sirt` |
| 58 | Export Org WAN/Gateway Config (JSON bundle for cross-org migration) | Safe org exports | `lambda: cast(Any, OrgConfigMigrationManager)(apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input).export_config()` |
| 59 | Export configuration settings for all sites | Resource intensive | `SiteConfigExporter.settings` |
| 60 | Export device list for a selected site | Interactive safe | `SiteDeviceExporter.devices` |
| 61 | Export device statistics for a selected site | Interactive safe | `SiteDeviceExporter.device_stats` |
| 62 | Export port statistics for a selected site | Interactive safe | `SiteDeviceExporter.port_stats` |
| 63 | Export virtual chassis information for a selected switch device | Interactive safe | `SiteDeviceExporter.device_virtual_chassis` |
| 64 | Export currently connected WiFi clients and session data for a selected site to SiteWiFiClients.CSV | Interactive safe | `SiteClientExporter.wifi_clients` |
| 65 | Export client statistics for a selected site | Interactive safe | `SiteClientExporter.clients` |
| 66 | Export beacon information for a selected site | Interactive safe | `SiteClientExporter.beacons` |
| 67 | Export map information for a selected site | Interactive safe | `SiteConfigExporter.maps` |
| 68 | Export zone information for a selected site | Interactive safe | `SiteConfigExporter.zones` |
| 69 | Export WLAN configuration for a selected site | Interactive safe | `SiteConfigExporter.wlans` |
| 70 | Export OSPF adjacency statistics for a selected site | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).ospf_stats()` |
| 71 | Export MxEdge upgrade status for a selected site | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).mxedge_upgrade_status()` |
| 72 | Export auto-map assignment status for a selected site | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).auto_map_assignment_status()` |
| 73 | Export SLE (Service Level Experience) metrics insights for a selected site | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).insights()` |
| 74 | Export general insight metrics for a selected site | Interactive safe | `lambda: SiteMetricOperation(apisession=apisession, PromptUtils=PromptUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, mistapi=mistapi).execute()` |
| 75 | Export client-specific insight metrics for a selected site | Interactive safe | `SiteClientExporter.client_insights` |
| 76 | Export device-specific insight metrics for a selected site | Interactive safe | `lambda: DeviceMetricOperation(apisession=apisession, PromptUtils=PromptUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, mistapi=mistapi).execute()` |
| 77 | Export Site Anomaly Events (dynamic discovery of all anomaly-related metrics from Mist API) | Interactive safe | `SiteAnomalyExporter.anomaly_events` |
| 78 | Export Site Device Anomaly Events (device-specific anomaly detection) | Interactive safe | `SiteAnomalyExporter.device_anomaly_events` |
| 79 | Export Site Client Anomaly Events (client-specific anomaly detection: connectivity, roaming, throughput) | Interactive safe | `SiteAnomalyExporter.client_anomaly_events` |
| 80 | Export site aggregate health & capacity statistics | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).site_stats()` |
| 81 | Export site gateway performance metrics summary | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).gateway_metrics()` |
| 82 | Export site switch performance metrics summary | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).switches_metrics()` |
| 83 | Export site BLE beacon statistics | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).beacons_stats()` |
| 84 | Export site WxLAN rule usage statistics | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).wxrules_usage()` |
| 85 | Export site asset statistics | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).assets_stats()` |
| 86 | Export current RRM channel & power plan per AP radio | Interactive safe | `lambda: SiteExportUtils(apisession=apisession, PromptUtils=PromptUtils, ConfigUtils=ConfigUtils, DataProcessingUtils=DataProcessingUtils, DataExporter=DataExporter, TimeUtils=TimeUtils, EnhancedSSHRunner=EnhancedSSHRunner, InsightMetricsUtils=InsightMetricsUtils, PacketCaptureManager=PacketCaptureManager, APICoreFetchUtils=APICoreFetchUtils, check_fn=IsDebugMode.check, PrettyTable=PrettyTable, tqdm=tqdm, mistapi=mistapi).current_channel_planning()` |
| 87 | Export HA gateway cluster info, stats & node pair for a site | Interactive safe | `GatewayHaExporter.ha_cluster_info` |
| 88 | Export sites by AP model with site address (CSV) | Interactive safe | `SitesByAPModelExporter.export_sites_by_ap_model` |
| 89 | E911 BSSID Compliance Report | Interactive safe | `OrgExportUtils.e911_bssid_compliance_report` |
| 90 | Global Wired Client Report (operator-based MAC/MFG filtering) | Interactive safe | `GlobalWiredClientReportGenerator.execute` |
| 91 | Wired Client Manufacturer Report (browse & select) | Interactive safe | `WiredClientManufacturerReportGenerator.execute` |
| 92 | Select a site (used by other functions) | Interactive safe | `PromptUtils.select_site_with_logging` |
| 93 | View device inventory for a selected site | Interactive safe | `InteractiveDisplayUtils.site_inventory` |
| 94 | View statistics for a selected device at a site | Interactive safe | `InteractiveDisplayUtils.device_stats` |
| 95 | View synthetic test stats for a selected gateway device | Interactive safe | `InteractiveDisplayUtils.device_tests` |
| 96 | View configuration details for a selected device | Interactive safe | `InteractiveDisplayUtils.device_config` |
| 97 | Export all org device events from the last 52 weeks (streaming with checkpoint/resume) | Resource intensive | `OrgAlarmEventExporter.device_events_52w` |
| 98 | Export ALL audit logs for the organization (last 52 weeks) | Resource intensive | `lambda: OrgExportUtils.audit_logs(full_history=True, duration='52w')` |
| 99 | Export configuration details for all gateway devices across all sites | Resource intensive | `_dispatch_gateway_device_configs` |
| 100 | Process and merge CSV files of SFP Module locations into a single CSV file | Resource intensive | `SFPTransceiverDataProcessor.merge_transceiver_data` |
| 101 | Generate support package for each site | Resource intensive | `DataCollectionManager.generate_support_packages` |
| 102 | Show MAC table on switch device via WebSocket (Layer 2 switching table) | WebSocket | `lambda: MacTableCommand.execute(_ws_cmd_deps())` |
| 103 | Show forwarding table on gateway device via WebSocket (Layer 3 routing table) | WebSocket | `lambda: RoutingUtils(RoutingDeps(apisession=apisession, select_site_fn=PromptUtils.select_site_id_from_csv, select_device_fn=lambda site_id, dtype: PromptUtils.select_device_id_from_inventory(site_id, device_type=dtype), safe_input_fn=InputUtils.safe_input, websocket_manager_factory=WebSocketManager, check_fn=IsDebugMode.check)).execute_show_forwarding_table()` |
| 104 | Show routing table on switches via WebSocket (Switch L3 routing - BGP/OSPF/Static) | WebSocket | `lambda: RoutingUtils(RoutingDeps(apisession=apisession, select_site_fn=PromptUtils.select_site_id_from_csv, select_device_fn=lambda site_id, dtype: PromptUtils.select_device_id_from_inventory(site_id, device_type=dtype), safe_input_fn=InputUtils.safe_input, websocket_manager_factory=WebSocketManager, check_fn=IsDebugMode.check)).execute_show_routing_table()` |
| 105 | Show SSR/SRX routing table via dedicated API (128T/SRX gateways - Advanced BGP analysis) | WebSocket | `lambda: RoutingUtils(RoutingDeps(apisession=apisession, select_site_fn=PromptUtils.select_site_id_from_csv, select_device_fn=lambda site_id, dtype: PromptUtils.select_device_id_from_inventory(site_id, device_type=dtype), safe_input_fn=InputUtils.safe_input, websocket_manager_factory=WebSocketManager, check_fn=IsDebugMode.check)).execute_show_ssr_routes()` |
| 106 | Show OSPF Neighbors on SSR/SRX Gateway | WebSocket | `lambda: _get_duc_instance().show_ospf_neighbors()` |
| 107 | Show OSPF Interfaces on SSR/SRX Gateway | WebSocket | `lambda: _get_duc_instance().show_ospf_interfaces()` |
| 108 | Show OSPF Database on SSR/SRX Gateway | WebSocket | `lambda: _get_duc_instance().show_ospf_database()` |
| 109 | Show OSPF Summary on SSR/SRX Gateway | WebSocket | `lambda: _get_duc_instance().show_ospf_summary()` |
| 110 | Show Sessions on SSR/SRX Gateway | WebSocket | `lambda: _get_duc_instance().show_session()` |
| 111 | Show Service Path on SSR Gateway | WebSocket | `lambda: _get_duc_instance().show_service_path()` |
| 112 | Show BGP Summary on Switch or Gateway | WebSocket | `lambda: _get_duc_instance().show_bgp_summary()` |
| 113 | Show ARP Table on Switch or Gateway | WebSocket | `lambda: _get_duc_instance().show_arp_table()` |
| 114 | Show DHCP Leases on Switch or Gateway | WebSocket | `lambda: _get_duc_instance().show_dhcp_leases()` |
| 115 | Show 802.1X Table on Switch | WebSocket | `lambda: _get_duc_instance().show_dot1x()` |
| 116 | Show EVPN Database on Switch or Gateway | WebSocket | `lambda: _get_duc_instance().show_evpn_database()` |
| 117 | Test DNS Resolution on SSR Gateway | WebSocket | `lambda: _get_duc_instance().resolve_dns()` |
| 118 | WebSocket Device Ping - Execute ping command on device via WebSocket stream (real-time output) | WebSocket | `lambda: PingDeviceExecutor().execute(_ws_cmd_deps())` |
| 119 | WebSocket Device ARP - Execute ARP command on device via WebSocket stream (real-time output) | WebSocket | `lambda: ArpDeviceExecutor().execute(_ws_cmd_deps())` |
| 120 | WebSocket Service Ping - Execute service-specific ping on SSR gateways via WebSocket stream (real-time output) | WebSocket | `lambda: ServicePingLauncher().launch()` |
| 121 | Run ARP command on an AP and receive output via WebSocket | WebSocket | `ARPCommandManager.execute` |
| 122 | Cable Test on Switch Port | WebSocket | `lambda: _get_duc_instance().cable_test()` |
| 123 | Traceroute from device to destination host (AP/Switch/Gateway) | WebSocket | `lambda: _get_duc_instance().traceroute()` |
| 124 | Monitor Traffic on Switch/SRX Port (streaming, Ctrl+C to stop) | Interactive | `lambda: _get_duc_instance().monitor_traffic()` |
| 125 | Run Top Command on Switch/SRX (streaming, Ctrl+C to stop) | Interactive | `lambda: _get_duc_instance().run_top()` |
| 126 | Poll Fresh Statistics from Switch | Interactive | `lambda: _get_duc_instance().poll_switch_stats()` |
| 127 | Create Device Snapshot on Switch | Interactive | `lambda: _get_duc_instance().create_device_snapshot()` |
| 128 | Locate Device - Blink LED on AP or Switch | Interactive | `lambda: _get_duc_instance().locate_device()` |
| 129 | Unlocate Device - Stop LED Blinking on AP or Switch | Interactive | `lambda: _get_duc_instance().unlocate_device()` |
| 130 | Re-adopt Switch Device | Interactive | `lambda: _get_duc_instance().readopt_device()` |
| 131 | Get ZTP Password for Switch/Gateway (console only) | Interactive | `lambda: _get_duc_instance().get_ztp_password()` |
| 132 | Get Config CLI Commands for Switch Adoption | Interactive | `lambda: _get_duc_instance().get_config_commands()` |
| 133 | Upload Support File from Switch/Gateway | Interactive | `lambda: _get_duc_instance().upload_support_file()` |
| 134 | Start Site Packet Capture - Wireless/Wired/Gateway/Scan captures with WebSocket streaming | Interactive | `lambda: PacketCaptureManager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).start_site_packet_capture()` |
| 135 | Start Organization Packet Capture - MxEdge captures for org-level Mist Edges only | Interactive | `lambda: PacketCaptureManager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).start_org_packet_capture()` |
| 136 | MSP (Managed Service Provider) info - Displays guidance only (MSP data requires MSP-level API access, not org-level) | Interactive | `OrgConfigExporter.msp` |
| 137 | Check current firmware upgrade status across organization with detailed progress monitoring and export to CSV | Interactive | `lambda: _build_firmware_manager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).check_firmware_upgrade_status()` |
| 138 | Compare inventory data with external CSV file using configurable address similarity threshold (ADDRESS_MATCH_THRESHOLD in .env) | Interactive | `lambda fast=False, address_check=False, debug=False, skip_ssl_verify=False: InventoryCSVComparator(fast=fast, address_check=address_check, debug=debug, skip_ssl_verify=skip_ssl_verify).execute()` |
| 139 | Interactive Marvis (VNA) AI troubleshooting - guided client, device, and network analysis | Interactive | `TroubleshootUtils.launch_interactive` |
| 140 | Interactively execute a CLI command on a gateway or switch (exit with ~) | Interactive | `CLIShellManager.launch` |
| 141 | Launch Terminal User Interface (TUI) mode - Visual navigation of Mist API library with interactive exploration | Interactive | `lambda: TUILauncher().launch()` |
| 142 | Maps Manager - Interactive site floorplan and map operations (sub-menu) | Interactive | `lambda: MapsManagerLauncher().launch()` |
| 143 | Switch to interactive login (email/password) - Enables MSP-level API access for current session | Interactive | `lambda: SwitchToInteractiveLoginManager().run()` |
| 144 | MSP Inventory Export - Export device inventory across all MSPs and all organizations to CSV (requires MSP privileges via --login) | Interactive | `MSPInventoryExporter.execute` |
| 145 | SSID Template Consolidation (5-Phase Guided Workflow) | Interactive | `OrgExportUtils.ssid_template_consolidation` |
| 146 | WAN Hub Group Number Manager | Interactive | `lambda: WanHubGroupNumberManager.execute(apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input)` |
| 147 | WAN Hub-Spoke VPN Builder | Interactive | `lambda: WanVpnBuilder.execute(apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input)` |
| 148 | Manage WLAN RADIUS Authentication Timers - Configure auth_servers_timeout, auth_servers_retries, auth_server_selection, and fast_dot1x_timers for site or template WLANs | Interactive | `lambda: WLANRadiusTimerManager().manage()` |
| 149 | Set WAN2 Interface Site Variable - Configure 'wan2_interface' site variable for template-based WAN migration (Reports sites with ge-0/0/1 overrides) | Interactive | `lambda: WAN2MigrationLauncher().launch()` |
| 150 | Extract Gateway Template Configuration (DIA_Pico, Picocell) - Save specific configs to JSON for replication | Interactive | `lambda: GatewayTemplateConfigManager(org_id=ConfigUtils.get_cached_or_prompted_org_id(), apisession=apisession, input_fn=InputUtils.safe_input, get_csv_path_fn=FilePathUtils.get_csv_path, save_data_fn=DataExporter.write_with_format_selection, check_and_generate_csv_fn=CacheUtils.check_and_generate_csv, generate_sites_fn=OrgSiteExporter.sites, sanitize_filename_fn=EnhancedSSHRunner.sanitize_filename).extract()` |
| 151 | Loop refresh of core datasets (site list, inventory, stats, ports, VPN) Stop with CTRL+C or create 'stop_loop.txt' | Continuous loop | `DataCollectionManager.continuous_loop` |
| 152 | Run continuous data collection loop (5 core API calls with rate limiting) | Continuous loop | `DataCollectionManager.continuous_loop` |
| 153 | Bulk Org Data Collection (populate ArangoDB/Redis/SQLite with all org-level APIs) | Resource intensive | `lambda: OrgDataCollector.execute(OrgExportUtils.export_data, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input)` |
| 154 | DESTRUCTIVE: Advanced AP firmware upgrade with mode selection - upgrade by site list/selection or by Gateway Template assignment | Destructive | `lambda: _build_firmware_manager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).execute_firmware_upgrade_with_mode_selection()` |
| 155 | DESTRUCTIVE: Advanced Switch firmware upgrade with mode selection - upgrade by site list/selection or by Gateway Template assignment | Destructive | `lambda: _build_firmware_manager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).execute_switch_firmware_upgrade_with_mode_selection()` |
| 156 | DESTRUCTIVE: Advanced SSR firmware upgrade with mode selection - upgrade by site list/selection or by Gateway Template assignment | Destructive | `lambda: _build_firmware_manager(apisession, ConfigUtils.get_cached_or_prompted_org_id()).execute_ssr_firmware_upgrade_with_mode_selection()` |
| 157 | DESTRUCTIVE: Org-Level AP Firmware Upgrade - Efficient multi-site upgrade using org-level API (1 call per version vs 1 per site), MSP multi-org support, supports --dry-run | Destructive | `lambda: _build_org_ap_upgrader().run()` |
| 158 | DESTRUCTIVE: Reboot all devices associated with templates listed in GatewayTemplateRebootList.CSV and log results | Destructive | `DeviceRebootManager.by_gateway_template_list` |
| 159 | Bounce Switch/Gateway Port (y/N confirmation) | Destructive | `lambda: _get_duc_instance().bounce_port()` |
| 160 | Reprovision Switch/Gateway (y/N confirmation) | Destructive | `lambda: _get_duc_instance().reprovision_device()` |
| 161 | DESTRUCTIVE: Convert a virtual chassis switch to virtual MAC (interactive, supports --dry-run) | Destructive | `lambda dry_run=False: _configure_virtual_chassis_manager().launch_convert_single(dry_run=dry_run)` |
| 162 | DESTRUCTIVE: Convert all virtual chassis switches in sites listed in VCConvert.CSV (bulk operation) | Destructive | `lambda: _configure_virtual_chassis_manager().launch_convert_by_site_list()` |
| 163 | DESTRUCTIVE: Update Gateway Templates to Use WAN2 Variable - Replace hardcoded 'ge-0/0/1' references with {{wan2_interface}} variable (Requires uppercase 'MIGRATE' confirmation, supports --dry-run) | Destructive | `_dispatch_gateway_wan2_variable_migration` |
| 164 | DESTRUCTIVE: Apply Gateway Template Configuration - Replicate extracted configs to other templates (Requires uppercase 'APPLY' confirmation) | Destructive | `lambda: GatewayTemplateConfigManager(org_id=ConfigUtils.get_cached_or_prompted_org_id(), apisession=apisession, input_fn=InputUtils.safe_input, get_csv_path_fn=FilePathUtils.get_csv_path, save_data_fn=DataExporter.write_with_format_selection, check_and_generate_csv_fn=CacheUtils.check_and_generate_csv, generate_sites_fn=OrgSiteExporter.sites, sanitize_filename_fn=EnhancedSSHRunner.sanitize_filename).apply()` |
| 165 | DESTRUCTIVE: Clone Gateway Template by State and Country - Create state/country-specific templates and assign sites (Requires uppercase 'CLONE' confirmation) | Destructive | `lambda: GatewayTemplateConfigManager(org_id=ConfigUtils.get_cached_or_prompted_org_id(), apisession=apisession, input_fn=InputUtils.safe_input, get_csv_path_fn=FilePathUtils.get_csv_path, save_data_fn=DataExporter.write_with_format_selection, check_and_generate_csv_fn=CacheUtils.check_and_generate_csv, generate_sites_fn=OrgSiteExporter.sites, sanitize_filename_fn=EnhancedSSHRunner.sanitize_filename).clone_by_location()` |
| 166 | DESTRUCTIVE: Configure WAN Probe Override on Gateway Templates - Set ICMP probe IPs and profile for all WAN interfaces (Requires uppercase 'APPLY' confirmation, supports --dry-run) | Destructive | `lambda dry_run=False: WANProbeConfigManager.configure(dry_run=dry_run)` |
| 167 | DESTRUCTIVE: Configure WAN Probe on Device Port Overrides - Set ICMP probe on device-level WAN overrides only (Requires uppercase 'APPLY' confirmation, supports --dry-run) | Destructive | `lambda dry_run=False: WANProbeDeviceOverrideManager.configure(dry_run=dry_run)` |
| 168 | Site Auto-Upgrade Configuration - Configure AP auto-upgrade settings for sites with MSP multi-org support (supports --dry-run) | Destructive | `lambda: SiteAutoUpgradeConfigurator.execute(apisession=apisession, msp_privileges=msp_privileges if msp_privileges else [], safe_input_fn=InputUtils.safe_input, get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id, fetch_sites_fn=APICoreFetchUtils.all_sites_with_limit, check_stop_fn=ConfigUtils.check_stop_signal, dry_run=getattr(globals().get('args', None), 'dry_run', False), select_msps_fn=lambda: _build_org_ap_upgrader(org_id='')._select_msps(), select_orgs_fn=lambda msp: _build_org_ap_upgrader(org_id='')._select_orgs_from_msp(msp))` |
| 169 | DESTRUCTIVE: Site Analytics Configuration - Apply standard RTSA/Rogue/Engagement/Occupancy settings to deviating sites | Destructive | `lambda: ExtractedSiteAnalyticsConfigurator.execute(SiteAnalyticsConfiguratorDeps(apisession=apisession, mistapi=mistapi, get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id, check_stop_fn=ConfigUtils.check_stop_signal, safe_input_fn=InputUtils.safe_input, all_sites_fn=APICoreFetchUtils.all_sites_with_limit, save_data_fn=DataExporter.write_with_format_selection, tqdm_fn=tqdm))` |
| 170 | Bulk RADIUS WLAN Configuration - Configure auth_servers_timeout, auth_servers_retries, fast_dot1x_timers for org-level RADIUS WLANs | Destructive | `lambda dry_run=False: BulkRadiusWLANConfigManager().manage(dry_run=dry_run)` |
| 171 | DESTRUCTIVE: Create 137 test sites from NorthAmericanTestSites.csv - Real landmarks across 13 North American countries (Requires uppercase 'CREATE' confirmation) | Destructive | `lambda: _configure_site_config_manager().create_test_sites_from_csv()` |
| 172 | DESTRUCTIVE: Create country-specific RF templates and assign sites to matching templates (Requires uppercase 'CREATE' confirmation) | Destructive | `lambda: _configure_site_config_manager().create_country_rf_templates_and_assign()` |
| 173 | DESTRUCTIVE: Scan org for AP models and create Device Profile per model with inherit/auto settings (Requires uppercase 'CREATE' confirmation) | Destructive | `lambda: _configure_site_config_manager().create_ap_model_device_profiles()` |
| 174 | DESTRUCTIVE: Assign APs to Device Profiles matching their model type (AP-{model}) - Skips APs without matching profiles (Requires uppercase 'ASSIGN' confirmation) | Destructive | `lambda: _configure_site_config_manager().assign_aps_to_matching_device_profiles()` |
| 175 | Enhanced SSH Command Runner - Execute commands on remote network devices via SSH | Destructive | `lambda: SSHRunnerManager.interactive(_build_ssh_runner_deps())` |
| 176 | SSH Runner - Target gateways by template name (online gateways with management IPs only) | Destructive | `lambda: SSHRunnerManager.by_gateway_template(_build_ssh_runner_deps())` |
| 177 | DESTRUCTIVE: Clear ARP Cache (type CLEAR) | Destructive | `lambda: _get_duc_instance().clear_arp_cache()` |
| 178 | DESTRUCTIVE: Clear BGP Routes (type CLEAR) | Destructive | `lambda: _get_duc_instance().clear_bgp_routes()` |
| 179 | DESTRUCTIVE: Clear Session on SSR/SRX (type CLEAR) | Destructive | `lambda: _get_duc_instance().clear_session()` |
| 180 | DESTRUCTIVE: Clear MAC Table (type CLEAR) | Destructive | `lambda: _get_duc_instance().clear_mac_table()` |
| 181 | DESTRUCTIVE: Clear BPDU Errors on Switch (type CLEAR) | Destructive | `lambda: _get_duc_instance().clear_bpdu_error()` |
| 182 | DESTRUCTIVE: Clear Learned MACs from Switch Port (type CLEAR) | Destructive | `lambda: _get_duc_instance().clear_learned_macs()` |
| 183 | DESTRUCTIVE: Clear Policy Hit Count on SSR (type CLEAR) | Destructive | `lambda: _get_duc_instance().clear_policy_hit_count()` |
| 184 | Release DHCP Lease on Switch/Gateway (y/N) | Destructive | `lambda: _get_duc_instance().release_dhcp_lease()` |
| 185 | Release DHCP Lease on SSR/SRX (y/N) | Destructive | `lambda: _get_duc_instance().release_dhcp_ssr()` |
| 186 | Clear CSV Cache Files (delete all generated cache CSVs) | Destructive | `CacheUtils.clear_cache` |
| 187 | Import Org WAN/Gateway Config (cross-org migration with conflict detection) | Destructive | `lambda: cast(Any, OrgConfigMigrationManager)(apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input).import_config()` |
| 188 | Export all organization support tickets to CSV | Safe org exports | `OrgTicketManager.list_tickets` |
| 189 | Create a new organization support ticket | Destructive | `OrgTicketManager.create_ticket` |
| 190 | Add a comment (with optional file attachment) to a support ticket | Destructive | `OrgTicketManager.add_comment` |
| 191 | Update fields on an existing support ticket | Destructive | `OrgTicketManager.update_ticket` |
| 192 | View a support ticket with full comments and history | Interactive | `OrgTicketManager.view_ticket` |
| 193 | Export all tickets with full details and comments | Safe org exports | `OrgTicketManager.export_ticket_details` |
| 194 | DESTRUCTIVE: Clone Device Config to Gateway Template - Select a gateway, extract its local config, and create a new org gateway template (Requires typing 'CREATE' to confirm) | Destructive | `DeviceConfigTemplateClonerManager.clone` |
| 195 | Audit site addresses from CSV (data/) - fuse Mist + SNMP + CSV hints, verify vs. web; READ-ONLY, saves report. Tier-3 browser geocoding auto-engages when available (ADDRESS_AUDIT_GEOCODE=off to skip) | Safe org exports | `lambda: AddressAuditEngine().run(apisession, ConfigUtils.get_cached_or_prompted_org_id())` |
| 196 | Export async organization license-claim status summary (and optional per-device details) | Safe org exports | `LicenseExportUtils.export_org_license_async_claim_status` |
| 197 | Download client packet captures grouped by VLAN (site -> client -> VLAN -> data/packet_captures/) | Interactive safe | `lambda: ClientPacketCaptureDownloader(apisession).run()` |
| 198 | Search Site WAN Usages (searchSiteWanUsage) - Export per-site WAN usage records to SiteWanUsages.csv | Interactive safe | `SiteWanUsageExporter.wan_usages` |
| 199 | Search Site Webhook Deliveries (searchSiteWebhooksDeliveries) - Per site+webhook delivery audit CSV | Interactive safe | `SiteWebhookDeliveriesExporter.deliveries` |
| 200 | Search Site Guest Authorization (searchSiteGuestAuthorization) - Per-site authorized guest CSV | Interactive safe | `SiteGuestAuthorizationExporter.guest_authorizations` |
| 201 | Search Site Mist Edge Events (searchSiteMistEdgeEvents) - Per-site Mist Edge event CSV | Interactive safe | `SiteMistEdgeEventsExporter.mist_edge_events` |
| 202 | Search Site NAC Client Events (searchSiteNacClientEvents) - Per-site NAC client event CSV | Interactive safe | `SiteNacClientEventsExporter.nac_client_events` |
| 203 | Search WAN client events for a selected site (spec 899 / issue #1407) | Interactive safe | `SiteClientExporter.wan_client_events` |
| 204 | Export JSI assets and contract search results | Safe org exports | `OrgExportUtils.jsi_assets` |
| 205 | Export Org Mist Edge event search results | Safe org exports | `OrgExportUtils.mist_edge_events` |
| 206 | DESTRUCTIVE: Manage org Zscaler synthetic probes - Build/merge/swap synthetic_test.custom_probes from curated Zscaler catalogue | Destructive | `lambda: manage_org_synthetic_probes(apisession, ConfigUtils.get_cached_or_prompted_org_id())` |
| 207 | DESTRUCTIVE: Migrate APs between device profiles - Reassign every AP bound to a source device profile to a chosen target profile (Requires typing 'MIGRATE' or 'DRY-RUN' to confirm) | Destructive | `lambda: APProfileMigrationManager.migrate_aps_between_device_profiles(apisession)` |
| 208 | DESTRUCTIVE: Revert an AP profile migration from a backup file - Reassign each listed AP back to its original device profile (Requires typing 'REVERT' to confirm) | Destructive | `lambda: APProfileMigrationManager.revert_ap_profile_migration(apisession)` |
| 209 | Get site beacon detail by site_id + beacon_id (getSiteBeacon) | Interactive safe | `SiteClientExporter.get_site_beacon` |

This page should be regenerated whenever `menu_actions` or the operation registry
changes, so the wiki stays aligned with the code.
