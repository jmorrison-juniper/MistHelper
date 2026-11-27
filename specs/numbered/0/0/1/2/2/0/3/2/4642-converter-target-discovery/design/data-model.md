# Data Model: Read-only Mist target discovery

The discovery stores no data. It returns values for one request and keeps them in memory. No table, file, or cache holds a result. The entities below define the values that the API returns.

## Entity: DiscoveryResult

One outcome of one check.

| Field | Type | Rule |
| - | - | - |
| `check` | text | One of `status`, `sites`, or `gateways`. |
| `state` | text | One of `verified`, `unavailable`, `denied`, or `failed`. |
| `reason` | text | One reason code from `design/contracts/discovery-http.md`. The value `none` appears only with `verified`. |
| `org_id` | UUID or null | Null for `status`. Set for `sites` and `gateways`. |
| `pages` | integer | Zero when no request reached Mist. At most 50. |
| `items` | list or null | A list only when `state` is `verified`. Null for every other state (FR-003). |

Invariants:

- A verified result holds a list, possibly empty. An empty list means verified absence (FR-002).
- A result that is not verified holds null `items`. A client never reads an empty list as absence for those states.
- `pages` never exceeds 50 (FR-010).

## Entity: SiteTarget

One site in a verified site check.

| Field | Type | Rule |
| - | - | - |
| `id` | UUID | Natural key from the Mist site record (R63). The only selection key. |
| `name` | text | Display text from the Mist site record (R64). Not a key. |
| `duplicate_name` | boolean | True when another site has the same name after trimming spaces (R12). |

## Entity: GatewayTarget

One gateway in a verified gateway check.

| Field | Type | Rule |
| - | - | - |
| `id` | UUID | Device identifier from the inventory item (R61). The natural key for selection. |
| `mac` | text | MAC address from the inventory item. Display and matching only. |
| `serial` | text | Serial number from the inventory item. Display only. |
| `model` | text | Model from the inventory item. Display only. |
| `name` | text | Display name from the inventory item. Not a key. |
| `site_id` | UUID or null | The assigned site (R62). Null or empty means unassigned (U2). |
| `assignment` | text | `assigned` when `site_id` has a value. Otherwise `unassigned` (FR-012). |

## Entity: OrganizationMembership

One privilege entry from the `getSelf` response, used only for the membership check.

| Field | Type | Rule |
| - | - | - |
| `org_id` | UUID | Organization identifier (R59). A check passes when one entry matches the requested `org_id`. |
| `scope` | text | Privilege scope (R60). Returned to the client as stated. |
| `role` | text | Privilege role. Returned to the client as stated. |

## Constants

| Name | Value | Source |
| - | - | - |
| Rows per page | 1000 | Repository precedent (R28), and the shared page limit that the portal uses. |
| Maximum pages per list | 50 | Design decision D-7. |

## State Transitions

```text
pending (page label only, before the first check)
  -> check starts
  -> verified      (complete read, items set)
  -> unavailable   (no session, rate limit, service unavailable, no status)
  -> denied        (401, 403, or organization not a membership)
  -> failed        (other HTTP error, malformed data, incomplete read, page bound, exception)
```

- A new check replaces the previous result on the page.
- A target change does not change the discovery state. It dispatches `cisco-target-changed`, and issue #4641 clears the review (FR-014).
- Discovery keeps no state after the response. A reload starts at `pending`.
