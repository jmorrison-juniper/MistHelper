# Implementation Plan: downloadSiteRfdiagRecording Menu Item

**Branch**: `574-mist-download-site-rfdiag-recording` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/574-mist-download-site-rfdiag-recording/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download` (operationId
`downloadSiteRfdiagRecording`) to download an RF diagnostics recording blob
(`raw_events`) for a given site and recording ID. Unlike most cataloged read
endpoints, this one returns a binary file (base64-encoded payload) rather than
tabular JSON rows, so the menu item persists the decoded blob to disk under
`data/rfdiags/` AND records a one-row metadata receipt
(`site_id`, `rfdiag_id`, `filename`, `byte_count`, `sha256`, `downloaded_at`)
through `DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all keep a consistent ledger. The user is prompted for
`site_id` and `rfdiag_id` via `safe_input()`; the org context comes from the
existing `mistapi.APISession` loaded from `.env`. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated downloads upsert cleanly. The
operation is proposed as menu number **96** -- the next available slot in the
interactive viewers cluster (92-96) and a natural fit alongside other
single-shot retrieval tools.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transitive transport);
`python-dotenv` (loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`);
`hashlib` and `base64` from the standard library for blob decode and SHA-256
fingerprinting.
**Storage**: Multi-backend through `DataExporter.write_with_format_selection()`
for the metadata receipt row. The binary recording blob itself lands at
`data/rfdiags/<site_id>_<rfdiag_id>.raw` using `os.path.join()` for
Windows-safe paths. SQLite file `data/mist_data.db` is the local fallback;
CSV files land in `data/`; polyglot ArangoDB + Redis containers handle the
graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` will exercise menu 96 with a known
`site_id` and `rfdiag_id` injected via `.env` test variables
(`MIST_TEST_SITE_ID`, `MIST_TEST_RFDIAG_ID`). When those variables are absent
the test stub logs a `WARNING` and exits 0 (the recording ID is per-site and
ephemeral, so the test must be opt-in). Local quality gates remain
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 96 lives outside the
heavy/destructive skip list (14, 18, 63-65, 90-100).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH on port
2200; both must work without code change. The mounted `data/` volume must be
writable (`chmod -R 777 data/` on first run, per the existing data-directory
contract).
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on port 8055. This feature lives entirely in
the CLI.
**Performance Goals**: Single GET completes in <=10 seconds for typical
recordings (a few MB of base64 payload). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; the
endpoint is non-paginated so no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; binary payload is NEVER logged (only its byte count and
SHA-256 hash); all output under `data/`; Windows-safe path joining via
`os.path.join` or `pathlib.Path`.
**Scale/Scope**: One new public menu method (~22 lines) on a new
`RfDiagnosticsManager` class (rationale in the Project Structure section);
one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`; one new SQLite metadata
table (`site_rfdiag_downloads`); one menu registration entry; one README
operation-count bump; one CHANGELOG line. No new third-party dependencies.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `download_site_rfdiag_recording()` stays under 25 lines, takes <=4
  parameters (`self`, `site_id`, `rfdiag_id`, `output_dir`), and contains
  <=5 logical blocks (prompt -> API call -> decode + hash -> write blob ->
  DataExporter call). Hierarchy adds one new class with one public method
  and one private helper (`_persist_blob`); the helper itself is <=15 lines.
  No new packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- A new `RfDiagnosticsManager` class is introduced in
  `MistHelper.py` because no existing class owns the "rfdiags" surface
  (grep on `MistHelper.py` finds zero existing references to `rfdiag`,
  `RFDiag`, or `RfDiag`). The class is the natural home for the family of
  rfdiag endpoints (list, get, start, stop, delete, download) so future
  spec branches can hang sibling methods off it. The menu dispatch in the
  main loop references the class method directly -- no standalone wrapper
  function is introduced. Variable names use full words (`recording_blob`,
  `metadata_row`, `output_path`); no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()`
  with explicit `context=` strings (`"rfdiag_download:site_id"`,
  `"rfdiag_download:rfdiag_id"`) so SSH / container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET);
  the only write is to the local filesystem under `data/rfdiags/` so no
  destructive-confirmation gate is required. Both IDs are validated against
  the Mist UUID regex before the API call; on validation failure the
  method logs a `WARNING` and returns early. API token comes from `.env`
  via `mistapi.APISession` and is never logged. The decoded blob is
  written with `mode="wb"` and 0600-equivalent permissions where the
  underlying filesystem honors them.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `ruff check` -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 downloadSiteRfdiagRecording` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs
  -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `INFO` is emitted before the API call ("Downloading rfdiag
  recording site=%s rfdiag=%s"); `DEBUG` after the call with size summary
  ("Received %d encoded bytes, %d decoded bytes, sha256=%s"); `INFO`
  before the file write ("Writing rfdiag blob to %s"); `WARNING` on 404
  or empty payload; `ERROR` on unexpected exception via
  `logging.exception(...)` with full traceback. No secrets, API tokens,
  full URLs, or raw blob bytes are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new class methods, the
  new `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu
  registration line carries an inline comment that explains *why* the line
  exists, not merely *what* it does. Blank lines, closing parentheses, and
  decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched menu-dispatch block get comments added in the same
  PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after
  pattern: `logging.info(...)` before prompts, `logging.debug(...)` after
  validation; `logging.info(...)` before the SDK call, `logging.debug(...)`
  after with byte counts; `logging.info(...)` before the blob write,
  `logging.debug(...)` after with the final path; `logging.info(...)`
  before `DataExporter.write_with_format_selection()`, `logging.debug(...)`
  after. The DataExporter call already emits its own per-backend log lines;
  the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/574-mist-download-site-rfdiag-recording/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- download_site_rfdiag_recording.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New RfDiagnosticsManager class with download_site_rfdiag_recording()
                         # method + new PK strategy entry + menu 96 registration. No new modules;
                         # same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target
data/rfdiags/            # NEW subdirectory for binary recording blobs; created on first run
                         # via os.makedirs(..., exist_ok=True). One file per download:
                         # <site_id>_<rfdiag_id>.raw
data/mist_data.db        # SQLite file gets a new table `site_rfdiag_downloads` on first run
                         # (created by DataExporter using the new PK strategy entry)
```

**Structure Decision**: Single-file monolith. The new menu item is added as
a public method on a new `RfDiagnosticsManager` class in `MistHelper.py`.
A new class (rather than reusing an existing one) is justified because no
existing class owns the rfdiags surface today and several sibling endpoints
exist (`listSiteRfdiags`, `getSiteRfdiag`, `startSiteRfdiag`,
`stopSiteRfdiag`, `deleteSiteRfdiag`) that will land on the same class in
future spec branches. The menu number proposal is **96**, chosen because
operations 92-96 are the Viewers cluster (per the README menu category
table) and 96 is the next available slot below the resource-intensive
block at 97-101. The full menu list is re-verified at task generation
time; if 96 collides with an in-flight feature branch, the next free
integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks.
  The new class has exactly two methods (one public, one private helper);
  no level-5 hierarchy explosion. The `ENDPOINT_PRIMARY_KEY_STRATEGIES`
  dictionary entry is a single insert against the existing structure.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `RfDiagnosticsManager`. No wrappers introduced. Future sibling rfdiag
  methods will land on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect on Mist Cloud.
  `safe_input()` is the documented prompt path. UUID validation happens
  before the SDK call. The local file write is guarded by
  `os.makedirs(..., exist_ok=True)` and `mode="wb"`.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design
  are ASCII-only with `%s` formatting; the API token, full URL, and raw
  blob bytes never appear in logs.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows
  the expected comment density on every executable line, including the
  PK strategy entry, the file write, and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action
  (prompts, API call, decode, blob write, DataExporter ledger write).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
