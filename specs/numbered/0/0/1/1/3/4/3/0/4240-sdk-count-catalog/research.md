# Research: Count Catalog Completeness

## SDK Operation Locations

**Decision**: Add `countOrgVars` from `mistapi.api.v1.orgs.vars` and `countOrgClientFingerprints` from `mistapi.api.v1.orgs.insights`.

**Rationale**: mistapi 0.64.1 defines both functions. Each takes the API session and organization ID as its first two arguments, which matches the count exporter call.

**Alternatives considered**: Excluding either function would leave the catalog completeness test false. Direct HTTP requests are not needed.

## Fingerprint Scope and Identity

**Decision**: Keep `countSiteClientFingerprints` as the sole intentional catalog exclusion. Keep the existing composite key for `countOrgClientFingerprints`.

**Rationale**: Issues #3334 and #3691 establish that the working fingerprint count endpoint uses organization scope. The existing composite key supports the site fingerprint census export with `site_id`, `distinct`, and `value`.

**Alternatives considered**: Replacing the fingerprint key would break the existing census export identity. Adding another exclusion would hide a supported SDK operation.

## Variable Count Persistence

**Decision**: Use the established auto-increment count strategy for `countOrgVars`, with `org_id` and `distinct` indexes.

**Rationale**: The endpoint returns grouped count rows without a stable row identifier. Existing organization count operations use the same generated primary-key pattern.

**Alternatives considered**: A composite key is not supported by the documented variable-count response shape.
