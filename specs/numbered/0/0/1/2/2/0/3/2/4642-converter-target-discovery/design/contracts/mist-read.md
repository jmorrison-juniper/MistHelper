# Contract: Mist read calls for discovery

Scope: the three mistapi reads and the page helper that the discovery client uses. Each read is a GET. The client calls each function with keyword arguments only (FR-004). The client calls no write function (FR-005, FR-006).

## Calls

| Check | mistapi function and module | Keyword arguments | Mist operation | Evidence |
| - | - | - | - | - |
| status | `getSelf` in `mistapi.api.v1.self.self` | `mist_session` | GET `/api/v1/self`, operation `getSelf` | R52, R65 |
| sites | `listOrgSites` in `mistapi.api.v1.orgs.sites` | `mist_session`, `org_id`, `limit` 1000, `page` 1 for the first page | GET `/api/v1/orgs/{org_id}/sites`, operation `listOrgSites` | R53, R66 |
| gateways | `getOrgInventory` in `mistapi.api.v1.orgs.inventory` | `mist_session`, `org_id`, `type` set to `gateway`, `limit` 1000, `page` 1 for the first page | GET `/api/v1/orgs/{org_id}/inventory`, operation `getOrgInventory` | R54, R56, R67 |
| later pages | `mistapi.get_next` (`mistapi.__pagination`) | `mist_session`, `response` | Issues GET for the URL in `response.next` | R68, R69 |

## Membership Read

Each site check and gateway check calls `getSelf` before its list read. The client reads the `privileges` list from the response body. A privilege entry holds `org_id`, `scope`, and `role` (R59 and R60 show the fields in the `admin_privilege` schema). A check passes the membership step when one entry has the requested `org_id`. Otherwise the result is denied with reason `not_member` (FR-009).

## Response Fields Used

| Mist schema | Field | Use | Evidence |
| - | - | - | - |
| `site` | `id` | Natural key and selection value | R63 |
| `site` | `name` | Display text and duplicate detection | R64 |
| inventory item | `id` | Natural key for a gateway | R61 |
| inventory item | `site_id` | Assignment: value means assigned, empty means unassigned | R62, U2 |
| inventory item | `mac`, `serial`, `model`, `name` | Display only | Schema `inventory`, same block as R61 |
| admin privilege | `org_id`, `scope`, `role` | Membership and display | R59, R60 |

## Paging Contract

- The first page uses `limit` 1000 and `page` 1 (D-7). The value 1000 matches the repository page limit (R28).
- A later page uses `mistapi.get_next`, which calls `mist_get` only when `response.next` is set (R68).
- The client stops at 50 pages. A list that needs more pages gives failed with `page_limit_exceeded`.
- A verified list needs the completion proof of D-6: no `next` value, and either fewer than 1000 rows or the `X-Page-Total` header.
- `X-Page-Total` is read by the SDK for `next` (R69). The live header behavior is unverified (U1).

## Retry Contract

The SDK retries a 429 up to three times and waits 5, 10, and 20 seconds when `Retry-After` is absent (R70, R71). The client adds no retry loop (D-8). The SDK returns the final response as an `APIResponse` object and does not raise for HTTP error statuses (R71).

## Status Mapping

The status mapping follows D-5. Each status gives one state and one reason. The table in `design/contracts/discovery-http.md` lists the reasons.

## Write Boundary

The discovery client never imports or calls these write functions: `createOrgSite`, `updateSiteInfo`, `updateOrgInventoryAssignment`, `updateSiteDevice`, `addOrgInventory`, or `importOrgMapToSiteFile`. The list is a deny-list for test TC-02. TC-02 fails when a call in the list appears in the recorded call list (FR-006).

## Redaction Boundary

The client logs state codes and counts only. Test TC-19 searches each response body and each captured log line for the synthetic token value (FR-016).
