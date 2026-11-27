# Contract: Gateway History Page

## Identity

- Method and path: `GET /wan-performance/live/gateway/<gateway_id>`, with the query value `site_id`. The route is defined at `src/interfaces/wan_performance/presentation/live_routes.py` line 282 (R93). The end-to-end test E1 requests this path (R31).
- Path value `gateway_id`: the gateway identifier.
- Query value `site_id`: the site identifier.

## Selection

The page keeps the cached records whose identity names both `gateway_id` and `site_id` exactly (R94). The page passes those records to the history read.

## Responses

| Case | Status | Visible result | Evidence |
| - | - | - | - |
| No record matches both values | 404 | Description: `The requested WAN identity is absent from the cached organization.` | R95 |
| One gateway resolves in the service organization | 200 | Calendar summaries from the history store. E1 checks the daily summary text. | R20, R99 |
| Two or more gateways, or a gateway of another organization | 200 | Gateway refusal message: `Select records for exactly one full gateway identity to read history.` | R23, R24, R99 |
| History store is absent | 200 | `History is unavailable. The selected application store is not available.` | R96 |
| History store read raises a listed error | 200 | `History is unavailable. The selected application store did not return valid records.` | R97 |

## Side Effects

- The route reads the snapshot cache and the history store. It writes nothing to either store.
- The route sends no Mist request (FR-007).
- The refresh routes are outside this contract. This change edits none of them.

## Logging

- The history read logs an info line before the resolution and the read, and a debug line after each one (T004).
- Each log line carries counts only. No identifier, token, or password appears in a log line.
- A storage error logs the exception with the existing message.
