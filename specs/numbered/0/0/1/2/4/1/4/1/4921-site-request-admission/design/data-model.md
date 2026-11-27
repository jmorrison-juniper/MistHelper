# Data Model: Site Request Admission by Organization

This model covers the in-process state of the request ledger. It has no database table, no file, and no persisted record.

## Entities

### Site Organization Map

- **Represents**: The organization that owns each site, as one organization listing reported it.
- **Natural key**: The site identifier, the `id` field of a site record (`documentation\mist-api-openapi31yaml.yaml` line 100539).
- **Value**: The organization identifier from the listing URL path (`/api/v1/orgs/{org_id}/sites`).
- **Lifetime**: One `SiteOrganizationMap` object. The object lives with one `RequestLedger` object, so it lasts for one process.
- **Bound**: 50,000 entries. The oldest entry leaves first.
- **Concurrency**: One lock guards each read and each write.

### Ledger Organization

- **Represents**: The organization that the caller passes to `RequestLedger.connect` or to the constructor.
- **Natural key**: Not applicable. The value is one organization identifier or None.
- **Lifetime**: The ledger object. This change removes the runtime writes that `AdmissionBinding` made.
- **Default**: None. Production code passes no value after this change.

### Session Organization

- **Represents**: The organization that the session selected or cached. It comes from `ConfigUtils.get_cached_org_id`.
- **Natural key**: Not applicable. The value is one organization identifier or None.
- **Access**: The admission path reads it through a callable. The admission path never writes it.
- **Prompt**: The read never prompts. The read returns None when no value exists.

### Organization Listing Record

- **Represents**: One site record in a successful `listOrgSites` page.
- **Source**: `GET /api/v1/orgs/{org_id}/sites`, schema `sites` (`documentation\mist-api-openapi31yaml.yaml` line 102626).
- **Used fields**: `id` (string). The record may also carry `org_id` (line 100566). This change reads `id` and the path organization only.

### Site Request

- **Represents**: One HTTP attempt to a path under `/api/v1/sites/{site_id}`.
- **Natural key**: The site identifier in the path segment at index 4.
- **Attribution result**: One organization identifier, or a refusal. The result source is one of `map`, `ledger`, `session`, or `none`.

### Quota Key

- **Represents**: A Redis key that counts attempts. Each request reserves one key per credential and one key per organization.
- **Existing format**: `misthelper:api:v1:requests:{fingerprint}` and `misthelper:api:v1:org:{org_id}` (`request_admission.py` lines 82 and 85 on `main`).
- **Change**: The format stays the same. A site request now reaches the organization key when attribution succeeds.

## Relationships

- One site identifier maps to at most one organization identifier in the map at a time.
- One organization identifier has many site identifiers in the map.
- One listing page creates many map entries. Each entry carries the path organization.
- One site request yields one attribution result. That result selects at most one organization key.

## State Transitions

### Site Organization Map entry

1. **Absent**: The site has no entry. Attribution moves to the next source.
2. **Present**: A successful listing wrote the entry. Attribution returns the stored organization.
3. **Refreshed**: A later listing names the same site. The entry moves to the newest position. The value stays the same unless the listing names another organization.
4. **Evicted**: The map holds more than 50,000 entries. The oldest entry leaves the map. The site returns to the **Absent** state.

### Ledger Organization

1. **None**: The ledger has no constructor value. Attribution moves to the session organization.
2. **Set**: The constructor received a value. Attribution uses the value after the map.

### Session Organization

1. **None**: The cache has no value. Attribution refuses the site request.
2. **Set**: The cache has a value. Attribution uses it for a site request that the map did not resolve.

## Validation Rules

- A listing record without a string `id` gives no map entry.
- A listing response without HTTP status 200 gives no map entry.
- A listing response that is not a JSON list gives no map entry.
- A path without an organization segment or without a site segment does not write the map.
- A site request with no site segment (`/api/v1/sites`) uses the ledger organization or the session organization. It fails closed when neither exists.
