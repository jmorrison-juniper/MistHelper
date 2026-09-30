# Contract: WAN Edge Scorecard Outputs

## Command surface

| Field | Value |
| - | - |
| Menu number | `279` |
| Safety category | `safe` |
| Handler | `WanEdgeScorecard.run()` |
| Data source | `listOrgDevicesStats` with `type=gateway` |
| Prompt behavior | No prompt in `--test` |

## Output files

| File | Rows | Purpose |
| - | - | - |
| `WanEdgeScorecard.csv` | One row per gateway | Main organization gateway scorecard. |
| `WanEdgeDhcpPools.csv` | One row per gateway and DHCP pool | DHCP pressure evidence. |
| `WanEdgeScorecardBySite.csv` | One row per site with gateways | Site tile percentages. |

## `WanEdgeScorecard.csv` columns

| Column | Rule |
| - | - |
| `site` | Use the site name when available. |
| `site_id` | Use the Mist site identifier. |
| `gateway_name` | Use the Mist gateway name when available. |
| `gateway_id` | Use the stable gateway identifier. |
| `model` | Use the gateway model from statistics. |
| `version` | Use the gateway version from statistics. |
| `predominant_version` | Use the most common gateway version in the organization. |
| `version_compliant` | True when `version` equals `predominant_version`. |
| `config_status` | Use the gateway configuration status when available. |
| `ha_state` | Use empty or unknown when HA data is absent. |
| `cluster_peer_state` | Use empty or unknown when peer data is absent. |
| `service_status_summary` | Summarize service state fields when available. |
| `dhcp_pool_count` | Use `0` when DHCP statistics are absent. |
| `worst_pool_utilization_percent` | Use the highest valid DHCP pool utilization. |
| `vpn_peers_up` | Count VPN peers with `up` true. |
| `vpn_peers_down` | Count VPN peers with `up` false. |
| `bgp_peers_established` | Count established BGP peers. |
| `bgp_peers_not_established` | Count all non-established BGP peers. |
| `uptime_days` | Convert uptime to days when possible. |
| `last_trouble` | Use latest trouble evidence when available. |

## `WanEdgeDhcpPools.csv` columns

| Column | Rule |
| - | - |
| `site` | Use the site name when available. |
| `site_id` | Use the Mist site identifier. |
| `gateway_name` | Use the parent gateway name. |
| `gateway_id` | Use the parent gateway identifier. |
| `pool_name` | Use the pool name when available. |
| `leased` | Use the leased IP count. |
| `total` | Use the total IP count. |
| `percent` | Calculate only when total is greater than zero. |
| `warn_threshold_percent` | Use `80` unless a valid environment override exists. |
| `over_threshold` | True when percent is at or above the threshold. |

## `WanEdgeScorecardBySite.csv` columns

| Column | Rule |
| - | - |
| `site` | Use the site name when available. |
| `site_id` | Use the Mist site identifier. |
| `gateway_count` | Count gateways for the site. |
| `config_success_percent` | Percent of site gateways with successful configuration. |
| `version_compliance_percent` | Percent of site gateways with compliant version. |
| `wan_edge_uptime_percent` | Percent of site gateways that meet the uptime rule. |
| `potential_anomalies_percent` | `100` when no site gateway has an anomaly. |

## Console summary

The console summary must print the organization gateway count, site count, `Config Success`, `Version Compliance`, `WAN Edge Uptime`, and `Potential Anomalies`.

## Failure behavior

- Missing optional fields must not stop the report.
- Invalid `DHCP_POOL_WARN_PERCENT` must fall back to `80`.
- Missing gateway statistics must produce empty report files and a clear summary.
- A fetch failure must report the error through repository-standard logging.
