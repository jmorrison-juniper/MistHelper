# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 279 | Organization WAN Edge Scorecard | src.mist.intelligence.reports.wan_edge_scorecard.scorecard | WanEdgeScorecard.run | safe |  | False | False |

## OperationRegistry comment

One `# WHY:` paragraph for menu 279:

```python
# WHY: menu 279 is safe because it reads organization gateway statistics only, writes report files under data/, and makes no Mist configuration change.
```

## Primary key strategies

No persistent endpoint primary key entry is required for this feature package.
The scorecard is a report that writes derived rows through the existing
`listOrgDevicesStats` output path. If the integration pull request elects to
store derived rows in a separate table, use this strategy:

```python
"wan_edge_scorecard_report": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["gateway_id", "site_id"],
    "indexes": ["site_id", "gateway_name", "version", "config_status"],
},
```

## copilot-instructions category table

Add menu `279` to the `safe` category row.

## Import line for MistHelper.py

```python
from src.mist.intelligence.reports.wan_edge_scorecard.scorecard import WanEdgeScorecard  # Menu 279 (issue #3560) -- export the organization WAN edge scorecard.
```

## Deferred integration notes

- Register menu `279` in `MistHelper.py` with the title `Organization WAN Edge Scorecard`.
- Register menu `279` as `safe` in `src/foundation/support/utils/operation_registry.py`.
- Update the operation count and menu table in `README.md`.
- Regenerate the menu reference and the menu API endpoint map in the integration pull request.
- Confirm the generated references include menu `279`.

## Verified data source

- `src/operations/exporting/export/org_device_stats_exporter.py` uses `listOrgDevicesStats` through the shared `APIDataFetcher` seam.
- `MistHelper.py` dispatches menu `18` through `_dispatch_gateway_stats_device_stats_with_freshness`.
- `listOrgDevicesStats` maps to `GET /api/v1/orgs/{org_id}/stats/devices`.
- The query parameters include `type`, `status`, `site_id`, and `fields`.
- The installed `mistapi` SDK exposes `mistapi.api.v1.orgs.stats.listOrgDevicesStats`.
- The implementation uses `type="gateway"` and `fields="*"`.

## Verified schema fields

- `stats_gateway` contains `config_status`, `version`, `model`, `is_ha`, `cluster_stat`, `service_status`, `dhcpd_stat`, `vpn_peers`, `bgp_peers`, `uptime`, `route_summary_stats`, and `arp_table_stats`.
- `dhcpd_stat_lan` contains `num_leased` and `num_ips`.
- `bgp_peer` contains `state`, `up`, `neighbor`, `node`, `rx_routes`, `tx_routes`, and `vrf_name`.
- `stats_gateway_vpn_peer` contains `up`, `peer_router_name`, `peer_mac`, `peer_site_id`, `port_id`, `type`, and `uptime`.

## Output files

- `WanEdgeScorecard.csv`
- `WanEdgeDhcpPools.csv`
- `WanEdgeScorecardBySite.csv`
