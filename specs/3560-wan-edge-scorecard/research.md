# Research: Organization WAN Edge Scorecard

## Decision: Use `listOrgDevicesStats` with `type=gateway`

**Rationale**: The feature needs one organization-wide gateway data set. The fleet contract names `listOrgDevicesStats` with `type=gateway` as the source. The implementation must reuse the existing gateway statistics fetch from menu `15` or menu `18`.

**Alternatives considered**: A new pagination loop was rejected. It would duplicate behavior and violate FR-014.

## Decision: Reuse the menu 18 gateway statistics path

**Rationale**: Before coding, the implementation must read `src/export/org_device_stats_exporter.py` and the menu `18` gateway stats path named `_dispatch_gateway_stats_device_stats_with_freshness`. That path is the required source for freshness behavior and the shared gateway statistics fetch.

**Alternatives considered**: Menu `279` could call Mist directly. That was rejected because the fleet contract forbids a second pagination loop.

## Decision: Read required OpenAPI schemas before coding

**Rationale**: Before coding, the implementation must read the `stats_gateway`, `dhcpd_stat_lan`, `vpn_peers`, and `bgp_peers` schemas in `documentation/mist-api-openapi3json.json`. Those schemas define the available gateway, DHCP, VPN, and BGP fields.

**Alternatives considered**: Inferring field names from samples was rejected. Mist can omit optional fields, and schema review reduces unsafe assumptions.

**Verified OpenAPI operation**: `listOrgDevicesStats` is `GET /api/v1/orgs/{org_id}/stats/devices`. The required path parameter is `org_id`. The query parameters include `type`, `status`, `site_id`, and `fields`. The implementation uses `type="gateway"` and `fields="*"`.

**Verified response shape**: The `stats_gateway` schema contains `config_status`, `version`, `model`, `is_ha`, `cluster_stat`, `service_status`, `dhcpd_stat`, `vpn_peers`, `bgp_peers`, `uptime`, `route_summary_stats`, and `arp_table_stats`. `dhcpd_stat` is an object keyed by network name, and each value uses the `dhcpd_stat_lan` schema with `num_leased` and `num_ips`.

**Verified peer fields**: `bgp_peer` contains `state`, `up`, `neighbor`, `node`, `rx_routes`, `tx_routes`, and `vrf_name`. `stats_gateway_vpn_peer` contains `up`, `peer_router_name`, `peer_mac`, `peer_site_id`, `port_id`, `type`, and `uptime`.

**Verified SDK function**: The installed SDK exposes `mistapi.api.v1.orgs.stats.listOrgDevicesStats`.

## Decision: Match Mist WAN edge tile concepts

**Rationale**: The WAN edge skill states that `WAN Edges > WAN Edges` shows `Config Success`, `Version Compliance`, `WAN Edge Uptime`, and `Potential Anomalies`. It states that `Potential Anomalies` is `100%` when no WAN edge has anomalies, and that two anomalous WAN edges in ten gives `80%`. It also states that the WAN edge detail page includes `DHCP Statistics`, with `Usage`, `Pool Name`, `Leased IPs`, and `Total IPs`.

**Alternatives considered**: Creating new tile names was rejected. Operators already know the Mist WAN edge tile terms.

**Skill citation**: `juniper-mist-wan 10-monitoring-sles-and-troubleshooting/01-wan-edge-inventory-insights-and-alerts.md`.

## Decision: Use organization insight context for the console summary

**Rationale**: The AIOps skill states that Organization Insights uses the `Entire Org` context and that `Top Alerts` can include `WAN Edge/Switch DHCP Pool Exhausted`. The console summary must be organization-wide and must help the operator choose the next investigation point.

**Alternatives considered**: Site-only summaries were rejected. The feature scope is organization-wide reporting.

**Skill citation**: `juniper-mist-aiops 02-insights/02-organization-insights.md`.

## Decision: Reuse cross-domain tile scoring patterns

**Rationale**: The wired skill states that `Version Compliance`, `Switch Uptime`, `Config Success`, and `Potential Anomalies` are percentage metrics. The WAN edge report should use the same style for site and organization summaries.

**Alternatives considered**: A raw count-only summary was rejected. It would not match the Mist dashboard pattern.

**Skill citation**: `juniper-mist-wired 09-wired-visibility-and-switch-management/01-switches-page-metrics-and-front-panel.md`.

## Decision: Keep row identity explicit for bulk review

**Rationale**: The wireless skill states that bulk operational pages must confirm identity fields such as name, MAC address, site, model, and profile before action. This scorecard is read-only, but it must still include enough identity for safe review.

**Alternatives considered**: A site-only rollup was rejected. Operators need one gateway row to confirm the device that creates each risk.

**Skill citation**: `juniper-mist-wireless 04-device-profiles-and-ap-operations/02-access-points-page-and-bulk-actions.md`.

## Decision: Default DHCP warning threshold to 80 percent

**Rationale**: FR-010 requires an `80` percent default. FR-011 allows `DHCP_POOL_WARN_PERCENT` to override it when the value is valid.

**Alternatives considered**: A fixed threshold without an environment override was rejected because FR-011 requires an override.

## Decision: Treat missing optional fields as empty or unknown

**Rationale**: Mist can omit optional gateway fields. FR-018 requires the export to continue and to use empty or clear unknown values.

**Alternatives considered**: Failing on the first missing optional field was rejected. It would block the whole organization report.
