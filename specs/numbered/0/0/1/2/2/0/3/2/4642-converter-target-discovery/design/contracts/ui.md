# Contract: Discovery UI markers and states

Scope: the discovery section in the converter page and its script. The page stays in `src/interfaces/portals/cisco_config_converter/presentation/` (R19 and R20 show the current page and script). The markers follow the repository rule for stable `data-testid` attributes in web UI tests.

## Markers

| Element | Identifier | Purpose |
| - | - | - |
| Section | `data-testid="cisco-discovery"` | Holds the whole discovery panel. |
| Organization input | `id="cisco-discovery-org"`, `data-testid="cisco-discovery-org"` | Accepts one UUID for the organization. |
| Connection check button | `data-testid="cisco-discovery-status-check"` | Starts the status check. |
| Site check button | `data-testid="cisco-discovery-sites-check"` | Starts the site check for the organization. |
| Gateway check button | `data-testid="cisco-discovery-gateways-check"` | Starts the gateway check for the organization. |
| State line | `id="cisco-discovery-state"`, `role="status"`, `aria-live="polite"`, `data-testid="cisco-discovery-state"`, attribute `data-state` | Shows the current state label. The attribute holds `pending`, `verified`, `unavailable`, `denied`, or `failed`. |
| Site selector | `data-testid="cisco-discovery-sites"` | Lists verified sites. Each option value is the site `id`. |
| Gateway list | `data-testid="cisco-discovery-gateways"` | Lists verified gateways. Each row has a checkbox labeled with the gateway name and serial. |
| Read-only notice | `data-testid="cisco-discovery-notice"` | Shows the sentence: "Read-only check. Selecting a target does not change Mist." |

## State Labels

| State attribute | Visible label |
| - | - |
| `pending` | Not checked |
| `verified` | Verified |
| `unavailable` | Unavailable |
| `denied` | Denied |
| `failed` | Failed |

## Reason Sentences

The page shows one plain sentence for each state group. The sentence never implies an empty list for a state that is not verified.

| State | Sentence |
| - | - |
| unavailable | Mist cannot answer now. Try the check again later. |
| denied | This operator session cannot read the organization. |
| failed | The check did not finish. The list is not empty. Try the check again. |
| verified with zero rows | No sites or gateways exist in this organization. |

## Duplicate Names

A duplicate site name adds the text "Duplicate name. Select by identifier." to the option label. The option value stays the site `id` (FR-011).

## Target Change Event

Each change of the site selector or a gateway checkbox dispatches `cisco-target-changed` on `document`. The event detail holds `kind` (`site` or `gateway`) and `id` (the selected identifier). Issue #4641 owns the listener that clears the review (FR-014). The page does not clear the review itself.

## Browser Storage

The script stores no value in `localStorage`, `sessionStorage`, or a cookie. The organization identifier and the selections live in page memory only (FR-007).
