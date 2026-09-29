# Data Model: Organization Switch Scorecard

## Entity: SwitchStat

One runtime switch record from `listOrgDevicesStats`.

| Field | Source | Rule |
| - | - | - |
| `org_id` | `org_id` | Required for export keys. |
| `site_id` | `site_id` | Empty string when absent. |
| `site_name` | `site_name` or lookup result | Empty string when absent. |
| `name` | `name` or `hostname` | Use the display name first. |
| `mac` | `mac` | Stable switch identifier. |
| `model` | `model` | Used to group versions. |
| `version` | `version` | Compared to the predominant model version. |
| `config_status` | `config_status` | `success` means compliant. |
| `ap_count` | `clients_stats.total.num_aps` or `ap_redundancy.num_aps` | Arrays are summed. |
| `redundant_ap_count` | `ap_redundancy.num_aps_with_switch_redundancy` | Empty becomes zero. |
| `uptime_seconds` | `uptime` | Converted to days. |
| `last_trouble` | `last_trouble` | Flattened into a readable value. |
| `module_stat` | `module_stat[]` | Empty list is valid. |

## Entity: SwitchScorecardRow

One output row in `SwitchScorecard.csv`.

| Field | Rule |
| - | - |
| `site_id` | Copied from the switch record. |
| `site_name` | Copied from the switch record or site lookup. |
| `switch_name` | Copied from `name` or `hostname`. |
| `switch_mac` | Copied from `mac`. |
| `model` | Copied from `model`. |
| `version` | Copied from `version`. |
| `predominant_model_version` | Most common version for this model in the organization. |
| `version_compliant` | `true` when `version` equals `predominant_model_version`. |
| `config_status` | Copied from `config_status`. |
| `config_success` | `true` when `config_status` is `success`. |
| `ap_count` | Total APs on the switch. |
| `affinity_limit` | The resolved AP limit. |
| `affinity_exceeded` | `true` when `ap_count` is greater than the limit. |
| `redundant_ap_count` | APs with switch redundancy. |
| `poe_budget_watts` | Sum of module PoE budgets when present. |
| `poe_draw_watts` | Sum of module PoE draw when present. |
| `pending_versions` | Combined module pending versions. |
| `bios_versions` | Combined module BIOS versions. |
| `fpga_versions` | Combined module FPGA versions. |
| `backup_versions` | Combined module backup versions. |
| `fan_errors` | Combined non-normal fan states. |
| `psu_errors` | Combined non-normal power supply states. |
| `temperature_errors` | Combined non-normal temperature states. |
| `uptime_days` | `uptime_seconds / 86400`, rounded to two decimals. |
| `last_trouble` | Readable trouble value. |

## Entity: SiteScorecardRow

One output row in `SwitchScorecardBySite.csv`.

| Field | Rule |
| - | - |
| `site_id` | Site identifier. |
| `site_name` | Site name from switch records. |
| `switch_count` | Total switches in the site. |
| `switch_ap_affinity_percent` | Switches not over the AP limit divided by switch count. |
| `switch_ap_affinity_count` | Count behind the affinity percentage. |
| `poe_compliance_percent` | Switches without PoE overdraw divided by switch count. |
| `poe_compliance_count` | Count behind the PoE percentage. |
| `version_compliance_percent` | Version-compliant switches divided by switch count. |
| `version_compliance_count` | Count behind the version percentage. |
| `switch_uptime_percent` | Switches with positive uptime divided by switch count. |
| `switch_uptime_count` | Count behind the uptime percentage. |
| `config_success_percent` | Config-success switches divided by switch count. |
| `config_success_count` | Count behind the config percentage. |
| `potential_anomalies_percent` | Switches without last trouble divided by switch count. |
| `potential_anomalies_count` | Count behind the anomaly percentage. |

## Validation Rules

1. If `SWITCH_AP_AFFINITY_LIMIT` is absent, use `12`.
2. If `SWITCH_AP_AFFINITY_LIMIT` is invalid, use `12` and report the fallback.
3. If a switch has no `module_stat`, module output fields stay empty.
4. If a model has a version tie, select the lexicographically first version for stable output.
5. If the API returns no switches, write both outputs with headers.
