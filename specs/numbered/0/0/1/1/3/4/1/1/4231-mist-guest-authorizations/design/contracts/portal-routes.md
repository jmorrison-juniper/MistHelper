# Contract: Portal Routes

## Scope

These Flask routes sit under `/guest-access`. The blueprint `GuestAccessBlueprint` in `presentation/routes.py` owns them. The routes exist only when `GUEST_ACCESS_ENABLED` is true (FR-001). When the flag is false, each route returns 404 and makes zero Mist calls (TC-031).

Once D-11 is approved, every route requires an authenticated operator (FR-005). Every POST route requires a CSRF token. The app enables `CSRFProtect` at `web_portal/services/config.py` line 301 (R-48).

## Routes

| Method | Path | Purpose | Mist calls | Write | Typed word |
| --- | --- | --- | --- | --- | --- |
| GET | /guest-access | Site and WLAN selectors | `listOrgSites` and `listSiteWlans` | No | None |
| GET | /guest-access/authorizations | Masked guest list for one WLAN | `listSiteAllGuestAuthorizations` with `wlan_id` | No | None |
| POST | /guest-access/review | Validate one change and return the review panel and hash | None | No | None |
| POST | /guest-access/grant | Grant one guest authorization | `updateSiteGuestAuthorization` and `getSiteGuestAuthorization` | Yes, blocked until G5 | GRANT |
| POST | /guest-access/change | Edit allowlisted fields | `updateSiteGuestAuthorization` and `getSiteGuestAuthorization` | Yes | CHANGE |
| POST | /guest-access/extend | Set a new duration | `updateSiteGuestAuthorization` and `getSiteGuestAuthorization` | Yes | EXTEND |
| POST | /guest-access/revoke | End one guest authorization | `updateSiteGuestAuthorization` with minutes 0 and `getSiteGuestAuthorization` | Yes | REVOKE |
| POST | /guest-access/clients/search | Search connected clients at one site | `listSiteWirelessClientsStats` | No | None |
| POST | /guest-access/import/preview | Parse and validate one CSV file | None | No | None |
| POST | /guest-access/import/run | Run one reviewed import batch | Per row: `updateSiteGuestAuthorization` and `getSiteGuestAuthorization` | Yes | IMPORT |

## Request and response rules

- Each write route requires the reviewed-content hash from its review or preview response (D-7).
- A validation failure returns 400 with zero Mist calls.
- A permission failure returns 403 with zero Mist calls.
- A stale or mismatched hash returns 409 with zero Mist calls.
- A journal or audit failure returns 503 with zero Mist calls.
- A Mist outcome that is unknown returns 502 with the state `unknown`. The response offers reconciliation and no automatic retry (FR-018).
- Tables show masked MAC addresses. The review panel shows the full MAC address for one selected row (D-15).
- Responses and errors never include tokens, raw payloads, or names (FR-026).
