# Phase 0 Research: getOrgUserMac

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-07-01

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_usermacs_usermac_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the module path
`mistapi.api.v1.orgs.user_macs.getOrgUserMac(apisession, org_id, usermac_id)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the
parsed JSON body. The body is a single JSON object (not a list and not
paginated), with the following top-level keys per the doc:

- `id` (string UUID -- unique ID of the user-MAC record within the org, read-only)
- `mac` (string -- the user MAC address; only non-local-admin MACs accepted;
  this is the **only required field** in the 200 OK schema)
- `name` (string -- human-readable name, e.g. `Printer2`)
- `notes` (string -- free-text notes)
- `labels` (array of strings -- tag list, e.g. `["byod","flr1"]`)
- `radius_group` (string -- RADIUS group name, e.g. `VIP`)
- `vlan` (string -- VLAN ID as a string, e.g. `"30"`)

Required path parameters: `org_id` (UUID string) and `usermac_id` (UUID string).
No query parameters. No request body.

**Rationale**:
The enriched per-endpoint doc explicitly lists the SDK path as
`mistapi.api.v1.orgs.user_macs.getOrgUserMac()` (with an underscore --
`user_macs`), matching the mistapi convention of pluralizing plus snake-casing
the URL segment when it contains a hyphen or camelCase collision. The spec.md
lists the module as `mistapi.api.v1.orgs.usermacs`, but the authoritative
mistapi SDK path is the one printed in the enriched doc; final verification
happens at implementation via
`python -c "from mistapi.api.v1.orgs import user_macs; help(user_macs.getOrgUserMac)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/usermacs/{usermac_id}`.* Rejected --
   the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the module path from spec.md (`...orgs.usermacs...` without the
   underscore).* Rejected -- the enriched doc lists the canonical SDK path
   with `user_macs` (underscore), and the spec.md path is a human-readable
   summary rather than an SDK path assertion.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy on a single output table
`org_usermacs`, with PK = `id` (the UUID returned by the API), and a unique
secondary index on `(org_id, mac)` to enforce the business rule that a given
MAC exists at most once per org.

Register in `ENDPOINT_PRIMARY_KEY_STRATEGIES` under the operationId
`getOrgUserMac` with type `natural_pk`, `primary_key: ['id']`, and
`indexes: ['org_id', 'mac', 'radius_group', 'vlan']`.

**Rationale**:
The 200 OK response includes an `id` field described as "Unique ID of the
object instance in the Mist Organization" (a UUID, read-only). This is the
stable natural business key for the record; re-running the menu for the same
`(org_id, usermac_id)` pair must upsert the same row via `INSERT OR REPLACE`.
The `(org_id, mac)` pair is also unique per Mist's data model (a MAC is
assigned to at most one usermac record in an org), so a secondary unique
index guards against inconsistent data if the caller later ingests bulk
usermac exports. `radius_group` and `vlan` are common filter columns in NAC
analytics, so they receive non-unique indexes.

**Alternatives Considered**:

1. *`composite_pk` on `(org_id, mac)`.* Rejected -- `id` is already the
   canonical Mist UUID for the record; using it as PK matches the natural_pk
   pattern used elsewhere in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (e.g.
   `listOrgSites` on `['id']`).
2. *`auto_increment_with_unique`.* Rejected -- the API provides a stable UUID;
   using an artificial autoincrement column would defeat clean SQL joins from
   NAC-client tables that also reference `usermac_id`.
3. *`composite_pk` on `(org_id, id)`.* Rejected -- `id` is globally unique
   within Mist (UUID), so pairing it with `org_id` adds no uniqueness value
   and only complicates joins.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_usermac_<usermac_id_short>.csv`
- SQLite table: `org_usermacs`
- ArangoDB collection: `org_usermacs` (same name; graph edges linking to the
  parent org vertex are handled by the existing polyglot writer)
- `org_id_short` is the first 8 hex characters of the org UUID and
  `usermac_id_short` is the first 8 hex characters of the usermac UUID --
  matching the naming convention used by adjacent per-object reads in
  MistHelper for human-readable filenames without leaking full UUIDs into
  shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgUserMac"` (matching
the operationId). The DataExporter uses that string as the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by other per-object read endpoints in
MistHelper (single-object GETs land in per-object files under `data/`). Using
the operationId as the `api_function_name` keeps the PK-strategy lookup
unambiguous and consistent with how bulk endpoints such as `searchOrgUserMacs`
would register.

**Alternatives Considered**:

1. *One shared file `data/all_usermacs.csv` that accumulates rows across
   invocations.* Rejected -- forces the user to filter downstream and mixes
   snapshots from unrelated orgs; also complicates upsert semantics on CSV
   backend (no natural PK enforcement).
2. *Full UUID in the filename.* Rejected -- leaks the org UUID into shell
   history and `ls` output unnecessarily. The short form is enough to
   disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, inside the Safe Org Exports
cluster (1-59), under the Misc sub-range (56-59). Category label: "Safe Org
Exports -- User MACs".

**Rationale**:
`.github/copilot-instructions.md` describes menu ranges as:
1-59 Safe Org Exports (with Misc at 56-59), 60-96 Interactive Safe, 97-101
+ 153 Resource Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194
Destructive. `getOrgUserMac` is a single-object read of a user-MAC assignment
record -- a small, safe org-level GET that fits cleanly in the Misc bucket
alongside other one-off org reads. Number 58 is the next contiguous integer
in that sub-range that is provisionally free. The number is verified at
`/speckit.tasks` time by grep'ing `MistHelper.py` for the latest allocated
menu integer; if 58 is taken, the next free integer in the same cluster is
used (59, then 57).

**Alternatives Considered**:

1. *Slot inside NAC / Interactive Safe (60-96) alongside NAC client
   diagnostics.* Rejected -- this is not an interactive troubleshooting flow;
   it is a plain read of a config record. Safe Org Exports is the correct
   risk tier.
2. *Append to the very end (e.g., 195).* Rejected -- the destructive cluster
   ends at 194, and placing a safe read above the destructive block visually
   mis-signals the risk level to a junior NOC engineer scrolling the menu.
3. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a
   single unpaginated GET returning ~7 fields; it has no long-running work
   and does not belong in that bucket.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_user_mac:org_id"`. Default: the value of `MIST_ORG_ID` in `.env` if
   present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING`
   and return early.
2. `usermac_id` -- prompt: `"User MAC ID (UUID): "`, context:
   `"org_user_mac:usermac_id"`. No `.env` default (per-record lookup, so no
   sensible default exists). Validated via `is_valid_uuid()` before the API
   call; on failure, log `WARNING` and return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint's path parameters are exactly `org_id` and `usermac_id`; there
are no query parameters and no request body. Prompting for anything beyond
these two IDs would be gratuitous. The `usermac_id` cannot be defaulted from
`.env` because it identifies a specific record; the user is expected to have
learned the ID from a prior `searchOrgUserMacs` / `listOrgUserMacs` export.

**Alternatives Considered**:

1. *Add a MAC-address prompt and internally resolve to `usermac_id` via
   `searchOrgUserMacs` first.* Rejected -- doubles the API call count for
   what is meant to be a lightweight per-record read, and expands the menu
   method beyond the 5-Item Rule ceiling. If MAC-address-based lookup is
   needed, that is a separate menu item wrapping `searchOrgUserMacs`.
2. *Skip both prompts and read both IDs from `.env`.* Rejected --
   `usermac_id` is not a stable environment-level value; wiring it into
   `.env` would encourage stale-ID reads.
3. *Add an output filename override prompt.* Rejected -- adds keystrokes
   without operational value. The deterministic filename scheme in Research
   Task 3 makes results easy to find under `data/`.
