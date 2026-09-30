# Data Model: Organization WAN Edge Scorecard

## Organization

| Field | Type | Required | Notes |
| - | - | - | - |
| `org_id` | string | Yes | Reporting scope. |
| `name` | string | No | Used only when available from existing context. |

## Site

| Field | Type | Required | Notes |
| - | - | - | - |
| `site_id` | string | Yes | Grouping key for site summary rows. |
| `site_name` | string | No | Empty when gateway stats do not include a site name. |

## WanGateway

| Field | Type | Required | Notes |
| - | - | - | - |
| `gateway_id` | string | Yes | Stable gateway identifier from Mist statistics. |
| `site_id` | string | Yes | Site grouping key. |
| `site_name` | string | No | Display value for report readers. |
| `name` | string | No | Gateway display name. |
| `model` | string | No | Gateway platform model. |
| `version` | string | No | Running or reported version from gateway stats. |
| `predominant_version` | string | Yes | Most common gateway version in the organization data set. |
| `version_compliant` | boolean | Yes | True when `version` matches `predominant_version`. |
| `config_status` | string | No | Gateway configuration state. |
| `ha_state` | string | No | HA or cluster state when available. |
| `cluster_peer_state` | string | No | Peer state when available. |
| `service_status_summary` | string | No | Compact service status string. |
| `dhcp_pool_count` | integer | Yes | `0` when DHCP data is absent. |
| `worst_pool_utilization_percent` | number | No | Highest DHCP pool utilization for the gateway. |
| `vpn_peers_up` | integer | Yes | Count of peers with `up` true. |
| `vpn_peers_down` | integer | Yes | Count of peers with `up` false. |
| `bgp_peers_established` | integer | Yes | Count of established BGP peers. |
| `bgp_peers_not_established` | integer | Yes | Count of non-established BGP peers. |
| `uptime_days` | number | No | Uptime converted to days when possible. |
| `last_trouble` | string | No | Latest trouble or event summary when available. |

### Validation rules

- `gateway_id` must be unique in `WanEdgeScorecard.csv`.
- If `dhcpd_stat` is absent, `dhcp_pool_count` must be `0`.
- If a VPN peer has `up` false, it must increase `vpn_peers_down`.
- If a BGP peer is not established, it must increase `bgp_peers_not_established`.
- If a percent cannot be calculated safely, the output must use an empty value.

## DhcpPool

| Field | Type | Required | Notes |
| - | - | - | - |
| `gateway_id` | string | Yes | Parent gateway identity. |
| `gateway_name` | string | No | Parent gateway display name. |
| `site_id` | string | Yes | Parent site identity. |
| `site_name` | string | No | Parent site display name. |
| `pool_name` | string | No | Mist DHCP pool name. |
| `leased_count` | integer | Yes | Leased address count. |
| `total_count` | integer | Yes | Total address count. |
| `utilization_percent` | number | No | `leased_count / total_count * 100` when total is greater than zero. |
| `warn_threshold_percent` | number | Yes | Default `80`, or a valid `DHCP_POOL_WARN_PERCENT` value. |
| `over_threshold` | boolean | Yes | True when utilization is at or above the threshold. |

### Validation rules

- `total_count` must not be used as a divisor when it is zero or missing.
- Missing DHCP pool data must create no `DhcpPool` row.
- The gateway row worst pool value must equal the highest pool value for that gateway.

## SiteScorecard

| Field | Type | Required | Notes |
| - | - | - | - |
| `site_id` | string | Yes | Site grouping key. |
| `site_name` | string | No | Site display name. |
| `gateway_count` | integer | Yes | Count of gateways used for the site score. |
| `config_success_percent` | number | Yes | Percent of gateways with successful configuration state. |
| `version_compliance_percent` | number | Yes | Percent of gateways with compliant version. |
| `wan_edge_uptime_percent` | number | Yes | Percent of gateways that meet the uptime rule. |
| `potential_anomalies_percent` | number | Yes | `100` when no gateway has an anomaly. |

### Validation rules

- A site with no gateways must not create a site scorecard row.
- Site percentages must use the same gateway rows written to `WanEdgeScorecard.csv`.
- Percent values may differ by no more than one percentage point from test expectations.

## OrganizationScorecard

| Field | Type | Required | Notes |
| - | - | - | - |
| `gateway_count` | integer | Yes | Count of gateways in the report. |
| `site_count` | integer | Yes | Count of sites with at least one gateway. |
| `config_success_percent` | number | Yes | Organization-wide configuration success. |
| `version_compliance_percent` | number | Yes | Organization-wide version compliance. |
| `wan_edge_uptime_percent` | number | Yes | Organization-wide uptime score. |
| `potential_anomalies_percent` | number | Yes | Organization-wide anomaly score. |

### Validation rules

- Organization percentages must use the same gateway rows written to `WanEdgeScorecard.csv`.
- Console values must match the organization model within one percentage point.
