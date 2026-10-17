# Discovery Contract: Multi-site WebSocket targets

**Issue**: #4259

## Portal Discovery Routes

These new read routes support the Multi Site controls.
They do not replace current picker endpoints.

| Route | Scope |
| - | - |
| `GET /api/websockets/batches/sites?kind=channel&key=site.stats.devices` | Configured organization |
| `GET /api/websockets/batches/sites/{site_id}/targets?kind=utility&key={catalog_key}` | Eligible resources for one operation and site |

The second route accepts `device_id` or `map_id` only when catalog metadata requires that parent.
Reject unknown query keys.
Validate the site against the complete organization site list before reading its resources.
Use explicit SDK arguments.
Never accept an SDK function name or raw path from the request.

### Success shape

```json
{
  "rows": [],
  "complete": true,
  "reason": "The site has no eligible targets.",
  "scope": {"site_id": "11111111-1111-4111-8111-111111111111"}
}
```

Each nonempty row contains a natural source ID, safe label, target type, and required parent identity.
Device rows include the verified family and site.
The service retains device MAC scope privately when required for wired-client discovery.
An empty complete list returns `200`.
An upstream or pagination failure returns the error shape from [batch-api.md](batch-api.md).
Never return `complete: true` after a failed page.
Do not return raw upstream response text.

## SDK Calls

Use the authenticated `apisession` for every call.
Use the validated runtime page limit for methods that accept `limit`.
The application default is 1000.
The accepted runtime setting range is 1 through 1000.
The OpenAPI default is 100 and has no stated maximum.
Do not claim that either default is the Mist API maximum.

| Target source | SDK method | Required arguments |
| - | - | - |
| Sites | `mistapi.api.v1.orgs.sites.listOrgSites` | `apisession`, configured `org_id`, validated `limit` |
| Devices | `mistapi.api.v1.sites.devices.listSiteDevices` | `apisession`, verified `site_id`, `type="all"`, validated `limit` |
| Wired clients | `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients` | `apisession`, verified `site_id`, verified `device_mac`, validated `limit` |
| Maps | `mistapi.api.v1.sites.maps.listSiteMaps` | Existing verified site arguments |
| Assets | `mistapi.api.v1.sites.assets.listSiteAssets` | Existing verified site arguments |
| SDK clients | `mistapi.api.v1.sites.stats.getSiteSdkStatsByMap` | Verified site and map |
| Site Mist Edges | `mistapi.api.v1.sites.mxedges.listSiteMxEdges` | Verified site |
| Organization Mist Edges | `mistapi.api.v1.orgs.mxedges.listOrgMxEdges` | Configured organization |

Fetch every page with the authenticated Mist SDK session:

`next_response = mistapi.get_next(mist_session=apisession, response=response)`

Verify the supported SDK signature before adding `limit` to other resource methods.
Do not forward arbitrary keyword arguments.
Do not use `limit` when the SDK signature does not accept it.
Normalize list responses and documented search envelopes through the existing SDK response rules.
Validate every page status and shape before adding its records.
Stop with an explicit error when a later page fails.
Do not use `mistapi.get_all` where it cannot report a failed page.
Never implement a second HTTP pagination client.

## Completeness and Error Rules

1. Validate the initial SDK status and response shape.
2. Fetch every page or cursor through supported SDK calls.
3. Validate returned records and required association fields.
4. Deduplicate by the full natural-key tuple.
5. Mark a scope complete only after pagination succeeds.

If a later page fails, reject the discovery scope.
Keep errors distinct from an empty result.
If the SDK cannot expose a complete response, return `picker_incomplete`.
Do not substitute the first page.

Rely on the Mist SDK's bounded rate-limit retries and backoff.
Do not add an outer retry loop.
Do not repeat successful reads for an unchanged batch scope.
Cache complete empty lists as complete results.
Do not cache failures as empty lists.

Bound preview cache lifetime to 300 seconds.
Share a complete read across compatible views within the same preview.
Invalidate a browser response when its operation or scope revision differs.
A manual refresh creates a new preview and invalidates its confirmation.

## Eligibility Rules

- Use `ChannelDefinition.identifiers` and `repeatable` for channel target structure.
- Use `UtilityDefinition.targets`, `fields`, `family`, `scope`, and `safety` for utilities.
- Keep device families `ap`, `ex`, `srx`, `ssr`, and `mxedge` distinct.
- Use explicit site membership from discovery before including a device.
- Require wired-client site and switch association from documented response fields.
- Accept `device_mac` or `device_mac_port` association only after normalized comparison.
- Keep gateway client discovery unavailable when verified association is absent.
- Preserve manual client entry only when the existing validator can prove its required scope.
- Do not turn an unverified manual MAC into an all-client candidate.
- Keep map and SDK-client parent relationships intact.
- Build one catalog path per channel target and subscribe through one owned WebSocket connection.
- Retain each channel path-to-target association so the event router can demultiplex output.

For an all-target preview, fail if any required site discovery fails.
The operator can select a valid explicit subset and request a new preview.
List exclusions for incompatible families separately from access and pagination failures.
Do not silently omit denied sites.

## Required Contract Tests

Use mocks and deterministic fixtures.
Include at least one HTTP 4xx and one HTTP 5xx case.
Count the examined scopes, pages, and resulting targets.

| Scenario | Required result |
| - | - |
| Two organization pages | Every site appears exactly once |
| Two device pages with mixed families | `type="all"` and correct catalog family filtering |
| Two wired-client pages | All verified clients appear under the selected switch |
| Configured limit 250 | Every applicable initial SDK call uses 250 |
| Default runtime limit | Every applicable initial SDK call uses 1000 |
| Later-page failure | Explicit error, no complete target snapshot |
| Complete empty scope | `200`, empty rows, and `complete: true` |
| Foreign site or mismatched device | Rejection before target execution |
| Duplicate MAC across sites | Separate full natural-key targets |
| Missing association | No unverified client choice |
| Delayed stale response | Browser discards the old revision |
| Unchanged preview scope | No repeated completed discovery request |

Extend current intake tests inside their existing package.
Do not add a direct child to a full test directory.
