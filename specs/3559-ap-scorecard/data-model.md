# Data Model: Organization Access Point Scorecard

## Entity: ApStatsSourceRow

One `stats_ap` record from `listOrgDevicesStats` with `type=ap`.

| Field | Type | Required | Rule |
| - | - | - | - |
| `mac` | string | Yes | Use as the stable AP identifier. |
| `name` | string | No | Use an empty value when missing. |
| `site_id` | string | Yes | Use as the site key. |
| `site_name` | string | No | Use when present. Otherwise use `site_id` as the site display value. |
| `model` | string | Yes | Use with `version` to find the predominant version. |
| `version` | string | No | Empty versions are non-compliant unless no AP of that model has a version. |
| `status` | string | No | `connected` passes the connection tile. Other values fail it. |
| `last_trouble` | object | No | Keep a readable code or summary in the AP row. |
| `inactive_wired_vlans` | list[int] | No | Empty or missing passes the VLAN tile. Non-empty fails it. |
| `switch_redundancy` | object or number | No | Normalize to a redundancy count. |
| `power_constrained` | bool | No | Export as the AP power-constrained flag. |
| `power_opmode` | string | No | Export as the power operating mode. |
| `power_budget` | number | No | Export as the power budget value. |
| `lldp_stat` | object | No | Read power values only when present. |
| `config_reverted` | bool | No | Export as stale configuration evidence. |
| `expiring_certs` | object | No | Count keys to get expiring certificate count. |
| `uptime` | number | No | Convert seconds to days. |
| `auto_upgrade_stat` | object | No | Use when it contains explicit firmware compliance evidence. |

## Entity: ApScorecardRow

One export row for `ApScorecard.csv`.

| Field | Source | Validation rule |
| - | - | - |
| `site` | `site_name` or `site_id` | Must not be empty. |
| `site_id` | `site_id` | Must not be empty. |
| `ap_name` | `name` | Empty is allowed. |
| `mac` | `mac` | Must not be empty. |
| `model` | `model` | Must not be empty. |
| `version` | `version` | Empty is allowed. |
| `predominant_version` | model calculation | Predominant version for the AP model. |
| `version_compliant` | model calculation | True when AP version equals the expected version. |
| `status` | `status` | Empty is allowed. |
| `offline_reason` | source reason or `last_trouble` | Empty is allowed. |
| `inactive_wired_vlans` | `inactive_wired_vlans` | Join VLAN IDs as text. |
| `switch_redundancy_count` | normalized redundancy | Empty is allowed when source is missing. |
| `switch_redundancy_class` | model calculation | `none`, `good`, `excellent`, or `unknown`. |
| `power_constrained` | `power_constrained` | Empty is allowed when source is missing. |
| `power_opmode` | `power_opmode` | Empty is allowed. |
| `power_budget` | `power_budget` | Empty is allowed. |
| `lldp_power_allocated` | `lldp_stat.power_allocated` | Empty is required when `lldp_stat` is missing. |
| `lldp_power_needed` | `lldp_stat.power_needed` | Empty is required when source field is missing. |
| `config_reverted` | `config_reverted` | Empty is allowed when source is missing. |
| `last_trouble` | `last_trouble` | Empty is allowed. |
| `expiring_certificate_count` | `expiring_certs` key count | Zero when missing or empty. |
| `uptime_days` | `uptime / 86400` | Empty when uptime is missing. |

## Entity: SiteScorecardRow

One export row for `ApScorecardBySite.csv`.

| Field | Rule |
| - | - |
| `site` | The site display value. |
| `site_id` | The site identifier. |
| `ap_count` | Count of AP rows for the site. |
| `connection_status_percent` | Connected APs divided by AP count. |
| `connection_status_band` | Color band from the AP threshold rule. |
| `vlans_percent` | APs with no inactive wired VLANs divided by AP count. |
| `vlans_band` | Color band from the AP threshold rule. |
| `version_compliance_percent` | Version-compliant APs divided by AP count. |
| `version_compliance_band` | Color band from the AP threshold rule. |
| `switch_redundancy_percent` | APs with redundancy count `2` or more divided by AP count. |
| `switch_redundancy_band` | Color band from the AP threshold rule. |
| `potential_anomalies_percent` | APs with no anomaly signal divided by AP count. |
| `potential_anomalies_band` | Color band from the AP threshold rule. |
| `switch_redundancy_none_count` | APs with redundancy count `1`. |
| `switch_redundancy_good_count` | APs with redundancy count `2`. |
| `switch_redundancy_excellent_count` | APs with redundancy count `3` or more. |

## Entity: OrganizationSummary

The console summary for all AP rows in the run.

| Field | Rule |
| - | - |
| `ap_count` | Count all AP scorecard rows. |
| `connection_status_percent` | Connected APs divided by AP count. |
| `vlans_percent` | APs with no inactive wired VLANs divided by AP count. |
| `version_compliance_percent` | Version-compliant APs divided by AP count. |
| `switch_redundancy_percent` | APs with redundancy count `2` or more divided by AP count. |
| `potential_anomalies_percent` | APs with no anomaly signal divided by AP count. |

## Value Objects

### TileColorBand

| Band | Rule |
| - | - |
| `green` | Percentage is `98.5` or higher. |
| `orange` | Percentage is greater than `80` and less than `98.5`. |
| `red` | Percentage is `80` or lower. |

### SwitchRedundancyClass

| Class | Rule |
| - | - |
| `none` | Redundancy count is `1`. |
| `good` | Redundancy count is `2`. |
| `excellent` | Redundancy count is `3` or more. |
| `unknown` | Redundancy count is missing or invalid. |

## State Transitions

The feature has no persistent mutable state.

1. Fetch AP statistics.
2. Normalize AP statistics into `ApScorecardRow` records.
3. Aggregate rows into `SiteScorecardRow` records.
4. Aggregate rows into `OrganizationSummary`.
5. Export both files.
6. Print the console summary.
