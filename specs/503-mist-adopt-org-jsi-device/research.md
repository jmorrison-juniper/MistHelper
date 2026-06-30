# Phase 0 Research: adoptOrgJsiDevice

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-28

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_jsi_devices_outbound_ssh_cmd.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the URL-mirroring module path:
`mistapi.api.v1.orgs.jsi.devices.outbound_ssh_cmd.adoptOrgJsiDevice(apisession, org_id)`.
The SDK returns a `mistapi.APIResponse` whose `.data` attribute is the parsed JSON
body. The body is a single JSON object with one required field:

- `cmd` (string, REQUIRED) -- the outbound SSH command string that an operator copies
  onto a Juniper device to make it dial back to the Mist cloud for adoption into the
  organization.

Required path parameter: `org_id` (UUID string). No query parameters. No request body.
Not paginated. Standard Mist 5000-call/hour rate limit applies.

**Rationale**:
The enriched doc lists the SDK as `mistapi.api.v1.orgs.jsi.adoptOrgJsiDevice()`, but
the OpenAPI URL is `/api/v1/orgs/{org_id}/jsi/devices/outbound_ssh_cmd`. The mistapi
SDK historically derives module paths from the URL (one Python module per URL segment),
not from the OpenAPI tag. The spec.md explicitly names
`mistapi.api.v1.orgs.jsi.devices.outbound_ssh_cmd`, matching the URL one-for-one, so
we follow the spec. Final verification happens at implementation time with
`python -c "from mistapi.api.v1.orgs.jsi.devices import outbound_ssh_cmd; help(outbound_ssh_cmd)"`
inside the venv. If the actual installed `mistapi` 0.59+ exposes the function only at
the shorter `mistapi.api.v1.orgs.jsi` module path, the import is adjusted in
implementation without any contract change.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/jsi/devices/outbound_ssh_cmd`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the doc's shorter path (`mistapi.api.v1.orgs.jsi.adoptOrgJsiDevice`).*
   Rejected as the primary -- the URL-based path is canonical for the SDK; the
   shorter form is only an implementation-time fallback.

## Research Task 2: Primary Key Strategy

**Decision**:
Use **natural_pk** with `org_id` as the sole primary key, on a single output table
`org_jsi_outbound_ssh_cmd`. One row per organization. Re-running the menu item against
the same org performs an `INSERT OR REPLACE` upsert on `org_id`, refreshing the `cmd`
string and the `polled_at_utc` timestamp.

Registration in `ENDPOINT_PRIMARY_KEY_STRATEGIES`:

```python
'adoptOrgJsiDevice': {
    'type': 'natural_pk',
    'primary_key': ['org_id'],
    'indexes': ['polled_at_utc'],
    'table': 'org_jsi_outbound_ssh_cmd',
}
```

**Rationale**:
The response body contains only `cmd` -- no UUID, no timestamp, no per-row identifier.
The only stable identifier in the call context is the `org_id` the user supplied. The
`cmd` itself is org-scoped (each org's outbound SSH command is unique to that org's
adoption bootstrap), so one row per org is the correct cardinality. `natural_pk` on
`org_id` matches MistHelper's convention for other org-scoped singleton endpoints
(e.g., org settings) and gives clean upsert semantics on repeated polls.

**Alternatives Considered**:

1. *`composite_pk` on `(org_id, polled_at_utc)`.* Rejected -- this would accumulate one
   row per poll, which is wasteful and gives no operational value since the `cmd`
   string changes only when Mist rotates the adoption bootstrap (rare).
2. *`auto_increment_with_unique` keyed on `cmd`.* Rejected -- `cmd` strings are long
   and hashed as PK is fragile; `org_id` is the natural business key.
3. *Skip persistence entirely and just print the `cmd` to stdout.* Rejected -- breaks
   the multi-backend export contract every other MistHelper menu item honors, and the
   `cmd` may be sensitive enough that stdout logging is undesirable.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_jsi_outbound_ssh_cmd.csv`
- SQLite table: `org_jsi_outbound_ssh_cmd`
- `org_id_short` is the first 8 hex characters of the org UUID, matching the
  convention used by adjacent license and JSI exports for human-readable filenames
  without leaking full UUIDs into shell history.

The `api_function_name` passed to `DataExporter.write_with_format_selection()` is
`"adoptOrgJsiDevice"` (matching the operationId). The DataExporter uses this string as
the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Naming matches the pattern used by adjacent JSI exports (e.g.,
`org_<short>_jsi_devices.csv` from the related `listOrgJsiDevices` endpoint). The
table name `org_jsi_outbound_ssh_cmd` is parallel to the URL segment, immediately
recognizable to a NOC engineer browsing `data/mist_data.db` with `sqlite3` or DB
Browser.

**Alternatives Considered**:

1. *Single shared table for all JSI outputs.* Rejected -- breaks the one-table-per-
   endpoint convention used throughout MistHelper and conflates schemas.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell history
   unnecessarily. The 8-char short form is enough to disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting at the boundary between the
Safe Org Exports cluster and the Resource Intensive cluster (96 is the first integer
of the 96-101 + 153 resource-intensive band per the published menu map, but the call
itself is a single small GET with no pagination, so the placement is purely about
preserving sequential allocation). Category label: "Safe Org Exports -- JSI".

If `MistHelper.py` already contains a `JsiExportUtils` class (or equivalent), the
method attaches there. If not, a new `JsiExportUtils` class is introduced as the home
for this method and for future JSI endpoints (`listOrgJsiDevices`,
`listOrgJsiInventory`, etc.). Introducing a focused class is preferred over adding a
JSI method to a generic existing class -- it keeps the 5-Item Rule healthy as JSI
coverage grows.

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. Spec 500 proposed 95, so
96 is the next contiguous integer. The endpoint is read-only and not destructive, so
it must sit well outside the 154-194 destructive block. The number is provisional --
at `/speckit.tasks` time `MistHelper.py` is grep'd for the latest allocated menu
integer and 96 is shifted forward if a conflict exists with another in-flight branch.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194,
   and placing a read-only JSI utility above the destructive block visually
   mis-signals risk to a junior NOC engineer.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET that returns a small JSON object with one string field. It is not resource
   intensive.
3. *Attach to an existing generic export class.* Rejected -- a dedicated JSI class
   keeps the per-class method count under the 5-Item Rule as more JSI endpoints are
   added later.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly one** value via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_jsi_outbound_ssh_cmd:org_id"`. Default: the value of `MIST_ORG_ID` in `.env`
   if present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and return
   early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for the org_id prompt.

**Rationale**:
The endpoint is org-scoped only. There are no site, device, or template parameters --
the OpenAPI spec lists only the single `org_id` path parameter and no query
parameters. Asking for nothing else keeps the menu item efficient and minimizes EOF
exposure in SSH/container contexts.

**Alternatives Considered**:

1. *Add an output filename override prompt.* Rejected -- adds keystrokes without
   operational value. The deterministic naming scheme in Research Task 3 makes
   results easy to find under `data/`.
2. *Add a "print to stdout instead of file" prompt.* Rejected -- the `cmd` string may
   be sensitive (it embeds adoption credentials); printing to stdout would leak into
   shell history and SSH session logs. The export-only path is the safer default.
3. *Skip the org_id prompt and always use `MIST_ORG_ID` from `.env`.* Rejected --
   forces operators with multiple orgs to edit `.env` between runs, which is poor UX
   and risks committing a stale default.
