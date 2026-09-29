# Contract: Site Variable Audit Reports

## Inputs

The operation reads one organization through `SourceDependencyResolver`.

Required API inputs:

- Organization ID from the resolver.
- API session from the resolver.

Required Mist reads:

- Sites from `listOrgSites`.
- Gateway templates from `listOrgGatewayTemplates`.
- Network templates from `listOrgNetworkTemplates`.
- Templates from `listOrgTemplates`.
- WLANs from `listOrgWlans`.
- Device profiles from `listOrgDeviceProfiles`.
- Site variables from `searchOrgVars`.

## Output: `SiteVariableAudit.csv`

One row reports one missing variable use for one site.

Required columns:

| Column | Description |
| - | - |
| `site_name` | Mist site name. |
| `site_id` | Mist site ID. |
| `template_type` | `gateway_template`, `network_template`, or `wlan`. |
| `template_name` | Assigned template or WLAN name. |
| `template_id` | Assigned template or WLAN ID. |
| `variable_name` | Missing variable name after normalization. |
| `field_path` | JSON path for the field that contains the token. |

Ordering:

1. `site_name`
2. `site_id`
3. `template_type`
4. `template_name`
5. `variable_name`
6. `field_path`

## Output: `SiteVariableSummary.csv`

One row reports variable coverage for one site.

Required columns:

| Column | Description |
| - | - |
| `site_name` | Mist site name. |
| `site_id` | Mist site ID. |
| `assigned_templates` | Sorted display names for assigned templates and WLANs. |
| `required_variable_count` | Count of unique required variable names. |
| `defined_variable_count` | Count of unique defined variable names. |
| `missing_count` | Count of unique missing variable names. |
| `unused_variable_count` | Count of unique unused variable names. |
| `unused_variable_names` | Sorted unused names joined for display. |

Ordering:

1. `site_name`
2. `site_id`

## Console summary

The operation prints the number of sites that have at least one missing
variable.

Required message data:

- Distinct missing site count.
- Audit CSV file name.
- Summary CSV file name.

## Error behavior

If required organization data is unavailable, the operation must raise or
display a clear user-facing error. The error must identify the missing data
type without exposing secrets.

If one Mist read fails, the operation must not report success. It must stop
before writing success-shaped output.

## Non-goals

- The operation does not change Mist configuration.
- The operation does not call per-site settings retrieval.
- The operation does not write database records.
- The operation does not create the Menu 275 registration in this plan step.
