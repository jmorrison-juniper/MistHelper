# Interface Contract: Mist BGP Peer Statistics Search

This contract defines the request and response shape that the feature reads from Mist. The feature calls the mistapi method. It makes no direct REST call (constitution, Technology constraints, RC-13).

## Request

- Method and path: `GET /api/v1/sites/{site_id}/stats/bgp_peers/search` (RC-41 coverage row, RC-42 documentation page, RC-43 operation block at lines 39170 to 39211).
- Path parameter: `site_id`.
- Query parameters in the operation block (RC-43): `mac`, `neighbor_mac`, `vrf_name`, `limit`, `start`, `end`, `duration`, `sort`, and `search_after`.
- SDK method: `mistapi.api.v1.sites.stats.searchSiteBgpStats`. Its signature takes `mist_session`, `site_id`, and the optional query arguments above (RC-117, line 532). The installed version is mistapi 0.64.1 (RC-116).
- Call site: `SiteSearchExporter.bgp_stats` (RC-89), which passes the operation name `searchSiteBgpStats` (RC-100).

## Response

- The 200 response uses the `BgpStatsArraySearch` response reference (RC-43).
- The response results are items of the `bgp_stats` schema (RC-44, line 93377).

## Item Fields Used for Identity

| Field | Declared in `bgp_stats` | Evidence |
| - | - | - |
| `mac` | Yes. Router MAC address of the reporting device. | RC-45 |
| `neighbor` | Yes. IP address of the BGP neighbor. | RC-46 |
| `timestamp` | Yes. Observation time. | RC-47 |
| `id` | No. The schema declares no `id` property. | RC-48 |

The strategy entry for this endpoint declares `mac`, `neighbor`, and `timestamp` (RC-64). The writer derives the identity key from those three fields (`contracts/arango-document-key.md`).

## Graph Mapping Note

The ArangoDB graph mapping keys vertices by `id` (RC-59). The vertex builder skips records without that field (RC-60). Because `id` is not declared (RC-48), the BGP vertex path needs a follow-up issue (T018 b). This contract does not change the graph mapping.

## Contract Tests

- The existing parametrized test keeps the operation name pair unchanged (RC-100).
- No new request is added, so no new authentication or endpoint test is needed.
- Secret redaction stays unchanged. The feature reads no credential.
