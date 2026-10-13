# Data Model: Mist Organization Licensing Comparison

**Date**: 2026-10-13
**Feature**: [spec.md](spec.md)

## Organization Choice

Represents an organization available to the shared Mist session.

| Field | Meaning | Validation |
| - | - | - |
| `org_id` | Mist organization identifier | Must match a server-side organization grant |
| `name` | Name shown to the operator | Escape before HTML rendering |
| `access_scope` | Direct organization or MSP grant | Must come from the shared session |

## Organization Comparison

Represents Mist data for one selected organization.

| Field | Meaning | Validation |
| - | - | - |
| `org_id` | Selected Mist organization | Must be in the current server-side access list |
| `license_summary` | License types and totals | Preserve the SDK response shape |
| `license_use_by_site` | License use by site | Distinguish an empty result from a failed request |
| `inventory` | Inventory records or totals | Do not fabricate a zero result after failure |
| `request_status` | Success or visible error | Keep status separate from values |

## Browser Comparison State

Represents operator input for the current browser session.

| Field | Meaning | Validation |
| - | - | - |
| `selected_org_ids` | Selected Mist organizations | Revalidate on the server before each Mist request |
| `manual_rows` | Operator-entered organization values | Reject blank required fields, invalid numbers, and duplicate rows |
| `purchased_amounts` | Purchased counts by license type | Require finite, non-negative whole numbers |
| `updated_at` | Latest browser-session edit time | Use UTC ISO 8601 when recorded |

The browser keeps this state in `sessionStorage`. A closed browser session removes the state. The API must not write it to a database, Redis, or another durable service.

## License Balance

Represents one license type for one organization.

| Field | Meaning | Validation |
| - | - | - |
| `license_type` | License identifier | Match the returned license type or known bundle component |
| `used_count` | Reported use | Preserve missing and failed values as unavailable |
| `purchased_count` | Operator-entered purchase count | Non-negative whole number or unavailable |
| `remaining_count` | Purchased count less use | Calculate only when both inputs are valid |
| `bundle_components` | Component license types in a SUB-AI bundle | Preserve each component as a distinct balance |

## Comparison Export

Represents a CSV created only after an operator requests an export.

| Field | Meaning | Validation |
| - | - | - |
| `organization` | Organization name and ID | Escape CSV delimiters and neutralize formula prefixes |
| `license_type` | License or bundle component | Use the displayed label |
| `used_count` | Reported use | Keep unavailable values distinct from zero |
| `purchased_count` | Browser-session input | Include only when supplied |
| `remaining_count` | Calculated balance | Include only when both source values are valid |
| `inventory` | Displayed inventory values | Match the current comparison |
| `request_status` | Result or error status | Include failures without hiding successful organizations |

## State Flow

1. The portal loads accessible organization choices from the shared session.
2. The operator selects organizations and enters optional manual and purchased values.
3. The portal validates each organization and value before processing.
4. The comparison service reads license and inventory data through the Mist SDK.
5. The page shows each result with its request status.
6. An explicit export action writes the current comparison through the shared exporter.
7. Browser-session values expire when the browser session ends.
