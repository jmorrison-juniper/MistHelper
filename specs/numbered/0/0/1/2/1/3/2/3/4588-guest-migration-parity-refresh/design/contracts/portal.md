# Portal surface contract

This contract defines the proposed target routes inside one feature blueprint. It is a design proposal. Route registration waits for [D-4](../research.md#d-4-target-pin-and-shared-file-ownership), and route availability waits for [D-6](../research.md#d-6-operator-access-and-write-authority).

## Route map

| Source surface | Proposed target surface | Contract |
| --- | --- | --- |
| `/` (S01 L85 to L88) | `/guest-authorizations/` | Existing portal shell with a stable guest tab and scoped content. |
| `POST /api/test-connection` (S01 L91 to L99) | `GET /guest-authorizations/api/connection` | Read-only session status. No automatic organization selection (P055). |
| `GET /api/sites` (S01 L123 to L128) | `GET /guest-authorizations/api/sites` | Approved organization binding. Absence and failure stay distinct. |
| `GET /api/sites/<site_id>/wlans` (S01 L147 to L152) | `GET /guest-authorizations/api/sites/<site_id>/wlans` | Exact applicable guest WLAN list. |
| `GET /api/sites/<site_id>/wlans/<wlan_id>/guests` (S01 L159 to L164) | Scoped review API in the feature namespace. | Verified scope, observation revision, and permitted fields only. |
| `POST /api/sites/<site_id>/wlans/<wlan_id>/guests` (S01 L171 to L184) | Reviewed grant request, then confirmed grant request. | CSRF, approved operator, typed `GRANT` word, exact payload, durable intent. |
| `PUT /api/sites/<site_id>/wlans/<wlan_id>/guests/<guest_mac>` (S01 L234 to L255) | Reviewed update or extension request, then confirmed request. | Separate detail and duration actions. No implicit extension. Typed `UPDATE` or `EXTEND` word. |
| `DELETE /api/sites/<site_id>/wlans/<wlan_id>/guests/<guest_mac>` (S01 L210 to L231) | Reviewed revoke request. Not enabled. | D-8 controls the operation. A browser verb does not establish cloud semantics. |
| `GET /api/sites/<site_id>/clients/search` (S01 L270 to L276) | Scoped client search in the feature namespace. | Exact-site search and approved client fields only. |
| `GET /api/csv-template` (S01 L285 to L334) | `GET /guest-authorizations/api/csv-template` | Ten declared headers and fictional examples. No secret content. |
| `GET /api/sites-wlans-map` (S01 L349 to L362) | Server-side scope resolver. | Unambiguous ID resolution inside the approved scope. No browser-global map authority. |
| `POST /api/bulk-import` (S01 L377 to L407) | Batch preview, confirmation, execution, and status routes. | Reviewed immutable rows, D-11 limits, D-12 audit, and no blind replay. |
| `GET /health` (S01 L423 to L424) | Existing MistHelper health surface. | No second health server. |

Source URLs and payloads do not become target compatibility promises.

## Response categories

Every response uses one of these categories: `unavailable`, `denied`, `invalid`, `stale`, `rejected`, `rate_limited`, `success`, `unknown`, or `unstarted`.

- Each response binds to an opaque operation reference and the exact permitted scope.
- The response never includes a credential, a private rejected payload, or a full MAC in a URL.
- The response never includes a raw token name. The operator sees the approved actor reference.

## Input rules

- Validate every route input before use. Return at the first failure (AGENTS.md, input and data).
- Accept only the MAC formats approved by P022.
- Accept `minutes` only as an integer from 0 to 259200 (D-7).
- Reject unknown JSON fields for a write route. Do not ignore them silently.
- Render every external value as text. Escape it in HTML and neutralize spreadsheet formula text in any CSV output.

## Navigation and ownership

- The guest tab reaches only registered guest routes. It does not change other portal pages (TEST-001).
- The feature adds one blueprint registration and one navigation entry after PR 4208 closes or the owner hands over the files (D-4).
- Shared configuration keys stay in the existing configuration loader (T05 L65 to L84).
