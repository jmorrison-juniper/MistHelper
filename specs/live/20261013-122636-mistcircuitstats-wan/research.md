# Research: MistCircuitStats WAN Dashboard

## Decisions

### Use the existing MistHelper Flask portal

- **Decision**: Add the dashboard as a blueprint and navigation tab in the Flask portal on port 8055.
- **Rationale**: The user asked to keep the existing MistHelper portal as the shared interface. Its navigation already serves the dashboard, data browser, operations, maps, and WebSockets.
- **Alternatives considered**: Embed the source application in an iframe or run another web server. Both options retain separate application boundaries and complicate navigation, credentials, deployment, and access policy.
- **Evidence**: `documentation/wiki/Web-Portal.md`, `web_portal/app.py`, and `web_portal/templates/base.html`.

### Use MistHelper's Mist session and SDK boundary

- **Decision**: Reuse the Mist session supplied to the existing portal and call only supported `mistapi` methods.
- **Rationale**: MistHelper pins `mistapi` to a supported version and its instructions prohibit direct HTTP calls when an SDK method exists.
- **Alternatives considered**: Keep the source application's standalone API wrapper or build a second HTTP client. Both choices duplicate token handling and rate-limit behavior.
- **Evidence**: The source guide lists 18 calls across organization, site, gateway, insights, and SLE APIs. The feature specification records each method.

### Use shared cache and data services

- **Decision**: Keep telemetry transient. Use the existing shared Redis service only for namespaced, expiring cache entries. Add no service or database.
- **Rationale**: The base source uses bounded in-process caches. MistHelper already has one Redis Stack service in its compose group. A second service would violate the user's single-stack requirement.
- **Alternatives considered**: Add another Redis container, create a dashboard-specific database, or write live telemetry into long-term storage. These options duplicate infrastructure or retain data without a requirement.
- **Cache policy**: Preserve the source's 300-second site-list TTL and 600-second profile and gateway-template TTL. Confirm whether the shared Redis cache adapter can support these values before implementation. If it cannot, use the existing cache pattern without creating a new Redis service.
- **Evidence**: `compose.yml`, `src/foundation/persistence/db/`, and the source guide's cache descriptions.

### Keep rate-limit failures visible and preserve the last result

- **Decision**: Try each authorized token at most once per Mist SDK request when configured credentials share the same organization and access scope. Honor the existing 60-second per-token cooldown. Show an explicit rate-limit status and keep the last successful view.
- **Rationale**: The source page remains useful during a short rate limit, but MistHelper's rules reject success-shaped errors with empty data.
- **Alternatives considered**: Return an empty successful response after all tokens enter cooldown. This hides the failure cause and makes stale or missing data ambiguous.

### Keep the source dashboard workflow and credit the source

- **Decision**: Preserve the dashboard's table, filters, details, traffic charts, WAN Insights, peer-path view, theme behavior, and CSV exports. Retain attribution and record changes.
- **Rationale**: The user values the current design and workflows. Both repositories publish CC BY-NC-SA 4.0, so the plan keeps the license terms.
- **Alternatives considered**: Replace the page with a new layout or copy only the data fields. Either choice would discard the requested user experience.
- **Evidence**: The source `README.md`, `docs/guide.md`, and `LICENSE`; MistHelper `LICENSE`.

### Keep the base and Redis-specific source repositories separate

- **Decision**: This issue covers `MistCircuitStats`, not `MistCircuitStats-Redis`.
- **Rationale**: The user requested a serial workflow with one issue and pull request for each repository. The Redis sibling has its own worker and cache behavior, which needs a separate comparison against MistHelper's single shared Redis service.
- **Alternatives considered**: Combine both repositories in one pull request. This would break the requested one-repository-per-issue sequence.

## Source Feature Inventory

The source dashboard provides:

- Organization-wide gateway and WAN-port status with search, site filtering, and pagination.
- Port configuration from device profiles and gateway templates.
- Expandable port details with traffic counters and VPN peer paths.
- Traffic charts for 1-hour, 6-hour, 24-hour, and 7-day windows. The 1-hour chart uses 10-minute buckets.
- WAN Insights for 1-hour, 6-hour, 24-hour, 3-day, and 7-day windows.
- Hourly average and peak bandwidth, native WAN link health, and Application Health SLE.
- Main-table CSV and 12-column per-port hourly CSV.
- Comma-separated token support with a 60-second cooldown after HTTP 429.
- Responsive dark-theme presentation.
- Pagination through `mistapi.get_all(limit=1000)`.

## Mist API Methods

The source guide documents these SDK methods:

1. `mistapi.api.v1.self.self.getSelf`
2. `mistapi.api.v1.orgs.orgs.getOrg`
3. `mistapi.api.v1.orgs.sites.listOrgSites`
4. `mistapi.api.v1.orgs.inventory.getOrgInventory`
5. `mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile`
6. `mistapi.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate`
7. `mistapi.api.v1.orgs.stats.listOrgDevicesStats`
8. `mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts`
9. `mistapi.api.v1.sites.devices.getSiteDevice`
10. `mistapi.api.v1.sites.devices.searchSiteDevices`
11. `mistapi.api.v1.sites.stats.getSiteDeviceStats`
12. `mistapi.api.v1.orgs.stats.searchOrgPeerPathStats`
13. `mistapi.api.v1.sites.insights.getSiteInsightMetricsForGateway`
14. `mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice`
15. `mistapi.api.v1.sites.sle.getSiteSleSummaryTrend`
16. `mistapi.api.v1.sites.sle.listSiteSleImpactedInterfaces`
17. `mistapi.api.v1.sites.sle.getSiteSleThreshold`

The source guide uses `getSiteInsightMetricsForGateway` with two argument sets. These calls share one SDK method.

## Open Research Items for Implementation

- Verify the exact installed `mistapi` signatures and returned models for all calls in the compatibility test.
- Compare MistHelper's existing API session and token configuration with the source's multiple-token contract.
- Confirm the shared cache adapter can use feature-prefixed keys and the source TTL values.
- Confirm CSV formula neutralization follows the shared exporter policy.
- Measure source and integrated page latency with synthetic large organizations. Set no new performance threshold before collecting a baseline.
