# Phase 0 Research: getOrgNacPortal

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/orgs/{org_id}/nacportals/{nacportal_id}`
**Enriched doc**: `documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id.md`

## Research Task 1 -- SDK Function Signature and Behavior

### Decision

The Mist API call is invoked through the `mistapi` SDK using:

```python
mistapi.api.v1.orgs.nac_portals.getOrgNacPortal(
    apisession,
    org_id,
    nacportal_id,
)
```

Note the SDK module path is `mistapi.api.v1.orgs.nac_portals` (underscore form),
not `nacportals`, even though the URL path token is `nacportals`. The SDK
returns a `mistapi.api_response.APIResponse` whose `.data` attribute is a
single JSON object (not a list) matching the schema documented in
`documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id.md`. The call
is **not** paginated -- a single GET returns the full portal configuration.

### Rationale

The enriched per-endpoint documentation at
`documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id.md` lists the
SDK call as `mistapi.api.v1.orgs.nac_portals.getOrgNacPortal()` and confirms
"Not paginated" with HTTP 200 returning a single object. This matches Thomas
Munzer's `mistapi_python` convention where multi-word URL tokens are mapped to
snake_case module names while operation IDs remain camelCase. The two path
parameters (`org_id`, `nacportal_id`) become positional arguments in the
documented order. No query parameters or request body apply.

### Alternatives Considered

1. **Raw `requests` call against the URL template** -- rejected; the project's
   constitution mandates the `mistapi` SDK as the sole permitted interface to
   the Mist Cloud, and the SDK already handles session, retry, and rate-limit
   plumbing.
2. **Calling the list endpoint `listOrgNacPortals` and filtering in Python** --
   rejected; the spec is explicit about cataloging the single-resource GET, and
   the list endpoint will be cataloged in its own future spec. Reusing the
   list call would also force the user to know the portal name rather than the
   already-known UUID and would waste API quota.

## Research Task 2 -- Primary Key Strategy

### Decision

Register `getOrgNacPortal` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` as
**`natural_pk`** with composite uniqueness across `(org_id, id)`:

```python
'getOrgNacPortal': {
    'type': 'natural_pk',
    'primary_key': ['org_id', 'id'],
    'indexes': ['name', 'type', 'ssid'],
},
```

The top-level `id` field returned in the response body is the stable, Mist-
assigned UUID of the NAC portal and equals the `nacportal_id` path parameter
the caller supplied. Pairing it with `org_id` makes the composite key globally
unique even if a portal UUID is somehow reused across orgs (defensive belt-and-
braces; in practice UUIDs do not collide).

### Rationale

NAC portals are configuration entities -- they have a Mist-assigned UUID that
persists across reads and is the natural business key. They are not time-series
events, so `composite_pk` with `timestamp` is wrong. They have a stable
UUID, so `auto_increment_with_unique` is unnecessary and would only obscure
the natural key. The pattern matches sibling entries already in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for other org-scoped configuration GETs
(e.g. WLAN templates, network templates, RF templates, alarm templates).
Secondary indexes on `name`, `type`, and `ssid` accelerate the common
"find portal by name / type / SSID" lookups a NOC engineer performs after
ingest.

### Alternatives Considered

1. **`primary_key: ['id']` only** -- rejected as marginally less safe; the
   tiny extra cost of carrying `org_id` in the PK pays off in multi-tenant
   inspection scenarios and matches existing sibling strategies.
2. **`composite_pk` with `timestamp`** -- rejected; this endpoint returns a
   configuration object, not a time-stamped event. There is no timestamp in
   the response schema.
3. **`auto_increment_with_unique`** -- rejected; the response provides a
   stable natural key. Artificial IDs would prevent clean upserts on re-runs
   and break the constitution's preference for natural business keys.

## Research Task 3 -- Output Filename and SQLite Table

### Decision

- **CSV filename** (primary, top-level scalars): `data/org_nac_portal.csv`
- **CSV filename** (SSO sub-object, flattened to one row when present):
  `data/org_nac_portal_sso.csv`
- **CSV filename** (SSO role-matching array, one row per match):
  `data/org_nac_portal_sso_role_matching.csv`
- **SQLite tables** (auto-created by `DataExporter` on first write):
  - `org_nac_portal`
  - `org_nac_portal_sso`
  - `org_nac_portal_sso_role_matching`
- **ArangoDB collection / Redis namespace**: `org_nac_portal` (the parent
  document; sub-tables become embedded sub-documents per the existing
  DataExporter convention).

### Rationale

Naming follows the existing MistHelper convention `data/<resource_singular>.csv`
for single-resource GET reads (matching, for example, `data/org_site.csv`
and `data/org_wlan_template.csv`). The single-table-per-flat-shape rule means
the deeply nested `sso` object and its `sso_role_matching` array must split
out into child tables to keep each table flat and queryable. The
parent / child tables share `org_id` + portal `id` as the join key.

### Alternatives Considered

1. **One mega-flat table with `sso_*` and `role_match_*` columns** -- rejected;
   `sso_role_matching` is a variable-length array (zero to many entries) and
   would force the schema to either pick a fixed cap or stringify the array.
   Both options break SQL queryability.
2. **Stringified JSON column for `sso` and `sso_role_matching`** -- rejected;
   CSV consumers (the project's primary user surface) cannot easily filter
   inside JSON cells, and the constitution prefers explicit columns.
3. **Plural filename `data/org_nac_portals.csv`** -- rejected; this menu item
   reads exactly one portal per invocation. The plural name is reserved for
   the future `listOrgNacPortals` menu item.

## Research Task 4 -- Menu Category Placement and Next Available Number

### Decision

- **Proposed menu number**: **94**
- **Category**: Safe Org Exports / NAC configuration sub-cluster (within the
  documented 1-96 safe-export band, below the resource-intensive 97-101
  block).
- **Owning class**: existing NAC-portal / org-configuration export class --
  preferred: **`NacExportUtils`** if already declared, fallback
  **`OrgConfigExportUtils`** (the same class that owns adjacent org-config
  template exports). A new class is **not** introduced.

### Rationale

The full menu range 1-194 is documented in `.github/copilot-instructions.md`.
Read-only org-config GETs live in the 1-96 safe-export band. Per the running
project context the next free integer in the NAC / template configuration
sub-cluster is 94 (numbers immediately adjacent are already assigned to the
NAC list and template exports). Attaching to an existing class keeps the
class count flat per Constitution Principle I and Principle II (no wrapper
classes). The exact class name is verified by `grep -n "class .*NacExport\|class
OrgConfigExport" MistHelper.py` at task time -- whichever class is present
gets the new method; if neither exists, the closest existing org-export class
in the file is chosen, with the choice recorded in the task notes.

### Alternatives Considered

1. **New class `NacPortalExportUtils`** -- rejected; the constitution prefers
   adding methods to existing classes for adjacent functionality. A new class
   for a single-method addition violates Principle II's "No wrappers; restructure
   into classes" intent (the intent is to avoid both bare-function wrappers
   *and* trivial one-method classes).
2. **Menu number in the destructive 154-194 band** -- rejected; this is a
   read-only GET, the band is explicitly reserved for destructive actions,
   and the test sweep skip list 90-100 would mask the new menu under default
   test runs if placed badly.
3. **Menu number 95 or 96** -- rejected; 95 is reserved by spec 500
   (`GetOrgLicenseAsyncClaimStatus`) currently in flight, and using 96 risks
   adjacency to the resource-intensive boundary at 97. 94 is the safest
   adjacent slot.

## Research Task 5 -- Required User Prompts

### Decision

The menu item collects two identifiers, both through `safe_input()`:

1. **`org_id`** -- prompted as
   `safe_input("Org ID [press Enter for default from .env]: ",
   context="org_nac_portal:org_id")`. If the prompt is empty, fall back to
   the `MIST_ORG_ID` environment variable. If both are empty, log a warning
   and return early.
2. **`nacportal_id`** -- prompted as
   `safe_input("NAC Portal ID: ", context="org_nac_portal:nacportal_id")`.
   No `.env` default; this value identifies the specific portal to fetch and
   must be supplied per invocation. In `--test` mode the value comes from
   the optional `.env` variable `MIST_TEST_NACPORTAL_ID`; if absent, the
   test sweep logs a warning and skips this op without failing the run.

Neither identifier is validated against the live Mist API before the SDK
call -- a UUID-shape regex check is sufficient and avoids an extra round-trip.
The API token is loaded from `.env` (`MIST_API_TOKEN`) by the existing
`mistapi.APISession`; no prompt is issued for it.

### Rationale

`safe_input()` is the project-wide pattern for prompts; it handles SSH /
container EOF and exits 0 cleanly. The `.env` fallback for `org_id` matches
the convention used by every other org-scoped menu method in the codebase --
NOC engineers usually run against a single org per session. A regex-based
UUID validation gate (`^[0-9a-fA-F]{8}-...` 36-char form) is cheap and
prevents a malformed identifier from reaching the SDK, where the failure
mode would be a less-friendly HTTP 400 / 404. The test-mode `.env` knob
keeps `python MistHelper.py --test` non-interactive while still allowing
the operation to be exercised when an op-specific test ID is provisioned.

### Alternatives Considered

1. **Live `listOrgNacPortals` pre-fetch to let the user pick from a list** --
   rejected for v1; this menu item targets the single-resource GET. A
   picker UI is appropriate when the list endpoint is itself cataloged in a
   future spec, and can be added then without changing this implementation.
2. **Hard-fail in `--test` mode when `MIST_TEST_NACPORTAL_ID` is absent** --
   rejected; the test sweep is designed to skip-not-fail when prerequisites
   are missing. Logging a warning and returning is consistent with sibling
   ops.
3. **Read the API token from `safe_input()` rather than `.env`** -- rejected;
   secrets must come from `.env` per the constitution and to prevent token
   exposure in shell history or SSH session logs.
