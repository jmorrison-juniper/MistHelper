# Research: Organization Switch Scorecard

## Mist API operation

**Decision**: Use `listOrgDevicesStats`.

**Rationale**: The OpenAPI file defines `GET /api/v1/orgs/{org_id}/stats/devices` with operationId `listOrgDevicesStats`. The operation has path parameter `org_id` and query parameters `type`, `status`, `site_id`, `mac`, `evpntopo_id`, `evpn_unused`, `fields`, `start`, `end`, `duration`, `limit`, and `page`. The response is an array of `stats_device`. Switch rows use the `stats_switch` schema.

**Alternatives considered**: Per-site device reads were rejected because menu 15 already uses the organization statistics endpoint and its pagination path.

## SDK verification

**Decision**: Use `mistapi.api.v1.orgs.stats.listOrgDevicesStats`.

**Rationale**: The implementation step must verify this symbol in the installed SDK before coding the client. If the symbol is absent, the client records the mismatch and uses the session path method.

**Alternatives considered**: A hand-built pagination loop was rejected by the fleet contract.

## Pagination path

**Decision**: Reuse `APIDataFetcher` behavior from menu 15.

**Rationale**: `OrgDeviceStatsExporter.device_stats()` uses `APIDataFetcher` with `mistapi.api.v1.orgs.stats.listOrgDevicesStats`, `type="all"`, `duration`, and `limit=1000`. The switch scorecard will use the same fetcher behavior with `type="switch"`.

**Alternatives considered**: Direct `mistapi.get_all()` in a new loop was rejected because it would duplicate the pagination design.

## Switch schema fields

**Decision**: Read the exact field names from `stats_switch`, `stats_switch_module_stat_item`, and `stats_switch_ap_redundancy`.

**Rationale**: The OpenAPI schemas define these fields for the report:

- `clients_stats.total.num_aps`
- `ap_redundancy.num_aps`
- `ap_redundancy.num_aps_with_switch_redundancy`
- `fw_versions_outofsync`
- `config_status`
- `version`
- `model`
- `uptime`
- `last_trouble`
- `module_stat[].poe`
- `module_stat[].bios_version`
- `module_stat[].fpga_version`
- `module_stat[].pending_version`
- `module_stat[].backup_version`
- `module_stat[].fans`
- `module_stat[].psus`
- `module_stat[].temperatures`

**Alternatives considered**: Flattening every field was rejected because the user requested specific scorecard columns.

## Mist wired scorecard source

**Decision**: Match the Mist `Switches` page tile names.

**Rationale**: The `juniper-mist-wired` skill page `09-wired-visibility-and-switch-management/01-switches-page-metrics-and-front-panel.md` defines `Switch-AP Affinity`, `PoE Compliance`, `Version Compliance`, `Switch Uptime`, `Config Success`, `Switchport Usage`, and `Potential Anomalies`. It states that `Switch-AP Affinity` uses a default threshold of `12` APs per switch, `Switch Uptime` averages the past `7` days, and `Switchport Usage` turns red at `90%`.

**Alternatives considered**: A custom tile vocabulary was rejected because operators compare this report to the Mist portal.

## BIOS and snapshot evidence

**Decision**: Surface module `bios_version`, `fpga_version`, `pending_version`, and backup partition version fields as evidence columns.

**Rationale**: The `juniper-mist-wired` skill page `09-wired-visibility-and-switch-management/04-firmware-upgrades-reboots-and-snapshots.md` explains that EX4400 warnings can involve Junos, BIOS, or both. It also states that recovery snapshots protect the OAM volume and that remote shell can show BIOS and CPLD firmware evidence.

**Alternatives considered**: Hiding module firmware fields was rejected because the brief explicitly requests pending BIOS or FPGA and backup partition values.

## Comparable tile language

**Decision**: Use consistent compliance and anomaly language across domains.

**Rationale**: The `juniper-mist-wireless` page `01-architecture-and-ap-platforms/03-ap-dashboard-insights-and-utilities.md` defines AP `Version Compliance`, AP switch redundancy, and `Potential Anomalies`. The `juniper-mist-wan` page `10-monitoring-sles-and-troubleshooting/01-wan-edge-inventory-insights-and-alerts.md` defines WAN Edge `Config Success`, `Version Compliance`, `WAN Edge Uptime`, and `Potential Anomalies`. The `juniper-mist-aiops` page `05-marvis-actions/08-potential-anomalies-and-event-card.md` explains that potential anomalies are early warnings from device telemetry, system logs, and performance metrics. The `juniper-mist-aiops` page `04-alerts/01-alerts-dashboard-categories-and-severity.md` defines severity words that operators already know.

**Alternatives considered**: New status words were rejected because mixed terminology can confuse junior NOC engineers.

## Percentage rules

**Decision**: Express tile values as percentages with the switch count behind each value.

**Rationale**: The brief requires a per-site percentage and the switch count behind each tile. The model will count compliant switches over total switches for each site and for the organization.

**Alternatives considered**: Weighted percentages by AP count were rejected for the first implementation because the required output names switch counts.
