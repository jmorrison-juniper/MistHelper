# Phase 0 Research: getOrgDeviceProfile

**Feature**: 604-mist-get-org-device-profile
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

Research output for the five decisions required before Phase 1 design. Each
section uses the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Invoke
`mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile(apisession, org_id, deviceprofile_id)`
and consume the returned `mistapi.APIResponse` object via its `.data` attribute,
which holds a single JSON dict (not a list).

**Rationale**: The enriched per-endpoint doc at
`documentation/api/orgs/GET_orgs_org_id_deviceprofiles_deviceprofile_id.md`
documents the SDK path as
`mistapi.api.v1.orgs.device_profiles.getOrgDeviceProfile()` and the response as
a single object (`"type": "object"`). The mistapi 0.59+ convention used
throughout `MistHelper.py` is to pass the active `APISession` as the first
positional argument followed by path parameters in OpenAPI order, and to read
the JSON body off the response's `.data` field. Two adjacent siblings already
follow this exact pattern in the project: `listOrgDeviceProfiles` (Menu 35) and
`getOrgSiteTemplate` -- both confirm the calling convention. Note: the enriched
doc spells the module as `device_profiles` (snake_case with underscore) while
the OpenAPI tag uses `deviceprofiles` (no underscore). The actual mistapi
package layout in 0.59+ ships the module as `mistapi.api.v1.orgs.deviceprofiles`
(no underscore, matching the URL slug); the snake_case form is a doc artifact.
The implementation must import from `mistapi.api.v1.orgs.deviceprofiles` and
verify at task time by `python -c "from mistapi.api.v1.orgs import deviceprofiles; print(deviceprofiles.getOrgDeviceProfile)"`.

**Alternatives Considered**:
- *Direct REST via `requests`*: Rejected. Project rule -- mistapi SDK is the
  sole permitted Mist Cloud interface. Bypassing it would lose adaptive delay
  metrics, retry logic, and auth handling.
- *Async variant*: Rejected. mistapi 0.59+ exposes only the synchronous
  function for this endpoint, and MistHelper's menu loop is fully synchronous.
- *Batch fetch by iterating list*: Rejected. The user request is for a
  single-record viewer; bulk iteration is already covered by Menu 35
  (`listOrgDeviceProfiles`).

## Research Task 2: Primary Key Strategy

**Decision**: `natural_pk` with `primary_key=['id']` and secondary indexes on
`org_id`, `name`, and `type`.

**Rationale**: Mist device profiles carry a stable server-assigned UUID in
the `id` field that uniquely identifies the profile across the entire
organization and persists across updates. This matches the existing
`natural_pk` pattern used for sibling entities (`listOrgSites`,
`listOrgDeviceProfiles`, `listOrgWlanTemplates`) and enables clean
`INSERT OR REPLACE` upserts on repeated runs. Secondary indexes on `org_id`
support cross-org queries, on `name` support human lookup, and on `type`
support filtering between AP / switch / gateway profiles (the doc's only
documented gotcha).

**Alternatives Considered**:
- *`composite_pk` on `(org_id, id)`*: Rejected. The Mist `id` is already
  globally unique across the API surface; composite keys are reserved for
  time-series rows where the same logical record recurs with a different
  timestamp.
- *`auto_increment_with_unique`*: Rejected. The endpoint returns a record
  with a stable natural identifier, which is the explicit precondition for
  preferring `natural_pk` per the database strategy section of
  `.github/copilot-instructions.md`.

## Research Task 3: Output Filename and SQLite Table

**Decision**:
- CSV filename: `org_device_profile.csv` (singular, since the endpoint
  returns a single record).
- SQLite table name: `org_device_profile`.
- ArangoDB collection name: `org_device_profile`.
- Pass `api_function_name="getOrgDeviceProfile"` to
  `DataExporter.write_with_format_selection()` so the exporter can look up the
  PK strategy from `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**: The MistHelper convention (visible across the org-templates,
org-sites, and org-devices exporters) is to name the artifact in lowercase
snake_case after the resource, singular when the endpoint returns one record
and plural when it returns a collection. Sibling `listOrgDeviceProfiles` uses
`org_device_profiles` (plural list). The new singular form `org_device_profile`
keeps the two clearly distinct in `data/` listings and SQLite schemas, so a
user can tell at a glance whether they ran the list-all or read-one operation.

**Alternatives Considered**:
- *`device_profile.csv`*: Rejected. Loses the `org_` scope prefix used
  consistently by every other org-level exporter.
- *`org_deviceprofile.csv`*: Rejected. The project standard is snake_case
  with explicit word separation; `deviceprofile` runs the words together.
- *Re-use the existing `org_device_profiles` table*: Rejected. Mixing single
  and bulk reads in one table would mask the difference between a complete
  list snapshot and a single targeted read, and would complicate any future
  per-profile diffing.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place the new operation at menu number **96**, inside the
**92-96 Viewers** cluster.

**Rationale**: The MistHelper menu category table in
`.github/copilot-instructions.md` defines `92-96` as Viewers -- single-record
interactive lookups by ID, exactly matching the read-one-by-UUID semantics of
this endpoint. The block `97-101` immediately above is Resource Intensive and
the block `90-91` immediately below is Stats; neither fits a single-record
config viewer. Menu 96 is the topmost free slot in the Viewers cluster as of
this plan, and ships in the default `--test` sweep (the skip list 14, 18,
63-65, 90-100 does not exclude single safe GET viewers when they fit the
Viewers cluster -- the implementation verifies by checking the live skip list
at task time and, if 96 is in the skip range for any reason, falls back to 94,
then 93, then 92 in that order).

**Alternatives Considered**:
- *Menu in the 37-41 Templates block*: Rejected. That block currently lists
  bulk template / profile **collection** exports, not single-record reads,
  and is already fully populated.
- *Menu in 60-72 Site Devices*: Rejected. The endpoint is org-scoped, not
  site-scoped.
- *Menu in 154-194 Destructive*: Rejected. Read-only GET does not belong in
  the destructive range and would gate a safe operation behind the typed
  confirmation requirement.

## Research Task 5: Required User Prompts

**Decision**: Two `safe_input()` prompts in this exact order:
1. `org_id` -- default value loaded from `MIST_ORG_ID` in `.env`; user can
   press Enter to accept the default or type a different UUID.
2. `deviceprofile_id` -- no default; user must supply a UUID (no `.env`
   variable currently maps to a default deviceprofile, and creating one
   would be misleading since orgs typically have many).

Both prompts validate the input matches the Mist UUID shape
(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`) before
the API call. On EOF (SSH / container disconnect) `safe_input()` exits 0
cleanly. On regex mismatch the method logs a `WARNING` and returns early
without calling the API.

**Rationale**: The existing MistHelper convention for org-scoped operations
is to offer `MIST_ORG_ID` as a smart default so power users running against a
single primary org do not retype the UUID for every menu invocation, while
still allowing override for multi-org accounts. The `deviceprofile_id` has
no analogous single-record default because orgs typically have many
profiles (AP, switch, gateway, plus per-model variants), so any default
would be wrong more often than right. Pre-validation of UUID shape avoids
an avoidable 404 round-trip and gives the user a faster, clearer error
message.

**Alternatives Considered**:
- *Prompt for profile name and look up the ID*: Rejected. Would require a
  second API call (`listOrgDeviceProfiles`) and add ambiguity if multiple
  profiles share a name; the user can already run Menu 35 first to get the
  ID.
- *Skip UUID validation*: Rejected. Cheaper to fail fast locally than to
  send a malformed request and parse the API's 400 / 404 response.
- *Accept multiple deviceprofile IDs in one invocation*: Rejected. Scope
  creep -- bulk read is what Menu 35 is for.
