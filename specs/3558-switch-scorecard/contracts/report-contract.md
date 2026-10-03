# Contract: Organization Switch Scorecard

## Operation Contract

| Item | Value |
| - | - |
| Menu | `277` |
| Category | `safe` |
| Handler import | `src.mist.intelligence.reports.switch_scorecard.operation` |
| Handler attribute | `SwitchScorecard.run` |
| Prompt behavior | No prompt |
| Mist API | `listOrgDevicesStats` |
| Mist API filter | `type="switch"` |

## Detail Output Contract

File: `SwitchScorecard.csv`

The detail output has one row for each switch. Required columns are:

- `site_id`
- `site_name`
- `switch_name`
- `switch_mac`
- `model`
- `version`
- `predominant_model_version`
- `version_compliant`
- `config_status`
- `config_success`
- `ap_count`
- `affinity_limit`
- `affinity_exceeded`
- `redundant_ap_count`
- `poe_budget_watts`
- `poe_draw_watts`
- `pending_versions`
- `bios_versions`
- `fpga_versions`
- `backup_versions`
- `fan_errors`
- `psu_errors`
- `temperature_errors`
- `uptime_days`
- `last_trouble`

## Site Output Contract

File: `SwitchScorecardBySite.csv`

The site output has one row for each site with at least one switch. Required columns are:

- `site_id`
- `site_name`
- `switch_count`
- `switch_ap_affinity_percent`
- `switch_ap_affinity_count`
- `poe_compliance_percent`
- `poe_compliance_count`
- `version_compliance_percent`
- `version_compliance_count`
- `switch_uptime_percent`
- `switch_uptime_count`
- `config_success_percent`
- `config_success_count`
- `potential_anomalies_percent`
- `potential_anomalies_count`

## Environment Contract

| Variable | Default | Valid value |
| - | - | - |
| `SWITCH_AP_AFFINITY_LIMIT` | `12` | Positive integer |

Invalid values use the default and add a console summary note.

## Test Contract

Unit tests must prove these requirements:

1. The client uses the shared API fetcher with `type="switch"`.
2. The default AP affinity threshold is `12`.
3. A valid environment override changes the threshold.
4. The predominant version is computed per model.
5. A missing `module_stat` produces empty module columns.
6. The site output includes percentages and counts for each tile.
7. The operation writes both required output files.
