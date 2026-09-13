# Data Model: Global Wired Client Search Report

## Entity: WiredClientSearchCriteria

Represents the operator-defined filter settings for a run.

| Field | Type | Required | Notes |
| - | - | - | - |
| mac_operator | enum | No | One of shared operator catalog |
| mac_value | string | Conditional | Required for value-based operators |
| manufacturer_operator | enum | No | One of shared operator catalog |
| manufacturer_value | string | Conditional | Required for value-based operators |

### Operator Catalog

`is`, `is not`, `contains`, `doesn't contain`, `starts with`, `doesn't start with`, `ends with`, `doesn't end with`, `is blank`, `is not blank`, `is null`, `is not null`

### Validation Rules

- Value-required operators must have non-empty normalized input.
- Blank/null operators ignore provided values.
- If both fields are configured, final inclusion uses logical AND.

## Entity: WiredClientRecord

Normalized representation of each retrieved wired client entry used for local filtering and output.

| Field | Type | Required | Notes |
| - | - | - | - |
| mac | string | Yes/Expected | Normalized for MAC operator evaluation |
| manufacturer | string/null | No | Normalized for manufacturer operator evaluation |
| raw_record | object | Yes | Original retrieved client payload for export fidelity |

## Entity: FilteringDecisionMetadata

Run-level metrics used in output summary sections.

| Field | Type | Required | Notes |
| - | - | - | - |
| remote_filter_used | boolean | Yes | Whether remote prefiltering was attempted/applied |
| local_filter_used | boolean | Yes | Always true when any filter is provided |
| records_retrieved | integer | Yes | Count before final local evaluation |
| records_matched | integer | Yes | Final matched count |
| generated_at | datetime string | Yes | Run timestamp |

## Entity: GlobalWiredClientReport

Final report payload persisted through local artifact and standard export path.

| Field | Type | Required | Notes |
| - | - | - | - |
| summary | FilteringDecisionMetadata | Yes | Header/summary metadata |
| matched_records | list[WiredClientRecord/raw export rows] | Yes | Final dataset after operator evaluation |

## State Flow

1. Load org context and criteria (`WiredClientSearchCriteria`)
2. Retrieve records (with optional remote prefilter)
3. Normalize/evaluate operators locally against `WiredClientRecord`
4. Produce `GlobalWiredClientReport`
5. Write outputs via local artifact + standard export flow
