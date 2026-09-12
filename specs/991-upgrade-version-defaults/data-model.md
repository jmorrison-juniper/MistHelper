# Data Model: Per-Type Upgrade Version Defaults

## Device type

The selector supports exactly `ap`, `switch`, and `gateway`. A device must have
a supported type, normalized MAC address, and model to become eligible.

## Returned version

The portal reads a returned version from `versions_by_model`. The selector
trims surrounding whitespace and uses the normalized exact value for matching.
It retains the returned display value for the page and saved target.

## Compatible candidate

| Field | Type | Rule |
| --- | --- | --- |
| `device_type` | string | One of `ap`, `switch`, or `gateway`. |
| `version` | string | An exact normalized version present for every eligible device of the type. |
| `numeric_key` | tuple of integers | Numeric version components used to rank candidates. |

The selector creates candidates by intersecting the version sets for all
eligible devices of one type. A type with no eligible device or no intersection
has no candidate.

## Type selection

| Field | Type | Rule |
| --- | --- | --- |
| `device_type` | string | The type that owns the selection. |
| `candidates` | list of strings | Common compatible returned versions, in numeric rank order. |
| `selected_version` | string or null | A compatible override, else the highest candidate, else null. |
| `override_value` | string or null | The trimmed value from the mapped environment variable. |
| `warning` | string or null | A clear message when no common candidate exists. |

A valid override equals a normalized compatible candidate exactly. A blank,
malformed, unavailable, or incompatible override does not become a selection.

## Saved target

The existing target record remains the persisted form. It contains `mac`,
`device_type`, `model`, `version_before`, and `version_target`, plus existing
progress fields. A save accepts a `version_target` only when current inventory
recognizes the device, its current type matches the selected type, and current
returned availability offers the version. A failed save changes no target or
option field.

## State rules

1. The options view reads inventory and availability, then calculates defaults.
2. The browser applies a type selection only to matching device rows that offer
   the exact version.
3. The save path reads inventory and availability again, then validates targets.
4. The save path writes a plan only after all submitted targets pass.
5. The confirmation and start path remains unchanged and requires `CONFIRM`.
