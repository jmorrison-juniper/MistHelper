# WAN Dashboard Interface Contract

This document defines the browser-facing contract for the read-only MistCircuitStats tab. Route names are proposed for planning. Implementation must follow MistHelper's route and response conventions.

## Portal Page

| Item | Contract |
|---|---|
| Navigation | Add a `WAN Dashboard` link to the existing MistHelper navigation. |
| Page | Render the dashboard inside the current portal shell and security middleware. |
| Access | Use the active Mist session and its authorized organization. |
| Empty state | Explain when no gateways, ports, or data exist. |
| Failure state | Show a clear error or stale-data notice. Never represent a failed request as a successful empty result. |
| Accessibility | Use semantic headings, labels, keyboard-operable controls, and stable test identifiers. |

## Read-Only Data Interfaces

| Proposed route | Purpose | Required input | Response behavior |
|---|---|---|---|
| `/wan-dashboard` | Render the page | None | Requires existing portal access. |
| `/wan-dashboard/api/overview` | Read organization gateways and port totals | Optional site, gateway, and search filters | Return validated rows and explicit status metadata. |
| `/wan-dashboard/api/gateways/<device_id>/ports` | Read gateway port details and peer paths | Gateway identifier | Reject an identifier outside the selected organization. |
| `/wan-dashboard/api/gateways/<device_id>/ports/<port_id>/traffic` | Read a traffic chart | Gateway, port, and one of `1h`, `6h`, `24h`, `7d` | Return timestamped samples for the requested range. |
| `/wan-dashboard/api/gateways/<device_id>/ports/<port_id>/insights` | Read WAN Insights | Gateway, port, and one of `1h`, `6h`, `24h`, `3d`, `7d` | Return available bandwidth, link health, and SLE values. |
| `/wan-dashboard/api/gateways/export` | Export selected gateway rows | Validated filters | Return CSV with a safe filename and formula-neutralized cells. |
| `/wan-dashboard/api/gateways/<device_id>/ports/<port_id>/hourly/export` | Export hourly port metrics | Gateway, port, and valid range | Return the source's 12-column CSV layout. |

## Mist Transport

Every Mist call must use a documented SDK method from the specification. The caller must validate the organization, site, device, port, and time range before the request. Calls must use explicit arguments.

## Error Semantics

| Condition | Required result |
|---|---|
| Invalid range or identifier | Reject the request and return an input error. |
| Unauthorized organization or gateway | Reject the request without exposing data. |
| HTTP 429 with another valid token available | Try each authorized token at most once per Mist SDK request. Honor the existing 60-second per-token cooldown. |
| All configured tokens are rate-limited | Retain the last successful data and return a rate-limit status. |
| Mist 4xx, 5xx, timeout, or malformed response | Return an explicit failure status. Do not return success with empty data. |
| Shared cache unavailable | Read Mist through the existing session when safe, or return a clear service status. Do not create another cache service. |
| No source records | Return an explicit empty-data status. |

Responses and logs must not contain API tokens. Escape Mist-provided text before rendering. Neutralize formula-leading values before writing CSV.

## End-to-End Test Identifiers

Use stable attributes for:

- `data-testid="wan-dashboard-tab"`
- `data-testid="wan-site-filter"`
- `data-testid="wan-gateway-search"`
- `data-testid="wan-gateway-table"`
- `data-testid="wan-gateway-row"`
- `data-testid="wan-port-details"`
- `data-testid="wan-traffic-range"`
- `data-testid="wan-insights-range"`
- `data-testid="wan-gateway-export"`
- `data-testid="wan-port-export"`
- `data-testid="wan-status"`
