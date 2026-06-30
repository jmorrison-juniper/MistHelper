# Phase 0 Research: getOrgMxEdgeVmParams

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_mxedges_mxedge_id_vm_params.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the module path that mirrors the
OpenAPI URL:
`mistapi.api.v1.orgs.mxedges.vm_params.getOrgMxEdgeVmParams(apisession, org_id,
mxedge_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a list
and not paginated), with the following top-level keys per the enriched doc's
200 OK schema:

- `model` (string) -- VM SKU. Example: `"ME-VM"`.
- `name` (string, optional) -- user-supplied display name for the VM.
- `user_data` (string) -- base64-encoded cloud-init user data used by the VM
  on first boot. Treated as sensitive (may contain bootstrap credentials).

Required path parameters: `org_id` (UUID string) and `mxedge_id` (UUID string).
No query parameters. No request body.

**Rationale**:
The enriched per-endpoint doc lists the SDK as
`mistapi.api.v1.orgs.mxedges.getOrgMxEdgeVmParams()` directly under the
`mxedges` module. The spec.md, however, names the deeper path
`mistapi.api.v1.orgs.mxedges.vm_params`. Mistapi's code generator typically
mirrors the OpenAPI URL path one-for-one, so `/orgs/{org_id}/mxedges/{mxedge_id}/vm_params`
maps to `mistapi.api.v1.orgs.mxedges.vm_params`. We follow the spec.md path
(the authoritative contract) and verify at implementation time via
`python -c "from mistapi.api.v1.orgs.mxedges import vm_params; help(vm_params)"`
inside the venv. If the symbol is actually exposed on the parent `mxedges`
module (the doc's claim), the implementation falls back to that import without
changing behavior.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/mxedges/{mxedge_id}/vm_params`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method
   exists.
2. *Use the shorter path implied by the doc
   (`mistapi.api.v1.orgs.mxedges.getOrgMxEdgeVmParams`).* Held in reserve as
   the fallback import. The spec.md path is preferred because it is consistent
   with how adjacent mxedge sub-paths
   (`mistapi.api.v1.orgs.mxedges.tunnels`, etc.) are organized.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table
`org_mxedge_vm_params` with `PRIMARY KEY (org_id, mxedge_id)`. Register under
the operationId `getOrgMxEdgeVmParams` in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
with `type='composite_pk'` and an additional index on `model` for cross-org
SKU reporting.

```python
'getOrgMxEdgeVmParams': {
    'type': 'composite_pk',
    'primary_key': ['org_id', 'mxedge_id'],
    'indexes': ['model'],
    'table': 'org_mxedge_vm_params',
}
```

`org_id` and `mxedge_id` are injected by MistHelper from the user prompts
before the upsert. Mist does not echo them in the response body; this matches
the pattern already used by other per-device endpoints in MistHelper.

**Rationale**:
The endpoint returns the *current* VM parameters for one Mist Edge in one
organization. Re-running the menu item against the same `(org_id, mxedge_id)`
pair must update the existing row rather than append a duplicate (the user
may poll to see if `name` or `user_data` changed after a re-provision).
`(org_id, mxedge_id)` is the natural composite key: `mxedge_id` is globally
unique in practice but pairing it with `org_id` keeps the schema consistent
with every other per-mxedge MistHelper table and supports per-org filtering
without a join. `INSERT OR REPLACE` upserts every poll's view of the VM
parameters cleanly. `model` is indexed because operators routinely audit
which SKU (`ME-VM` vs. future variants) is deployed across many mxedges.

**Alternatives Considered**:

1. *`natural_pk` on `mxedge_id` alone.* Rejected -- breaks the per-org
   filtering pattern used throughout MistHelper and would force a code path
   different from every other mxedge table.
2. *`auto_increment_with_unique`.* Rejected -- would let repeated polls
   accumulate duplicate snapshots, defeating the upsert behavior the spec
   requires (FR-005).
3. *Composite key including `model` to support edge re-modeling.* Rejected
   -- `model` is a queryable attribute, not an identity. Re-modeling a Mist
   Edge VM is rare and is correctly represented as an update of the same
   row.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_mxedge_<mxedge_id_short>_vm_params.csv`
- SQLite table: `org_mxedge_vm_params`
- `org_id_short` = first 8 hex characters of the org UUID;
  `mxedge_id_short` = first 8 hex characters of the mxedge UUID -- the
  convention already used by adjacent per-mxedge exports in MistHelper for
  human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgMxEdgeVmParams"`
(matching the operationId). The DataExporter uses that string as the lookup
key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by existing mxedge exports
(`org_<short>_mxedges.csv`, etc.). One output file / one SQLite table keeps
the schema clean. The two short UUID slugs in the filename disambiguate when
a developer runs the menu item against several mxedges in the same org.

**Alternatives Considered**:

1. *Single org-wide file with one row per mxedge.* Rejected -- the menu
   item targets exactly one mxedge per invocation (per spec). Aggregating
   across mxedges would change the prompt contract (would require listing
   mxedges first) and is a separate spec.
2. *Full UUIDs in the filename.* Rejected -- leaks the org and mxedge UUIDs
   into shell history and `ls` output unnecessarily. The 8-character short
   form is enough to disambiguate locally.
3. *JSON dump of the raw response with no flattening.* Rejected -- breaks
   SQL queryability and conflicts with the flattening convention used
   everywhere else in MistHelper. The flatten step is trivial here (three
   fields).

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 91**, sitting at the bottom of the
Stats slice (80-91) inside the Interactive Safe band (60-96). Category label:
"Interactive Safe -- MxEdge VM Parameters".

**Rationale**:
`.github/copilot-instructions.md` describes the menu ranges as: 1-59 Safe Org
Exports, 60-96 Interactive Safe (Site devices 60-72, Insights 73-79, Stats
80-91, Viewers 92-96), 97-101 + 153 Resource Intensive, 102-123 WebSocket,
124-152 Interactive, 154-194 Destructive. This endpoint requires *two*
interactive prompts (`org_id` and `mxedge_id`), placing it firmly in the
Interactive Safe band. Inside that band, Stats (80-91) is the closest
semantic fit since VM parameters describe a single edge appliance's
provisioning state, and 91 is the last open slot before the Viewers cluster
begins at 92. The number is provisional -- at `/speckit.tasks` time,
`MistHelper.py` is grep'd for the latest allocated menu integer and 91 is
shifted forward if a conflict exists.

If the final number lands inside the `--test` skip range (90-100), task
generation moves it out so the smoke sweep covers it (the skip range is for
destructive / heavy operations, neither of which applies here).

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends
   at 194, and placing a read-only mxedge query above the destructive block
   visually mis-signals the risk level to a junior NOC engineer scrolling
   the menu.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a
   single GET that returns a tiny JSON object with three fields, no
   pagination, and no long-running work. It does not belong with the
   resource-intensive ops.
3. *Slot inside the Viewers cluster (92-96).* Rejected -- Viewers in the
   existing menu render data already in `data/`; this menu item is an
   *export*, not a viewer.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_mxedge_vm_params:org_id"`. Default: the value of `MIST_ORG_ID` in
   `.env` if present (pressing Enter accepts the default). Validated via the
   existing `is_valid_uuid()` helper before the API call; on failure, log
   `WARNING` and return early.
2. `mxedge_id` -- prompt: `"Mist Edge ID (UUID): "`, context:
   `"org_mxedge_vm_params:mxedge_id"`. Default: the value of
   `MIST_MXEDGE_ID` in `.env` if present (pressing Enter accepts the
   default). Validated via `is_valid_uuid()` before the API call; on
   failure, log `WARNING` and return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_MXEDGE_ID` -- optional default for prompt 2 (new env var; documented
  in `quickstart.md` and `deploy/.env.example` updates that ship with this
  PR).

**Rationale**:
The endpoint is keyed on two UUIDs: `org_id` and `mxedge_id`. No site, device,
or template scoping applies, and there are no query parameters. Two prompts is
the minimum and matches the prompt density of adjacent per-mxedge menu items.
A new `MIST_MXEDGE_ID` env default keeps the prompt count effectively zero for
the most common dev-loop case (re-running against the same edge during
debugging) without forcing it for first-time users.

**Alternatives Considered**:

1. *Auto-discover all mxedges in the org and run against each.* Rejected --
   that is a different operation (org-wide VM-params dump). When the user
   wants the per-edge view, batching adds latency and obscures which edge
   produced which row. A future spec can layer a "for-each-mxedge" wrapper
   on top of this single-edge menu item.
2. *Prompt for an output filename override.* Rejected -- adds keystrokes
   without operational value. The deterministic filename scheme in Research
   Task 3 makes results easy to find under `data/`.
3. *Skip the mxedge prompt and require it as a CLI flag only.* Rejected --
   breaks parity with adjacent interactive menu items and the spec's FR-002
   requirement that `safe_input()` be used for all required inputs.
