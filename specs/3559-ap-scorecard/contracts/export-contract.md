# Export Contract: Organization Access Point Scorecard

## Operation contract

| Item | Value |
| - | - |
| Menu | `278` |
| Category | `safe` |
| Handler import | `src.mist.intelligence.reports.ap_scorecard.operation` |
| Handler attribute | `ApScorecard.run` |
| Data source | `mistapi.api.v1.orgs.stats.listOrgDevicesStats` |
| Required query | `type=ap` |
| Pagination | `APIDataFetcher` or `mistapi.get_all` through the existing seam |
| AP detail file | `ApScorecard.csv` |
| Site summary file | `ApScorecardBySite.csv` |

## API contract

The client must call `listOrgDevicesStats` with:

| Parameter | Source | Required |
| - | - | - |
| `mist_session` | `SourceDependencyResolver.apisession` | Yes |
| `org_id` | `ConfigUtils.get_cached_or_prompted_org_id()` | Yes |
| `type` | Literal `ap` | Yes |
| `limit` | Shared page size, default `1000` | Yes |

The client must not implement a custom page loop. It must call the existing `APIDataFetcher` flow or `mistapi.get_all` directly after the first SDK response.

## `ApScorecard.csv` columns

| Column | Required behavior |
| - | - |
| `site` | Use `site_name` when present. Otherwise use `site_id`. |
| `site_id` | Copy from source row. |
| `org_id` | Copy from the operation context. |
| `ap_name` | Copy from `name`. |
| `mac` | Copy from `mac`. |
| `model` | Copy from `model`. |
| `version` | Copy from `version`. |
| `predominant_version` | Calculate per model. |
| `version_compliant` | True when AP version equals expected version. |
| `status` | Copy from `status`. |
| `offline_reason` | Copy source reason when present. Otherwise use `last_trouble` summary. |
| `inactive_wired_vlans` | Join VLAN IDs. Empty means pass. |
| `switch_redundancy_count` | Normalize `switch_redundancy`. |
| `switch_redundancy_class` | `none`, `good`, `excellent`, or `unknown`. |
| `power_constrained` | Copy from `power_constrained`. |
| `power_opmode` | Copy from `power_opmode`. |
| `power_budget` | Copy from `power_budget`. |
| `lldp_power_allocated` | Copy from `lldp_stat.power_allocated`. |
| `lldp_power_needed` | Copy from `lldp_stat.power_needed` when present. |
| `config_reverted` | Copy from `config_reverted`. |
| `last_trouble` | Flatten to a readable value. |
| `expiring_certificate_count` | Count keys in `expiring_certs`. |
| `uptime_days` | Convert uptime seconds to days. |

## `ApScorecardBySite.csv` columns

| Column | Required behavior |
| - | - |
| `site` | Site display value. |
| `site_id` | Site identifier. |
| `org_id` | Organization identifier from the operation context. |
| `ap_count` | Number of APs at the site. |
| `connection_status_percent` | Connected AP percent. |
| `connection_status_band` | Color band. |
| `vlans_percent` | APs without inactive wired VLANs. |
| `vlans_band` | Color band. |
| `version_compliance_percent` | Version-compliant AP percent. |
| `version_compliance_band` | Color band. |
| `switch_redundancy_percent` | APs with redundancy count `2` or more. |
| `switch_redundancy_band` | Color band. |
| `potential_anomalies_percent` | APs with no anomaly signal. |
| `potential_anomalies_band` | Color band. |
| `switch_redundancy_none_count` | APs with count `1`. |
| `switch_redundancy_good_count` | APs with count `2`. |
| `switch_redundancy_excellent_count` | APs with count `3` or more. |

## Console summary contract

The operation must print one summary after export.

Required values:

- AP count.
- Organization `Connection Status` percentage.
- Organization `VLANs` percentage.
- Organization `Version Compliance` percentage.
- Organization `AP Switch Redundancy` percentage.
- Organization `Potential Anomalies` percentage.

## Error contract

- If the API returns no AP rows, the operation logs a clear message and writes no misleading success summary.
- If one AP lacks `lldp_stat`, the AP row keeps empty LLDP power columns and the run continues.
- If a row has invalid redundancy data, the AP row uses `unknown` and the site counts exclude it from pass counts.
- If an export write fails, the operation logs an error that names the file.
