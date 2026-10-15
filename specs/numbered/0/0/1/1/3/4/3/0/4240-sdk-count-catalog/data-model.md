# Data Model: Count Catalog Completeness

## Count Operation

| Field | Meaning |
|---|---|
| Operation | The Mist operation name used by the operator and exporter |
| Module | The SDK module that defines the operation |
| Scope | The organization, site, or service-provider identifier scope |
| Persistence identity | The key used to store each exported result row |

The two added operations use organization scope. `countOrgVars` uses the existing generated-key pattern for count rows. `countOrgClientFingerprints` retains the composite key used by the fingerprint census.

No database schema changes are required.
