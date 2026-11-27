# Contract: HTTP routes

Base prefix: the WAN performance blueprint uses `/wan-performance` (`routes.py` line 24, R93). The live blueprint uses `/live` (`live_routes.py` line 43, R92).

## Live routes (`/wan-performance/live/`)

| Method | Path | Handler | Page | Source |
|---|---|---|---|---|
| GET | `/wan-performance/live/` | overview | overview page | R92 (line 268) |
| GET | `/wan-performance/live/site/<site_id>` | site view | site page | R135 (line 275) |
| GET | `/wan-performance/live/gateway/<gateway_id>` | gateway view | gateway page | R135 (line 281) |
| GET | `/wan-performance/live/port/<site_id>/<path:port_name>` | port view | WAN port page | R135 (line 287) |
| GET | `/wan-performance/live/vpn/<site_id>/<peer_mac>` | peer view | VPN peer page | R135 (line 295) |
| POST | `/wan-performance/live/refresh` | overview refresh | overview page | R135 (line 304) |
| POST | `/wan-performance/live/refresh-port` | port refresh | WAN port page | R135 (line 326) |
| POST | `/wan-performance/live/refresh-peer` | peer refresh | VPN peer page | R135 (line 354) |

## Synthetic preview routes (`/wan-performance/preview/`)

The synthetic preview paths replace the PR 4208 root paths (D-6). The PR 4208 root paths appear in R136.

| Method | Path | Page | Source |
|---|---|---|---|
| GET | `/wan-performance/preview/` | synthetic overview | R136 (line 77) |
| GET | `/wan-performance/preview/gateway/<gateway_id>` | synthetic gateway | R136 (line 94) |
| GET | `/wan-performance/preview/port/<site_id>/<path:port_name>` | synthetic WAN port | R136 (line 115) |
| GET | `/wan-performance/preview/vpn/<site_id>/<peer_mac>` | synthetic VPN peer | R136 (line 142) |

## Out-of-scope routes

- The SLE route `/sle` (`live_routes.py` line 259) and the replacement route (`live_routes.py` line 260) are out of scope (spec.md, Out of Scope).

## Response rules

- A valid request returns status 200 with HTML.
- An invalid identifier returns status 400 before any Mist call or store query (FR-007).
- A Mist API error, a store error, or a Redis error returns status 200 with a named state (FR-015). The page never shows a server error page.
- Each POST route requires the CSRF token from the existing protection (FR-013).
- Each synthetic route sets the banner and `data_origin` set to `synthetic` (FR-004).
- Each live route excludes synthetic records (FR-004, SC-005).
