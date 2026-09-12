# Data Model: Complete Tier 3 Capture Output

## Capture section view

| Field | Type | Rule |
| - | - | - |
| `key` | string | Stable section key. |
| `label` | string | Operator-facing heading. |
| `columns` | list of string | Safe fields in stable order. |
| `rows` | list of maps | Text values for the visible rows. |
| `held` | integer | Stored row count before the page cap. |
| `requested` | boolean | True for client groups and requested Tier 3 groups. |

## Export row

The existing common columns remain in their current order.

The repair adds these fields.

| Field | Type | Rule |
| - | - | - |
| `kind` | string | Stable row kind. |
| `details_json` | string | Compact JSON of every safe source field. |

## Stable kinds

- `device`
- `client_wired`
- `client_wireless`
- `client_guest`
- `switch_port`
- `poe`
- `radio`
- `tunnel`
- `bgp_peer`
- `alarm`

## Safety rules

1. Remove a field when its name matches the existing credential word list.
2. Disarm every CSV cell that can run as a spreadsheet formula.
3. Replace line breaks in common text columns.
4. Keep structured values in valid compact JSON.
5. Keep an empty section visible when the capture requested it.
