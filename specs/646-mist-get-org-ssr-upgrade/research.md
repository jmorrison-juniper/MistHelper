# Phase 0 Research: getOrgSsrUpgrade

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/utilities/GET_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md`
(the enriched OpenAPI per-endpoint doc for path
`/api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel`).

**Decision**:
Invoke the endpoint via the mistapi SDK at the URL-mirroring module path
`mistapi.api.v1.orgs.ssr.upgrade.cancel.getOrgSsrUpgrade(apisession, org_id,
upgrade_id)`. The SDK returns a `mistapi.APIResponse`; `.data` is the parsed
JSON body. The body is a single JSON object (not a list, not paginated) with
the following top-level keys per the doc:

- `id` (string, UUID) -- unique upgrade job identifier, marked `readOnly` and
  `contentEncoding: uuid` in the schema.
- `channel` (string, non-empty) -- SSR release channel used by the job
  (`alpha`, `beta`, `stable`, or a build-specific channel string).
- `device_type` (string) -- target device type identifier (SSR family).
- `status` (string, non-empty) -- job status (values observed by MistHelper's
  existing `listOrgSsrUpgrades` code path include `created`, `queued`,
  `upgrading`, `done`, `failed`, `cancelled`).
- `targets` (object, required) -- per-bucket arrays of device MAC strings
  with keys `failed`, `queued`, `success`, `upgrading`, each an array of
  unique strings.
- `versions` (object) -- free-form map of `{ device_mac_or_hostname:
  version_string }` describing the intended version per target.

Required path parameters: `org_id` (UUID) and `upgrade_id` (UUID). No query
parameters. No request body.

The critical gotcha from the enriched doc: **despite the `/cancel` URL suffix
this is a GET that returns status, not a cancel action.** The actual cancel
operation is `POST /api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel`,
which lives in a separate file (`POST_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md`)
and is explicitly out of scope for this feature.

**Rationale**:
The enriched doc lists the SDK path as
`mistapi.api.v1.utilities.upgrade.getOrgSsrUpgrade()`, but MistHelper's
existing SSR upgrade caller in `FirmwareManager._fetch_ssr_upgrades_payload`
(MistHelper.py line 19106) uses `mistapi.api.v1.orgs.ssr.listOrgSsrUpgrades`,
which mirrors the OpenAPI URL rather than the tag. Verified pattern: the SDK
generates module paths from URL segments, not from OpenAPI tags. The
spec.md is authoritative and names `mistapi.api.v1.orgs.ssr.upgrade.cancel`,
which matches the URL segments one-for-one. Final verification runs at
implementation time via
`python -c "from mistapi.api.v1.orgs.ssr.upgrade import cancel; help(cancel)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method
   exists, and the existing SSR code path in `FirmwareManager` already uses
   the SDK.
2. *Trust the doc tag and use `mistapi.api.v1.utilities.upgrade`.* Rejected --
   adjacent SSR calls in MistHelper live under `mistapi.api.v1.orgs.ssr.*`
   (URL-based), so the URL path is canonical. The doc's tag-based hint is a
   secondary reference at best.
3. *Reuse `listOrgSsrUpgrades` and filter client-side by `upgrade_id`.*
   Rejected -- wasteful for a single-record lookup and misses the per-target
   detail arrays that only the per-upgrade endpoint returns.

## Research Task 2: Primary Key Strategy

**Decision**:
Two separate output tables, each with its own strategy in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`:

- `org_ssr_upgrade_summary`: **`natural_pk`** on `id` (the API-provided
  upgrade UUID). Secondary indexes on `org_id`, `status`, and `channel`.
- `org_ssr_upgrade_targets`: **`composite_pk`** on
  `(org_id, upgrade_id, bucket, device_mac)`. Secondary indexes on `bucket`
  and `device_mac`. One row per (upgrade, target bucket, device MAC).

The `org_id` value is not returned in the API body but is always known to
MistHelper at call time; the flattener injects it before the upsert. Contrast
with the sibling `listOrgSsrUpgrades` entry at MistHelper.py line 4796 which
uses `auto_increment_with_unique` because the list endpoint returns
truncated per-upgrade records without a stable per-target join key -- the
per-upgrade endpoint returns richer data suitable for a natural PK design.

**Rationale**:
The API-provided `id` on the summary is a stable UUID that MistHelper can
key on directly; using a natural PK gives clean `INSERT OR REPLACE` upsert
semantics when the operator polls the same upgrade twice while it is running.
The targets table needs `org_id` for multi-tenant safety, `upgrade_id` to
join back to the summary, `bucket` because the same MAC can theoretically
appear in different buckets over the upgrade lifecycle (queued -> upgrading
-> success), and `device_mac` because a bucket contains many devices. All
four components are stable business data returned or injected on every poll,
so the composite key is deterministic across polls of the same job.

**Alternatives Considered**:

1. *`auto_increment_with_unique` (mirror `listOrgSsrUpgrades`).* Rejected --
   would let repeated polls of a running job accumulate duplicate rows,
   defeating the upsert semantic required by spec Acceptance Scenario 3.
2. *Single combined table with the four bucket-name lists as text columns.*
   Rejected -- breaks SQL queryability and the flattening convention used
   everywhere else in MistHelper. Operators cannot filter or count devices
   by bucket without parsing embedded JSON.
3. *Composite key `(id, device_mac)` on the targets table without `bucket`
   or `org_id`.* Rejected -- multi-org MistHelper deployments would collide
   across orgs, and dropping `bucket` would silently overwrite the earlier
   state of a device that transitioned between buckets during the upgrade.
4. *`natural_pk` on `id` alone for the targets table.* Rejected -- the
   targets table has many rows per `id`; a natural PK on `id` would
   collapse them to one row.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_ssr_upgrade_<upgrade_id_short>_summary.csv`
- CSV (targets): `data/org_<org_id_short>_ssr_upgrade_<upgrade_id_short>_targets.csv`
- SQLite tables: `org_ssr_upgrade_summary` and `org_ssr_upgrade_targets`
- `org_id_short` and `upgrade_id_short` are each the first 8 hex characters
  of the respective UUIDs (the convention used by adjacent MistHelper
  exports for human-readable filenames that do not leak full UUIDs into
  shell history).
- `api_function_name` argument passed to
  `DataExporter.write_with_format_selection()`:
  - `"getOrgSsrUpgrade"` for the summary row.
  - `"getOrgSsrUpgradeTargets"` for the per-target rows (MistHelper-internal
    identifier for the flattened sub-array; no separate OpenAPI operationId
    exists for this sub-entity, mirroring the pattern used by the reference
    plan for spec 500).

**Rationale**:
Follows the naming pattern used by other per-object exports in MistHelper
that key by both org and object UUID. Two output files / two SQLite tables
keeps the schema normalized and lets an operator query the summary without
joining when they only need job status. The short-UUID convention is already
in use for other license and device exports.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `targets` and `versions` columns.*
   Rejected -- breaks SQL queryability, defeats the multi-backend design of
   `DataExporter`, and would require operators to parse embedded JSON.
2. *Full UUIDs in the filename.* Rejected -- leaks UUIDs into shell history
   and `ls` output. The 8-character short form is enough to disambiguate
   local files.
3. *Concatenate summary and targets into one file with a `record_type`
   column.* Rejected -- forces a heterogeneous schema (many columns are
   summary-only, several are target-only) and breaks the one-entity-per-table
   convention used elsewhere in MistHelper.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting in the Viewers
cluster (92-96 per `.github/copilot-instructions.md` "Menu Categories" table)
and immediately below the Resource Intensive cluster that begins at 97. The
category label is "Interactive Safe -- Viewers -- SSR Upgrade Status". At
`/speckit.tasks` time, `MistHelper.py` is grep'd for the highest currently
allocated menu integer; if 96 is taken by an in-flight branch, the proposal
shifts forward to the next free integer inside the Viewers cluster, and if
none is available it falls back to the safe end of Interactive Safe
(around 133).

**Rationale**:
The endpoint is a lightweight, read-only status query -- there is no
long-running work, no pagination, and no destructive effect (the `/cancel`
URL suffix notwithstanding). Viewers is the correct semantic cluster because
this menu item is a natural companion to the existing SSR-upgrade polling
code in `FirmwareManager` and lets a NOC engineer read status without
running the full "check all SSR upgrades" sweep. Placing it here also keeps
it visually distant from the destructive block at 154-194, which correctly
signals its risk level to a junior NOC engineer scrolling the menu.

**Alternatives Considered**:

1. *Slot inside Destructive (154-194) because the URL contains `cancel`.*
   Rejected -- the endpoint is a GET that returns status. The Destructive
   cluster is reserved for operations that mutate Mist Cloud state. The
   actual cancel operation (POST) will get its own future spec if needed.
2. *Slot inside Resource Intensive (97-101).* Rejected -- one non-paginated
   GET returning a small JSON object does not qualify as resource-intensive.
3. *Append at the end (e.g., 195).* Rejected -- placing a read-only status
   query above the destructive block would visually mis-signal risk level
   to a junior NOC engineer.
4. *Slot in Safe Org Exports (1-59).* Rejected -- that block is bulk export
   territory; a per-object status query is more naturally interactive
   (two prompts).

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID) [Enter for .env default]: "`,
   context: `"org_ssr_upgrade_status:org_id"`. Default: `MIST_ORG_ID` from
   `.env` when present (pressing Enter accepts the default). Validated via
   the existing `is_valid_uuid()` helper before the SDK call; on failure,
   log `WARNING` and return early.
2. `upgrade_id` -- prompt: `"SSR upgrade ID (UUID): "`, context:
   `"org_ssr_upgrade_status:upgrade_id"`. Default: `MIST_SSR_UPGRADE_ID`
   from `.env` when present (optional, primarily useful for the `--test`
   sweep). Also validated by `is_valid_uuid()`; log `WARNING` and return
   early on failure. If the operator needs to discover a valid
   `upgrade_id`, the existing `listOrgSsrUpgrades` menu item lists them.

`.env` values used (loaded by the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_SSR_UPGRADE_ID` -- optional default for prompt 2 (documented in
  `deploy/.env.example` in the same PR).

**Rationale**:
The endpoint is scoped by two path parameters and nothing else -- no site,
no device, no query parameters. Prompting for both is the minimum required
input surface. Defaults from `.env` let the `--test` sweep and repeated
manual polling run without keystrokes. UUID validation before any network
call catches the most common operator mistake (pasting a truncated UUID)
with a clean log line rather than a 400 from the API.

**Alternatives Considered**:

1. *Auto-discover the most-recent upgrade_id by calling `listOrgSsrUpgrades`
   first, then reading its status.* Rejected -- doubles API calls, adds a
   second failure mode, and the calling operator often already knows which
   upgrade they want to inspect (from an ongoing job they scheduled).
2. *Single combined prompt like `"org/upgrade: "` with a slash separator.*
   Rejected -- confusing for junior NOC engineers, hard to fall back to
   `.env` defaults cleanly, and inconsistent with the two-prompt pattern
   used by adjacent per-object menu items.
3. *Skip UUID validation and rely on Mist's 400/404 response.* Rejected --
   burns an API call for a preventable error and produces a less friendly
   log line than the local `is_valid_uuid()` check.
