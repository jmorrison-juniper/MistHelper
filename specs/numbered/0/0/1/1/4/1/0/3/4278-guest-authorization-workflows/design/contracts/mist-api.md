# Contract: Mist calls through mistapi

**Record**: `specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows`

**Rule**: Each Mist call uses one mistapi function with explicit named arguments (FR-028). The client class holds all calls. The client never sends a direct HTTP request. The client never calls a function in the organization guest module (FR-029).

## 1. Calls Allowed by This Feature

| Purpose | mistapi function | Arguments | HTTP call | Evidence | Gate |
| --- | --- | --- | --- | --- | --- |
| Site list | `mistapi.api.v1.orgs.sites.listOrgSites` | `apisession`, `org_id` | GET organization sites | R108 | G2 |
| WLAN list | `mistapi.api.v1.sites.wlans.listSiteWlans` | `apisession`, `site_id` | GET site WLANs | R106 | G2 |
| Review list | `mistapi.api.v1.sites.guests.listSiteAllGuestAuthorizations` | `apisession`, `site_id`, `wlan_id` | GET `/api/v1/sites/{site_id}/guests` | R028, R102 | G2, G5 (U03) |
| Read-back | `mistapi.api.v1.sites.guests.getSiteGuestAuthorization` | `apisession`, `site_id`, `guest_mac` | GET `/api/v1/sites/{site_id}/guests/{guest_mac}` | R029, R101 | G2, G5 |
| Grant, update | `mistapi.api.v1.sites.guests.updateSiteGuestAuthorization` | `apisession`, `site_id`, `guest_mac`, `body` | PUT `/api/v1/sites/{site_id}/guests/{guest_mac}` | R030, R031 to R036, R099, R111 | G5 for grant semantics |
| Extension | `mistapi.api.v1.sites.guests.updateSiteGuestAuthorization` | Same as grant | Same as grant | Same as grant | G5 for extension semantics |
| Revoke | `mistapi.api.v1.sites.clients.unauthorizeSiteWirelessClient` | `apisession`, `site_id`, `client_mac` | POST `/api/v1/sites/{site_id}/clients/{client_mac}/unauthorize` | R038, R039, R104, R072, R073 | G5 for read-back |
| Client search | `mistapi.api.v1.sites.stats.listSiteWirelessClientsStats` | `apisession`, `site_id`, and the window arguments that the SDK defines | GET `/api/v1/sites/{site_id}/stats/clients` | R041, R105 | G2, G5 (U05) |

## 2. Calls Excluded by This Feature

| Function | Reason | Evidence |
| --- | --- | --- |
| `mistapi.api.v1.sites.guests.deleteSiteGuestAuthorization` | Deletes a production record (D-10, FR-013) | R100 |
| `mistapi.api.v1.orgs.guests.updateOrgGuestAuthorization` | Organization scope (D-5, FR-029) | R103 |
| Any organization guest function, including the list call | Organization scope (D-5, FR-029) | R103 (same SDK module) |
| `mistapi.api.v1.sites.wlans.listSiteWlansDerived` | Derived WLANs wait for gate G5 (D-5) | R107 |
| Any direct HTTP call to a Mist endpoint | Violates FR-028 | Constitution technology rules |

## 3. Body Rules for Updates

- The grant body holds `authorized` set to true and `minutes` from 1 through 259200 (D-8).
- The update body holds only the writable fields from `authorized`, `minutes`, `company`, `email`, `field1`, `field2`, `field3`, and `field4` (R032). A field outside this list rejects before the call (TEST-006).
- The body never holds `mac`, `name`, or any other read-only field (R033, R035).
- The body omits any notification field (D-7).
- The MAC address travels in the URL path only (R029).

## 4. Outcome Classification

The SDK retries HTTP 429 up to three times for PUT and POST (R109, R110). The client reads the final response.

| Final response | Outcome | Next step |
| --- | --- | --- |
| HTTP 2xx | `succeeded` | Write the outcome row. Revoke runs the read-back |
| HTTP 401 or 403 | `failed` | Write the outcome row. Continue |
| HTTP 400, 404, 409, or 422 | `rejected` | Write the outcome row. Continue |
| HTTP 429 after SDK retries | `rate_limited` | Write the outcome row. Stop the batch |
| HTTP 5xx | `unknown` | Write the outcome row. Stop. No retry |
| Timeout, connection error, or no response object | `unknown` | Write the outcome row. Stop. No retry |

Warning: an `unknown` result can hide an applied change. Read the record before any new write to the same target.

## 5. Read-Back Rules

- After an update, the client reads the record with `getSiteGuestAuthorization`. The result is `verified` only when the returned `authorized` value matches the request. TEST-012 covers the revoke case. The update case uses the same read-back in T007.
- After a revoke, the client reads the record. The result is `verified` only when `authorized` is false. Any other value returns `accepted, not verified` (TEST-012).
- A read-back failure returns `unknown` for the verification step. The write outcome stays as the call returned it.

## 6. Logging Rules

- Each call logs an info line before the call and a debug line after it.
- The debug line holds the status class, the function name, and a masked target. It holds no request body and no response body.
- A call logs no token, no API session attribute, and no full MAC address.
