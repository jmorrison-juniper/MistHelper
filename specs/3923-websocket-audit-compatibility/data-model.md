# Data Model: WebSocket Audit Compatibility

This plan adds no persistent model or database table. It changes two in-memory audit records.

## Read scope

| Value | Type | Source | Rule |
| - | - | - | - |
| Approved site IDs | Set of UUID strings | Valid site picker response | Replace only after the full response passes validation. |
| Approved map IDs by site | Map from site ID to a set of UUID strings | Valid map response for that site | Do not use a map from another site. |
| Approved device IDs by site | Map from site ID to a set of UUID strings | Valid device response for that site | Do not use a device from another site. |

The client path is eligible only when its site ID is approved and its device ID occurs in that site's approved device set. The request policy still requires GET, the exact origin, no query or path encoding, and no redirect.

## Dialog inspection record

Each inventory entry keeps one result record, even when inspection raises an error.

| Field | Type | Meaning |
| - | - | - |
| `key` | String | Catalog entry key used to identify the form. |
| `status` | String | Existing inspection status. |
| `observations` | List of strings | Existing sanitized audit observations. |
| `cancel` | Integer | Count of visible exact-name Cancel controls in the operation form. |
| `ux_review.findings` | List of finding records | Includes `operation-cancel` when no visible Cancel control exists. |

Zero controls produce the existing missing-cancel finding. One control records a count of one and no missing-cancel finding. Hidden controls do not contribute to the count. Duplicate visible controls produce their actual count and do not satisfy the single-control expectation.

## State transitions

1. A valid site response replaces approved site scope.
2. A valid device response for an approved site replaces that site's device scope.
3. A child client GET is allowed only when both identifiers match the registered scope.
4. An invalid response does not grant child scope.
5. Dialog inspection records its visible Cancel count with the current catalog entry. An inspection error still produces a record for that entry.
