# Contract: Dashboard Port Series Payload and View

This contract defines the JSON that the existing traffic and insight routes return. It also defines the port view elements and their identifiers. The routes keep their paths and their cache-only behavior (R-03, R-04).

## Route Payload

The routes keep the envelope that the service already returns (R-88). The envelope holds `status`, `data`, `notice`, and `stale`. Each status maps to a data state.

| Envelope status | Data state shown | Condition |
| - | - | - |
| `ok` | `live` | The value was written in the current refresh |
| `ok` with `partial` in data | `partial` | Coverage below 1 |
| `stale` | `stale` | A prior value is shown with its collection time |
| `unavailable` | `unavailable` | No prior value exists |
| `invalid` | `unavailable` | The identifier or range is invalid |
| `forbidden` | `unavailable` | The port is not in the active gateway |

The traffic route returns a list of samples (R-03 and R-86). The insight route returns an object (R-04 and R-87). The insight object gains two fields. The field `port_totals` holds the seven-day totals. The field `coverage` holds the coverage value. The link and SLE sections stay absent for the worker values and render as unavailable.

## Port View Elements

| Element identifier | Content | Requirement |
| - | - | - |
| `wan-port-series-state` | One data state word, for example `Live` or `Partial` | FR-010 |
| `wan-port-series-collected` | The UTC collection time in ISO 8601 text | FR-010 |
| `wan-port-series-coverage` | The coverage as a percentage with no decimal places | FR-009 |
| `wan-port-derived-totals` | The seven-day RX and TX totals with the label "Derived from hourly samples" | FR-008 |

The stable identifiers follow the browser test rule in `.github/copilot-instructions.md` (R-67). The refresh controls keep their current identifiers (`wan-refresh` at line 17 in R-89 and `wan-refresh-panel` in R-90), and the state element keeps `wan-refresh-state`.

## Overview Copy

Replace the seven-day claim (R-14) with the following sentence. Use this exact text: "RX and TX counters are cumulative since the last device reboot."

The text matches the OpenAPI definition (R-41).

## Labels

- Each state word uses one spelling. The words are `Live`, `Stale`, `Partial`, and `Unavailable`.
- The port view never shows `Live` for a stale or synthetic value (FR-010).
- The port view shows the resolution `1 hour` next to every chart.
