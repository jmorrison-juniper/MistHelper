# Contract: mistapi calls

Each function name below comes from the pinned SDK (`mistapi` 0.64.1, R118). The feature makes no direct HTTP request to a Mist endpoint (FR-008, constitution Technology section).

| Function | SDK module | SDK definition | Main call site | Use in this feature | Source |
|---|---|---|---|---|---|
| `searchOrgSwOrGwPorts` | `mistapi.api.v1.orgs.stats` | line 1157 | `collection/snapshot_client.py` line 109 | WAN port rows for one gateway. Passes `device_type="gateway"`, `mac`, and `limit`. | R120, R137, R60 |
| `searchOrgPeerPathStats` | `mistapi.api.v1.orgs.stats` | line 1592 | `collection/snapshot_client.py` line 121 | VPN peer statistics for one scope. Passes `mac`, `site_id`, `duration="1h"`, and `limit`. | R119, R130 |
| `listOrgDevicesStats` | `mistapi.api.v1.orgs.stats` | line 397 | `collection/snapshot_client.py` line 283 | Gateway inventory with running state. | R121, R60 |
| `getSiteInsightMetricsForGateway` | `mistapi.api.v1.sites.insights` | line 290 | `collection/snapshot_client.py` line 295 | Gateway metrics for one site and device. | R122, R60 |
| `getSiteInsightMetricsForDevice` | `mistapi.api.v1.sites.insights` | line 219 | none | Optional. Used only for a metric that a verified contract names. | R123 |

## Not used

- `getSiteGatewayMetrics` is in `mistapi.api.v1.sites.stats` (line 1536, R124). The source call `sites.insights.getSiteGatewayMetrics` is absent (R125). The feature does not call either function.
- `getSiteSleSummary` (line 770, R127) and `listSiteSlesMetrics` (line 1004, R128) belong to the SLE scope, which is out of scope (D-3).

## Parameters

- `limit` is at most 100 records per page (`SNAPSHOT_PAGE_LIMIT`, R60, line 17).
- Peer rows are at most 2 (`PEER_ROW_LIMIT`, R58, line 12).
- Pagination reads the cursor from the `next` URL. The feature never builds a `search_after` value (R117, OpenAPI line 60227).
- The shared admission ledger allows 5000 requests per rolling hour per credential (R59, line 24). Each request counts before it runs.

## Endpoint evidence (OpenAPI)

| Operation | OpenAPI path | OpenAPI line | Source |
|---|---|---|---|
| `listOrgDevicesStats` | `/api/v1/orgs/{org_id}/stats/devices` | 21396 | R108 |
| `searchOrgSwOrGwPorts` | `/api/v1/orgs/{org_id}/stats/ports/search` | 22034 | R111 |
| `searchOrgPeerPathStats` | `/api/v1/orgs/{org_id}/stats/vpn_peers/search` | 22457 | R110 |
| `getSiteInsightMetricsForDevice` | `/api/v1/sites/{site_id}/insights/device/{device_mac}/{metric}` | 32678 | R112 |
| `getSiteInsightMetricsForGateway` | `/api/v1/sites/{site_id}/insights/gateway/{device_id}/stats` | 32717 | R113 |

The OpenAPI file has no VPN peer time-series path. Only `vpn_peers/count` (line 22422) and `vpn_peers/search` exist (R109).
