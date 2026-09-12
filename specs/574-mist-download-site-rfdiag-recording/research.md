# Phase 0 Research: downloadSiteRfdiagRecording

## Research Task 1: SDK Function Signature and Behavior

**Decision**: Use
`mistapi.api.v1.sites.rfdiags.download.downloadSiteRfdiagRecording(apisession, site_id, rfdiag_id)`
and treat the returned object as a `mistapi.APIResponse` whose `.data` field
holds the base64-encoded recording payload (per the OpenAPI 200 schema:
`{"type": "string", "description": "File", "contentEncoding": "base64"}`).
The menu method base64-decodes `response.data` and writes the decoded bytes
to `data/rfdiags/<site_id>_<rfdiag_id>.raw`.

**Rationale**: The enriched per-endpoint doc at
`documentation/api/sites/GET_sites_site_id_rfdiags_rfdiag_id_download.md`
explicitly states the response is a base64-encoded file and includes the
"Gotcha" warning: *"Returns binary file data, not JSON. Handle the response
as a file download."* Every other `mistapi` SDK call in MistHelper follows
the `apisession` + path-param positional argument convention, so this
endpoint is no different at the call boundary. The decode step happens in
MistHelper, not in mistapi.

**Alternatives Considered**:

- *Pass the raw response object to `DataExporter` and let it figure out
  binary handling.* Rejected -- `DataExporter` is row-oriented (CSV / SQLite
  tabular / ArangoDB document) and has no contract for binary blobs.
  Forcing it would either base64-encode the blob into a single CSV cell
  (defeats reuse) or silently truncate at the SQLite TEXT/BLOB boundary on
  large recordings.
- *Stream the response directly to disk via the underlying `requests`
  object.* Rejected -- mistapi already buffered the body by the time the
  caller receives the `APIResponse`, so there is no streaming benefit.
  Adding a parallel `requests` path would also bypass the adaptive delay /
  retry instrumentation that lives in the mistapi session wrapper.

## Research Task 2: Primary Key Strategy

**Decision**: Use **composite_pk** with primary key
`['site_id', 'rfdiag_id']` and indexes on `downloaded_at` and `sha256`.
This applies to the *metadata receipt row* persisted via `DataExporter`,
not to the binary blob itself.

**Rationale**: A given `(site_id, rfdiag_id)` pair uniquely identifies one
recording in Mist Cloud. Re-downloading the same recording must upsert
(not insert a duplicate) so the SQLite ledger always reflects the most
recent download attempt. Composite PK matches the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` convention used by sibling time-series
and per-resource entries (e.g. `searchOrgDeviceEvents`). `downloaded_at`
is indexed for historical queries ("show me all rfdiag downloads in the
last 24 hours"); `sha256` is indexed for de-duplication queries ("did we
already download an identical blob under a different rfdiag_id?").

**Alternatives Considered**:

- *natural_pk on `rfdiag_id` alone.* Rejected -- `rfdiag_id` is documented
  as opaque to the caller and is generated per-site by the recording
  start endpoint; there is no documented org-wide uniqueness guarantee,
  so scoping the PK to `(site_id, rfdiag_id)` is safer.
- *auto_increment_with_unique.* Rejected -- the natural composite key is
  stable and meaningful; an auto-increment column would add a synthetic
  ID that the user never references and would complicate idempotent
  re-downloads.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- **Binary blob**: `data/rfdiags/<site_id>_<rfdiag_id>.raw` (one file per
  `(site_id, rfdiag_id)` pair, overwritten on re-download).
- **CSV ledger**: `data/site_rfdiag_downloads.csv` (when CSV backend is
  active).
- **SQLite table**: `site_rfdiag_downloads` (created on first run by
  `DataExporter` using the PK strategy above).
- **api_function_name passed to DataExporter**:
  `"downloadSiteRfdiagRecording"` (matches the operationId, which is the
  key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`).

**Rationale**: Separating the binary payload from the tabular ledger keeps
the SQLite database small (the recording can be many MB), keeps the CSV
human-readable (no inlined base64), and gives the user a predictable
on-disk path to point downstream tooling at. The `data/rfdiags/`
subdirectory is created via `os.makedirs(..., exist_ok=True)` on first
download. The table name matches the existing snake_case convention
used by adjacent `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries.

**Alternatives Considered**:

- *Store the blob inside SQLite as a `BLOB` column.* Rejected -- SQLite
  handles large blobs but page-bloat hurts other queries; filesystem
  storage is simpler and faster for downstream consumers.
- *Use a timestamped filename per download
  (`<site_id>_<rfdiag_id>_<epoch>.raw`).* Rejected -- the upsert
  semantics on `(site_id, rfdiag_id)` would then go stale because the
  ledger row would point at an old filename. Overwriting on re-download
  keeps the disk-state and DB-state consistent. (Users who need
  versioning can copy the file out before re-running the menu item.)

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place the new operation at menu number **96** in the
"Interactive Safe / Viewers" cluster (operations 92-96 per the README
menu category table).

**Rationale**: The README cluster definitions (mirrored in
`.github/copilot-instructions.md`) put operations 92-96 in the
"Viewers" sub-band of "Interactive Safe", which is the right home for
a single-shot retrieval that requires user-supplied identifiers and
returns one artifact (a recording file). Slot 96 is the next free
integer in that band: slots 92-95 are documented as viewers, and the
next cluster (97-101) is "Resource Intensive". The proposal is
re-validated at task-generation time -- if 96 collides with an
in-flight feature branch, the next free integer (97 only if it has
not yet been reassigned, otherwise the cluster boundary is
re-negotiated with the maintainer).

**Alternatives Considered**:

- *Place in 124-127 (Interactive Diagnostics).* Rejected -- that band
  is documented for live-diagnostics tools that initiate a
  WebSocket-style session against the device; this endpoint is a
  one-shot file download, not a streaming diagnostic.
- *Place in 134-135 (Packet captures).* Rejected -- packet captures
  are pcap files produced by a specific capture pipeline; rfdiag
  recordings are RF-environment recordings produced by a different
  Mist subsystem. Co-locating them would mis-imply equivalence.
- *Place in 154-194 (Destructive).* Rejected -- the endpoint is read-only.

## Research Task 5: Required User Prompts (User Input vs .env)

**Decision**: Prompt the user for `site_id` and `rfdiag_id` via
`safe_input()` on every invocation. Do NOT prompt for `org_id` or the
API token; both come from `.env` via the existing
`mistapi.APISession`. Do NOT prompt for an output filename; the
filename is deterministic (see Task 3).

**Rationale**: `rfdiag_id` is per-recording and ephemeral -- the user
must already know it (typically by running the sibling
`listSiteRfdiags` operation first), so it has no sensible default and
must always be a prompt. `site_id` could in principle come from a
session-cached selection, but the current MistHelper convention for
all rfdiag-related sibling endpoints will be "prompt for both", and
following that convention keeps the menu surface predictable. The
`org_id` is not in the path (the endpoint is site-scoped, not
org-scoped) and the `mistapi.APISession` carries the necessary auth
context. Optional prompts (e.g. a custom output directory) are
deferred to a future feature to keep the v1 menu under the 5-Item
Rule.

**Alternatives Considered**:

- *Auto-discover the latest `rfdiag_id` by calling
  `listSiteRfdiags` first.* Rejected -- that is convenient but
  silently couples two endpoints (introducing implicit ordering
  semantics and an extra API call on every invocation). The user
  can explicitly chain the two menu items if they want that flow.
- *Read `site_id` and `rfdiag_id` from `.env` to support fully
  non-interactive use.* Rejected as a default, but the `--test`
  invocation honors `MIST_TEST_SITE_ID` and `MIST_TEST_RFDIAG_ID`
  environment variables when present, falling back to a `WARNING`
  log and a clean exit when absent (see `quickstart.md`).
