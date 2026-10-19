# Mist API Contract: MistCircuitStats Redis Dashboard Migration

**Status**: Candidate map. Verify every request against the source implementation, current SDK signatures, and current OpenAPI schemas before implementation.

## Existing SDK Evidence

Merged PR #4252 supplies `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py`. It checks 17 method signatures for the `mist_session` parameter and the `0.64` SDK version.

This proves method availability and a shared-session argument. It does not prove source metric fields, units, timestamps, port identity, interval, or time-window parity. The source worker's direct HTTP Insights path remains distinct from the SDK contract. Do not infer transport approval from a passing signature test.

## Contract Source

- OpenAPI document: `documentation/mist-api-openapi31json.json`
- OpenAPI version: 3.1.0
- Mist API document version: 2609.1.0
- Document date: 2026-09-07
- SDK range: `mistapi>=0.64.0,<0.65`

## Candidate Read Operations

| Operation ID | Method and path | Known query arguments in OpenAPI | Verification required |
|---|---|---|---|
| `listOrgSites` | `GET /api/v1/orgs/{org_id}/sites` | `limit`, `page` | Resolve referenced schemas and compare the source arguments. |
| `listSiteDevices` | `GET /api/v1/sites/{site_id}/devices` | `type`, `name`, `limit`, `page` | Verify gateway filtering and returned natural identifiers. |
| `getSiteGatewayMetrics` | `GET /api/v1/sites/{site_id}/stats/gateways/metrics` | No operation-level arguments listed | Confirm that the source uses this operation and inspect the response schema. |
| `getSiteInsightMetricsForGateway` | `GET /api/v1/sites/{site_id}/insights/gateway/{device_id}/stats` | Required `metrics`, optional `port_id`, time window, interval, and pagination references | Resolve references and verify every requested metric, unit, time boundary, and page. The source implementation review reports `rx_bps`, `tx_bps`, `port_id`, `interval=3600`, and a seven-day window. |
| `countOrgPeerPathStats` | `GET /api/v1/orgs/{org_id}/stats/vpn_peers/count` | `distinct`, time window, and limit references | Confirm whether the source uses a count request and its effect on call bounds. |
| `searchOrgPeerPathStats` | `GET /api/v1/orgs/{org_id}/stats/vpn_peers/search` | `mac`, `site_id`, `type`, time window, sort, and pagination references | Verify peer identity, filter, sort, time, and pagination semantics. |

These operation names are present in the repository OpenAPI document. Their presence does not prove that the source dashboard calls them or that they return the source's required fields.

## Request Rules

- Use the existing authenticated `mistapi` session and selected organization context.
- Use explicit method arguments. Do not forward arbitrary `*args` or `**kwargs`.
- Bound page size and page count using the shared API policy.
- Follow SDK pagination only. Do not follow an arbitrary URL returned by an API.
- Share request admission with other MistHelper users of the same token and organization.
- Keep portal reads cache-only. Refresh work must use one approved owner and shared admission.
- Do not log tokens, authorization headers, cookies, or raw sensitive responses.
- The source insight path uses direct `requests.get` calls and manual token-header extraction. Do not port that path. A direct HTTP alternative requires a failing SDK contract test and approval under the repository constitution.

## Required Contract Tests Before Implementation Approval

1. Confirm each SDK operation and its arguments against the exact source call, including the reported insight interval, seven-day window, `port_id`, `rx_bps`, and `tx_bps`.
2. Confirm organization and site context uses the existing authenticated MistHelper session.
3. Confirm response schema and natural identity for sites, gateways, ports, peers, and insights.
4. Confirm pagination stops at the shared configured bound and retains an explicit partial state.
5. Simulate HTTP 4xx, 5xx, rate limits, timeout, and malformed response behavior.
6. Confirm the shared admission ledger observes every request attempt and prevents an unbounded retry.
7. Confirm errors and structured logs redact tokens and other credentials.
8. If the SDK is insufficient, add a failing contract test that proves the exact loss before proposing any alternative transport.

## Open Questions

- Which operations does the source actually call for each dashboard journey?
- Does the source use `getSiteGatewayMetrics`, gateway insight data, or both?
- Does the gateway insight response match the source's expected `rx_bps`, `tx_bps`, units, timestamps, and port identifiers? This response mismatch blocks any insight implementation.
- Does peer-path data include a stable peer identifier and observation timestamp?
- Which metric identifiers, units, intervals, and time windows does the source request?
- What is the exact pagination and partial-result behavior?
- Which API calls are already owned by the accepted #4195 or #4200 scope?
