# Research: Subscription Contract Expiry Report

## Decision: Use Mist subscription status terms exactly as documented

Subscription status values are `Active`, `Expired`, `Exceeded`, and `Inactive`.
Mist shows alerts after a 30-day grace period. After expiration, the network
continues to operate. Inactive subscriptions have no support. After 90 days,
Juniper can give read-only access or terminate access. Mist supports
organization-level and site-level subscription scope.

**Citation**:
`C:\Users\jmorrison\.copilot\skills\juniper-mist-management\04-subscriptions-and-orders\03-subscription-scope-activation-status-and-orders.md`

**Rationale**: The report must use the same status words and risk windows that
operators see in Mist subscription management.

**Alternatives considered**: Custom status names were rejected because they would
not match Mist terminology.

## Decision: Use Mist contract status and support state terms exactly

The Contracts page is `Organization > Admin > Contracts`. Contract Status values
are `Declined`, `EOS`, `Service Available`, and `Active`. Contract State values
are `Supported` and `Unsupported`. Contract Expiration values are `Expired`,
`0 - 3 months`, `0 - 12 months`, and `> 12 months`. `Supported` means active
support and JTAC support eligibility. `Unsupported` means `Declined`, `EOS`, or
`Service Available`.

**Citation**:
`C:\Users\jmorrison\.copilot\skills\juniper-mist-management\02-organization-sites-and-inventory\02-organization-settings-support-and-contracts.md`

**Rationale**: The report must align with Mist contract management labels.
Operators must not translate between different terms.

**Alternatives considered**: A custom severity field was rejected because the
specified CSV requires contract status, contract state, and bucket values.

## Decision: Use `getOrgLicensesSummary` for subscription entitlement rows

OpenAPI operation `getOrgLicensesSummary` is `GET /api/v1/orgs/{org_id}/licenses`.
It requires the path parameter `org_id` as a UUID string. The `200` response
schema is `license`. The documented example includes `amendments[]`, an
`entitled` map, `licenses[]` rows with `type`, `end_time`, `quantity`,
`remaining_quantity`, `start_time`, and `subscription_id`, and a `summary` map.

**Rationale**: This endpoint gives subscription type, entitlement, start and end
time, and subscription identifiers in one organization-level response.

**Alternatives considered**: Reusing raw CSV output from an earlier menu was
rejected for implementation because the new report should call the SDK seam
directly and remain testable with fake client data.

## Decision: Use `getOrgLicensesBySite` for site usage context

OpenAPI operation `getOrgLicensesBySite` is
`GET /api/v1/orgs/{org_id}/licenses/usages`. It requires the path parameter
`org_id` as a UUID string. The `200` response is an array of
`license_usage_org` rows with `site_id`, `num_devices`, a `usages` map, and a
`fully_loaded` map.

**Rationale**: This endpoint provides site-level usage values that can be
summed by subscription type for entitlement comparison.

**Alternatives considered**: Device inventory counts were rejected because the
license usage endpoint already returns the licensed usage scope.

## Decision: Use `searchOrgJsiAssetsAndContracts` for device contract rows

OpenAPI operation `searchOrgJsiAssetsAndContracts` is
`GET /api/v1/orgs/{org_id}/jsi/inventory/search`. It requires the path parameter
`org_id` as a UUID string. Query parameters include `model`, `serial`, `status`,
`warranty_type`, `eol_duration`, `eos_duration`, `text`, `sort`, `limit`, and
`page`. The `200` response schema is `js_inventory_search`. Its `results[]`
rows include `model`, `serial`, `sku`, `type`, `warranty_type`, `eol_time`, and
`eos_time` in the documented example. A `400` response can mean no Juniper
account is linked.

**Rationale**: This endpoint is the SDK source for device contract and support
data. The report can paginate it through `client.py`.

**Alternatives considered**: Scraping the Mist UI Contracts page was rejected
because a supported SDK operation exists.

## Decision: Verify SDK methods before implementation

Installed SDK verification passed for these methods:

- `mistapi.api.v1.orgs.licenses.getOrgLicensesSummary`
- `mistapi.api.v1.orgs.licenses.getOrgLicensesBySite`
- `mistapi.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts`

**Rationale**: The implementation can use SDK calls rather than direct HTTP
calls. This satisfies the constitution and keeps API access testable.

**Alternatives considered**: Direct HTTP calls were rejected because the SDK
contains the required operations.

## Decision: Keep integration wiring out of this branch

The implementation branch will create only the report package and unit tests.
Integration changes for `MistHelper.py`, `OperationRegistry`, `README.md`, the
generated menu reference, and primary key strategy are deferred to
[wiring.md](wiring.md).

**Rationale**: The user requested that wiring not be implemented in this
branch. The design must still record the work so a later branch can integrate
menu 271 safely.

**Alternatives considered**: Implementing menu 271 immediately was rejected
because it would violate the requested branch boundary.
