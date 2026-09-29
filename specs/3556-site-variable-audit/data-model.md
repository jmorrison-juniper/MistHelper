# Data Model: Site Variable Audit

## Entity: Site

**Purpose**: Represents one Mist site that can receive assigned templates and
site variable values.

**Fields**:

| Field | Type | Required | Rule |
| - | - | - | - |
| `site_id` | string | Yes | Use the Mist site `id`. |
| `site_name` | string | Yes | Use the Mist site `name`, or a clear fallback if absent. |
| `assigned_templates` | list of `TemplateReference` | Yes | Include gateway templates, network templates, and WLANs. |
| `defined_variables` | set of strings | Yes | Normalize names from `searchOrgVars`. |

**Relationships**:

- A site has zero or more assigned templates.
- A site has zero or more defined variables.
- A site has one summary row.
- A site has zero or more missing variable findings.

## Entity: TemplateReference

**Purpose**: Represents a template body that can apply to a site.

**Fields**:

| Field | Type | Required | Rule |
| - | - | - | - |
| `template_id` | string | Yes | Use the Mist record `id` when present. |
| `template_type` | string | Yes | Use `gateway_template`, `network_template`, or `wlan`. |
| `template_name` | string | Yes | Use the Mist name field, or a clear fallback if absent. |
| `body` | mapping or list | Yes | Preserve nested data for token scanning. |
| `site_ids` | set of strings | Yes | Hold all sites that receive the template. |

**Relationships**:

- A template reference can apply to one or more sites.
- A template reference can contain zero or more variable token uses.

## Entity: VariableTokenUse

**Purpose**: Represents one `{{name}}` token found in a template field.

**Fields**:

| Field | Type | Required | Rule |
| - | - | - | - |
| `variable_name` | string | Yes | Trim spaces inside braces. Reject empty names. |
| `field_path` | string | Yes | Use a deterministic JSON path with list indexes. |
| `template_type` | string | Yes | Copy from the template reference. |
| `template_name` | string | Yes | Copy from the template reference. |
| `template_id` | string | Yes | Copy from the template reference. |

**Validation rules**:

- Accept `{{name}}` and `{{ name }}`.
- Accept underscores in names.
- Reject names that contain spaces after trimming.
- Ignore malformed brace text.

## Entity: SiteVariableDefinition

**Purpose**: Represents one site variable returned by `searchOrgVars`.

**Fields**:

| Field | Type | Required | Rule |
| - | - | - | - |
| `site_id` | string | Yes | Use the site scope from the search result. |
| `variable_name` | string | Yes | Normalize to the same form as token names. |
| `source` | string | No | Preserve source when present for diagnostics. |

**Relationships**:

- A variable definition belongs to one site.
- A variable definition can satisfy one or more token uses.

## Entity: MissingVariableFinding

**Purpose**: Represents one row in `SiteVariableAudit.csv`.

**Fields**:

| Field | Type | Required | Rule |
| - | - | - | - |
| `site_name` | string | Yes | Sort by this field first. |
| `site_id` | string | Yes | Include stable evidence for duplicate site names. |
| `template_type` | string | Yes | Use the normalized template type. |
| `template_name` | string | Yes | Name the assigned template. |
| `template_id` | string | Yes | Include stable evidence for duplicate names. |
| `variable_name` | string | Yes | Name the missing variable. |
| `field_path` | string | Yes | Name the field that uses the variable. |

**Deterministic order**:

Sort by `site_name`, `site_id`, `template_type`, `template_name`,
`variable_name`, and `field_path`.

## Entity: SiteVariableSummary

**Purpose**: Represents one row in `SiteVariableSummary.csv`.

**Fields**:

| Field | Type | Required | Rule |
| - | - | - | - |
| `site_name` | string | Yes | Sort by this field first. |
| `site_id` | string | Yes | Include stable evidence for duplicate site names. |
| `assigned_templates` | string | Yes | Join sorted template display names. |
| `required_variable_count` | integer | Yes | Count unique required variable names for the site. |
| `defined_variable_count` | integer | Yes | Count unique defined variable names for the site. |
| `missing_count` | integer | Yes | Count unique required names that are not defined. |
| `unused_variable_count` | integer | Yes | Count unique defined names that are not required. |
| `unused_variable_names` | string | Yes | Join sorted unused names. |

**Deterministic order**:

Sort by `site_name` and `site_id`.

## Entity: SiteVariableAuditResult

**Purpose**: Carries complete model output to the operation layer.

**Fields**:

| Field | Type | Required | Rule |
| - | - | - | - |
| `findings` | list of `MissingVariableFinding` | Yes | Feed `SiteVariableAudit.csv`. |
| `summaries` | list of `SiteVariableSummary` | Yes | Feed `SiteVariableSummary.csv`. |
| `missing_site_count` | integer | Yes | Count distinct sites with at least one finding. |

## State Transitions

```text
raw Mist records
  -> normalized sites, templates, variables
  -> token uses by template
  -> site required and defined variable sets
  -> missing findings and site summaries
  -> CSV rows and console summary
```

The model layer performs only the middle three transitions. The client layer
loads raw Mist records. The operation layer writes CSV reports and prints the
console summary.
