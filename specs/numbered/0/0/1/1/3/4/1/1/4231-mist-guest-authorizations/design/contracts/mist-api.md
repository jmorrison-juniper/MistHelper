# Mist API Contract: Guest Authorizations

## Status and Transport

G5 remains unresolved. Signature inspection is not request/response verification.
The worktree resolved `mistapi==0.64.1` from the permitted dependency range.
Future evidence must pin the exact SDK version, dependency commit, and API document revision.
Use the existing Mist session. Do not create credentials, direct REST fallback, or a WebSocket transport.

## Inspected Candidate Signatures

All methods below use the prefix `mistapi.api.v1.` and return `APIResponse`.
The first parameter is `mist_session` in every row.
Optional parameters default to `None`. This table records local inspection, not permission to invoke the methods.

| Method | Remaining parameters | Purpose |
| --- | --- | --- |
| `orgs.sites.listOrgSites` | `org_id, limit, page` | Discover permitted sites |
| `orgs.wlans.listOrgWlans` | `org_id, limit, page` | Discover organization WLANs |
| `sites.wlans.listSiteWlans` | `site_id, limit, page` | Discover site WLANs |
| `sites.guests.listSiteAllGuestAuthorizations` | `site_id, wlan_id` | Read site authorizations |
| `orgs.guests.listOrgGuestAuthorizations` | `org_id` | Read organization authorizations |
| `sites.stats.listSiteWirelessClientsStats` | `site_id, wired, limit, start, end, duration` | Read connected clients |
| `sites.guests.updateSiteGuestAuthorization` | `site_id, guest_mac, body` | Candidate site change |
| `orgs.guests.updateOrgGuestAuthorization` | `org_id, guest_mac, body` | Candidate organization change |
| `sites.guests.getSiteGuestAuthorization` | `site_id, guest_mac` | Candidate site reconciliation |
| `orgs.guests.getOrgGuestAuthorization` | `org_id, guest_mac` | Candidate organization reconciliation |
| `sites.guests.deleteSiteGuestAuthorization` | `site_id, guest_mac` | Inspected only, not approved revocation |
| `orgs.guests.deleteOrgGuestAuthorization` | `org_id, guest_mac` | Inspected only, not approved revocation |

Use explicit arguments. Do not forward variadic arguments into SDK methods.
`listOrgGuestAuthorizations` has no `wlan_id` parameter in this version.
Do not invent a filter or imply its output is restricted to a selected WLAN.
Discovery of inherited templates or site-group WLANs requires a separate verified resolution contract before those selections become available.
The source names `orgs.templates.getOrgTemplate` and `orgs.sitegroups.getOrgSiteGroup` as possible inputs, not verified integration methods here.

## Required Request and Response Evidence

| Concern | Evidence required before route work |
| --- | --- |
| Identity and scope | Existing session forwarding, organization membership, WLAN eligibility, and exact site/organization method selection |
| Reads | Exact response container, pagination or all-results behavior, missing fields, expired-record coverage, and field-level disclosure |
| Writes | Explicit payload allowlist per scope, supported edit fields, confirmation binding, and correct response interpretation |
| Duration | Approved grant minimum, maximum, extension semantics, and timezone handling supported by current documentation |
| Revocation | Supported method, zero-duration meaning if used, and reconciliation evidence that distinguishes acceptance from termination |
| Failures | Missing credentials, HTTP 4xx including permission denial and 429, HTTP 5xx, malformed responses, timeouts, and unknown outcomes |
| Privacy | Mask identifiers and exclude personal fields, credentials, request bodies, and raw responses from logs |

The checked-in API file is `documentation/mist-api-openapi3json.json`.
It names `guest.minutes` and `guest_org.minutes` limits of 0 and 259200.
Its site guest `name` is read-only. Its organization guest schema differs.
Neither a generic SDK `body: dict` nor that numeric minimum proves how a deployed revoke operation works.
Do not copy the source five-year duration claim or treat its zero-duration approach as verified.

## Write and Import Safety

Bind the resource, supported payload, and confirmation to the reviewed request.
Reject unsupported fields before the SDK call.
Never retry after an unknown write or fall back from site to organization scope.
Use sequential row writes within the approved request budget.
Stop after rate limiting, unknown results, or audit failure. Mark later rows not attempted.
Read-only retry behavior must use bounded exponential backoff within the approved budget.

## Offline Verification

Planned tests use SDK boundary mocks and fictional schema-valid responses.
They must assert exact method arguments and output shapes, not only nonempty results.
They must include positive, negative, and edge paths and make zero live calls.
API behavior not established by approved documentation remains blocked, even if every mock passes.
Any later nonproduction contract experiment needs separate approval and must not use production credentials.
