# Implementation Plan: ExportSiteDevices Menu Item

**Branch**: `575-mist-export-site-devices` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/575-mist-export-site-devices/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/devices/export` (operationId `exportSiteDevices`) to
download Mist's server-side device inventory export for a single site. Unlike most
adjacent endpoints, this one returns a **base64-encoded CSV file** (not JSON), so the
new method must base64-decode the SDK response, parse it as CSV into a list of row
dictionaries, register the operation in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, and persist
the parsed rows through `DataExporter.write_with_format_selection()` so the CSV,
SQLite, and ArangoDB+Redis backends all receive consistent output. The menu item
prompts the user for a `site_id` via `safe_input()`, defaulting to `MIST_SITE_ID` from
`.env`. The new operation is proposed as menu number **72** -- the next free slot
inside the Interactive Safe / Site Devices cluster (60-72), placed immediately after
the existing per-site device listings so a junior NOC engineer finds it next to the
other site-device exports rather than buried in the resource-intensive block.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); Python standard library `base64` (decode the
returned file payload) and `csv` (parse the decoded text into dict rows); `requests`
(transport, transitive via mistapi); `python-dotenv` (loading `MIST_HOST`,
`MIST_API_TOKEN`, and `MIST_SITE_ID` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; the
polyglot ArangoDB + Redis containers handle the graph + cache backend. The Mist-
generated CSV is *parsed* before write -- MistHelper does not pass the base64 blob
through to the backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using the site UUID configured in `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy/destructive skip list (14, 18, 63-65,
90-100) is unaffected -- new item 72 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both
must work without code change. File paths use `pathlib.Path` / `os.path.join` for
Windows-safe joining.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET completes in <=5 seconds for sites with up to a few
thousand devices (the endpoint is non-paginated and Mist streams a single CSV file).
The adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue to
govern back-off; this endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging (no Unicode/emoji); `safe_input()` for every
prompt; no secrets in logs (API token, base64 blob length only, never the decoded
content at INFO/DEBUG); all output under `data/`; Windows-safe path joining.
**Scale/Scope**: One new public menu method (~25 lines) on the existing
`SiteDeviceExportUtils` class (the same class that owns adjacent per-site device
exports such as `listSiteDevices`), one private helper to decode + parse the CSV,
one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
(`site_device_export`), one menu registration entry, one README operation-count bump,
one CHANGELOG line. No new dependencies (base64 + csv are stdlib), no new modules,
no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_devices()` stays under 25
  lines, takes <=2 parameters (`self`, `site_id`), and contains <=5 logical blocks
  (prompt -> API call -> base64 decode + CSV parse -> flatten rows -> DataExporter
  call). The CSV decode/parse step is extracted to a private helper method
  `_decode_and_parse_device_csv()` on the same class to keep the entrypoint under
  25 lines. Hierarchy is unchanged: two new methods on an existing class, no new
  packages, modules, or top-level constants.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as methods on the existing
  `SiteDeviceExportUtils` class (the same class that owns the related
  `listSiteDevices` and `searchSiteDevices` exports). No standalone wrapper function
  is introduced. The menu dispatch in the main loop references the class method
  directly. Variable names use full words (`decoded_bytes`, `device_rows`,
  `csv_reader`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with an
  explicit `context="site_device_export:site_id"` string so SSH / container EOF
  exits cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. The `site_id`
  is validated against the Mist UUID shape (`is_valid_uuid()`) before the API call;
  on failure the method logs a `WARNING` and returns early. The API token comes
  from `.env` via the existing `mistapi.APISession` and is never logged. The
  base64 blob is decoded into memory and is never written to the log -- only its
  length in bytes is recorded at DEBUG.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 72
  exportSiteDevices` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Exporting devices for site %s"); `DEBUG` after
  the call with the base64 blob length only ("Received %d bytes of base64 payload");
  `INFO` before CSV decode ("Decoding base64 payload"); `DEBUG` after with row
  count ("Parsed %d device rows from CSV"); `WARNING` on 404 / empty payload;
  `ERROR` on base64 / CSV parse failure via `logging.exception`. No secrets,
  tokens, request URLs, or decoded CSV content are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in both new methods, the new PK
  strategy dictionary entry, and the menu registration line carries an inline
  comment explaining *why* the line exists, not merely what it does. Blank lines,
  closing parentheses, and decorators are exempt per the constitution. Any
  previously uncommented adjacent lines in the touched block (the existing
  site-device export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the prompt, after the prompt, before the SDK call,
  before the base64 decode, before the CSV parse, before each DataExporter write;
  matching `logging.debug(...)` after each step with a result summary (byte count,
  row count). The DataExporter call emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/575-mist-export-site-devices/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - parsed CSV row entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- export_site_devices.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # Two new methods on SiteDeviceExportUtils class + PK strategy
                         # entry + menu 72 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 72
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 72 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `SiteDeviceExportUtils` class in `MistHelper.py` (the
same class that owns the other site-scoped device exports). The menu number proposal
is **72**, chosen because operations 60-72 form the Interactive Safe / Site Devices
cluster and 72 is the next available slot below the Insights cluster that begins at
73. The full menu list will be re-verified at task generation time; if 72 collides
with an in-flight feature branch, the next free integer inside the same cluster is
used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines for the entrypoint and <=25 lines for the
  CSV decode/parse helper, <=2 parameters on the entrypoint, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary receives a single insert; no
  level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `SiteDeviceExportUtils`. No wrappers introduced. The CSV decode/parse helper is
  a private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms GET
  only, no destructive side effect. `safe_input()` is the documented prompt path.
  UUID validation happens before the SDK call. The base64 payload size is bounded
  by Mist API response limits; MistHelper does not log payload content.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or decoded CSV
  content.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, base64
  decode, CSV parse, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
