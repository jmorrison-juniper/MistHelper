# Contract: Mist API Calls

## Scope

These mistapi calls belong to `SiteGuestGateway` in `src/mist/access/guests/gateway.py`. Each call uses keyword arguments. The gateway uses site scope for every guest operation (D-3). The only organization read is the site selector.

## Allowed calls

| Operation | mistapi function | Source location | Use | Notes |
| --- | --- | --- | --- | --- |
| List WLANs | `listSiteWlans` | `sites/wlans.py` line 17 (R-107) | WLAN selector | Site scope |
| List sites | `listOrgSites` | `orgs/sites.py` line 17 (R-109) | Site selector | Organization read only |
| List guests | `listSiteAllGuestAuthorizations` | `sites/guests.py` line 17 (R-94) | Masked list for one WLAN | Accepts the `wlan_id` argument (line 18) |
| Get guest | `getSiteGuestAuthorization` | `sites/guests.py` line 224 (R-96) | Reconciliation read | Argument names confirmed at T003 |
| Update guest | `updateSiteGuestAuthorization` | `sites/guests.py` line 280 (R-98) | PUT for grant, change, extend, and revoke | Body allowlist (D-6) |
| Client statistics | `listSiteWirelessClientsStats` | `sites/stats.py` line 960 (R-106) | Client search | Site scope |

## Excluded calls

- `searchSiteGuestAuthorization` (R-95) and `deleteSiteGuestAuthorization` (R-97) are not used. D-4 excludes DELETE for revoke.
- Every organization guest function is not used. The organization list has no WLAN argument (R-99). The organization update and delete functions (R-100, R-101) are excluded by D-3.

## Write body rules

- Allowed fields: `authorized`, `company`, `email`, `field1`, `field2`, `field3`, and `minutes`. The site schema lists these as writable.
- Forbidden fields: `name`, `mac`, `random_mac`, `ssid`, `wlan_id`, and `field4`. The site schema marks the first four read-only (openapi lines 80989 to 81020). The source overwrites `field4` (D-6).
- Revoke sends the body `{"minutes": 0}` after a WLAN check (D-4).
- Grant body: the WLAN binding is unverified. Grants stay disabled until gate G5 closes (U-3, D-16).

## Response handling

- A 2xx status is success (FR-016). The SDK stores the status on the response (`__api_response.py` line 48, R-105).
- A 4xx status other than 429 is failure. The batch continues for import rows.
- A final 429 after the SDK retries is failure. The import stops (FR-025). The SDK retry limit is 3 (`__api_request.py` line 59, R-102).
- A 401 or 403 status stops the batch because the credential lacks permission.
- A 5xx status, a missing status, or a connection failure is unknown. The batch stops (FR-018).

## Retry and reconciliation

- The gateway makes one SDK write call for each confirmed change (SC-005). The gateway adds no retry.
- After each write, the gateway makes one `getSiteGuestAuthorization` read (FR-013).
- A revoke shows "ended" only when the read shows an unauthorized or expired record. A record that the read cannot find shows "not found" (TC-039).
