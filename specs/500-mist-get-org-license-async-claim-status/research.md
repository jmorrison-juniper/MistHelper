# Phase 0 Research: GetOrgLicenseAsyncClaimStatus

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-28

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_claim_status.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.claim.status.getOrgLicenseAsyncClaimStatus(apisession,
org_id, detail=None)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a list and not
paginated), with the following top-level keys per the doc:

- `status` (string enum: `prepared`, `ongoing`, `done`)
- `total` (int -- devices included in claim)
- `processed` (int -- devices processed so far)
- `succeed` (int -- devices successfully claimed so far)
- `failed` (int -- devices that failed)
- `scheduled_at` (int epoch seconds)
- `timestamp` (number epoch seconds -- response generation time)
- `completed` (array of strings -- MAC addresses already done)
- `incompleted` (array of strings -- MAC addresses still pending)
- `details` (array of objects: `{mac, status, timestamp}` -- per-device detail rows,
  only present when the `detail=true` query parameter is supplied)

Required path parameter: `org_id` (UUID string).
Optional query parameter: `detail` (boolean). When omitted, `details` is absent from the
response.

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.licenses.GetOrgLicenseAsyncClaimStatus()`, but the operationId
appears under the `licenses` tag while the OpenAPI path is `/orgs/{org_id}/claim/status`.
The mistapi SDK historically generates module paths from the URL, not the tag (verified
by inspecting adjacent endpoints under the same path, e.g. `POST /orgs/{org_id}/claim`
which lives in `mistapi.api.v1.orgs.claim`). The spec.md explicitly names
`mistapi.api.v1.orgs.claim.status` and that path matches the URL one-for-one, so we
follow the spec. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs.claim import status; help(status)"` inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/claim/status`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the path implied by the doc tag (`...orgs.licenses...`).* Rejected -- the SDK
   organizes modules by URL path, not OpenAPI tag, and the spec.md (the authoritative
   feature contract) names the URL-based path.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `org_claim_status_summary`: PK = `(org_id, scheduled_at)` -- one row per claim job.
  `scheduled_at` is supplied by the API as the epoch at which the async job was scheduled,
  and is stable across polls of the same job.
- `org_claim_status_details`: PK = `(org_id, scheduled_at, mac)` -- one row per device in
  the `details` array. `mac` is the device MAC address returned by the API.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` for both
tables, with `org_id` injected by MistHelper before the upsert (Mist does not return
`org_id` in the body but MistHelper always knows which org the call targeted).

**Rationale**:
The endpoint reports the *current* state of an async claim job. Re-running the menu item
against the same org while the job is in flight (`status=ongoing`) must update the
existing row rather than append a duplicate. `scheduled_at` is the most reliable stable
identifier per the response schema (`status` and `timestamp` change between polls;
`processed/succeed/failed` change between polls). Pairing `org_id` with `scheduled_at`
guarantees one summary row per job per org, and `(org_id, scheduled_at, mac)` is the
natural key for per-device detail. `INSERT OR REPLACE` upserts every poll's view of the
job state.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls accumulate
   duplicate snapshots, defeating the upsert behavior the spec requires.
2. *Single combined table with all eight summary fields plus `mac`.* Rejected -- when
   `detail=false` there is no `mac`, so a single-table design would require nullable PK
   columns. Splitting into a summary table and a detail table cleanly handles both modes.
3. *`natural_pk` on `scheduled_at` alone.* Rejected -- a single MistHelper deployment may
   target multiple orgs over the same MistHelper instance; `scheduled_at` is not unique
   across orgs.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_claim_status_summary.csv`
- CSV (detail): `data/org_<org_id_short>_claim_status_details.csv`
- SQLite tables: `org_claim_status_summary` and `org_claim_status_details`
- `org_id_short` is the first 8 hex characters of the org UUID -- already the convention
  used by adjacent license exports in MistHelper for human-readable filenames without
  leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getOrgLicenseAsyncClaimStatus"` (matching the operationId). The DataExporter uses
that string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `getOrgLicensesSummary` and `getOrgLicensesBySite`
(the two adjacent license exports). Two output files / two SQLite tables keeps the
schema clean and lets a user query the summary without joining when they don't need
per-device detail.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `details` column.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention used everywhere else in
   MistHelper.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell history
   and ls output unnecessarily. The short form is enough to disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 95**, sitting inside the Safe Org Exports
cluster between the existing license-by-site export (around the 51-94 range) and the
resource-intensive cluster that begins at 96. The category label is "Safe Org Exports --
Licenses".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. License operations historically live
inside the safe-org-export prefix; 95 is the next contiguous integer below the
resource-intensive block at 96, and is far away from the destructive block. The number
is provisional -- at `/speckit.tasks` time, MistHelper.py is grep'd for the latest
allocated menu integer and 95 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194, and
   placing a read-only license check above the destructive block visually mis-signals the
   risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a single GET
   that returns a small JSON object, with no pagination and no long-running work. It
   belongs in the safe block.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_license_claim_status:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter accepts the
   default). Validated via the existing `is_valid_uuid()` helper before the API call;
   on failure, log `WARNING` and return early.
2. `include_detail` -- prompt: `"Include per-device detail? (y/N): "`, context:
   `"org_license_claim_status:detail"`. Default: `N` (no detail). On `y` or `yes`
   (case-insensitive), pass `detail=True` to the SDK.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
Mist's claim status endpoint is org-scoped. Site, device, and template IDs are not
involved. The optional `detail` query parameter materially changes the response shape, so
asking the user keeps the menu item efficient when only the summary is needed (common
poll-the-job case) while still letting an operator capture full per-device detail when
the summary shows failures.

**Alternatives Considered**:

1. *Always request `detail=true` to keep the prompt count to one.* Rejected -- the
   `details` array grows linearly with claim size; for orgs with thousands of devices the
   default poll should be cheap.
2. *Add a third prompt for an output filename override.* Rejected -- adds keystrokes
   without operational value. The deterministic filename scheme in Research Task 3 makes
   results easy to find under `data/`.
