# API contracts: Site health dashboard

## Evidence boundary

The installed MistHelper SDK exposes these source-referenced methods.
The module prefix for every row is `mistapi.api.v1`.
Inspection verifies names and signatures without constructing a session or sending a request.
Response parity, token privileges, and service entitlements remain B04.

| Domain module | Methods | Source `mist_connection.py` lines |
| --- | --- | --- |
| `orgs.orgs`, `self.self` | `getOrg`, `getSelf` | 213, 229 |
| `orgs.sites`, `sites.sites` | `listOrgSites`, `getSiteInfo` | 296, 332, 2557 |
| `orgs.templates`, `orgs.wlans` | `listOrgTemplates`, `listOrgWlans` | 409, 432 |
| `sites.stats` | `listSiteDevicesStats`, `listSiteWirelessClientsStats` | 465, 1682, 1756, 2087 |
| `sites.clients` | `searchSiteWirelessClients`, `searchSiteWirelessClientSessions` | 1773, 1815 |
| `sites.wired_clients` | `searchSiteWiredClients` | 1948 |
| `orgs.stats` | `searchOrgPeerPathStats`, `searchOrgBgpStats` | 2127, 2156 |
| `sites.sle` | `listSiteSlesMetrics`, `listSiteSleMetricClassifiers` | 741, 883, 1217 |
| `sites.sle` | `getSiteSleSummaryTrend`, `getSiteSleSummary` | 779, 792, 1261, 1279 |
| `sites.sle` | `getSiteSleClassifierDetails`, `getSiteSleImpactSummary` | 932, 998, 1454, 1466 |
| `sites.sle` | `listSiteSleImpactedGateways`, `listSiteSleImpactedInterfaces` | 1068, 1072 |
| `sites.sle` | `listSiteSleImpactedApplications`, `listSiteSleImpactedWiredClients`, `listSiteSleImpactedWirelessClients` | 1076, 1080, 1084 |

There are 24 distinct typed methods above.
The candidate `orgs.insights.getOrgSitesSle` supports category, start, end, duration, interval, limit, and page.
It targets `/api/v1/orgs/{org_id}/insights/sites-sle`, not the private worst-sites endpoint.
Do not claim sorted worst-100 parity before a response contract proves it.

## Required SDK contracts

Future tests must verify explicit named arguments, not `*args` or `**kwargs` forwarding.
Site/device list calls require pagination and `type="all"` for device stats.
Search methods require verified cursor behavior.
SLE calls require site identity, `scope="site"`, the validated scope identity, metric, and verified period.
Do not infer scope identity equality from naming alone.
Affected-item methods need classifier and item-type fixtures with units.

Minimum token access is read access to the selected organization and its permitted sites.
Exact privileges and subscription requirements are unverified.
No administrator or write privilege is required by the intended behavior.
Reject denied sites instead of discovering data through a broader organization search.

Each collector needs success, empty, malformed payload, partial pagination, HTTP 400/401/403/404/429, HTTP 5xx, and timeout tests.
Validate that no failed request becomes a success-shaped empty result.
Test server-side redaction, accepted cloud region, and forbidden cross-organization results.
Use the shared SDK rate-limit mechanism and at most three transient retries.
Never retry invalid input or denied access.

## Unverified contracts

The private `/api/v1/orgs/{org_id}/insights/worst-sites-by-sle` path is B02.
The source uses a low-level session call and claims undocumented limit support.
No new direct transport is permitted.
Period discrepancies are B03.
No SDK response parser belongs to the offline model slice.

## Offline model contract

The [data model](../data-model.md) defines normalized inputs.
That interface needs no token, source code, SDK response, or service entitlement.
Its tests must prove absent, zero, complete, partial, invalid, and immutable states.
