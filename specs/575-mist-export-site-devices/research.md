# Phase 0 Research: exportSiteDevices

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/sites/GET_sites_site_id_devices_export.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical URL-aligned module path:
`mistapi.api.v1.sites.devices.export.exportSiteDevices(apisession, site_id)`. The
SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed
JSON body. The body is **not** a list of device dicts and is **not** paginated --
it is a single JSON object that wraps a base64-encoded CSV file:

```json
{
  "type": "string",
  "description": "File",
  "contentEncoding": "base64"
}
```

The actual payload value (i.e., the string of base64 characters) lives in the
top-level scalar value of the response. MistHelper must:

1. Pull the base64 string from `response.data` (handling both the literal scalar
   case and the wrapper-object case the doc schema describes).
2. `base64.b64decode()` the string into raw CSV bytes.
3. Decode the bytes as UTF-8 (Mist's CSV exports are UTF-8).
4. Feed the decoded text to `csv.DictReader` to produce a list of row dicts whose
   keys are the CSV header names (typically `name`, `mac`, `serial`, `model`,
   `type`, `hw_rev`, `version`, `site_id`, `status`, and similar device fields).

Required path parameter: `site_id` (UUID string). No query parameters. No request
body.

**Rationale**:
The enriched doc explicitly states "Returns CSV text, not JSON. Parse accordingly."
and gives the wrapper schema above. The mistapi SDK historically generates module
paths from the URL, not the OpenAPI tag -- the spec.md (the authoritative feature
contract) names `mistapi.api.v1.sites.devices.export`, which mirrors the URL path
`/api/v1/sites/{site_id}/devices/export` one-for-one. Final verification happens at
implementation time via `python -c "from mistapi.api.v1.sites.devices import export;
help(export)"` inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/sites/{site_id}/devices/
   export`.* Rejected -- the constitution forbids direct HTTP when a mistapi method
   exists.
2. *Write the base64 blob straight to disk without parsing.* Rejected -- defeats
   the multi-backend export contract. SQLite and ArangoDB cannot query an opaque
   blob, and the per-row upsert behavior required by the spec depends on a flat
   row list.
3. *Use Mist's existing `listSiteDevices` JSON endpoint instead and skip
   `exportSiteDevices`.* Rejected -- the user explicitly requested coverage of
   this missing endpoint, and Mist's server-side export includes serial numbers
   and hardware revision data that `listSiteDevices` may not surface uniformly.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single table `site_device_export`:

- PK = `(site_id, mac)` -- one row per (site, device).
- Type: `composite_pk`.
- Index: `serial` (for fast lookup by device serial number).
- Index: `model` (for fast filtering by model number).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk`. The
`site_id` is injected by MistHelper before the upsert (Mist's CSV export does
include a `site_id` column on each row, but pinning to the user-supplied site_id
guarantees consistency even if the CSV column is ever omitted from a future Mist
release).

**Rationale**:
The endpoint reports a snapshot of the device inventory for a single site.
Re-running the menu item against the same site after, say, a hardware swap must
update the existing row for each device rather than append a duplicate. Device
MAC is globally unique on Mist hardware (it is the hardware factory MAC), but
pairing it with `site_id` in the primary key:

- Mirrors the natural querying pattern ("show me devices in site X").
- Avoids relying on a Mist-supplied column that the doc does not formally
  guarantee.
- Aligns with the composite_pk pattern adjacent endpoints already use for
  site-scoped exports.

`INSERT OR REPLACE` upserts every poll's view of the device inventory.

**Alternatives Considered**:

1. *`natural_pk` on `mac` alone.* Rejected -- a multi-site MistHelper deployment
   would collide rows across sites if a device was ever re-deployed and its MAC
   reused (rare but possible with replacement hardware that inherits a MAC).
2. *`auto_increment_with_unique`.* Rejected -- would let repeated polls
   accumulate duplicate snapshots, defeating the upsert behavior the spec
   requires and bloating the SQLite database over time.
3. *Composite of `(site_id, serial)`.* Rejected -- `mac` is the more universal
   primary key inside MistHelper; other tables (clients, RRM neighbors) join on
   MAC, not serial. Keeping the PK consistent eases future joins.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/site_<site_id_short>_devices_export.csv`
- SQLite table: `site_device_export`
- `site_id_short` is the first 8 hex characters of the site UUID -- the same
  convention used by adjacent site-scoped exports in MistHelper for human-readable
  filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"exportSiteDevices"` (matching the
operationId exactly). The DataExporter uses that string as the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `listSiteDevices` and `searchSiteDevices` (the
two adjacent site-device endpoints). A single output file / single SQLite table
keeps the schema clean because the parsed CSV is already a flat list of device
rows with no nested arrays to split.

**Alternatives Considered**:

1. *Preserve the raw base64 blob as a sidecar file
   (`data/site_<short>_devices_export.raw.b64`).* Rejected -- the blob is purely
   a transport artifact; the parsed rows are the operational data. Sidecar files
   create cleanup burden without operational value.
2. *Full site UUID in the filename.* Rejected -- leaks the site UUID into shell
   history and `ls` output unnecessarily. The short form is enough to
   disambiguate locally and matches the pattern used by adjacent exports.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 72**, sitting at the tail of the
Interactive Safe / Site Devices cluster (60-72), placed immediately after the
existing per-site device listings. The category label is "Interactive Safe --
Site Devices".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges
as: 1-59 Safe Org Exports, 60-96 Interactive Safe (60-72 Site devices, 73-79
Insights, 80-91 Stats, 92-96 Viewers), 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. Per-site device exports
historically live inside the 60-72 block; 72 is the next contiguous integer
below the Insights block at 73, and is far away from the destructive block. The
number is provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd for
the latest allocated menu integer and 72 is shifted forward if a conflict
exists.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at
   194, and placing a read-only site export above the destructive block visually
   mis-signals the risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Safe Org Exports (1-59).* Rejected -- this endpoint is
   site-scoped, not org-scoped, and the Safe Org Exports cluster is reserved for
   `/orgs/{org_id}/...` endpoints. Placement next to `listSiteDevices` is the
   intuitive choice for a NOC engineer.
3. *Slot inside Resource Intensive (97-101).* Rejected -- this is a single GET
   that returns a single CSV file with no pagination and no long-running work.
   It belongs in the safe block.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly one** value via `safe_input()`:

1. `site_id` -- prompt: `"Site ID (UUID): "`, context:
   `"site_device_export:site_id"`. Default: the value of `MIST_SITE_ID` in `.env`
   if present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and
   return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for the prompt.

**Rationale**:
The Mist `exportSiteDevices` endpoint has exactly one path parameter and zero
query parameters. There is no useful per-call toggle (no `detail` flag, no
device-type filter, no time window). Asking the user for anything beyond the
site UUID would be friction without operational value. The `MIST_SITE_ID`
default mirrors the pattern used by every other site-scoped menu item in
MistHelper, so SSH and `--test` invocations work without any keyboard input.

**Alternatives Considered**:

1. *Add a device-type filter prompt (ap / switch / gateway / all).* Rejected --
   the Mist endpoint itself accepts no such filter. Filtering would have to
   happen client-side after the CSV is parsed, which is a separate feature
   (`searchSiteDevices` already covers this).
2. *Add an output filename override prompt.* Rejected -- adds keystrokes without
   operational value. The deterministic filename scheme in Research Task 3
   makes results easy to find under `data/`.
3. *Skip the prompt entirely and always use `MIST_SITE_ID`.* Rejected -- a NOC
   engineer running interactively against multiple sites would have to edit
   `.env` between calls. The prompt-with-default pattern handles both
   interactive and non-interactive cases without code change.
