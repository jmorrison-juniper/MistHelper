# Phase 0 Research: getOrgMxEdgeUpgradeInfo

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_mxedges_versions.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors
the OpenAPI URL: `mistapi.api.v1.orgs.mxedges.versions.getOrgMxEdgeUpgradeInfo(
apisession, org_id, channel=None, distro=None)`. The SDK returns a
`mistapi.APIResponse` whose `.data` attribute is the parsed JSON body. The body is
a JSON **array** (not a single object and not paginated) of objects each shaped:

- `package` (string, **required**) -- Debian package name, e.g. `mxagent`, `tunterm`.
- `version` (string, **required**) -- semantic version string, e.g. `2.4.100`.
- `distro` (string, optional) -- distro code name, e.g. `bullseye`, `buster`.
- `default` (boolean, optional) -- `true` when this package+version is the default
  shipped for the requested channel and distro.

The schema declares `uniqueItems: true`, so within a single response no two items
share all four fields. The example payload in the doc:

```json
[
  {"default": true, "distro": "bullseye", "package": "mxagent", "version": "2.4.100"},
  {"distro": "bullseye", "package": "tunterm", "version": "1.0.0"}
]
```

Required path parameter: `org_id` (UUID string).
Optional query parameters: `channel` (`stable` (default) / `beta` / `alpha`),
`distro` (e.g. `buster`, `bullseye`). Both default to absent, in which case the
Mist API returns the full available-package list for the stable channel.

**Rationale**:
The enriched per-endpoint doc lists the SDK module under
`mistapi.api.v1.orgs.mxedges.getOrgMxEdgeUpgradeInfo()` (one level up from the URL
path). However, the mistapi SDK's convention -- verified by inspecting adjacent
endpoints under `/orgs/{org_id}/mxedges/*` -- generates module paths from the
full URL, so the canonical import is
`mistapi.api.v1.orgs.mxedges.versions`. Both forms typically work because mistapi
re-exports endpoint functions at the parent package level; the URL-mirroring path
is the authoritative one and matches the spec.md exactly. Final verification
happens at implementation time via
`python -c "from mistapi.api.v1.orgs.mxedges import versions; help(versions)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/mxedges/versions`.* Rejected -- the
   constitution forbids direct HTTP when a mistapi method exists.
2. *Use the parent module path (`mistapi.api.v1.orgs.mxedges`) as suggested by
   the enriched doc.* Rejected -- the SDK organizes modules by URL path, and the
   versions sub-path is its own module. We follow the URL-based convention to
   stay consistent with adjacent endpoints.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table
`org_mxedge_upgrade_info`. PK columns:

- `org_id` -- injected by MistHelper before write (the API does not echo the org
  back in the body).
- `channel` -- injected by MistHelper from the query-parameter value used
  (defaults to `"stable"` when the user omits the prompt).
- `distro` -- the `distro` field from each row; falls back to a sentinel
  `"_unspecified_"` when the API row omits it.
- `package` -- the `package` field from each row.
- `version` -- the `version` field from each row.

Registration in `ENDPOINT_PRIMARY_KEY_STRATEGIES` uses type `composite_pk`. The
strategy entry also declares a secondary index on `default` so callers can quickly
filter to "current default firmware per channel/distro" without a full scan.

**Rationale**:
A given Mist Edge org may query the same endpoint multiple times across different
channels and distros, and may re-poll the same channel/distro pair over time as
Juniper publishes new versions. Upserting on `(org_id, channel, distro, package,
version)` guarantees that:

1. Re-polling the same channel/distro/org never produces duplicate rows for the
   same package/version pair.
2. Polling a *different* channel (e.g. `beta` after `stable`) adds new rows
   without overwriting the stable rows.
3. When Juniper ships a new version of `mxagent` for `bullseye` on `stable`, a
   re-poll inserts the new `(package, version)` row alongside the older one --
   preserving history rather than blowing it away, which is what an operator
   wants when auditing firmware availability over time.

The Mist API does not provide a stable artifact identifier (no UUID per package
row), so a natural composite key built from the business-meaningful fields is
the only correct option.

**Alternatives Considered**:

1. *`natural_pk` on `package` alone.* Rejected -- the same package name (e.g.
   `mxagent`) exists across multiple channels, distros, and versions; a single-
   column PK would collide on the first re-poll.
2. *`auto_increment_with_unique`.* Rejected -- would let repeated polls
   accumulate duplicate snapshots, defeating the upsert behavior the spec
   requires (FR-005).
3. *Composite PK without `channel`.* Rejected -- if the user queries `stable`
   then `beta`, the same `(distro, package)` pair could exist in both channels
   with different defaults; without `channel` in the PK, the second poll would
   silently overwrite the first.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_mxedge_upgrade_info.csv`
- SQLite table: `org_mxedge_upgrade_info`
- `org_id_short` is the first 8 hex characters of the org UUID -- the existing
  MistHelper convention for human-readable filenames that do not leak full
  UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgMxEdgeUpgradeInfo"`
(matching the operationId exactly). The DataExporter uses that string as the
lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
The naming follows the pattern used by adjacent Mist Edge exports
(e.g. `getOrgMxEdges` -> `data/org_<id>_mxedges.csv`,
`org_mxedges` SQLite table). Singular SQLite table keeps schema simple; the
response is a flat list, no need for parent/child split.

**Alternatives Considered**:

1. *Separate table per channel (`org_mxedge_upgrade_info_stable`, `_beta`,
   `_alpha`).* Rejected -- three tables for what is conceptually one entity
   bloats the schema and complicates SQL queries; including `channel` as a PK
   column achieves the same isolation with a single, queryable table.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell
   history and `ls` output unnecessarily. The 8-char short form is enough to
   disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 59**, sitting inside the Safe Org
Exports cluster (1-59) in the "Misc" sub-range (56-59). The category label is
"Safe Org Exports -- Mist Edge".

**Rationale**:
`.github/copilot-instructions.md` documents the menu ranges as:
- 1-59 Safe Org Exports (with Sites 1-7, Inventory 8-14, Device stats 15-19,
  Events 20-26, Clients 27-30, Gateways 31-36, Templates 37-41, Config/Admin
  42-50, SLE 51-55, Misc 56-59).
- 60-96 Interactive Safe.
- 97-101 + 153 Resource Intensive.
- 102-123 WebSocket.
- 124-152 Interactive.
- 154-194 Destructive.

Mist Edge upgrade information is a single, lightweight GET that returns a small
JSON array. It is read-only, non-destructive, and not interactive (no per-item
prompts during execution beyond the upfront `org_id` / `channel` / `distro`
selection). It therefore belongs in the safe org exports cluster, specifically
the Misc sub-range, and 59 is the highest available integer below the
Interactive Safe block at 60. The number is provisional -- at `/speckit.tasks`
time `MistHelper.py` is grep'd for the latest allocated menu integer and 59 is
shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Slot inside the Inventory sub-range (8-14).* Rejected -- those operations
   list devices currently in inventory, not available firmware versions.
   Semantically distinct.
2. *Slot inside Interactive Safe (60-96) adjacent to Mist Edge stats.*
   Rejected -- the endpoint is non-interactive once the user has answered the
   initial prompts; it does not poll, page, or stream. Safe Org Exports is the
   correct category.
3. *Append at end of menu (e.g. 195+).* Rejected -- placing a read-only call
   above the destructive cluster (154-194) misleads NOC engineers about its
   risk level.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **three** values via `safe_input()`. All
three accept an Enter-press default and use explicit `context=` tags so EOF
(common in containerized SSH-via-2200 sessions) exits cleanly.

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_mxedge_upgrade_info:org_id"`. Default: the value of `MIST_ORG_ID` in
   `.env` if present. Validated via the existing `is_valid_uuid()` helper
   before the API call; on failure, log `WARNING` and return early.
2. `channel` -- prompt:
   `"Upgrade channel (stable / beta / alpha) [stable]: "`, context:
   `"org_mxedge_upgrade_info:channel"`. Default: `"stable"`. Accepted values
   normalized to lowercase; unrecognized values are passed through to Mist,
   which will respond with HTTP 400 (logged as a `WARNING`).
3. `distro` -- prompt:
   `"Distro filter (e.g. bullseye, buster) [all]: "`, context:
   `"org_mxedge_upgrade_info:distro"`. Default: empty string (no filter, Mist
   returns all distros). Passed straight through to the SDK as `distro=...`
   when non-empty, omitted otherwise.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint is org-scoped and supports two optional filters. Exposing both
filters as prompts gives a junior NOC engineer the obvious knobs without forcing
them to memorize query-string syntax. Defaulting `channel` to `stable` matches
Mist's own API default and is the value almost every operator wants. Leaving
`distro` empty by default returns the full catalog, which is the most useful
first-look output.

**Alternatives Considered**:

1. *Single prompt for `org_id` only, always request all channels and distros.*
   Rejected -- the response with no filters is small (tens of rows), but the
   prompts add zero risk and let an operator narrow scope when investigating a
   specific channel during a firmware roll-out.
2. *Drive `channel` and `distro` from `.env` only.* Rejected -- these are
   per-invocation choices, not deployment-wide settings; making them
   interactive matches the rest of MistHelper's UX.
3. *Add a fourth prompt for an output filename override.* Rejected -- the
   deterministic filename scheme in Research Task 3 already makes results easy
   to find under `data/`; an override prompt adds keystrokes without
   operational value.
