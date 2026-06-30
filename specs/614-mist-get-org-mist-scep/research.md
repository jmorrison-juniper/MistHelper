# Phase 0 Research: getOrgMistScep

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_setting_mist_scep.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.setting.mist_scep.getOrgMistScep(apisession, org_id)`.
The SDK returns a `mistapi.APIResponse` whose `.data` attribute is the parsed JSON body.
The body is a single JSON object (not a list, not paginated), with the following top-level
keys per the doc:

- `cert_providers` (array of string enum: `intune`, `jamf`, `byod`) -- list of SCEP cert
  providers configured for the org.
- `enabled` (boolean, read-only) -- whether SCEP is enabled for the org.
- `intune_scep_url` (string, read-only) -- Intune SCEP enrollment URL, e.g.
  `https://scep.mistsys.com/api/v1/incoming/intune/:org_id/scep`.
- `jamf_access_token` (string, read-only) -- bearer token used by Jamf to authenticate to
  the Mist SCEP webhook. SENSITIVE: never log this value.
- `jamf_scep_url` (string, read-only) -- Jamf SCEP enrollment URL.
- `jamf_webhook_url` (string, read-only) -- Jamf webhook URL.
- `suspended` (boolean, default `false`) -- whether SCEP is suspended for this org.

Required path parameter: `org_id` (UUID string). No query parameters. No request body.

**Rationale**:
The enriched doc names the SDK module as `mistapi.api.v1.orgs.scep` in its "mistapi SDK"
section, but the OpenAPI URL is `/api/v1/orgs/{org_id}/setting/mist_scep` and the
spec.md (the authoritative feature contract) names the module `mistapi.api.v1.orgs.setting.mist_scep`.
The mistapi SDK historically generates module paths from the URL, not the doc-page tag --
verified by inspecting adjacent endpoints under the same URL prefix (for example
`PUT /orgs/{org_id}/setting/mist_scep` which lives at `mistapi.api.v1.orgs.setting.mist_scep`).
We follow the URL-derived path the spec already documents. Final verification happens at
implementation time via `python -c "from mistapi.api.v1.orgs.setting import mist_scep;
help(mist_scep)"` inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/setting/mist_scep`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the doc page's `mistapi.api.v1.orgs.scep` path.* Rejected -- the doc page is a
   convenience link and does not match the SDK's URL-derived layout; the URL-based path
   is canonical and matches sibling endpoints (PUT/DELETE) under the same URL.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy with PK = `(org_id,)`. The SCEP settings record is
a singleton per organization -- one org has exactly one settings document. Repeated runs
of the menu item must overwrite the prior row for the same org, not append duplicates.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `natural_pk` and injects
`org_id` from the MistHelper context before the upsert (Mist does not return `org_id` in
the body, but MistHelper always knows which org the call targeted).

```python
'getOrgMistScep': {
    'type': 'natural_pk',
    'primary_key': ['org_id'],
    'indexes': ['enabled', 'suspended'],
    'table': 'org_setting_mist_scep',
}
```

**Rationale**:
The endpoint describes a per-org settings singleton. There is exactly one row per org,
keyed by `org_id`. `INSERT OR REPLACE` cleanly handles re-runs. Natural PK is the simplest
strategy that satisfies the upsert contract; composite PK would add no value (there is no
second business field that uniquely partitions the data) and auto-increment would let
re-runs accumulate stale snapshots.

**Alternatives Considered**:

1. *`composite_pk` on `(org_id, polled_at_utc)`.* Rejected -- would let every poll create
   a new row and defeat the upsert semantics. SCEP settings change rarely (manual
   admin action) and a history audit, if ever needed, belongs in a separate audit table.
2. *`auto_increment_with_unique` with unique constraint on `org_id`.* Rejected -- adds a
   surrogate key that nothing references and complicates joins; natural PK on `org_id`
   gives the same upsert behavior with less ceremony.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_mist_scep_setting.csv`
- SQLite table: `org_setting_mist_scep`
- `org_id_short` is the first 8 hex characters of the org UUID -- the same convention
  used by adjacent org-settings exports for human-readable filenames that do not leak
  full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getOrgMistScep"` (matching the operationId). The DataExporter uses that string as
the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by sibling org-setting reads (for example
`getOrgSetting` -> `org_<short>_setting.csv`). One row per org keeps the file trivially
small and trivially queryable; no JSON-encoded blobs in CSV cells.

**Alternatives Considered**:

1. *Per-provider sub-file (`..._scep_intune.csv`, `..._scep_jamf.csv`).* Rejected --
   over-fragments output for a one-row payload and forces joins on every read.
2. *Full org UUID in the filename.* Rejected -- leaks the UUID into shell history and
   `ls` output unnecessarily. The 8-char short form disambiguates locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 88**, sitting inside the Safe Org Exports
cluster, in the org-settings sub-band. The category label is "Safe Org Exports --
Org Settings (SCEP)".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. Org-settings reads live inside the
safe export band. 88 is the next free integer in the 80s settings sub-cluster per the
current README menu table, well clear of the resource-intensive block at 96-101 and the
destructive block at 154-194. The number is provisional -- at `/speckit.tasks` time,
MistHelper.py is grep'd for the latest allocated menu integer and 88 is shifted forward
if a conflict exists.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194, and
   placing a read-only settings query above the destructive block visually mis-signals
   the risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Interactive (124-152).* Rejected -- this is a single non-interactive GET
   with one prompt; it does not belong in the interactive cluster.
3. *Slot inside Resource Intensive (96-101).* Rejected -- the endpoint returns a single
   small JSON object with no pagination and no long-running work. It belongs in the safe
   block.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly one** value via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_mist_scep:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter accepts the
   default). Validated via the existing `is_valid_uuid()` helper before the API call; on
   failure, log `WARNING` and return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for the org_id prompt.

**Rationale**:
The Mist SCEP setting is an org-scoped singleton. No site, device, template, or query
parameter is required. Adding any second prompt would only add keystrokes without
operational value.

**Alternatives Considered**:

1. *Prompt for an output filename override.* Rejected -- adds keystrokes without
   operational value. The deterministic filename scheme in Research Task 3 makes results
   easy to find under `data/`.
2. *Prompt for a "redact sensitive fields" flag to suppress `jamf_access_token` from
   output.* Rejected at this stage -- the field is needed in some operational workflows
   (rotating Jamf integration credentials, debugging webhook failures). The sensitivity
   rule is enforced at the *log* layer (never logged above DEBUG; DEBUG only logs
   presence, not value), not at the *output* layer. A future redaction flag can be added
   as a separate spec if a user requests it.
